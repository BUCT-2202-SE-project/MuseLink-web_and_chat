from flask import Flask, request, jsonify, session
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import re
from neo4j import GraphDatabase
from pypinyin import  lazy_pinyin
import random
import os
import glob
import requests, json, time, pymysql
from flask import Blueprint, request, current_app, Response, stream_with_context, jsonify,session
from utils.db import neo4j_conn
from utils.utils import extract_entity_attributes, error_response, save_qa_record,get_history_context,build_chat_context,enhance_query_with_llm,extract_limit_from_attr
from utils.db import get_db
from qa.RAG.RAG import search_similar_knowledge, build_prompt, classify_question_with_gpt, answer_statistical_question
from openai import OpenAI
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
CORS(app, supports_credentials=True)

def get_db_connection():
    return mysql.connector.connect(
        host='123.56.94.39',
        user='cs2202',
        password='',
        database='data',
        charset='utf8mb4'
    )

def get_local_db_connection():
    return mysql.connector.connect(
        host='123.56.94.39',
        user='cs2202',
        password='',
        database='data',
        charset='utf8mb4'
    )

# 文物
@app.route('/api/artifacts', methods=['GET'])
def get_artifacts():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "数据库连接失败"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        query = 'SELECT * FROM relic WHERE Image != "未知"'
        conditions = []
        params = []

        search_params = request.args

        # 处理排序 (拼音排序，中文排在英文之前)
        sort_order = search_params.get('sort', 'asc')
        order_by_clause = "ORDER BY Title " + ("ASC" if sort_order == 'asc' else "DESC")

        # 处理其他查询条件
        field_mapping = {
            'title': 'Title',
            'artist': 'Artist',
            'period': 'Period',
            'museum': 'Museum',
            'descripe': 'descripe'
        }

        for param, field in field_mapping.items():
            if param in search_params:
                values = [v.strip() for v in search_params[param].split(',') if v.strip()]
                if values:
                    field_conditions = []
                    for value in values:
                        field_conditions.append(f"{field} LIKE %s")
                        params.append(f"%{value}%")
                    conditions.append(f"({' AND '.join(field_conditions)})")

        # 处理通用搜索
        if 'q' in search_params:
            search_term = f"%{search_params['q']}%"
            or_conditions = [
                "Title LIKE %s",
                "Artist LIKE %s",
                "Period LIKE %s",
                "Museum LIKE %s",
                "descripe LIKE %s"
            ]
            conditions.append(f"({' OR '.join(or_conditions)})")
            params.extend([search_term] * 5)

        if conditions:
            query += " AND " + " AND ".join(conditions)

        # 获取数据
        cursor.execute(query, params)
        artifacts = cursor.fetchall()


        def sort_by_title(item):
            title = item['Title']

            if any('\u4e00' <= char <= '\u9fff' for char in title):  # 判断中文字符
                return ''.join(lazy_pinyin(title))  # 转换为拼音
            else:
                return title
        artifacts.sort(key=lambda x: (any('\u4e00' <= char <= '\u9fff' for char in x['Title']), sort_by_title(x)), reverse=(sort_order == 'desc'))

        return jsonify(artifacts)

    except Exception as e:
        print(f"查询错误: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/artifact/<artifact_id>', methods=['GET'])
def get_artifact_detail(artifact_id):
    # 连接远程数据库获取文物数据
    remote_conn = get_db_connection()
    if not remote_conn:
        return jsonify({"error": "远程数据库连接失败"}), 500

    remote_cursor = remote_conn.cursor(dictionary=True)

    try:
        # 1. 查询文物详情
        remote_cursor.execute('SELECT * FROM relic WHERE `Object ID` = %s', (artifact_id,))
        artifact = remote_cursor.fetchone()

        if not artifact:
            return jsonify({"error": "文物不存在"}), 404

        # 2. 查询相关文物（同一作者或标题50%相同）
        related_artifacts = []

        # 如果作者不为"未知"，则查找同一作者的文物
        if artifact.get('Artist') and artifact['Artist'] != '未知':
            remote_cursor.execute(
                'SELECT `Object ID`, Title, Artist, Period, Museum, Image FROM relic WHERE Artist = %s AND `Object ID` != %s LIMIT 6',
                (artifact['Artist'], artifact_id))
            related_artifacts = remote_cursor.fetchall()
        # 如果没有找到相关文物，进行标题50%字符匹配
        if not related_artifacts:
            search_title = artifact['Title']
            min_match_length = max(1, len(search_title) // 2)  # 至少匹配50%的字符
            remote_cursor.execute(
                'SELECT `Object ID`, Title, Artist, Period, Museum, Image FROM relic WHERE `Object ID` != %s',
                (artifact_id,))
            all_artifacts = remote_cursor.fetchall()
            for candidate in all_artifacts:
                candidate_title = candidate['Title']
                if not candidate_title:
                    continue
                # 计算最长公共子串长度
                def lcs_length(s1, s2):
                    m = len(s1)
                    n = len(s2)
                    dp = [[0] * (n + 1) for _ in range(m + 1)]
                    max_len = 0
                    for i in range(1, m + 1):
                        for j in range(1, n + 1):
                            if s1[i - 1] == s2[j - 1]:
                                dp[i][j] = dp[i - 1][j - 1] + 1
                                if dp[i][j] > max_len:
                                    max_len = dp[i][j]
                            else:
                                dp[i][j] = 0
                    return max_len

                match_length = lcs_length(search_title, candidate_title)
                if match_length >= min_match_length:
                    related_artifacts.append(candidate)
                    if len(related_artifacts) >= 20:
                        break
        # 如果相关文物不足，补充来自同一个博物馆的文物
        if len(related_artifacts) < 20 and artifact.get('Museum'):
            remote_cursor.execute(
                'SELECT `Object ID`, Title, Artist, Period, Museum, Image FROM relic WHERE Museum = %s AND `Object ID` != %s LIMIT 20',
                (artifact['Museum'], artifact_id))
            museum_artifacts = remote_cursor.fetchall()

            remaining_count = 20 - len(related_artifacts)
            if museum_artifacts:
                random_artifacts = random.sample(museum_artifacts, min(remaining_count, len(museum_artifacts)))
                related_artifacts.extend(random_artifacts)

        # 3. 连接本地数据库查询互动状态（点赞和收藏）
        local_conn = get_local_db_connection()
        if not local_conn:
            return jsonify({"error": "本地数据库连接失败"}), 500

        local_cursor = local_conn.cursor(dictionary=True)

        # 获取点赞总数
        local_cursor.execute("SELECT COUNT(*) as count FROM likes WHERE artifact_id = %s", (artifact_id,))
        like_count = local_cursor.fetchone()['count']

        # 获取收藏总数
        local_cursor.execute("SELECT COUNT(*) as count FROM collection WHERE artifact_id = %s", (artifact_id,))
        collect_count = local_cursor.fetchone()['count']

        # 初始化互动状态
        interaction = {
            "likeCount": like_count,
            "collectCount": collect_count,
            "isLiked": False,
            "isCollected": False
        }

        # 检查当前用户是否点赞/收藏（如果已登录）
        if 'user_id' in session:
            # 检查点赞状态
            local_cursor.execute("SELECT * FROM likes WHERE user_id = %s AND artifact_id = %s",
                                 (session['user_id'], artifact_id))
            interaction['isLiked'] = local_cursor.fetchone() is not None

            # 检查收藏状态
            local_cursor.execute("SELECT * FROM collection WHERE user_id = %s AND artifact_id = %s",
                                 (session['user_id'], artifact_id))
            interaction['isCollected'] = local_cursor.fetchone() is not None

        local_cursor.close()
        local_conn.close()

        return jsonify({
            "success": True,
            "artifact": artifact,
            "related": related_artifacts,
            "interaction": interaction
        })

    except Exception as e:
        print(f"查询错误: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if remote_conn.is_connected():
            remote_cursor.close()
            remote_conn.close()


@app.route('/api/likes/toggle', methods=['POST'])
def toggle_like():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    data = request.get_json()
    artifact_id = data.get('artifact_id')
    if not artifact_id:
        return jsonify({'success': False, 'message': '缺少文物ID'}), 400
    conn = get_local_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': '本地数据库连接失败'}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM likes WHERE user_id = %s AND artifact_id = %s",(session['user_id'], artifact_id))
        existing_like = cursor.fetchone()
        if existing_like:
            cursor.execute("DELETE FROM likes WHERE user_id = %s AND artifact_id = %s",(session['user_id'], artifact_id))
            message = '已取消点赞'
            is_liked = False
        else:
            cursor.execute("INSERT INTO likes (user_id, artifact_id) VALUES (%s, %s)",(session['user_id'], artifact_id))
            message = '点赞成功'
            is_liked = True
        cursor.execute("SELECT COUNT(*) as count FROM likes WHERE artifact_id = %s", (artifact_id,))
        like_count = cursor.fetchone()[0]
        conn.commit()

        return jsonify({
            'success': True,
            'isLiked': is_liked,
            'likeCount': like_count,
            'message': message
        })
    except Exception as e:
        conn.rollback()
        print(f"点赞操作错误: {e}")
        return jsonify({'success': False, 'message': '操作失败'}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/collection/toggle', methods=['POST'])
def toggle_collect():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    data = request.get_json()
    artifact_id = data.get('artifact_id')

    if not artifact_id:
        return jsonify({'success': False, 'message': '缺少文物ID'}), 400

    conn = get_local_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': '本地数据库连接失败'}), 500

    cursor = conn.cursor()

    try:
        # 检查是否已收藏
        cursor.execute("SELECT * FROM collection WHERE user_id = %s AND artifact_id = %s",
                       (session['user_id'], artifact_id))
        existing_collect = cursor.fetchone()

        if existing_collect:
            # 取消收藏
            cursor.execute("DELETE FROM collection WHERE user_id = %s AND artifact_id = %s",
                           (session['user_id'], artifact_id))
            message = '已取消收藏'
            is_collected = False
        else:
            # 添加收藏
            cursor.execute(
                "INSERT INTO collection (user_id, artifact_id, collect_time) VALUES (%s, %s, NOW())",
                (session['user_id'], artifact_id)
            )
            message = '收藏成功'
            is_collected = True

        # 获取新的收藏总数
        cursor.execute("SELECT COUNT(*) as count FROM collection WHERE artifact_id = %s", (artifact_id,))
        collect_count = cursor.fetchone()[0]

        conn.commit()

        return jsonify({
            'success': True,
            'isCollected': is_collected,
            'collectCount': collect_count,
            'message': message
        })
    except Exception as e:
        conn.rollback()
        print(f"收藏操作错误: {e}")
        return jsonify({'success': False, 'message': '操作失败'}), 500
    finally:
        cursor.close()
        conn.close()

# 登陆注册
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not all([username, password, email]):
        return jsonify({'success': False, 'message': '所有字段都是必填的'}), 400
    if len(username) < 4 or len(username) > 50:
        return jsonify({'success': False, 'message': '用户名长度应在4-50个字符之间'}), 400
    if len(password) < 8:
        return jsonify({'success': False, 'message': '密码长度至少为8个字符'}), 400
    if not is_valid_email(email):
        return jsonify({'success': False, 'message': '邮箱格式不正确'}), 400
    try:
        connection = get_local_db_connection()
        cursor = connection.cursor(dictionary=True)

        # 检查用户名是否已存在
        cursor.execute("SELECT * FROM user WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '用户名已存在'}), 400

        # 检查邮箱是否已存在
        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '邮箱已被注册'}), 400

        # 加密密码
        hashed_password = generate_password_hash(password)

        # 插入新用户
        cursor.execute(
            "INSERT INTO user (username, password, email) VALUES (%s, %s, %s)",
            (username, hashed_password, email)
        )
        connection.commit()

        # 获取新用户信息
        cursor.execute("SELECT user_id, username, email, permission_status FROM user WHERE user_id = %s", (cursor.lastrowid,))
        new_user = cursor.fetchone()

        return jsonify({
            'success': True,
            'message': '注册成功',
            'user': new_user
        }), 201

    except Exception as e:
        print(f"注册错误: {str(e)}")
        return jsonify({'success': False, 'message': '注册失败，请稍后再试'}), 500

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username_or_email = data.get('username_or_email')
    password = data.get('password')

    if not all([username_or_email, password]):
        return jsonify({'success': False, 'message': '用户名/邮箱和密码都是必填的'}), 400

    try:
        connection = get_local_db_connection()
        cursor = connection.cursor(dictionary=True)

        # 查询用户（支持用户名或邮箱登录）
        query = "SELECT * FROM user WHERE username = %s OR email = %s"
        cursor.execute(query, (username_or_email, username_or_email))
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': '用户名或邮箱不存在'}), 401
        # 验证密码
        if not check_password_hash(user['password'], password):
            return jsonify({'success': False, 'message': '密码错误'}), 401
        # 检查用户状态
        if user['permission_status'] != '正常':
            return jsonify({'success': False, 'message': '账户受限，请联系管理员'}), 403
        # 设置会话
        session['user_id'] = user['user_id']
        session['username'] = user['username']

        # 返回用户信息（不包含密码）
        user_data = {
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'permission_status': user['permission_status']
        }

        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': user_data
        })

    except Exception as e:
        print(f"登录错误: {str(e)}")
        return jsonify({'success': False, 'message': '登录失败，请稍后再试'}), 500

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': '登出成功'})
#导航栏
@app.route('/api/user', methods=['GET'])
def get_current_user():
    for key, value in request.cookies.items():
        print(f"{key}: {value}")
    print(1)
    if 'user_id' not in session:
        # 如果用户未登录，返回未登录状态

        print("用户未登录")
        return jsonify({'success': False, 'message': '未登录'}), 401

    try:
        print("user_id:", session['user_id'])
        connection = get_local_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_id, username, email, register_time, permission_status FROM user WHERE user_id = %s",
            (session['user_id'],)
        )
        user = cursor.fetchone()

        if not user:
            session.clear()
            return jsonify({'success': False, 'message': '用户不存在'}), 404

        return jsonify({
            'success': True,
            'user': user
        })

    except Exception as e:
        print(f"获取用户信息错误: {str(e)}")
        return jsonify({'success': False, 'message': '获取用户信息失败'}), 500

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


#获取用户点赞的文物
@app.route('/api/user/likes', methods=['GET'])
def get_user_likes():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    local_conn = get_local_db_connection()
    if not local_conn:
        return jsonify({'success': False, 'message': '本地数据库连接失败'}), 500

    remote_conn = get_db_connection()
    if not remote_conn:
        return jsonify({'success': False, 'message': '远程数据库连接失败'}), 500

    local_cursor = local_conn.cursor(dictionary=True)
    remote_cursor = remote_conn.cursor(dictionary=True)

    try:
        # 获取用户点赞的文物ID列表
        local_cursor.execute("SELECT artifact_id FROM likes WHERE user_id = %s ORDER BY like_id DESC",
                             (session['user_id'],))
        liked_artifact_ids = [item['artifact_id'] for item in local_cursor.fetchall()]

        if not liked_artifact_ids:
            return jsonify({'success': True, 'data': []})

        # 获取文物详情
        placeholders = ', '.join(['%s'] * len(liked_artifact_ids))
        query = f"SELECT * FROM relic WHERE `Object ID` IN ({placeholders})"
        remote_cursor.execute(query, liked_artifact_ids)
        liked_artifacts = remote_cursor.fetchall()


        artifact_map = {item['Object ID']: item for item in liked_artifacts}
        ordered_artifacts = [artifact_map[id] for id in liked_artifact_ids if id in artifact_map]

        return jsonify({
            'success': True,
            'data': ordered_artifacts
        })
    except Exception as e:
        print(f"获取点赞列表错误: {e}")
        return jsonify({'success': False, 'message': '获取点赞列表失败'}), 500
    finally:
        if local_conn.is_connected():
            local_cursor.close()
            local_conn.close()
        if remote_conn.is_connected():
            remote_cursor.close()
            remote_conn.close()


# 获取用户收藏的文物
@app.route('/api/user/collections', methods=['GET'])
def get_user_collections():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    local_conn = get_local_db_connection()
    if not local_conn:
        return jsonify({'success': False, 'message': '本地数据库连接失败'}), 500

    remote_conn = get_db_connection()
    if not remote_conn:
        return jsonify({'success': False, 'message': '远程数据库连接失败'}), 500

    local_cursor = local_conn.cursor(dictionary=True)
    remote_cursor = remote_conn.cursor(dictionary=True)

    try:
        # 获取用户收藏的文物ID列表
        local_cursor.execute("""
            SELECT artifact_id, collect_time 
            FROM collection 
            WHERE user_id = %s 
            ORDER BY collect_time DESC
        """, (session['user_id'],))
        collected_items = local_cursor.fetchall()
        collected_artifact_ids = [item['artifact_id'] for item in collected_items]
        collect_times = {item['artifact_id']: item['collect_time'] for item in collected_items}

        if not collected_artifact_ids:
            return jsonify({'success': True, 'data': []})

        # 从远程数据库获取文物详情
        placeholders = ', '.join(['%s'] * len(collected_artifact_ids))
        query = f"SELECT * FROM relic WHERE `Object ID` IN ({placeholders})"
        remote_cursor.execute(query, collected_artifact_ids)
        collected_artifacts = remote_cursor.fetchall()

        # 添加收藏时间并保持原始顺序
        artifact_map = {item['Object ID']: item for item in collected_artifacts}
        ordered_artifacts = []
        for id in collected_artifact_ids:
            if id in artifact_map:
                artifact = artifact_map[id]
                artifact['collect_time'] = collect_times[id]
                ordered_artifacts.append(artifact)

        return jsonify({
            'success': True,
            'data': ordered_artifacts
        })
    except Exception as e:
        print(f"获取收藏列表错误: {e}")
        return jsonify({'success': False, 'message': '获取收藏列表失败'}), 500
    finally:
        if local_conn.is_connected():
            local_cursor.close()
            local_conn.close()
        if remote_conn.is_connected():
            remote_cursor.close()
            remote_conn.close()


# 更新用户基本信息
@app.route('/api/user/update', methods=['POST'])
def update_user_info():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    data = request.get_json()
    username = data.get('username')
    email = data.get('email')

    if not username or not email:
        return jsonify({'success': False, 'message': '用户名和邮箱不能为空'}), 400

    conn = get_local_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500

    cursor = conn.cursor()
    try:
        # 检查用户名是否已被其他用户使用
        cursor.execute("SELECT user_id FROM user WHERE username = %s AND user_id != %s",
                       (username, session['user_id']))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '用户名已被使用'}), 400
        # 检查邮箱是否已被其他用户使用
        cursor.execute("SELECT user_id FROM user WHERE email = %s AND user_id != %s",
                       (email, session['user_id']))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '邮箱已被使用'}), 400
        # 更新用户信息
        cursor.execute("""
            UPDATE user 
            SET username = %s, email = %s 
            WHERE user_id = %s
        """, (username, email, session['user_id']))
        conn.commit()
        # 更新session中的用户名
        session['username'] = username

        return jsonify({
            'success': True,
            'message': '用户信息更新成功'
        })
    except Exception as e:
        conn.rollback()
        print(f"更新用户信息错误: {e}")
        return jsonify({'success': False, 'message': '更新用户信息失败'}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# 上传用户头像（使用本地文件系统）
from flask import send_from_directory

@app.route('/avatar/<filename>')
def get_avatar(filename):
    return send_from_directory('avatar', filename)

@app.route('/api/user/avatar', methods=['POST'])
def upload_avatar():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'}), 400

    # 检查文件类型
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        return jsonify({'success': False, 'message': '只支持图片文件(png, jpg, jpeg, gif)'}), 400

    try:
        from PIL import Image
        import io

        # 确保头像目录存在
        avatar_dir = os.path.join('avatar')
        if not os.path.exists(avatar_dir):
            os.makedirs(avatar_dir)

        # 删除旧的头像文件（如果有）
        old_files = glob.glob(os.path.join(avatar_dir, f"{session['user_id']}.*"))
        for old_file in old_files:
            try:
                os.remove(old_file)
            except OSError:
                pass

        # 读取图片并转换为PNG格式
        img = Image.open(file.stream)
        img = img.convert("RGB")  # 确保图片是RGB模式
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # 保存新头像文件
        filename = f"{session['user_id']}.png"
        filepath = os.path.join(avatar_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(img_byte_arr)

        # 返回头像URL
        avatar_url = f"/avatar/{filename}"

        return jsonify({
            'success': True,
            'avatarUrl': avatar_url,
            'message': '头像上传成功'
        })
    except Exception as e:
        print(f"上传头像错误: {e}")
        return jsonify({'success': False, 'message': '上传头像失败'}), 500
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'}), 400

    # 检查文件类型
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        return jsonify({'success': False, 'message': '只支持图片文件(png, jpg, jpeg, gif)'}), 400

    try:
        # 确保头像目录存在
        avatar_dir = os.path.join('avatar')
        if not os.path.exists(avatar_dir):
            os.makedirs(avatar_dir)

        # 删除旧的头像文件（如果有）
        old_files = glob.glob(os.path.join(avatar_dir, f"{session['user_id']}.*"))
        for old_file in old_files:
            try:
                os.remove(old_file)
            except OSError:
                pass

        # 获取文件扩展名
        _, ext = os.path.splitext(file.filename)
        # 保存新头像文件
        filename = f"{session['user_id']}{ext.lower()}"
        filepath = os.path.join(avatar_dir, filename)
        file.save(filepath)

        # 返回头像URL
        avatar_url = f"/avatar/{filename}"

        return jsonify({
            'success': True,
            'avatarUrl': avatar_url,
            'message': '头像上传成功'
        })
    except Exception as e:
        print(f"上传头像错误: {e}")
        return jsonify({'success': False, 'message': '上传头像失败'}), 500



NEO4J_URI = "bolt://123.56.94.39:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4j2202"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


@app.route('/api/museums', methods=['GET'])
def get_museums():
    museums = [
        {"name": "大都会博物馆"},
        {"name": "宾夕法尼亚大学考古与人类学博物馆"},
        {"name": "克利夫兰博物馆"}
    ]
    return jsonify(museums)


@app.route('/api/graph', methods=['GET'])
def get_graph():
    museum_name = request.args.get('museum_name')
    display_type = request.args.get('display_type')

    if not museum_name:
        return jsonify({"error": "museum_name is required"}), 400

    # 初始化查询和参数
    query = ""
    params = {"museum_name": museum_name}

    try:
        # 全部展示的查询
        if display_type == 'all':
            query = """
            MATCH (m:Museum {name: $museum_name})-[r1:包含]->(a:Artifact)
            OPTIONAL MATCH (a)-[r2:年代]->(p:Period)
            OPTIONAL MATCH (a)-[r3:作者]->(artist:Artist)
            RETURN m, r1, a, r2, p, r3, artist
            LIMIT 50
            """
        # 节点类型查询
        elif display_type in ["Artifact", "Artist", "Period"]:
            if display_type == "Artifact":
                query = """
                MATCH (m:Museum {name: $museum_name})-[:包含]->(a:Artifact)
                RETURN a as node, 'Artifact' as type
                LIMIT 50
                """
            elif display_type == "Artist":
                query = """
                MATCH (m:Museum {name: $museum_name})-[:包含]->(:Artifact)-[:作者]->(ar:Artist)
                RETURN ar as node, 'Artist' as type
                LIMIT 50
                """
            elif display_type == "Period":
                query = """
                MATCH (m:Museum {name: $museum_name})-[:包含]->(:Artifact)-[:年代]->(p:Period)
                RETURN p as node, 'Period' as type
                LIMIT 50
                """
        # 关系类型查询
        elif display_type in ["包含", "作者", "年代"]:
            if display_type == "包含":
                query = """
                MATCH (m:Museum {name: $museum_name})-[r:包含]->(a:Artifact)
                RETURN m as source, a as target, r as relation, '包含' as type
                LIMIT 50
                """
            elif display_type == "作者":
                query = """
                MATCH (m:Museum {name: $museum_name})-[:包含]->(a:Artifact)-[r:作者]->(ar:Artist)
                RETURN a as source, ar as target, r as relation, '作者' as type
                LIMIT 50
                """
            elif display_type == "年代":
                query = """
                MATCH (m:Museum {name: $museum_name})-[:包含]->(a:Artifact)-[r:年代]->(p:Period)
                RETURN a as source, p as target, r as relation, '年代' as type
                LIMIT 50
                """
        else:
            return jsonify({"error": "Invalid display_type"}), 400

        with driver.session() as session:
            result = session.run(query, params)
            nodes = []
            links = []

            for record in result:
                if display_type == 'all':
                    # 处理全部展示的复杂查询结果
                    m = record['m']
                    a = record['a']
                    r1 = record['r1']
                    # 博物馆节点
                    nodes.append({
                        "id": f"museum_{m.get('name')}",
                        "name": m.get('name'),
                        "type": "Museum",
                        "properties": dict(m)
                    })
                    # 文物节点
                    nodes.append({
                        "id": f"artifact_{a.get('id')}",
                        "name": a.get('title'),
                        "type": "Artifact",
                        "properties": dict(a)
                    })
                    # 包含关系
                    links.append({
                        "source": f"museum_{m.get('name')}",
                        "target": f"artifact_{a.get('id')}",
                        "type": "包含",
                        "properties": dict(r1)
                    })
                    # 年代节点和关系
                    if record['p']:
                        p = record['p']
                        r2 = record['r2']
                        nodes.append({
                            "id": f"period_{p.get('period')}",
                            "name": p.get('period'),
                            "type": "Period",
                            "properties": dict(p)
                        })
                        links.append({
                            "source": f"artifact_{a.get('id')}",
                            "target": f"period_{p.get('period')}",
                            "type": "年代",
                            "properties": dict(r2)
                        })
                    # 作者节点和关系
                    if record['artist']:
                        artist = record['artist']
                        r3 = record['r3']
                        nodes.append({
                            "id": f"artist_{artist.get('name')}",
                            "name": artist.get('name'),
                            "type": "Artist",
                            "properties": dict(artist)
                        })
                        links.append({
                            "source": f"artifact_{a.get('id')}",
                            "target": f"artist_{artist.get('name')}",
                            "type": "作者",
                            "properties": dict(r3)
                        })
                elif display_type in ["Artifact", "Artist", "Period"]:
                    # 处理节点查询结果
                    node = record['node']
                    node_id = node.get('id') or node.get('name') or node.get('period')
                    node_name = node.get('title') or node.get('name') or node.get('period')

                    nodes.append({
                        "id": f"{display_type.lower()}_{node_id}",
                        "name": node_name,
                        "type": display_type,
                        "properties": dict(node)
                    })

                elif display_type in ["包含", "作者", "年代"]:
                    # 处理关系查询结果
                    source = record['source']
                    target = record['target']

                    # 处理source节点
                    if 'name' in source:  # 博物馆节点
                        source_id = f"museum_{source.get('name')}"
                        source_type = "Museum"
                        source_name = source.get('name')
                    else:  # 文物节点
                        source_id = f"artifact_{source.get('id')}"
                        source_type = "Artifact"
                        source_name = source.get('title')

                    # 处理target节点
                    if 'period' in target:  # 时期节点
                        target_id = f"period_{target.get('period')}"
                        target_type = "Period"
                        target_name = target.get('period')
                    else:  # 作者节点
                        target_id = f"artist_{target.get('name')}"
                        target_type = "Artist"
                        target_name = target.get('name')

                    # 添加节点
                    nodes.append({
                        "id": source_id,
                        "name": source_name,
                        "type": source_type,
                        "properties": dict(source)
                    })

                    nodes.append({
                        "id": target_id,
                        "name": target_name,
                        "type": target_type,
                        "properties": dict(target)
                    })

                    # 添加关系
                    links.append({
                        "source": source_id,
                        "target": target_id,
                        "type": display_type,
                        "properties": dict(record['relation'])
                    })

            # 节点去重
            unique_nodes = {}
            for node in nodes:
                unique_nodes[node['id']] = node

            return jsonify({
                "nodes": list(unique_nodes.values()),
                "links": links
            })

    except Exception as e:
        print(f"Error executing query: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/qa/getHistoryList', methods=['GET'])
# @token_required
def getHistoryList():
    
    # user_id = session['user_id']
    
    # data = request.get_json()
    # user_id = data.get('userId')
    user_id = request.args.get('userId')
    print(user_id)

    # 参数校验
    if not user_id or not user_id.isdigit():
        return error_response(message="用户ID无效", http_status=400)
    
    conn = get_db()
    try:
        user_id = int(user_id)

        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                "SELECT history_id, history_name FROM history_list WHERE user_id = %s order by create_time desc" ,
                (user_id,)
            )
            rows = cursor.fetchall()

            # data = [
            #     {
            #         "historyId": row["history_id"], 
            #         "historyName": row["history_name"] 
            #     }
            #     for _, row in enumerate(rows)
            # ]
          # 更安全的方式处理可能的元组或字典
            data = []
            for _, row in enumerate(rows):
                if isinstance(row, dict):
                    # 如果是字典，使用键访问
                    data.append({
                        "historyId": row["history_id"],
                        "historyName": row["history_name"]
                    })
                else:
                    # 如果是元组，使用索引访问
                    data.append({
                        "historyId": row[0],  
                        "historyName": row[1]
                    })
        return jsonify({
            "code": 0,
            "message": "操作成功",
            "data": data
        })

    except Exception as e:
        print(f"[ERROR] {e}")
        return error_response(message="服务器内部错误", http_status=500)
    finally:
        conn.close()

@app.route('/api/qa/getHistoryInfo', methods=['GET'])
# @token_required
def getHistoryInfo():
    history_id = request.args.get('historyId', type=int)
    print("history_id:", history_id)

    if not history_id:
        return error_response(message="缺少参数：historyId", http_status=400)

    conn = get_db()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                "SELECT question, answer, reference "
                "FROM history WHERE history_id = %s "
                "ORDER BY create_time ASC", (history_id,)
            )

            results = cursor.fetchall()
        print("查询结果：", results)
        return jsonify({
            "code": 0,
            "message": "操作成功",
            "data": results
        })

    except Exception as e:
        print("查询异常：", e)
        return error_response(message="服务器内部错误", http_status=500)

@app.route('/api/qa/create', methods=['POST'])
# @token_required
def create():
    try:
        # user_id = session['user_id']
        
        # data = request.get_json()
        # user_id = data.get("userId")
        # history_name = data.get("historyName")
        user_id = request.form.get("userId")
        history_name = request.form.get("historyName")
        print(user_id, history_name)
        if not user_id:
            return error_response(message="userId不能为空")

        conn = get_db()
        print("userId:", user_id) 
        print("数据库连接")
        with conn.cursor() as cursor:
         
            # 插入新记录
            cursor.execute(
                "INSERT INTO history_list (user_id, history_name) "
                "VALUES ( %s, %s)",
                (user_id, history_name)
            )
            conn.commit()

            new_history_id = cursor.lastrowid

        return jsonify({
            "code": 0,
            "message": "操作成功",
            "data": {
                "historyId": new_history_id
            }
        })
    except Exception as e:
        return error_response(message=f'数据库操作失败：{str(e)}')
    
@app.route('/api/qa/rename', methods=['PATCH'])
# @token_required
def rename():
    try:
        # data = request.get_json()
        # history_id = data.get("historyId")
        # new_name = data.get("newName")

        # history_id = request.args.get('historyId')
        # new_name = request.args.get('newName')
        
        history_id = request.form.get('historyId')
        new_name = request.form.get('newName')        
        
        print(history_id, new_name)
        if not history_id or not new_name:
            return error_response(message="historyId 和 newName 均不能为空")

        conn = get_db()
        with conn.cursor() as cursor:
            # 更新记录名
            cursor.execute(
                "UPDATE history_list SET history_name = %s WHERE history_id = %s",
                (new_name, history_id)
            )
            conn.commit()

        return jsonify({
            "code": 0,
            "message": "操作成功",
            "data": None
        })

    except Exception as e:
        return error_response(message=f"数据库操作失败：{str(e)}")
    
@app.route('/api/qa/delete', methods=['DELETE'])
# @token_required
def delete_history():
    try:
        history_id = request.args.get('historyId')
        print(history_id)
        if not history_id:
            return error_response(message="historyId 参数不能为空")

        conn = get_db()
        with conn.cursor() as cursor:
            # 删除对应的历史记录
            cursor.execute(
                "DELETE FROM history_list WHERE history_id = %s",
                (history_id,)
            )
            conn.commit()

        return jsonify({
            "code": 0,
            "message": "操作成功",
            "data": None
        })

    except Exception as e:
        return error_response(message=f"数据库操作失败：{str(e)}")

@app.route('/api/qa/chat', methods=['POST'])
# @token_required
def chat():
    start_time = time.time()
    thoughts = []

    # 记录思考的辅助函数
    def thinking(message):
        print(f"[思考] {message}")  # 仍然输出到控制台
        thoughts.append(message)

    question = request.form.get('question')
    history_id = request.args.get('historyId') 
    rag_flag = request.args.get('rag')
    rag = (rag_flag or request.args.get('rag', 'true')).lower() == 'true'

    thinking(f"问题: {question}")
    thinking(f"rag_flag: {rag_flag}, 最终 rag: {rag}")
    
    if not question:
        def error_stream():
            yield "错误：问题不能为空"
        return Response(error_stream(), mimetype='text/plain')

    history_context = get_history_context(history_id, max_count=5) if history_id else []
    thinking(f"获取历史上下文: {len(history_context)} 条记录")
    chat_context = build_chat_context(history_context, question)

    # 实体属性提取预处理
    result = extract_entity_attributes(question)
    thinking(f"实体属性提取结果: {result}")
    
    entity_found = False
    if result and result.get("entity") and result.get("attributes"):
        entity = result['entity']
        attributes = result['attributes']
        thinking(f"识别实体: {entity}, 属性: {attributes}")
        entity_found = True
        

        # 提前构建 Cypher 语句
        cyphers = []
        db_query_start = time.time()
        for attr in attributes:

            
            if attr in ['描述', '特点']:
                attr = '特点'
                cypher = f"""
                    MATCH (a)
                    WHERE a.title = '{entity}'
                    RETURN a.descripe AS answer
                """
            elif attr in ['作者', '年代']:
                cypher = f"""
                    MATCH (a)-[r:{attr}]->(b)
                    WHERE a.title = '{entity}'
                    RETURN 
                    CASE 
                        WHEN type(r) = '作者' THEN b.name
                        WHEN type(r) = '年代' THEN b.period
                    END AS answer
                """
            elif attr in ['收藏地', '存放博物馆', '存放地']:
                cypher = f"""
                    MATCH (museum)-[:包含]->(artifact)
                    WHERE artifact.title = '{entity}'
                    RETURN museum.name AS answer
                """
            elif attr in ['url', 'URL']:
                attr = 'url'
                cypher = f"""
                    MATCH (a)
                    WHERE a.title = '{entity}'
                    RETURN a.url AS answer
                """
            elif re.match(r'^(\d+|[一二三四五六七八九十百千万几一些若干多])+(件|个)?(文物|藏品)$', attr):
                num = extract_limit_from_attr(attr)
                cypher = f"""
                    MATCH (museum:Museum)-[:包含]->(artifact)
                    WHERE museum.name = '{entity}'
                    RETURN artifact.title AS answer
                    LIMIT {num}
                """
            else:
                cypher = ""

            cyphers.append((attr, cypher.strip()))
            # thinking(f"构建Cypher - {attr}: {cypher}")

    
    # 判断是否需要分类问题
    if not entity_found and rag:
        thinking("未识别出有效实体属性，准备通过RAG处理")
        try:
            classification = classify_question_with_gpt(question)
            qtype = classification["type"]
            thinking(f"问题分类结果: {qtype}")
            
            if qtype != "未知":
                thinking(f"问题分类成功!为{qtype}类型问题")
                thinking("准备执行结构化搜索...")
        except Exception as e:
            thinking(f"问题分类失败: {str(e)}")

    @stream_with_context
    def generate():
        # 先输出所有思考过程，确保完整输出
        thoughts_text = "\n".join(thoughts)
        yield f"<think>{thoughts_text}</think>\n"
        thoughts.clear()
            
        def fallback_with_llm():
            """仅使用 LLM 简要回答"""
            try:
                thinking("正在调用大模型实现")
                thoughts_text = "\n".join(thoughts)
                yield f"<think>{thoughts_text}</think>\n"
                thoughts.clear()
                
                
                # 构建包含历史对话的消息
                messages = []
                if chat_context:
                    messages.append({"role": "system", "content": "你是MuseLink-千鉴。你的核心职责是连接古今、解码文明，为用户提供专业而富有诗意的文物知识与解读。请记住用户的对话历史并保持连贯性。依据给出的参考整合成完整的语句之后,使用中文进行完整回答，可以保持幽默诙谐"})
                    for msg in chat_context:
                        messages.append({
                            "role": "user" if msg["role"]=="user" else "assistant", 
                            "content": msg["content"]
                        })
                else:
                    messages.append({"role": "user", "content": "请简要的回复：" + question})
                
                client = OpenAI(
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    api_key = ""
                )
                
                # 使用客户端调用API
                response = client.chat.completions.create(
                    model="deepseek-r1",
                    messages=messages if chat_context else [{"role": "user", "content": "请简要的回复：" + question}],
                    temperature=0.5,
                    stream=True
                )

                reference = "回答由AI生成，考虑了对话历史" if chat_context and history_context else "回答由AI生成，请注意甄别"
                accumulated_answer = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        accumulated_answer += content
                        yield content
                        time.sleep(0.01)
                yield f"\n<!-- REFERENCE_DATA:{reference} -->"
                save_qa_record(history_id, question, accumulated_answer, reference)
            except requests.RequestException as e:
                error_msg = f"API请求失败: {str(e)}"
                yield error_msg
                yield f"\n<!-- REFERENCE_DATA:请求失败 -->"
                save_qa_record(history_id, question, error_msg, "API请求异常")

        def fallback_with_rag():
            """RAG增强流程"""
            try:
                thinking("RAG增强")
                thoughts_text = "\n".join(thoughts)
                yield f"<think>{thoughts_text}</think>\n"
                thoughts.clear()
                classification = classify_question_with_gpt(question)
                qtype = classification["type"]
                
                if qtype != "未知":
                    thinking(f"处理统计类问题：{qtype}")
                    thoughts_text = "\n".join(thoughts)
                    yield f"<think>{thoughts_text}</think>\n"
                    thoughts.clear()                    
                    answer = answer_statistical_question(question)
                    thinking(f"结构化搜索完成")
                    thoughts_text = "\n".join(thoughts)
                    yield f"<think>{thoughts_text}</think>\n"
                    thoughts.clear()                       
                    yield answer
                    yield f"\n<!-- REFERENCE_DATA:统计类问题 ({qtype}) -->"
                    save_qa_record(history_id, question, answer, f"统计类问题 ({qtype})")
                    return


                thinking("处理知识库检索问题")
                thoughts_text = "\n".join(thoughts)
                yield f"<think>{thoughts_text}</think>\n"
                thoughts.clear()   
                # 考虑历史上下文进行知识库检索
                enriched_query = question
                if chat_context:
                    thinking("使用大模型增强查询...")
                    thoughts_text = "\n".join(thoughts)
                    yield f"<think>{thoughts_text}</think>\n"
                    thoughts.clear()   
                    enriched_query = enhance_query_with_llm(question, chat_context)
                    thinking(f"增强后的查询: {enriched_query}")  
                    thoughts_text = "\n".join(thoughts)
                    yield f"<think>{thoughts_text}</think>\n"
                    thoughts.clear()   
                        
                knowledge = search_similar_knowledge(enriched_query)
                thinking(f"检索到 {len(knowledge)} 条相关知识")
                thoughts_text = "\n".join(thoughts)
                yield f"<think>{thoughts_text}</think>\n"
                thoughts.clear()                   
                prompt = build_prompt(knowledge, question, chat_context if chat_context else None)
                
                client = OpenAI(
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    api_key="",
                )
                
                thinking("调用LLM API")
                thoughts_text = "\n".join(thoughts)
                yield f"<think>{thoughts_text}</think>\n"
                thoughts.clear()   
                
                response = client.chat.completions.create(
                    model="deepseek-r1",
                    messages=[
                        {"role": "system", "content": "你是MuseLink-千鉴。你的核心职责是连接古今、解码文明，为用户提供专业而富有诗意的文物知识与解读。依据给出的参考整合成完整的语句之后,使用中文进行完整回答。如果没有找到参考，就使用大模型自己回答"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5,
                    stream=True
                )

                # 构建消息，包含历史对话
                messages = [
                    {"role": "system", "content": "你是MuseLink-千鉴。你的核心职责是连接古今、解码文明，为用户提供专业而富有诗意的文物知识与解读。依据给出的参考和对话历史，使用中文进行完整回答。保持回答的连贯性。"}
                ]
                
                # 添加历史消息
                if chat_context:
                    for msg in chat_context:
                        messages.append({
                            "role": "user" if msg["role"]=="user" else "assistant",
                            "content": msg["content"]
                        })
                
                # 添加当前提示
                messages.append({"role": "user", "content": prompt})

                accumulated_answer = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        accumulated_answer += content
                        yield content
                        time.sleep(0.01)

                reference = "向量检索：" + json.dumps(knowledge, ensure_ascii=False)
                yield f"\n<!-- REFERENCE_DATA:{reference} -->"
                save_qa_record(history_id, question, accumulated_answer, reference)

            except Exception as e:
                print(f"RAG fallback 失败: {e}")
                yield from fallback_with_llm()

        # ------------------ 主逻辑：处理回答 ------------------ #
        if not entity_found:
            thinking("未识别出有效实体属性")
            thoughts_text = "\n".join(thoughts)
            yield f"<think>{thoughts_text}</think>\n"
            thoughts.clear()   
            yield from (fallback_with_rag() if rag else fallback_with_llm())
            return
        
        answers_map = {}
        records_found = True
        for attr, cypher in cyphers:
            if not records_found:
                break
            try:
                records = neo4j_conn.query(cypher)
                print(cypher)
                if records:
                    all_answers = [r['answer'] for r in records if r.get('answer')]
                    if all_answers:
                        answers_map[attr] = all_answers if len(all_answers) > 1 else all_answers[0]
                    else:
                        records_found = False
                else:
                    records_found = False
            except Exception as e:
                records_found = False
                answers_map[attr] = f"{attr}查询失败：{str(e)}"

        db_query_end = time.time()
        print(f"数据库查询耗时: {db_query_end - db_query_start:.4f} 秒")

        if result.get("question_type") == "yes_no":
            if len(attributes) != 1:
                yield "无法处理多个是否判断。"
                return

            attr = attributes[0]
            match_found = False
            reference = ""
            attr_type = None  # 用于标记当前属性类型

            # 判断是否为描述性关键词（如“瓷”）
            if re.search(r'[瓷陶玉铜金银青铜桶盆凳碗椅桌]', attr):
                attr_type = '描述'
                cypher = f"""
                    MATCH (a)
                    WHERE a.title = '{entity}' AND a.descripe CONTAINS '{attr}'
                    RETURN a.descripe AS answer
                """
                reference = f"[描述匹配] {cypher}"
            # 判断是否为作者（中文人名或明确提出“李白”“张大千”等）
            elif re.match(r'^[\u4e00-\u9fa5]{2,4}$', attr):
                attr_type = '作者'
                cypher = f"""
                    MATCH (a)-[:作者]->(b)
                    WHERE a.title = '{entity}' AND b.name = '{attr}'
                    RETURN b.name AS answer
                """
                reference = f"[作者匹配] {cypher}"
            # 判断是否为年代（年份或朝代）
            elif re.match(r'^(公元前)?\d{1,4}年$|^\d{4}$|.*朝$', attr):
                attr_type = '年代'
                cypher = f"""
                    MATCH (a)-[:年代]->(b)
                    WHERE a.title = '{entity}' AND b.period = '{attr}'
                    RETURN b.period AS answer
                """
                reference = f"[年代匹配] {cypher}"
            # 判断是否为收藏地
            else:
                attr_type = '收藏地'
                cypher = f"""
                    MATCH (museum)-[:包含]->(artifact)
                    WHERE artifact.title = '{entity}' AND museum.name = '{attr}'
                    RETURN museum.name AS answer
                """
                reference = f"[收藏地匹配] {cypher}"

            try:
                print("[YES_NO] Cypher:", cypher)
                records = neo4j_conn.query(cypher.strip())
                if records:
                    for record in records:
                        if any(v for v in record.values() if attr in str(v)):
                            match_found = True
                            break

                if attr_type in ['作者', '年代']:
                    if match_found:
                        final_answer = f"是的，{entity}是{attr}所作。"
                    else:
                        final_answer = f"不是，{entity}不是{attr}所作。"
                elif attr_type == '收藏地':
                    if match_found:
                        final_answer = f"是的，{entity}收藏于{attr}。"
                    else:
                        final_answer = f"不是，{entity}不收藏于{attr}。"
                else:
                    # 描述和年代默认普通陈述
                    if match_found:
                        final_answer = f"是的，{entity}是{attr}。"
                    else:
                        final_answer = f"不是，{entity}不是{attr}。"

                yield final_answer
                yield f"\n<!-- REFERENCE_DATA:{reference} -->"
                save_qa_record(history_id, question, final_answer, reference)
                return
            except Exception as e:
                yield f"{attr}的判断查询失败：{str(e)}"
                return
            
   

        if records_found:
            response_segments = []
            for attr, answer in answers_map.items():
                if isinstance(answer, list):  # 多条记录（如多个文物）
                    response_segments.append(f"{attr}包括：{'、'.join(answer)}")
                else:  # 单条记录
                    response_segments.append(f"{attr}是{answer}")
            final_answer = f"{entity}的" + "，".join(response_segments) + "。"

            reference = "从Neo4j数据库获取:\n" + "\n".join(c for _, c in cyphers)
            yield final_answer
            yield f"\n<!-- REFERENCE_DATA:{reference} -->"
            save_qa_record(history_id, question, final_answer, reference)
        else:
            yield from (fallback_with_rag() if rag else fallback_with_llm())

        end_time = time.time()
        print(f"总耗时: {end_time - start_time:.2f}s")

    return Response(generate(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0',port=3200)
# MuseLink 后端服务

## 项目简介

MuseLink-web端是一个基于Flask的Web后端服务，提供文物知识查询、RAG知识问答、用户管理等功能。系统通过连接传统数据库与向量数据库，结合大语言模型，为用户提供专业而富有诗意的文物知识与解读服务。

## 核心功能

- 用户认证与管理系统
- 文物信息检索与展示
- 基于RAG的智能问答系统
- 文物收藏与点赞功能
- 聊天历史记录管理

## 环境要求

- Python 3.9+
- MySQL数据库
- Neo4j图数据库
- Milvus向量数据库

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置服务

在运行前，请确保正确配置以下服务：

- 数据库连接：在db.py中配置MySQL、Neo4j连接信息
- 向量数据库：确保Milvus服务已启动且可访问
- API密钥：在app.py中配置大语言模型API密钥

### 3. 启动服务

```bash
python app.py
```

服务将在本地3200端口启动，访问http://localhost:3200即可。

## API接口概览

- 用户管理：`/api/register`, `/api/login`, `/api/logout`
- 文物查询：`/api/artifacts`, `/api/artifact/<id>`
- 问答系统：`/api/qa/chat`, `/api/qa/getHistoryList`
- 用户交互：`/api/likes/toggle`, `/api/collection/toggle`

## 注意事项

- 当前配置使用阿里云DashScope API作为OpenAI接口的兼容模式
- 在avatar目录中存储用户头像，请确保目录可写
- 开发环境下，可通过设置`app.run(debug=True)`启用调试模式
- 生产环境建议使用Gunicorn或uWSGI作为WSGI服务器
- 配置文件中的敏感信息（如数据库密码、API密钥）应通过环境变量管理
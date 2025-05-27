import mysql.connector
from neo4j import GraphDatabase
import pymysql
def get_db_connection():
    """获取远程数据库连接"""
    return mysql.connector.connect(
        host='123.56.94.39',
        user='cs2202',
        password='',
        database='data',
        charset='utf8mb4'
    )
def get_db():
    return pymysql.connect(
        host='123.56.94.39',
        user='cs2202',
        password='',
        database='data',
        charset='utf8mb4'
    )  

def get_local_db_connection():
    """获取本地数据库连接"""
    return mysql.connector.connect(
        host='123.56.94.39',
        user='cs2202',
        password='',
        database='data',
        charset='utf8mb4'
    )

# Neo4j数据库
NEO4J_URI = "bolt://123.56.94.39:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = ""

def get_neo4j_driver():
    """获取Neo4j驱动连接"""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))



class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]

# 初始化连接
neo4j_conn = Neo4jConnection(
    uri=NEO4J_URI,
    user=NEO4J_USER,
    password=NEO4J_PASSWORD
)

if __name__ == "__main__":
    # 测试数据库连接
    try:
        conn = get_db_connection()
        print("远程数据库连接成功")
        conn.close()
    except Exception as e:
        print(f"远程数据库连接失败: {e}")

    try:
        local_conn = get_local_db_connection()
        print("本地数据库连接成功")
        local_conn.close()
    except Exception as e:
        print(f"本地数据库连接失败: {e}")




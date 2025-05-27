# MuseLink - 文物数字博物馆系统

MuseLink-web端是一个基于RAG技术的文物知识查询与展示平台，结合传统数据库、图数据库与向量数据库，为用户提供文物展示、智能问答、知识图谱等功能。

## 系统架构

系统由前端和后端两部分组成：

- **前端**：基于Vue.js构建的Web界面，提供用户交互和数据展示
- **后端**：基于Flask的RESTful API服务，处理数据查询、用户认证和智能问答

## 核心功能

- **文物浏览与检索**：支持多种筛选条件、排序和搜索方式
- **文物详情展示**：高清图片查看（支持缩放）、文物信息、相关推荐
- **智能知识问答**：基于RAG的AI对话系统，结合知识库提供专业解答
- **知识图谱可视化**：展示文物之间的关联关系
- **用户系统**：注册、登录、个人中心
- **互动功能**：收藏、点赞文物

## 快速开始

### 环境要求

- 后端：
  - Python 3.9+
  - MySQL数据库
  - Neo4j图数据库
  - Milvus向量数据库
  
- 前端：
  - Node.js 14.0+
  - npm 6.0+ 或 yarn 1.22+

### 后端设置

1. **安装依赖**

```bash
cd backend
pip install -r requirements.txt
```

2. **配置数据库**

在`db.py`中配置MySQL和Neo4j连接信息：
- 确保Milvus服务已启动且可访问
- 在`app.py`中配置大语言模型API密钥

3. **启动后端服务**

```bash
python app.py
```

服务将在本地3200端口启动，访问http://localhost:3200即可。

### 前端设置

1. **安装依赖**

```bash
cd frontend
npm install
# 或使用 yarn
yarn install
```

2. **开发模式运行**

```bash
npm run serve
# 或使用 yarn
yarn serve
```

应用将在http://localhost:8080运行（默认端口，可能会有变化）。

3. **生产环境构建**

```bash
npm run build
# 或使用 yarn
yarn build
```

构建后的文件将生成在`dist`目录。

## 项目结构

```
MuseLink/
├── backend/              # Flask后端代码
│   ├── app.py            # 主应用入口
│   ├── db.py             # 数据库连接配置
│   ├── utils/            # 工具函数
│   ├── qa/               # 问答系统模块
│   │   └── RAG/          # 检索增强生成模块
│   └── avatar/           # 用户头像存储目录
│
├── frontend/             # Vue前端代码
│   ├── public/           # 静态资源
│   ├── src/              # 源代码
│   │   ├── components/   # 组件
│   │   ├── views/        # 页面视图
│   │   ├── services/     # API服务
│   │   ├── stores/       # 状态管理
│   │   └── assets/       # 资源文件
│   └── vue.config.js     # Vue配置
│
└── README.md             # 项目说明文档
```

## API接口概览

### 用户管理
- 注册：`/api/register`
- 登录：`/api/login`
- 登出：`/api/logout`
- 用户信息：`/api/user`

### 文物查询
- 文物列表：`/api/artifacts`
- 文物详情：`/api/artifact/<id>`

### 问答系统
- 聊天：`/api/qa/chat`
- 获取历史记录：`/api/qa/getHistoryList`
- 创建新对话：`/api/qa/create`
- 重命名对话：`/api/qa/rename`
- 删除对话：`/api/qa/delete`

### 用户交互
- 点赞：`/api/likes/toggle`
- 收藏：`/api/collection/toggle`

## 注意事项

- 后端配置使用阿里云DashScope API作为OpenAI接口的兼容模式
- 敏感信息（如数据库密码、API密钥）应通过环境变量管理
- 开发环境下，可通过设置`app.run(debug=True)`启用调试模式
- 生产环境建议使用Gunicorn或uWSGI作为WSGI服务器

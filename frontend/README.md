# MuseLink 前端项目

## 项目简介

MuseLink-web端是一个文物数字博物馆的前端项目，基于Vue.js构建，提供文物展示、知识问答、知识图谱可视化等功能。项目通过与后端API交互，为用户提供丰富的文物知识体验和交互功能。

## 主要功能

- **文物浏览与检索**：支持多种筛选条件和排序方式
- **文物详情展示**：包含高清图片查看（支持缩放）、文物信息、相关推荐
- **知识问答系统**：基于RAG的智能问答功能，支持聊天历史管理
- **知识图谱可视化**：展示文物之间的关联关系
- **用户系统**：注册、登录、个人中心
- **互动功能**：收藏、点赞文物

## 技术栈

- Vue 3
- Axios（API请求）
- Element Plus（UI组件库）
- D3.js（知识图谱可视化）
- OpenSeadragon（图片缩放查看）
- HeroIcons（图标库）

## 快速开始

### 环境要求

- Node.js 14.0+
- npm 6.0+ 或 yarn 1.22+

### 安装依赖

```bash
# 使用 npm
npm install

# 或使用 yarn
yarn install
```

### 开发模式运行

```bash
# 使用 npm
npm run serve

# 或使用 yarn
yarn serve
```

应用将在 http://localhost:8080 运行（默认端口，可能会有变化）。

### 生产环境构建

```bash
# 使用 npm
npm run build

# 或使用 yarn
yarn build
```

构建后的文件将生成在 `dist` 目录。

## API接口

前端项目默认连接到以下API端点：

- 基础API地址：`http://localhost:3200/api`（在开发环境中已配置代理）
- 主要接口类型：
  - 用户认证：`/login`, `/register`, `/logout`
  - 文物数据：`/artifacts`, `/artifact/<id>`
  - 知识问答：`/qa/chat`, `/qa/getHistoryList`
  - 用户交互：`/likes/toggle`, `/collection/toggle`

## 开发注意事项

- 开发时需确保后端服务已启动并可访问
- 文件上传功能（如头像更新）需要后端支持
- 图片资源存放在 `public/images` 和 `src/assets` 目录
- 组件图标位于 `src/components/icons` 目录

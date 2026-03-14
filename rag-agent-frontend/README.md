# RAG Agent Frontend

## 快速启动

```bash
npm install
npm run dev
```

浏览器访问 http://localhost:5173

## 环境要求

后端服务运行在 http://127.0.0.1:8000（vite 已配置代理）

## 目录结构

```
src/
├── api/                # 接口封装
│   ├── client.ts       # axios 实例（自动注入 Token / 401 跳转）
│   ├── auth.ts         # 注册 / 登录
│   ├── chat.ts         # 普通对话 / 流式对话 / 会话管理
│   ├── knowledge.ts    # 知识库管理
│   └── tools.ts        # 工具管理
├── components/         # 通用组件
│   ├── MessageBubble.tsx    # 对话气泡
│   ├── StreamingBubble.tsx  # 流式输出气泡（含打字动画）
│   ├── Sidebar.tsx          # 侧边栏（导航 + 会话列表）
│   └── FileUploader.tsx     # 拖拽上传组件
├── pages/              # 页面
│   ├── LoginPage.tsx   # 登录 / 注册
│   ├── ChatPage.tsx    # 主对话页
│   ├── KnowledgePage.tsx   # 知识库管理
│   └── ToolsPage.tsx   # 工具管理
├── store/              # Zustand 状态
│   ├── authStore.ts    # Token / 用户名
│   └── chatStore.ts    # 消息 / 会话 / 流式状态
└── hooks/
    └── useStream.ts    # SSE 流式输出 Hook
```

## 功能说明

| 功能 | 说明 |
|------|------|
| 登录/注册 | JWT Token 认证，自动持久化 |
| 流式对话 | SSE 实时输出，打字机效果 |
| 会话管理 | 创建/切换/删除历史会话 |
| 临时文件上传 | 上传文件作为当次对话上下文 |
| 知识库管理 | 上传/查看/删除入库文件 |
| 工具管理 | 新增/编辑/启用/禁用/删除工具 |

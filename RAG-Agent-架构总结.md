# RAG Agent 项目架构总结

## 一、项目概述

本项目是一个**全栈 RAG（检索增强生成）智能对话系统**，支持知识库问答、工具调用、普通闲聊三种模式，具备用户认证、多会话管理、文件上传、流式输出等完整功能。

---

## 二、整体技术栈

| 层次 | 技术选型 |
|------|---------|
| **后端框架** | FastAPI (Python) |
| **LLM 调用** | LangChain + LangGraph (ReAct Agent) |
| **向量数据库** | FAISS（本地持久化） |
| **混合检索** | FAISS 向量检索 + BM25 关键词检索 |
| **嵌入模型** | OpenAI Embeddings（可替换 Base URL） |
| **视觉理解** | Vision LLM（图片内容提取） |
| **认证** | JWT（python-jose）+ bcrypt 密码哈希 |
| **限流** | SlowAPI（基于 IP 的速率限制） |
| **数据持久化** | SQLite（用户/会话/工具注册表） |
| **前端框架** | React + TypeScript + Vite |
| **UI 样式** | Tailwind CSS |
| **状态管理** | Zustand |
| **Markdown 渲染** | react-markdown + remark-gfm |
| **代码高亮** | prism-react-renderer |
| **流式通信** | SSE（Server-Sent Events）+ 原生 fetch |

---

## 三、后端架构详解

### 3.1 目录结构

```
rag-agent-backend/
├── app/main.py          # FastAPI 入口，所有路由定义
├── router/              # 意图路由层
│   ├── intent_router.py # LLM 分类器（rag / tool / chat）
│   └── router.py        # 分发到对应 Agent
├── agents/              # 三类 Agent
│   ├── general_agent.py # 普通对话 Agent
│   ├── rag_agent.py     # RAG 检索 Agent
│   └── tool_agent.py    # 工具调用 Agent
├── rag/                 # RAG 模块
│   ├── ingest.py        # 文档入库（chunk + embedding + FAISS）
│   ├── retriever.py     # 混合检索（FAISS + BM25）
│   ├── rag_chain.py     # RAG 链路
│   ├── loader_router.py # 文件类型路由
│   ├── file_handlers.py # 文件处理（txt/csv/image）
│   ├── csv_loader.py    # CSV 加载器
│   ├── image_loader.py  # 图片内容提取
│   └── knowledge_manager.py # 知识库文件管理
├── tools/               # 工具系统
│   ├── tool_registry.py # 工具注册、加载、CRUD
│   ├── sandbox.py       # 代码沙箱（安全执行）
│   ├── weather_tool.py  # 内置天气工具
│   ├── rag_tool.py      # RAG 检索工具（供 Agent 调用）
│   └── tool_response.py # 标准化工具返回格式
├── auth/                # 认证模块
│   ├── auth.py          # JWT 生成/验证、密码哈希
│   └── models.py        # 用户、会话、消息数据库操作
├── memory/
│   └── memory.py        # LangGraph MemorySaver（会话记忆）
├── core/
│   ├── config.py        # 环境变量配置
│   ├── llm.py           # LLM 工厂（普通/流式/视觉）
│   ├── file_security.py # 文件安全校验（magic bytes + 白名单）
│   ├── limiter.py       # SlowAPI 限流实例
│   └── logger.py        # 统一日志配置
├── vectorstore/         # FAISS 索引持久化
├── data/                # 知识库源文件
└── logs/                # 运行日志
```

### 3.2 核心流程：请求处理链路

```
用户请求
    │
    ▼
FastAPI 路由层 (main.py)
├── 认证校验（JWT Bearer Token）
├── 速率限制（SlowAPI，IP 粒度）
└── 分发到 /chat 或 /chat/stream
    │
    ▼
Intent Router (intent_router.py)
├── 用 LLM 分类问题意图
├── 返回标签：rag / tool / chat
└── 特殊：检查 user_id 对应的临时文件上下文
    │
    ├──[rag]──▶ RAG Agent (rag_agent.py)
    │           └── ReAct Agent + search_docs 工具
    │               └── HybridRetriever（FAISS + BM25）
    │
    ├──[tool]─▶ Tool Agent (tool_agent.py)
    │           └── ReAct Agent + 动态工具列表
    │               ├── 内置工具（天气等）
    │               └── 动态工具（沙箱加载）
    │
    └──[chat]─▶ General Agent (general_agent.py)
                └── ReAct Agent（无工具，纯对话）
```

### 3.3 RAG 模块详解

**文件入库流程：**

1. **文件路由** (`loader_router.py`)：根据文件后缀选择对应 Loader
2. **内容提取**：
   - `.txt/.md` → 直接读取
   - `.pdf/.docx` → 专用解析库
   - `.csv` → Pandas 转文本
   - 图片 → Vision LLM 提取内容描述
3. **分块** (`RecursiveCharacterTextSplitter`，chunk_size=500，overlap=100)
4. **去重** (MD5 哈希，存 SQLite)
5. **向量化** (OpenAI Embeddings)
6. **存储** (FAISS 本地索引，支持增量更新)

**混合检索 (`HybridRetriever`)：**

- 同时执行 **BM25 关键词检索** 和 **FAISS 向量相似度检索**
- 结果取并集，按 page_content 去重，返回 top-k

**两种文件上下文模式：**

| 模式 | 接口 | 用途 |
|------|------|------|
| 临时上下文 | `/uploadfile/` | 文件内容直接注入当前对话 Prompt，按 user_id 隔离 |
| 知识库入库 | `/knowledge/upload` | chunk + embedding，进入 FAISS 向量库供全局检索 |

### 3.4 工具系统详解

**动态工具注册机制：**

- 工具元数据（名称、描述、代码、启用状态）存储于 SQLite (`tools_registry.db`)
- 区分**内置工具**（代码固定）和**自定义工具**（动态 Python 代码）
- 每次 tool_agent 调用时，从数据库实时加载所有已启用工具

**代码沙箱 (`sandbox.py`)：**

- 静态分析：黑名单关键词检查（`subprocess`、`os.system`、`socket`、`requests`、`eval`、`open` 等）
- 运行时限制：替换 `__builtins__` 为白名单内置函数集合
- 模块白名单：仅允许 `json`、`math`、`datetime`、`re`、`random`、`tools.tool_response` 等安全模块
- 工具返回值标准化：`{ state: 200/400/500, result, error_message }`

### 3.5 认证与会话管理

- 用户数据：SQLite (`auth.db`)，密码用 bcrypt 哈希存储
- JWT Token：HS256 算法，payload 含 `user_id`、`username`、`exp`
- 会话 (thread_id)：UUID v4，绑定 user_id，会话间完全隔离
- 消息历史：存储于 SQLite，同时 LangGraph `MemorySaver` 在内存中维护 Agent 对话状态

### 3.6 流式输出实现

```
后端 /chat/stream
├── 启动子线程运行 run_agent_stream（同步生成器）
├── 通过 Queue 传递 chunk
├── 异步主线程读取 Queue
└── yield SSE 格式：data: {chunk}\n\n ... data: [DONE]\n\n

前端
├── 原生 fetch + ReadableStream
├── TextDecoder 解析 SSE 行
├── onChunk → Zustand appendStreamChunk
└── [DONE] → commitStreamMessage（流式气泡转正式消息）
```

---

## 四、前端架构详解

### 4.1 目录结构

```
src/
├── main.tsx             # 入口，BrowserRouter 包裹
├── App.tsx              # 路由守卫（登录/保护路由）
├── api/                 # API 层
│   ├── client.ts        # Axios 实例（Token 注入 + 401 跳转）
│   ├── auth.ts          # 注册/登录接口
│   ├── chat.ts          # 对话/会话接口 + chatStream
│   ├── knowledge.ts     # 知识库接口
│   └── tools.ts         # 工具管理接口
├── store/               # 全局状态（Zustand）
│   ├── authStore.ts     # Token/用户名，持久化到 localStorage
│   └── chatStore.ts     # 会话列表、消息、流式状态
├── hooks/
│   └── useStream.ts     # 流式发送封装 Hook
├── components/
│   ├── Sidebar.tsx      # 侧边栏（导航 + 会话列表管理）
│   ├── MessageBubble.tsx    # 消息气泡（含复制/引用按钮）
│   ├── MessageContent.tsx   # Markdown 渲染 + 代码高亮
│   ├── StreamingBubble.tsx  # 流式输出气泡（打字机动画）
│   └── FileUploader.tsx     # 拖拽上传组件
└── pages/
    ├── LoginPage.tsx    # 登录/注册页
    ├── ChatPage.tsx     # 主对话页
    ├── KnowledgePage.tsx    # 知识库管理页
    └── ToolsPage.tsx    # 工具管理页
```

### 4.2 页面功能

| 页面 | 核心功能 |
|------|---------|
| **ChatPage** | 流式对话、文件上传为临时上下文、引用 AI 消息追问、自动滚动 |
| **KnowledgePage** | 拖拽/点击上传文件入知识库、查看/删除已入库文件 |
| **ToolsPage** | 工具列表展示、新增/编辑/删除/启用禁用自定义工具（含代码编辑器） |
| **LoginPage** | 登录/注册切换、密码显示/隐藏、Enter 提交 |
| **Sidebar** | 导航切换、新建会话、会话列表（支持双击/按钮重命名）、删除会话、退出登录 |

### 4.3 状态管理设计

**authStore：**
```
token / username
├── 持久化：localStorage
├── setToken()：登录时保存
└── logout()：清除并跳转
```

**chatStore：**
```
conversations / currentThreadId / messages
├── streaming: boolean           # 是否正在流式输出
├── streamingContent: string     # 当前流式累积内容
├── appendStreamChunk()          # 追加流式 chunk
├── commitStreamMessage()        # 流式完成，转正式消息
└── resetStream()                # 出错时重置
```

---

## 五、安全设计

| 安全措施 | 实现方式 |
|---------|---------|
| **接口认证** | 所有核心接口需 Bearer JWT Token |
| **暴力破解防护** | 登录接口限流 10次/分钟（IP 粒度） |
| **对话接口限流** | 30次/分钟（IP 粒度） |
| **文件安全校验** | magic bytes 验证、文件类型白名单、大小限制 |
| **会话隔离** | 每个操作校验 `conversation_owner`，防止越权 |
| **用户数据隔离** | 临时文件上下文按 `user_id` 隔离 |
| **工具代码沙箱** | 黑名单静态扫描 + 运行时 builtins 替换 + 模块白名单 |
| **文件去重** | MD5 哈希防止重复入库 |
| **全局异常处理** | 统一返回格式，不暴露内部堆栈 |
| **请求日志** | 每个 HTTP 请求记录方法、路径、耗时、状态码 |

---

## 六、数据流汇总

```
[用户发送消息]
      │
      ▼
前端 useStream.send()
      │ SSE fetch
      ▼
后端 /chat/stream（认证+限流）
      │
      ▼
intent_router.route()     ← LLM 分类意图
      │
  ┌───┴───────┬──────────┐
  ▼           ▼          ▼
rag_agent  tool_agent  general_agent
  │           │          │
  │    动态工具加载       │
  │    沙箱执行          │
  │           │          │
  └──LangGraph ReAct Agent──┘
       ↕ MemorySaver（会话记忆）
            │
            ▼
      LLM 生成回复
            │
            ▼
   yield chunk → SSE → 前端 appendStreamChunk
            │
     [DONE] commitStreamMessage
            │
            ▼
      SQLite 持久化消息
```

---

## 七、项目亮点总结

1. **三模式智能路由**：LLM 作为分类器，自动判断走 RAG / 工具 / 普通对话，用户无感知
2. **混合检索**：BM25 + FAISS 双路召回，兼顾精确关键词匹配和语义相似度
3. **双文件上下文**：临时上下文（直接注入 Prompt）vs 持久知识库（向量检索），灵活应对不同场景
4. **动态工具系统**：支持运行时新增 Python 工具，沙箱保证安全，无需重启服务
5. **流式 SSE**：真正的 token 级流式输出，前端打字机效果，体验流畅
6. **完整会话管理**：多会话隔离、历史消息持久化、LangGraph 内存维护 Agent 上下文
7. **引用追问**：前端支持引用 AI 回复内容进行追问，引用内容自动拼接到 Prompt
8. **代码安全沙箱**：静态 + 动态双重防护，防止恶意代码执行

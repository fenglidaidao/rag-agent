# app/main.py
import asyncio
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from rag.file_handlers import process_text_file, process_csv_file, process_image_file
from rag.ingest import store_file_content_for_prompt
from rag.knowledge_manager import upload_to_knowledge_base, list_knowledge_files, delete_from_knowledge_base
from router.router import run_agent
from tools.tool_registry import list_tools, add_tool, update_tool, delete_tool
from fastapi.middleware.cors import CORSMiddleware
import uuid
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from langchain_core.callbacks import BaseCallbackHandler
from router.router import run_agent, run_agent_stream
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from core.logger import get_logger
from auth.auth import (
    hash_password, verify_password,
    create_access_token, get_current_user, generate_thread_id
)
from auth.models import (
    create_user, get_user,
    create_conversation, get_user_conversations,
    verify_conversation_owner, delete_conversation,
    update_conversation_time, save_message, get_conversation_messages
)

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from core.limiter import limiter
from core.file_security import validate_file
from auth.models import update_conversation_title
import json

app = FastAPI(
    title="RAG Agent API",
    description="RAG Agent Backend",
    version="1.0.0",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # 生产环境替换为具体前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 注册限流器
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


logger = get_logger("main")


# ========== 认证注册登陆接口 ==========
class RegisterRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/register")
async def register(req: RegisterRequest):
    hashed = hash_password(req.password)
    success = create_user(req.username, hashed)
    if not success:
        raise HTTPException(status_code=400, detail="用户名已存在")
    return {"message": f"用户 '{req.username}' 注册成功"}


# /auth/login：每个 IP 每分钟最多 10 次，防暴力破解
@app.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form.username)
    if not user or not verify_password(form.password, user["password"]):
        logger.warning(f"登录失败 | username={form.username}")
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(user["id"], user["username"])
    logger.info(f"登录成功 | username={form.username}")
    return {"access_token": token, "token_type": "bearer"}


# ========== 会话管理接口 ==========
@app.post("/conversations")
async def new_conversation(current_user: dict = Depends(get_current_user)):
    """创建新会话"""
    thread_id = generate_thread_id()
    create_conversation(thread_id, current_user["user_id"])
    return {"thread_id": thread_id, "title": "新对话"}


@app.get("/conversations")
async def list_conversations(current_user: dict = Depends(get_current_user)):
    """获取当前用户所有会话"""
    convs = get_user_conversations(current_user["user_id"])
    return {"conversations": convs}


@app.get("/conversations/{thread_id}/messages")
async def get_messages(thread_id: str, current_user: dict = Depends(get_current_user)):
    """获取某个会话的历史消息"""
    if not verify_conversation_owner(thread_id, current_user["user_id"]):
        raise HTTPException(status_code=403, detail="无权访问该会话")
    messages = get_conversation_messages(thread_id)
    return {"thread_id": thread_id, "messages": messages}


@app.delete("/conversations/{thread_id}")
async def remove_conversation(thread_id: str, current_user: dict = Depends(get_current_user)):
    """删除某个会话"""
    if not verify_conversation_owner(thread_id, current_user["user_id"]):
        raise HTTPException(status_code=403, detail="无权删除该会话")
    success = delete_conversation(thread_id, current_user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "会话已删除"}


# ========== chat接口 ==========
# ========== 流式回调处理器 ==========
class StreamingHandler(BaseCallbackHandler):
    def __init__(self, queue):
        self.queue = queue

    def on_llm_new_token(self, token: str, **kwargs):
        self.queue.put(token)

    def on_llm_end(self, response, **kwargs):
        self.queue.put(None)  # None 作为结束信号

    def on_llm_error(self, error, **kwargs):
        self.queue.put(f"[ERROR]: {str(error)}")
        self.queue.put(None)


class ChatStreamRequest(BaseModel):
    message: str
    thread_id: str
    quote: str = ""   # ✅ 新增，引用内容，默认空


class ChatRequest(BaseModel):
    message: str
    thread_id: str


@app.post("/chat")
@limiter.limit("30/minute")
async def chat(request: Request, req: ChatRequest, current_user: dict = Depends(get_current_user)):
    if not verify_conversation_owner(req.thread_id, current_user["user_id"]):
        raise HTTPException(status_code=403, detail="无权访问该会话")
    try:
        save_message(req.thread_id, "user", req.message)
        # ✅ 透传 user_id
        response = await asyncio.to_thread(
            run_agent, req.message, req.thread_id, current_user["user_id"]
        )
        save_message(req.thread_id, "assistant", response)
        update_conversation_time(req.thread_id)
        return {"response": response, "thread_id": req.thread_id}
    except Exception as e:
        logger.error(f"chat error: {e}", exc_info=True)
        return {"response": f"Error: {str(e)}", "thread_id": req.thread_id}


# /chat/stream：每个 IP 每分钟最多 30 次
@app.post("/chat/stream")
@limiter.limit("30/minute")
async def chat_stream(request: Request, req: ChatStreamRequest, current_user: dict = Depends(get_current_user)):
    if not verify_conversation_owner(req.thread_id, current_user["user_id"]):
        raise HTTPException(status_code=403, detail="无权访问该会话")

    actual_message = req.message
    if req.quote:
        actual_message = f"【引用内容】\n{req.quote}\n\n【追问】\n{req.message}"

    async def generate():
        full_response = ""
        try:
            save_message(req.thread_id, "user", req.message)
            import queue, threading
            q = queue.Queue()

            def run_stream():
                try:
                    # ✅ 透传 user_id
                    for chunk in run_agent_stream(actual_message, req.thread_id, current_user["user_id"]):
                        q.put(chunk)
                except Exception as e:
                    q.put(f"[ERROR]: {str(e)}")
                finally:
                    q.put(None)

            threading.Thread(target=run_stream).start()

            while True:
                chunk = await asyncio.to_thread(q.get)
                if chunk is None:
                    break
                full_response += chunk
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

            save_message(req.thread_id, "assistant", full_response)
            update_conversation_time(req.thread_id)
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"chat_stream error: {e}", exc_info=True)
            yield f"data: [ERROR]: {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    )


# /uploadfile/：每个 IP 每分钟最多 20 次 + 文件安全校验
@app.post("/uploadfile/")
@limiter.limit("20/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)  # ✅ 加上认证
):
    try:
        file_content = await file.read()
        safe_name = validate_file(file.filename, file_content)

        if safe_name.endswith((".txt", ".md")):
            result = process_text_file(safe_name, file_content)
        elif safe_name.endswith(".csv"):
            result = process_csv_file(safe_name, file_content)
        elif safe_name.endswith((".png", ".jpg", ".jpeg")):
            result = process_image_file(safe_name, file_content)
        else:
            raise ValueError("Unsupported file type")

        # ✅ 按 user_id 存储
        store_file_content_for_prompt(result, current_user["user_id"])
        return {"message": f"File {safe_name} processed successfully"}
    except ValueError as e:
        return {"message": str(e)}
    except Exception as e:
        logger.error(f"upload_file error: {e}", exc_info=True)
        return {"message": f"Error: {str(e)}"}


# ========== 知识库管理 ==========
# /knowledge/upload：每个 IP 每分钟最多 20 次 + 文件安全校验
@app.post("/knowledge/upload")
@limiter.limit("20/minute")
async def knowledge_upload(request: Request, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    try:
        file_content = await file.read()

        # ✅ 统一文件安全校验（文件名、大小、magic bytes）
        safe_name = validate_file(file.filename, file_content)

        result = await asyncio.to_thread(upload_to_knowledge_base, safe_name, file_content)
        return result
    except ValueError as e:
        logger.warning(f"文件校验失败：{e}")
        return {"success": False, "message": str(e)}
    except Exception as e:
        logger.error(f"knowledge_upload error: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}


@app.get("/knowledge/list")
async def knowledge_list():
    return {"files": list_knowledge_files()}


@app.delete("/knowledge/{filename}")
async def knowledge_delete(filename: str):
    try:
        result = await asyncio.to_thread(delete_from_knowledge_base, filename)
        return {"message": result}
    except FileNotFoundError as e:
        return {"message": str(e)}
    except Exception as e:
        return {"message": f"Error: {str(e)}"}


# ========== 工具管理 ==========
class ToolCreate(BaseModel):
    name: str
    description: str
    code: str


class ToolUpdate(BaseModel):
    description: Optional[str] = None
    code: Optional[str] = None
    enabled: Optional[bool] = None

@app.get("/tools")
async def get_tools():
    return {"tools": list_tools()}


@app.post("/tools")
async def create_tool(req: ToolCreate):
    try:
        # ✅ 保存前先做沙箱校验，有问题直接拒绝
        from tools.sandbox import validate_code, execute_in_sandbox

        is_safe, err = validate_code(req.code)
        if not is_safe:
            return {"message": f"代码安全校验失败：{err}"}

        fn, err = execute_in_sandbox(req.code, req.name)
        if fn is None:
            return {"message": f"代码校验失败：{err}"}

        add_tool(req.name, req.description, req.code)
        logger.info(f"新增工具：{req.name}")
        return {"message": f"Tool '{req.name}' added successfully"}
    except Exception as e:
        logger.error(f"create_tool error: {e}", exc_info=True)
        return {"message": f"Error: {str(e)}"}


@app.put("/tools/{tool_name}")
async def modify_tool(tool_name: str, req: ToolUpdate):
    try:
        # ✅ 修改代码时也校验
        if req.code:
            from tools.sandbox import validate_code, execute_in_sandbox

            is_safe, err = validate_code(req.code)
            if not is_safe:
                return {"message": f"代码安全校验失败：{err}"}

            fn, err = execute_in_sandbox(req.code, tool_name)
            if fn is None:
                return {"message": f"代码校验失败：{err}"}

        update_tool(tool_name, req.description, req.code, req.enabled)
        logger.info(f"更新工具：{tool_name}")
        return {"message": f"Tool '{tool_name}' updated successfully"}
    except Exception as e:
        logger.error(f"modify_tool error: {e}", exc_info=True)
        return {"message": f"Error: {str(e)}"}


@app.delete("/tools/{tool_name}")
async def remove_tool(tool_name: str):
    try:
        delete_tool(tool_name)
        return {"message": f"Tool '{tool_name}' deleted successfully"}
    except Exception as e:
        return {"message": f"Error: {str(e)}"}




# ========== 请求日志中间件 ==========
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    logger.info(f"→ {request.method} {request.url.path} | client={request.client.host}")
    try:
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 2)
        logger.info(f"← {request.method} {request.url.path} | status={response.status_code} | {duration}ms")
        return response
    except Exception as e:
        duration = round((time.time() - start) * 1000, 2)
        logger.error(f"← {request.method} {request.url.path} | ERROR: {e} | {duration}ms")
        raise


# ========== 全局异常处理 ==========
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "服务器内部错误，请稍后重试", "detail": str(exc)}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )



# ========== 对话记录名修改 ==========
class ConversationTitleUpdate(BaseModel):
    title: str

@app.put("/conversations/{thread_id}/title")
async def update_title(thread_id: str, req: ConversationTitleUpdate, current_user: dict = Depends(get_current_user)):
    if not verify_conversation_owner(thread_id, current_user["user_id"]):
        raise HTTPException(status_code=403, detail="无权修改该会话")
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="标题不能为空")
    success = update_conversation_title(thread_id, current_user["user_id"], req.title.strip())
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "标题已更新"}














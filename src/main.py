"""FastAPI 主应用程序"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST as OPENMETRICS_CONTENT_TYPE_LATEST
from sqlalchemy import text

from .config import settings
from .database import engine, Base
from .routers import agents, models, tools, runs, auth, chat, dashboard, chat_test, chat_history, advanced_agents, chat_sessions
from .middleware import rate_limit_middleware, auth_middleware

# 配置日志
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)

# Prometheus 指标
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'HTTP 请求总数', 
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds', 
    'HTTP 请求延迟', 
    ['method', 'endpoint']
)
AGENT_RUN_COUNT = Counter(
    'agent_runs_total', 
    'Agent 执行总数', 
    ['agent_id', 'status']
)
TOKEN_USAGE = Counter(
    'token_usage_total', 
    'Token 使用总数', 
    ['model', 'type']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("🚀 启动 ModelVS3 Agent Platform")
    
    # 等待数据库连接并创建表
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            logger.info(f"尝试连接数据库 (第 {attempt + 1} 次)")
            # 测试数据库连接
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # 创建数据库表
            Base.metadata.create_all(bind=engine)
            logger.info("📊 数据库表初始化完成")
            break
            
        except Exception as e:
            logger.warning(f"数据库连接失败 (第 {attempt + 1} 次): {e}")
            if attempt < max_retries - 1:
                logger.info(f"等待 {retry_delay} 秒后重试...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
            else:
                logger.error("数据库连接失败，应用启动失败")
                raise
    
    yield
    
    # 关闭时清理
    logger.info("🛑 关闭 ModelVS3 Agent Platform")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="现代化的多模型 Agent 平台",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 中间件配置
# 解析CORS来源列表
cors_origins = []
if settings.cors_origins:
    cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """指标收集中间件"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response


@app.middleware("http") 
async def rate_limit_middleware_handler(request: Request, call_next):
    """速率限制中间件"""
    return await rate_limit_middleware(request, call_next)


@app.middleware("http")
async def auth_middleware_handler(request: Request, call_next):
    """认证中间件"""
    return await auth_middleware(request, call_next)


# 异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": exc.status_code,
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "服务器内部错误",
            "error_code": 500,
            "timestamp": time.time()
        }
    )


# 路由注册
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(models.router, prefix="/api/v1/models", tags=["模型管理"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agent 管理"])
app.include_router(advanced_agents.router, prefix="/api/v1/advanced-agents", tags=["高级Agent管理"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["工具管理"])
app.include_router(runs.router, prefix="/api/v1/runs", tags=["执行管理"])
app.include_router(chat.router, prefix="/v1", tags=["OpenAI 兼容接口"])
app.include_router(chat_test.router, prefix="/api/v1/chat-test", tags=["模型测试对话"])
app.include_router(chat_history.router, prefix="/api/v1/chat-history", tags=["聊天历史记录"])
app.include_router(chat_sessions.router, prefix="/api/v1/chat-sessions", tags=["聊天会话管理"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["仪表板"])


# 健康检查
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": time.time()
    }


# Prometheus 指标端点
@app.get("/metrics", tags=["系统"])
async def metrics():
    """Prometheus 指标"""
    from fastapi import Response
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# 根路径
@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用 {settings.app_name}!",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }


# 静态文件服务（如果有前端）
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    # 如果 static 目录不存在，跳过
    pass


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers
    ) 
"""中间件模块"""

import time
import redis
import jwt
from datetime import timedelta
from typing import Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User

# Redis 客户端（用于速率限制）
try:
    redis_client = redis.from_url(settings.redis_url)
except Exception:
    redis_client = None


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """验证JWT token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token"
        )


async def get_current_user_from_token(token: str, db: Session) -> User:
    """从token获取当前用户"""
    payload = verify_jwt_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    return user


async def rate_limit_middleware(request: Request, call_next):
    """速率限制中间件"""
    # 跳过某些路径
    skip_paths = ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
    if any(request.url.path.startswith(path) for path in skip_paths):
        return await call_next(request)
    
    if not redis_client:
        # 如果 Redis 不可用，跳过速率限制
        return await call_next(request)
    
    try:
        # 获取客户端 IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 生成速率限制键
        rate_limit_key = f"rate_limit:{client_ip}"
        
        # 检查当前请求数
        current_requests = redis_client.get(rate_limit_key)
        if current_requests is None:
            # 第一次请求，设置计数器
            redis_client.setex(rate_limit_key, 60, 1)
        else:
            current_count = int(current_requests)
            if current_count >= settings.rate_limit_requests_per_minute:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "success": False,
                        "message": "请求过于频繁，请稍后重试",
                        "error_code": 429,
                        "timestamp": time.time()
                    }
                )
            # 增加计数器
            redis_client.incr(rate_limit_key)
        
        return await call_next(request)
        
    except Exception as e:
        # 如果速率限制出错，记录日志但不阻止请求
        print(f"速率限制错误: {e}")
        return await call_next(request)


async def auth_middleware(request: Request, call_next):
    """认证中间件"""
    # 跳过不需要认证的路径
    skip_paths = [
        "/health", "/metrics", "/docs", "/redoc", "/openapi.json",
        "/", "/api/v1/auth/login", "/api/v1/auth/register"
    ]
    
    if any(request.url.path.startswith(path) for path in skip_paths):
        return await call_next(request)
    
    # 检查 Authorization 头
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "需要认证令牌",
                "error_code": 401,
                "timestamp": time.time()
            }
        )
    
    # 验证 JWT token
    try:
        token = auth_header.replace("Bearer ", "")
        payload = verify_jwt_token(token)
        
        # 将用户信息添加到请求状态中
        request.state.user_id = payload.get("sub")
        request.state.user_payload = payload
        
        # 处理响应
        response = await call_next(request)
        
        # 检查token是否需要刷新
        from datetime import datetime
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            exp_time = datetime.fromtimestamp(exp_timestamp)
            time_until_expiry = exp_time - datetime.utcnow()
            
            # 如果token在刷新阈值时间内过期，建议前端刷新
            refresh_threshold = timedelta(minutes=settings.token_refresh_threshold_minutes)
            if time_until_expiry <= refresh_threshold:
                response.headers["X-Token-Refresh-Suggested"] = "true"
                response.headers["X-Token-Expires-In"] = str(int(time_until_expiry.total_seconds()))
        
        return response
        
    except HTTPException:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "无效的认证令牌",
                "error_code": 401,
                "timestamp": time.time()
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "认证失败",
                "error_code": 401,
                "timestamp": time.time()
            }
        ) 
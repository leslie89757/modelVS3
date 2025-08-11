"""应用配置模块"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置"""
    
    # 基础配置
    app_name: str = "ModelVS3 Agent Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = "change-this-in-production"
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # 数据库配置
    database_url: str = "postgresql://postgres:password@localhost:5432/modelvs3"
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT 配置
    jwt_secret_key: str = "your-jwt-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24小时 = 1440分钟
    token_refresh_threshold_minutes: int = 480  # 8小时后开始自动刷新
    
    # LLM 提供商 API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # 速率限制
    rate_limit_requests_per_minute: int = 60
    rate_limit_tokens_per_minute: int = 100000
    
    # 成本控制
    daily_budget_usd: float = 100.0
    monthly_budget_usd: float = 3000.0
    
    # 监控配置
    prometheus_port: int = 8090
    grafana_port: int = 3001
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"
    
    # CORS 配置 - 现在从环境变量读取
    cors_origins: str = "http://localhost:3000,http://localhost:3003,http://localhost:3004,http://127.0.0.1:3000,http://127.0.0.1:3003,http://127.0.0.1:3004"
    
    # 公网访问配置
    public_host: str = "36.153.25.22"  # 正式环境的公网IP
    production_port: int = 3003  # 正式环境端口
    
    # 外部服务
    webhook_secret: Optional[str] = None
    notification_email: str = "admin@example.com"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局设置实例
settings = Settings() 
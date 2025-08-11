#!/bin/bash

# ModelVS3 Agent Platform 快速启动脚本

echo "🚀 启动 ModelVS3 Agent Platform..."

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建环境变量文件（如果不存在）
if [ ! -f .env ]; then
    echo "📝 创建环境变量文件..."
    cat > .env << EOF
# 基础配置
APP_NAME=ModelVS3 Agent Platform
DEBUG=true
SECRET_KEY=your-secret-key-here-change-in-production

# 数据库配置
DATABASE_URL=postgresql://postgres:password@postgres:5432/modelvs3
REDIS_URL=redis://redis:6379/0

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM API Keys (请替换为您的实际 API Key)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key

# 速率限制
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# 成本控制
DAILY_BUDGET_USD=100.0
MONTHLY_BUDGET_USD=3000.0
EOF

    echo "✅ 已创建 .env 文件，请编辑并设置您的 API Key"
fi

# 停止可能正在运行的服务
echo "🛑 停止现有服务..."
docker-compose down

# 构建并启动服务
echo "🔨 构建并启动服务..."
docker-compose up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 显示访问地址
echo ""
echo "🎉 ModelVS3 Agent Platform 启动成功！"
echo ""
echo "📖 访问地址："
echo "  • 前端界面: http://localhost:3000"
echo "  • API 文档: http://localhost:8000/docs"
echo "  • Grafana 监控: http://localhost:3001 (admin/admin)"
echo "  • Prometheus: http://localhost:8090"
echo ""
echo "📝 查看日志："
echo "  docker-compose logs -f"
echo ""
echo "🛑 停止服务："
echo "  docker-compose down" 
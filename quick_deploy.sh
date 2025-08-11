#!/bin/bash

# ModelVS3 一键Docker部署脚本
# 适用于全新部署

set -e  # 遇到错误立即退出

echo "🚀 ModelVS3 AI Agent平台 - 一键Docker部署"
echo "================================================"

# 检查Docker环境
if ! command -v docker &> /dev/null; then
    echo "❌ 请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 请先安装Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker环境检查通过"

# 设置权限
chmod +x scripts/*.sh 2>/dev/null || true

# 创建.env文件（如果不存在）
if [ ! -f .env ]; then
    echo "📝 创建环境配置文件..."
    cat > .env << 'EOF'
# ModelVS3 基础配置
APP_NAME=ModelVS3
DEBUG=false
SECRET_KEY=super-secret-key-change-in-production-32chars

# 数据库配置
DATABASE_URL=postgresql://postgres:modelVS3_pwd_2024@postgres:5432/modelvs3
REDIS_URL=redis://redis:6379/0

# JWT 配置
JWT_SECRET_KEY=jwt-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API Keys（请替换为您的真实密钥）
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GOOGLE_API_KEY=your-google-api-key-here

# 安全配置
CORS_ORIGINS=http://localhost:3003,http://127.0.0.1:3003,http://localhost:3000

# 监控配置
ENABLE_METRICS=true
GF_SECURITY_ADMIN_PASSWORD=admin123
EOF

    echo "✅ 已创建.env配置文件"
    echo "⚠️  请编辑.env文件设置您的API密钥"
fi

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose down -v 2>/dev/null || true

# 清理旧镜像（可选）
read -p "🧹 是否清理旧的Docker镜像？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker system prune -f
    echo "✅ 已清理旧镜像"
fi

# 构建并启动服务
echo "🔨 构建并启动所有服务..."
docker-compose up --build -d

# 等待服务启动
echo "⏳ 等待服务启动完成..."
sleep 20

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 等待数据库就绪
echo "🗄️ 等待数据库就绪..."
until docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "   等待PostgreSQL启动..."
    sleep 3
done

# 运行数据库初始化
echo "🔧 初始化数据库..."
docker-compose exec -T api alembic upgrade head 2>/dev/null || {
    echo "⚠️  数据库迁移可能需要手动运行："
    echo "   docker-compose exec api alembic upgrade head"
}

# 健康检查
echo "🏥 服务健康检查..."
sleep 5

# 检查API服务
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API服务正常"
else
    echo "⚠️  API服务可能还在启动中"
fi

# 检查前端服务
if curl -f -s http://localhost:3003 > /dev/null 2>&1; then
    echo "✅ 前端服务正常"
else
    echo "⚠️  前端服务可能还在启动中"
fi

echo ""
echo "🎉 ModelVS3 部署完成！"
echo "================================================"
echo ""
echo "📱 访问地址："
echo "  🌐 前端界面:   http://localhost:3003"
echo "  📖 API文档:    http://localhost:8000/docs"
echo "  📊 Grafana:    http://localhost:3001 (admin/admin123)"
echo "  🔍 Prometheus: http://localhost:8090"
echo ""
echo "🔑 默认账户："
echo "  管理员: admin@example.com / admin123"
echo "  演示用户: demo@example.com / demo123"
echo ""
echo "🛠️ 常用命令："
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo ""
echo "⚠️  重要提醒："
echo "  1. 请编辑.env文件设置您的LLM API密钥"
echo "  2. 生产环境请修改默认密码和密钥"
echo "  3. 首次使用可能需要几分钟初始化"
echo ""

# 显示实时日志选项
read -p "🔍 是否查看实时日志？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📋 显示实时日志（Ctrl+C退出）..."
    docker-compose logs -f
fi

echo "✨ 部署完成，享受您的AI Agent平台！" 
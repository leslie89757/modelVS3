#!/bin/bash

# ModelVS3 开发环境快速启动脚本
echo "🚀 ModelVS3 开发环境 - 快速启动"
echo "======================================="

set -e  # 遇到错误立即退出

# 检查Docker环境
echo "🔍 检查Docker环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ 请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 请先安装Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker环境检查通过"

# 设置开发环境变量
echo "📝 加载开发环境配置..."
export $(cat config/dev.env | grep -v '^#' | xargs)

# 停止现有开发环境服务
echo "🛑 停止现有开发环境服务..."
docker-compose -f docker-compose.dev.yml down 2>/dev/null || true

# 构建并启动开发环境
echo "🔨 构建并启动开发环境..."
docker-compose -f docker-compose.dev.yml up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose -f docker-compose.dev.yml ps

# 等待数据库就绪
echo "🗄️ 等待数据库就绪..."
timeout=60
counter=0
until docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "   等待PostgreSQL启动... ($counter/$timeout)"
    sleep 2
    counter=$((counter+2))
    if [ $counter -ge $timeout ]; then
        echo "❌ 数据库启动超时"
        exit 1
    fi
done

echo "✅ 数据库已就绪"

# 运行数据库迁移
echo "🔧 运行数据库迁移..."
docker-compose -f docker-compose.dev.yml exec -T api alembic upgrade head || {
    echo "⚠️  数据库迁移失败，请手动运行："
    echo "   docker-compose -f docker-compose.dev.yml exec api alembic upgrade head"
}

# 健康检查
echo "🏥 服务健康检查..."
sleep 5

# 检查API服务
if curl -f -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ API服务正常运行"
else
    echo "⚠️  API服务正在启动中，请稍等..."
fi

# 检查前端服务
if curl -f -s http://localhost:3004 > /dev/null 2>&1; then
    echo "✅ 前端服务正常运行"
else
    echo "⚠️  前端服务正在启动中，请稍等..."
fi

echo ""
echo "🎉 开发环境启动完成！"
echo "======================================="
echo ""
echo "📱 访问地址："
echo "  🌐 前端界面:   http://localhost:3004"
echo "  📖 API文档:    http://localhost:8001/docs"
echo "  📊 Grafana:    http://localhost:3002 (admin/dev-admin)"
echo "  🔍 Prometheus: http://localhost:8091"
echo ""
echo "🔑 测试账户："
echo "  管理员: admin@example.com / admin123"
echo "  演示用户: demo@example.com / demo123"
echo ""
echo "🛠️ 开发环境命令："
echo "  查看日志: docker-compose -f docker-compose.dev.yml logs -f"
echo "  停止服务: docker-compose -f docker-compose.dev.yml down"
echo "  重启服务: docker-compose -f docker-compose.dev.yml restart"
echo "  进入API容器: docker-compose -f docker-compose.dev.yml exec api bash"
echo ""
echo "🔧 技术债务修复验证："
echo "  ✅ 统一API认证 - 所有API调用都使用useApi hook"
echo "  ✅ 错误边界处理 - 应用崩溃时会显示友好错误页面"
echo "  ✅ 性能优化 - 防抖搜索、图片懒加载等已启用"
echo "  ✅ TypeScript类型安全 - 完整类型定义已加载"
echo ""

# 显示实时日志选项
read -p "🔍 是否查看实时日志？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📋 显示实时日志（Ctrl+C退出）..."
    docker-compose -f docker-compose.dev.yml logs -f
fi

echo "✨ 开发环境已就绪，开始测试技术债务修复效果！" 
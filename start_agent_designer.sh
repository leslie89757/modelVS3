#!/bin/bash

echo "🚀 启动 ModelVS3 Agent 设计器"
echo "=================================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

echo "✅ Docker 环境检查通过"

# 停止现有容器
echo "🛑 停止现有容器..."
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

# 检查服务健康状态
echo "🏥 检查服务健康状态..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/v1/models > /dev/null 2>&1; then
        echo "✅ 后端 API 服务已就绪"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ 后端 API 服务启动超时"
        echo "📋 请检查日志: docker-compose logs api"
        exit 1
    fi
    echo "⏰ 等待后端服务启动... ($i/30)"
    sleep 2
done

for i in {1..15}; do
    if curl -s http://localhost:3003 > /dev/null 2>&1; then
        echo "✅ 前端服务已就绪"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ 前端服务启动超时"
        echo "📋 请检查日志: docker-compose logs frontend"
        exit 1
    fi
    echo "⏰ 等待前端服务启动... ($i/15)"
    sleep 2
done

echo ""
echo "🎉 Agent 设计器启动成功！"
echo "=================================="
echo "📱 前端访问地址: http://localhost:3003"
echo "🎨 Agent 设计器: http://localhost:3003/agent-designer"  
echo "🔧 后端 API: http://localhost:8000"
echo "📊 Grafana 监控: http://localhost:3001 (admin/admin)"
echo "📈 Prometheus: http://localhost:8090"
echo ""
echo "🔍 查看日志命令:"
echo "   docker-compose logs -f"
echo "   docker-compose logs frontend"
echo "   docker-compose logs api"
echo ""
echo "🛑 停止服务命令:"
echo "   docker-compose down"
echo ""

# 自动打开浏览器（如果可能）
if command -v xdg-open &> /dev/null; then
    echo "🌐 正在打开浏览器..."
    xdg-open http://localhost:3003/agent-designer
elif command -v open &> /dev/null; then
    echo "🌐 正在打开浏览器..."
    open http://localhost:3003/agent-designer
else
    echo "💡 请手动在浏览器中访问: http://localhost:3003/agent-designer"
fi

echo "✨ 享受您的 Agent 设计之旅！"
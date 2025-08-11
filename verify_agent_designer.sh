#!/bin/bash

echo "🔍 Agent 设计器功能验证"
echo "========================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查函数
check_service() {
    local service_name=$1
    local url=$2
    local expected_code=$3
    
    echo -n "检查 $service_name... "
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null); then
        if [ "$response" = "$expected_code" ]; then
            echo -e "${GREEN}✅ 正常${NC} (HTTP $response)"
            return 0
        else
            echo -e "${YELLOW}⚠️  异常${NC} (HTTP $response, 期望 $expected_code)"
            return 1
        fi
    else
        echo -e "${RED}❌ 无法连接${NC}"
        return 1
    fi
}

# 检查端口
check_port() {
    local port=$1
    local service=$2
    
    echo -n "检查端口 $port ($service)... "
    
    if nc -z localhost $port 2>/dev/null; then
        echo -e "${GREEN}✅ 开放${NC}"
        return 0
    else
        echo -e "${RED}❌ 关闭${NC}"
        return 1
    fi
}

echo "🔧 基础服务检查"
echo "----------------"

# 检查 Docker 服务
echo -n "检查 Docker... "
if docker info &> /dev/null; then
    echo -e "${GREEN}✅ 运行中${NC}"
else
    echo -e "${RED}❌ 未运行${NC}"
    echo "请先启动 Docker"
    exit 1
fi

# 检查 docker-compose
echo -n "检查 docker-compose... "
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✅ 已安装${NC}"
else
    echo -e "${RED}❌ 未安装${NC}"
    echo "请先安装 docker-compose"
    exit 1
fi

echo ""
echo "🌐 网络服务检查"
echo "----------------"

# 检查端口
check_port 3003 "前端服务"
check_port 8000 "后端API"
check_port 5432 "PostgreSQL"
check_port 6379 "Redis"

echo ""
echo "🔗 HTTP 服务检查"
echo "-----------------"

# 检查服务
check_service "前端主页" "http://localhost:3003" "200"
check_service "Agent 设计器" "http://localhost:3003/agent-designer" "200"
check_service "API 文档" "http://localhost:8000/docs" "200"
check_service "API 健康检查" "http://localhost:8000/api/v1/models" "200"

echo ""
echo "🗃️ 数据库连接检查"
echo "------------------"

echo -n "检查 PostgreSQL 连接... "
if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
    echo -e "${GREEN}✅ 连接正常${NC}"
else
    echo -e "${RED}❌ 连接失败${NC}"
fi

echo -n "检查 Redis 连接... "
if docker-compose exec -T redis redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✅ 连接正常${NC}"
else
    echo -e "${RED}❌ 连接失败${NC}"
fi

echo ""
echo "📋 容器状态检查"
echo "----------------"

echo "Docker Compose 服务状态："
docker-compose ps

echo ""
echo "🧪 API 功能测试"
echo "----------------"

echo -n "测试获取模型列表... "
if models_response=$(curl -s "http://localhost:8000/api/v1/models?enabled=true" 2>/dev/null); then
    if echo "$models_response" | jq . &> /dev/null; then
        model_count=$(echo "$models_response" | jq 'length' 2>/dev/null)
        echo -e "${GREEN}✅ 成功${NC} (找到 $model_count 个模型)"
    else
        echo -e "${YELLOW}⚠️  响应格式异常${NC}"
    fi
else
    echo -e "${RED}❌ 请求失败${NC}"
fi

echo -n "测试获取工具列表... "
if tools_response=$(curl -s "http://localhost:8000/api/v1/tools" 2>/dev/null); then
    if echo "$tools_response" | jq . &> /dev/null; then
        tool_count=$(echo "$tools_response" | jq 'length' 2>/dev/null)
        echo -e "${GREEN}✅ 成功${NC} (找到 $tool_count 个工具)"
    else
        echo -e "${YELLOW}⚠️  响应格式异常${NC}"
    fi
else
    echo -e "${RED}❌ 请求失败${NC}"
fi

echo ""
echo "📊 系统资源检查"
echo "----------------"

# 检查磁盘空间
echo -n "检查磁盘空间... "
disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$disk_usage" -lt 80 ]; then
    echo -e "${GREEN}✅ 充足${NC} (已使用 $disk_usage%)"
elif [ "$disk_usage" -lt 90 ]; then
    echo -e "${YELLOW}⚠️  较少${NC} (已使用 $disk_usage%)"
else
    echo -e "${RED}❌ 不足${NC} (已使用 $disk_usage%)"
fi

# 检查内存使用
echo -n "检查内存使用... "
if command -v free &> /dev/null; then
    mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$mem_usage" -lt 80 ]; then
        echo -e "${GREEN}✅ 正常${NC} (已使用 $mem_usage%)"
    elif [ "$mem_usage" -lt 90 ]; then
        echo -e "${YELLOW}⚠️  较高${NC} (已使用 $mem_usage%)"
    else
        echo -e "${RED}❌ 过高${NC} (已使用 $mem_usage%)"
    fi
else
    echo -e "${BLUE}ℹ️  无法检测${NC}"
fi

echo ""
echo "🎯 验证总结"
echo "============"

echo -e "${BLUE}🌐 访问地址：${NC}"
echo "  • Agent 设计器: http://localhost:3003/agent-designer"
echo "  • 主应用:      http://localhost:3003"
echo "  • API 文档:    http://localhost:8000/docs"
echo "  • Grafana:     http://localhost:3001"

echo ""
echo -e "${BLUE}🔧 管理命令：${NC}"
echo "  • 查看日志:    docker-compose logs -f"
echo "  • 重启服务:    docker-compose restart"
echo "  • 停止服务:    docker-compose down"

echo ""
echo -e "${BLUE}📝 功能测试清单：${NC}"
echo "  [ ] 访问 Agent 设计器页面"
echo "  [ ] 创建新的 Agent 配置"
echo "  [ ] 测试实时对话调试"
echo "  [ ] 验证工具调用展示"
echo "  [ ] 检查自动保存功能"

echo ""
if check_service "Agent 设计器" "http://localhost:3003/agent-designer" "200" &> /dev/null; then
    echo -e "${GREEN}🎉 Agent 设计器验证完成！可以开始使用了！${NC}"
    
    # 询问是否打开浏览器
    read -p "是否自动打开 Agent 设计器？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v open &> /dev/null; then
            open http://localhost:3003/agent-designer
        elif command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:3003/agent-designer
        else
            echo "请手动打开: http://localhost:3003/agent-designer"
        fi
    fi
else
    echo -e "${RED}❌ Agent 设计器验证失败，请检查服务状态！${NC}"
    echo ""
    echo "建议执行以下命令排查问题："
    echo "  docker-compose logs frontend"
    echo "  docker-compose logs api"
fi
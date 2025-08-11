#!/bin/bash

# ModelVS3 工具注册便捷脚本
# 用于快速注册所有Function Call工具到指定环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 ModelVS3 工具注册脚本${NC}"
echo "=================================="

# 检查Python3和所需模块
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 请先安装Python3${NC}"
    exit 1
fi

# 选择环境
echo ""
echo -e "${YELLOW}请选择要注册工具的环境:${NC}"
echo "1) 开发环境 (docker-compose.dev.yml)"
echo "2) 生产环境 (docker-compose.production.yml)"
read -p "请输入选择 (1-2): " env_choice

case $env_choice in
    1)
        ENV_NAME="开发环境"
        DEV_FLAG="--dev"
        COMPOSE_FILE="docker-compose.dev.yml"
        ;;
    2)
        ENV_NAME="生产环境"
        DEV_FLAG=""
        COMPOSE_FILE="docker-compose.production.yml"
        ;;
    *)
        echo -e "${RED}❌ 无效选择，默认使用生产环境${NC}"
        ENV_NAME="生产环境"
        DEV_FLAG=""
        COMPOSE_FILE="docker-compose.production.yml"
        ;;
esac

echo -e "${BLUE}📋 选择的环境: ${ENV_NAME}${NC}"
echo ""

# 检查Docker服务是否运行
echo -e "${BLUE}🔍 检查Docker服务状态...${NC}"
if ! sudo docker-compose -f $COMPOSE_FILE ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Docker服务未运行，正在启动...${NC}"
    sudo docker-compose -f $COMPOSE_FILE up -d
    echo -e "${BLUE}⏳ 等待服务启动...${NC}"
    sleep 15
fi

# 检查数据库是否就绪
echo -e "${BLUE}🗄️ 等待数据库就绪...${NC}"
timeout=30
counter=0
until sudo docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "   等待PostgreSQL启动... ($counter/$timeout)"
    sleep 2
    counter=$((counter+2))
    if [ $counter -ge $timeout ]; then
        echo -e "${RED}❌ 数据库启动超时${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ 数据库就绪${NC}"

# 运行工具注册脚本
echo ""
echo -e "${BLUE}🚀 开始注册工具到${ENV_NAME}...${NC}"
echo "=================================="

# 在API容器内运行注册脚本
sudo docker-compose -f $COMPOSE_FILE exec api python3 scripts/register_all_tools_docker.py $DEV_FLAG

# 显示结果
echo ""
echo -e "${GREEN}🎉 工具注册完成！${NC}"
echo "=================================="
echo -e "${BLUE}📱 访问地址：${NC}"

if [[ $env_choice == "1" ]]; then
    echo "  🌐 前端界面:   http://localhost:3004"
    echo "  🛠️ 工具管理:   http://localhost:3004/tools"
    echo "  📖 API文档:    http://localhost:8001/docs"
else
    echo "  🌐 前端界面:   http://36.153.25.22:3003"
    echo "  🛠️ 工具管理:   http://36.153.25.22:3003/tools"
    echo "  📖 API文档:    http://36.153.25.22:3003/docs"
fi

echo ""
echo -e "${YELLOW}💡 提示：${NC}"
echo "  - 现在可以在前端工具管理页面看到所有注册的工具"
echo "  - Agent创建时可以选择并使用这些工具"
echo "  - 如需重新注册，直接再次运行此脚本即可"
echo ""

# 询问是否查看工具列表
read -p "🔍 是否查看已注册的工具列表？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}📋 已注册的工具列表：${NC}"
    echo "=================================="
    
    # 通过API查看工具列表
    if [[ $env_choice == "1" ]]; then
        curl -s http://localhost:8001/api/v1/tools/ | python3 -m json.tool 2>/dev/null || echo "无法获取工具列表，请检查API服务"
    else
        curl -s http://36.153.25.22:3003/api/v1/tools/ | python3 -m json.tool 2>/dev/null || echo "无法获取工具列表，请检查API服务"
    fi
fi

echo -e "${GREEN}✨ 工具注册脚本执行完成！${NC}"
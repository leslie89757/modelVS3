#!/bin/bash

# 快速工具注册脚本
# 用途: 简化的工具注册流程

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 ModelVS3 快速工具注册脚本${NC}"
echo "================================="

# 检查是否在项目根目录
if [ ! -f "scripts/register_all_tools.py" ]; then
    echo -e "${RED}❌ 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 检查Python是否可用
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未找到，请先安装Python3${NC}"
    exit 1
fi

# 检查服务是否运行
echo -e "${BLUE}[INFO]${NC} 检查服务状态..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${YELLOW}⚠️ API服务未运行，请先启动服务:${NC}"
    echo "   docker-compose -f docker-compose.production.yml up -d"
    exit 1
fi

echo -e "${GREEN}✅ API服务运行正常${NC}"

# 执行工具注册
echo -e "${BLUE}[INFO]${NC} 开始注册工具..."
echo ""

if python3 scripts/register_all_tools.py; then
    echo ""
    echo -e "${GREEN}🎉 工具注册成功！${NC}"
    echo ""
    echo "下一步操作:"
    echo -e "  ${BLUE}1.${NC} 访问前端界面: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):3003"
    echo -e "  ${BLUE}2.${NC} 查看工具管理: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):3003/tools"
    echo -e "  ${BLUE}3.${NC} 创建Agent并选择工具"
    echo ""
else
    echo ""
    echo -e "${RED}❌ 工具注册失败${NC}"
    echo ""
    echo "故障排除建议:"
    echo "  1. 检查数据库是否运行: docker-compose ps postgres"
    echo "  2. 查看API日志: docker-compose logs api"
    echo "  3. 手动执行: python3 scripts/register_all_tools.py"
    echo ""
    exit 1
fi 
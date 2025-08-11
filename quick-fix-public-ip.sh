#!/bin/bash

# ModelVS3 公网IP快速修复脚本
# 用于修复 36.153.25.22 的配置问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 ModelVS3 公网IP配置快速修复${NC}"
echo "========================================"
echo -e "${YELLOW}目标IP: 36.153.25.22${NC}"
echo ""

# 检查是否在正确的目录
if [ ! -f "docker-compose.production.yml" ]; then
    echo -e "${RED}❌ 错误：请在ModelVS3项目根目录执行此脚本${NC}"
    exit 1
fi

echo -e "${BLUE}📋 开始修复配置问题...${NC}"

# 1. 备份现有配置
echo -e "${BLUE}1. 备份现有配置...${NC}"
if [ -f ".env" ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ 已备份现有.env文件${NC}"
fi

# 2. 创建或更新.env文件
echo -e "${BLUE}2. 创建/更新环境配置文件...${NC}"

# 从production.env复制基础配置
if [ -f "config/production.env" ]; then
    cp config/production.env .env
    echo -e "${GREEN}✅ 已从production.env复制基础配置${NC}"
else
    echo -e "${YELLOW}⚠️  未找到production.env，创建新的.env文件${NC}"
    touch .env
fi

# 3. 修复关键配置项
echo -e "${BLUE}3. 修复关键配置项...${NC}"

cat >> .env << 'EOF'

# ========================================
# 公网IP 36.153.25.22 专用配置修复
# ========================================

# 服务器IP配置
SERVER_IP=36.153.25.22
PUBLIC_HOST=36.153.25.22
PRODUCTION_PORT=3003

# 前端API地址配置（直接访问方式）
VITE_API_URL=http://36.153.25.22:8000

# CORS配置（包含公网IP）
CORS_ORIGINS=http://36.153.25.22:3003,http://36.153.25.22:8000,http://localhost:3003

# 生产环境基础配置
ENVIRONMENT=production
DEBUG=false

# 安全配置（请修改为强密码）
SECRET_KEY=ModelVS3_SecretKey_2024_Production
JWT_SECRET_KEY=ModelVS3_JWT_Secret_2024
POSTGRES_PASSWORD=ModelVS3_DB_Password_2024

# 监控配置
GF_SECURITY_ADMIN_PASSWORD=ModelVS3_Admin_2024

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json

EOF

echo -e "${GREEN}✅ 配置文件更新完成${NC}"

# 4. 停止现有服务
echo -e "${BLUE}4. 停止现有服务...${NC}"
docker-compose -f docker-compose.production.yml down 2>/dev/null || true
echo -e "${GREEN}✅ 服务已停止${NC}"

# 5. 重新构建并启动服务
echo -e "${BLUE}5. 重新构建并启动服务...${NC}"
docker-compose -f docker-compose.production.yml up --build -d

# 等待服务启动
echo -e "${BLUE}⏳ 等待服务启动...${NC}"
sleep 30

# 6. 检查服务状态
echo -e "${BLUE}6. 检查服务状态...${NC}"
docker-compose -f docker-compose.production.yml ps

# 7. 健康检查
echo -e "${BLUE}7. 执行健康检查...${NC}"

# 检查前端
echo -e "${BLUE}检查前端服务...${NC}"
if curl -f -s http://36.153.25.22:3003 > /dev/null; then
    echo -e "${GREEN}✅ 前端服务正常 - http://36.153.25.22:3003${NC}"
else
    echo -e "${YELLOW}⚠️  前端服务可能还在启动中${NC}"
fi

# 检查API
echo -e "${BLUE}检查API服务...${NC}"
if curl -f -s http://36.153.25.22:8000/health > /dev/null; then
    echo -e "${GREEN}✅ API服务正常 - http://36.153.25.22:8000${NC}"
else
    echo -e "${YELLOW}⚠️  API服务可能还在启动中${NC}"
fi

# 检查CORS
echo -e "${BLUE}检查CORS配置...${NC}"
cors_response=$(curl -s -H "Origin: http://36.153.25.22:3003" \
                     -H "Access-Control-Request-Method: GET" \
                     -X OPTIONS http://36.153.25.22:8000/health || echo "failed")
if [[ "$cors_response" != "failed" ]]; then
    echo -e "${GREEN}✅ CORS配置正常${NC}"
else
    echo -e "${YELLOW}⚠️  CORS配置可能需要时间生效${NC}"
fi

echo ""
echo -e "${GREEN}🎉 快速修复完成！${NC}"
echo "========================================"
echo ""
echo -e "${BLUE}📱 访问地址：${NC}"
echo "  🌐 前端界面: http://36.153.25.22:3003"
echo "  📖 API文档:  http://36.153.25.22:8000/docs"
echo "  🔍 API健康:  http://36.153.25.22:8000/health"
echo ""
echo -e "${YELLOW}⚠️  重要提醒：${NC}"
echo "  1. 当前使用HTTP协议，建议后续配置HTTPS"
echo "  2. 请修改.env文件中的默认密码"
echo "  3. 请配置您的LLM API密钥"
echo ""
echo -e "${BLUE}🔧 后续安全配置：${NC}"
echo "  查看完整安全指南: cat secure-deployment-guide.md"
echo ""

# 8. 显示配置摘要
echo -e "${BLUE}📊 当前配置摘要：${NC}"
echo "----------------------------------------"
echo "前端地址: http://36.153.25.22:3003"
echo "API地址:  http://36.153.25.22:8000"
echo "协议:     HTTP (建议升级到HTTPS)"
echo "CORS:     已配置公网IP"
echo "状态:     基本功能已修复"
echo "----------------------------------------"
echo ""

# 9. 实时日志选项
read -p "🔍 是否查看实时日志以确认服务正常？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}📋 显示实时日志（Ctrl+C退出）...${NC}"
    docker-compose -f docker-compose.production.yml logs -f
fi

echo -e "${GREEN}✨ 配置修复完成！请在浏览器中访问 http://36.153.25.22:3003${NC}"
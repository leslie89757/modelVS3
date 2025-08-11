#!/bin/bash

# ModelVS3 环境管理脚本
# 用途: 管理开发环境和生产环境的启动、停止和切换

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo -e "${BLUE}🔧 ModelVS3 环境管理脚本${NC}"
    echo "=================================="
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo -e "  ${GREEN}start-dev${NC}     启动开发环境 (端口: 3004, 8001)"
    echo -e "  ${GREEN}start-prod${NC}    启动生产环境 (端口: 3003, 8000)"
    echo -e "  ${GREEN}stop-dev${NC}      停止开发环境"
    echo -e "  ${GREEN}stop-prod${NC}     停止生产环境"
    echo -e "  ${GREEN}status${NC}        查看环境状态"
    echo -e "  ${GREEN}switch-to-dev${NC} 切换到开发环境 (停止生产,启动开发)"
    echo -e "  ${GREEN}switch-to-prod${NC} 切换到生产环境 (停止开发,启动生产)"
    echo -e "  ${GREEN}stop-all${NC}      停止所有环境"
    echo -e "  ${GREEN}logs-dev${NC}      查看开发环境日志"
    echo -e "  ${GREEN}logs-prod${NC}     查看生产环境日志"
    echo ""
    echo "环境配置:"
    echo -e "  ${CYAN}开发环境${NC}: localhost:3004 → localhost:8001 (数据库: modelvs3_dev)"
    echo -e "  ${CYAN}生产环境${NC}: localhost:3003 → localhost:8000 (数据库: modelvs3)"
    echo -e "  ${CYAN}远程生产${NC}: 192.168.3.27:3003 → 192.168.3.27:8000"
    echo ""
}

# 检查服务状态
check_status() {
    echo -e "${BLUE}📊 环境状态检查${NC}"
    echo "===================="
    
    # 检查开发环境
    echo -e "\n${CYAN}🔧 开发环境状态:${NC}"
    if docker-compose -f docker-compose.dev.yml ps 2>/dev/null | grep -q "Up"; then
        echo -e "  状态: ${GREEN}运行中${NC}"
        echo "  前端: http://localhost:3004"
        echo "  API:  http://localhost:8001"
        if curl -s http://localhost:8001/health >/dev/null 2>&1; then
            echo -e "  健康: ${GREEN}正常${NC}"
        else
            echo -e "  健康: ${RED}异常${NC}"
        fi
    else
        echo -e "  状态: ${YELLOW}未运行${NC}"
    fi
    
    # 检查生产环境
    echo -e "\n${CYAN}🚀 本机生产环境状态:${NC}"
    if docker-compose ps 2>/dev/null | grep -q "Up"; then
        echo -e "  状态: ${GREEN}运行中${NC}"
        echo "  前端: http://localhost:3003"
        echo "  API:  http://localhost:8000"
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            echo -e "  健康: ${GREEN}正常${NC}"
        else
            echo -e "  健康: ${RED}异常${NC}"
        fi
    else
        echo -e "  状态: ${YELLOW}未运行${NC}"
    fi
    
    # 检查远程生产环境
    echo -e "\n${CYAN}🌐 远程生产环境状态:${NC}"
    if curl -s http://192.168.3.27:3003 >/dev/null 2>&1; then
        echo -e "  状态: ${GREEN}可访问${NC}"
        echo "  前端: http://192.168.3.27:3003"
        echo "  API:  http://192.168.3.27:8000"
        if curl -s http://192.168.3.27:8000/health >/dev/null 2>&1; then
            echo -e "  健康: ${GREEN}正常${NC}"
        else
            echo -e "  健康: ${YELLOW}API不可访问${NC}"
        fi
    else
        echo -e "  状态: ${YELLOW}不可访问${NC}"
    fi
}

# 启动开发环境
start_dev() {
    echo -e "${BLUE}🔧 启动开发环境...${NC}"
    
    # 检查文件存在
    if [ ! -f "docker-compose.dev.yml" ]; then
        echo -e "${RED}❌ 找不到 docker-compose.dev.yml 文件${NC}"
        exit 1
    fi
    
    # 启动开发环境
    docker-compose -f docker-compose.dev.yml up -d --build
    
    echo -e "${BLUE}⏳ 等待服务启动...${NC}"
    sleep 15
    
    # 验证启动
    if curl -s http://localhost:8001/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ 开发环境启动成功！${NC}"
        echo ""
        echo "🌐 访问地址:"
        echo "  前端: http://localhost:3004"
        echo "  API:  http://localhost:8001/docs"
        echo ""
        echo "📝 下一步: python3 scripts/register_all_tools.py --dev"
    else
        echo -e "${RED}❌ 开发环境启动失败${NC}"
        docker-compose -f docker-compose.dev.yml logs
    fi
}

# 启动生产环境
start_prod() {
    echo -e "${BLUE}🚀 启动生产环境...${NC}"
    
    docker-compose up -d
    
    echo -e "${BLUE}⏳ 等待服务启动...${NC}"
    sleep 15
    
    # 验证启动
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ 生产环境启动成功！${NC}"
        echo ""
        echo "🌐 访问地址:"
        echo "  前端: http://localhost:3003"
        echo "  API:  http://localhost:8000/docs"
        echo ""
        echo "📝 下一步: python3 scripts/register_all_tools.py"
    else
        echo -e "${RED}❌ 生产环境启动失败${NC}"
        docker-compose logs
    fi
}

# 停止开发环境
stop_dev() {
    echo -e "${YELLOW}🛑 停止开发环境...${NC}"
    docker-compose -f docker-compose.dev.yml down
    echo -e "${GREEN}✅ 开发环境已停止${NC}"
}

# 停止生产环境
stop_prod() {
    echo -e "${YELLOW}🛑 停止生产环境...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ 生产环境已停止${NC}"
}

# 切换到开发环境
switch_to_dev() {
    echo -e "${BLUE}🔄 切换到开发环境...${NC}"
    stop_prod
    start_dev
}

# 切换到生产环境
switch_to_prod() {
    echo -e "${BLUE}🔄 切换到生产环境...${NC}"
    stop_dev
    start_prod
}

# 停止所有环境
stop_all() {
    echo -e "${YELLOW}🛑 停止所有环境...${NC}"
    stop_dev
    stop_prod
    echo -e "${GREEN}✅ 所有环境已停止${NC}"
}

# 查看开发环境日志
logs_dev() {
    echo -e "${BLUE}📄 开发环境日志:${NC}"
    docker-compose -f docker-compose.dev.yml logs -f
}

# 查看生产环境日志
logs_prod() {
    echo -e "${BLUE}📄 生产环境日志:${NC}"
    docker-compose logs -f
}

# 主逻辑
case "${1:-help}" in
    "start-dev")
        start_dev
        ;;
    "start-prod")
        start_prod
        ;;
    "stop-dev")
        stop_dev
        ;;
    "stop-prod")
        stop_prod
        ;;
    "status")
        check_status
        ;;
    "switch-to-dev")
        switch_to_dev
        ;;
    "switch-to-prod")
        switch_to_prod
        ;;
    "stop-all")
        stop_all
        ;;
    "logs-dev")
        logs_dev
        ;;
    "logs-prod")
        logs_prod
        ;;
    "help"|*)
        show_help
        ;;
esac 
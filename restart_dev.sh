#!/bin/bash

# ModelVS3 本地环境重启脚本 - 确保代码变更生效
echo "🔄 ModelVS3 本地环境重启 - 应用最新代码变更"
echo "=================================================="

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Docker环境
echo -e "${BLUE}🔍 检查Docker环境...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ 请先安装Docker: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ 请先安装Docker Compose: https://docs.docker.com/compose/install/${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker环境检查通过${NC}"

# 选择环境
echo ""
echo -e "${YELLOW}请选择要重启的环境:${NC}"
echo "1) 开发环境 (端口3004, 推荐用于测试技术债务修复)"
echo "2) 生产环境 (端口3003)"
echo "3) 同时重启两个环境"
read -p "请输入选择 (1-3): " env_choice

case $env_choice in
    1)
        COMPOSE_FILE="docker-compose.dev.yml"
        ENV_NAME="开发环境"
        FRONTEND_PORT="3004"
        API_PORT="8001"
        PROJECT_NAME="modelvs3-dev"
        ;;
    2)
        COMPOSE_FILE="docker-compose.production.yml"
        ENV_NAME="生产环境"
        FRONTEND_PORT="3003"
        API_PORT="8000"
        PROJECT_NAME="modelvs3"
        ;;
    3)
        echo -e "${BLUE}🔄 将同时重启两个环境...${NC}"
        ;;
    *)
        echo -e "${RED}❌ 无效选择，默认使用开发环境${NC}"
        COMPOSE_FILE="docker-compose.dev.yml"
        ENV_NAME="开发环境"
        FRONTEND_PORT="3004"
        API_PORT="8001"
        PROJECT_NAME="modelvs3-dev"
        ;;
esac

# 重启函数
restart_environment() {
    local compose_file=$1
    local env_name=$2
    local frontend_port=$3
    local api_port=$4
    local project_name=$5

    echo ""
    echo -e "${YELLOW}🔄 重启 ${env_name}...${NC}"
    echo "=================================="

    # 1. 停止现有服务
    echo -e "${BLUE}🛑 停止现有服务...${NC}"
    docker-compose -f $compose_file down --remove-orphans 2>/dev/null || true

    # 2. 清理旧容器和镜像（可选）
    read -p "🧹 是否清理旧容器和镜像以确保完全重建？(推荐) (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🧹 清理旧容器和镜像...${NC}"
        
        # 删除项目相关的容器
        docker ps -a --filter "name=${project_name}" -q | xargs -r docker rm -f 2>/dev/null || true
        
        # 删除项目相关的镜像
        docker images --filter "reference=${project_name}*" -q | xargs -r docker rmi -f 2>/dev/null || true
        
        # 清理未使用的构建缓存
        docker builder prune -f 2>/dev/null || true
        
        echo -e "${GREEN}✅ 清理完成${NC}"
    fi

    # 3. 重新构建并启动服务
    echo -e "${BLUE}🔨 重新构建并启动服务（这将应用所有代码变更）...${NC}"
    docker-compose -f $compose_file up --build -d

    # 4. 等待服务启动
    echo -e "${BLUE}⏳ 等待服务启动...${NC}"
    sleep 20

    # 5. 检查服务状态
    echo -e "${BLUE}📊 检查服务状态...${NC}"
    docker-compose -f $compose_file ps

    # 6. 等待数据库就绪
    echo -e "${BLUE}🗄️ 等待数据库就绪...${NC}"
    timeout=60
    counter=0
    until docker-compose -f $compose_file exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
        echo "   等待PostgreSQL启动... ($counter/$timeout)"
        sleep 2
        counter=$((counter+2))
        if [ $counter -ge $timeout ]; then
            echo -e "${RED}❌ 数据库启动超时${NC}"
            return 1
        fi
    done

    # 7. 运行数据库迁移（所有环境都需要）
    echo -e "${BLUE}🔧 运行数据库迁移...${NC}"
    docker-compose -f $compose_file exec -T api alembic upgrade head || {
        echo -e "${YELLOW}⚠️  数据库迁移可能失败，请手动运行：${NC}"
        echo "   docker-compose -f $compose_file exec api alembic upgrade head"
    }

    # 8. 健康检查
    echo -e "${BLUE}🏥 服务健康检查...${NC}"
    sleep 5

    # 检查API服务
    if curl -f -s http://localhost:$api_port/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API服务正常运行${NC}"
    else
        echo -e "${YELLOW}⚠️  API服务正在启动中，请稍等...${NC}"
    fi

    # 检查前端服务
    if curl -f -s http://localhost:$frontend_port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 前端服务正常运行${NC}"
    else
        echo -e "${YELLOW}⚠️  前端服务正在启动中，请稍等...${NC}"
    fi

    echo ""
    echo -e "${GREEN}🎉 ${env_name} 重启完成！${NC}"
    echo "=================================="
    echo ""
    echo -e "${BLUE}📱 访问地址：${NC}"
    if [[ $compose_file == *"production"* ]]; then
        echo "  🌐 前端界面:   http://36.153.25.22:$frontend_port"
        echo "  📖 API文档:    http://36.153.25.22:$frontend_port/docs"
        echo "  🔍 健康检查:   http://36.153.25.22:$frontend_port/health"
    else
        echo "  🌐 前端界面:   http://localhost:$frontend_port"
        echo "  📖 API文档:    http://localhost:$api_port/docs"
    fi
    echo ""
}

# 执行重启
if [ "$env_choice" = "3" ]; then
    # 同时重启两个环境
    restart_environment "docker-compose.dev.yml" "开发环境" "3004" "8001" "modelvs3-dev"
    restart_environment "docker-compose.production.yml" "生产环境" "3003" "8000" "modelvs3"
    
    echo ""
    echo -e "${GREEN}🎉 所有环境重启完成！${NC}"
    echo "=================================="
    echo -e "${BLUE}📱 访问地址：${NC}"
    echo "  🌐 开发环境:   http://localhost:3004"
    echo "  🌐 生产环境:   http://36.153.25.22:3003"
    echo "  📖 开发API:    http://localhost:8001/docs"
    echo "  📖 生产API:    http://36.153.25.22:3003/docs"
else
    restart_environment "$COMPOSE_FILE" "$ENV_NAME" "$FRONTEND_PORT" "$API_PORT" "$PROJECT_NAME"
fi

echo ""
echo -e "${YELLOW}🔧 技术债务修复验证清单：${NC}"
echo "=================================="
echo "请验证以下功能是否正常工作："
echo ""
echo "✅ 1. 用户登录/注册功能"
echo "   - 访问前端，尝试登录或注册新用户"
echo "   - 检查是否使用了统一的认证处理"
echo ""
echo "✅ 2. Agent管理功能"
echo "   - 创建、编辑、发布Agent"
echo "   - 检查API调用是否使用了useApi hook"
echo ""
echo "✅ 3. Agent市场功能"
echo "   - 查看公开Agent"
echo "   - 尝试分享功能"
echo ""
echo "✅ 4. 错误处理"
echo "   - 断网测试API调用"
echo "   - 检查是否显示友好错误提示"
echo ""
echo "✅ 5. 移动端适配"
echo "   - 使用手机或调整浏览器窗口大小"
echo "   - 检查移动端聊天界面"
echo ""
echo "🛠️ 常用调试命令："
echo "  查看日志: docker-compose -f $COMPOSE_FILE logs -f"
echo "  重启单个服务: docker-compose -f $COMPOSE_FILE restart [service_name]"
echo "  进入容器: docker-compose -f $COMPOSE_FILE exec [service_name] bash"
echo ""

# 显示实时日志选项
read -p "🔍 是否查看实时日志？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}📋 显示实时日志（Ctrl+C退出）...${NC}"
    if [ "$env_choice" = "3" ]; then
        echo "选择要查看的环境日志："
        echo "1) 开发环境"
        echo "2) 生产环境"
        read -p "请选择 (1-2): " log_choice
        case $log_choice in
            1) docker-compose -f docker-compose.dev.yml logs -f ;;
            2) docker-compose -f docker-compose.yml logs -f ;;
            *) docker-compose -f docker-compose.dev.yml logs -f ;;
        esac
    else
        docker-compose -f $COMPOSE_FILE logs -f
    fi
fi

echo -e "${GREEN}✨ 环境重启完成，所有代码变更已生效！开始测试吧！${NC}" 
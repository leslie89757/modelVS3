#!/bin/bash

# ModelVS3 生产环境部署脚本
# 作者: AI Assistant
# 用途: 在远程Linux服务器上一键部署ModelVS3平台

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查内存
    mem_total=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [ "$mem_total" -lt 2048 ]; then
        log_warning "系统内存少于2GB，可能影响性能"
    fi
    
    # 检查磁盘空间
    disk_free=$(df / | awk 'NR==2{print $4}')
    if [ "$disk_free" -lt 5242880 ]; then  # 5GB in KB
        log_warning "磁盘剩余空间少于5GB，可能不足"
    fi
    
    log_success "系统要求检查完成"
}

# 获取服务器IP
get_server_ip() {
    local ip=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || curl -s api.ipify.org 2>/dev/null)
    if [ -z "$ip" ]; then
        ip=$(hostname -I | awk '{print $1}')
    fi
    echo "$ip"
}

# 生成随机密码
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# 配置环境变量
configure_environment() {
    log_info "配置环境变量..."
    
    local server_ip=$(get_server_ip)
    log_info "检测到服务器IP: $server_ip"
    
    # 如果.env不存在，从模板创建
    if [ ! -f .env ]; then
        if [ -f config/production.env ]; then
            cp config/production.env .env
            log_info "从production.env模板创建.env文件"
        elif [ -f config/env.template ]; then
            cp config/env.template .env
            log_info "从env.template模板创建.env文件"
        else
            log_error "未找到环境变量模板文件"
            exit 1
        fi
    fi
    
    # 自动替换配置
    sed -i "s/您的服务器IP/$server_ip/g" .env
    sed -i "s/your-strong-password/$(generate_password)/g" .env
    sed -i "s/your-grafana-password/$(generate_password)/g" .env
    sed -i "s/请生成32位随机字符串/$(generate_password)/g" .env
    sed -i "s/请生成JWT密钥/$(generate_password)/g" .env
    
    # 设置生产环境
    sed -i "s/DEBUG=true/DEBUG=false/g" .env
    sed -i "s/ENVIRONMENT=development/ENVIRONMENT=production/g" .env
    
    log_success "环境变量配置完成"
    log_warning "请检查.env文件并配置您的LLM API密钥"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian UFW
        sudo ufw --force enable
        sudo ufw allow ssh
        sudo ufw allow 80
        sudo ufw allow 443
        sudo ufw allow 3003  # 前端
        sudo ufw allow 8000  # API
        log_success "UFW防火墙配置完成"
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL firewalld
        sudo systemctl enable firewalld
        sudo systemctl start firewalld
        sudo firewall-cmd --permanent --add-service=ssh
        sudo firewall-cmd --permanent --add-service=http
        sudo firewall-cmd --permanent --add-service=https
        sudo firewall-cmd --permanent --add-port=3003/tcp
        sudo firewall-cmd --permanent --add-port=8000/tcp
        sudo firewall-cmd --reload
        log_success "firewalld防火墙配置完成"
    else
        log_warning "未检测到防火墙，请手动配置"
    fi
}

# 部署服务
deploy_services() {
    log_info "开始部署服务..."
    
    # 停止现有服务
    if [ -f docker-compose.production.yml ]; then
        docker-compose -f docker-compose.production.yml down -v 2>/dev/null || true
        log_info "已停止现有服务"
    fi
    
    # 清理Docker资源
    docker system prune -f
    log_info "清理Docker资源完成"
    
    # 构建并启动服务
    log_info "构建并启动服务（这可能需要几分钟）..."
    docker-compose -f docker-compose.production.yml build --no-cache
    docker-compose -f docker-compose.production.yml up -d
    
    log_success "服务部署完成"
}

# 验证部署
verify_deployment() {
    log_info "验证部署状态..."
    
    local max_wait=60
    local wait_time=0
    
    # 等待服务启动
    while [ $wait_time -lt $max_wait ]; do
        if docker-compose -f docker-compose.production.yml ps | grep -q "Up"; then
            break
        fi
        sleep 5
        wait_time=$((wait_time + 5))
        log_info "等待服务启动... ($wait_time/$max_wait 秒)"
    done
    
    # 检查服务状态
    log_info "服务状态:"
    docker-compose -f docker-compose.production.yml ps
    
    # 健康检查
    local server_ip=$(get_server_ip)
    
    log_info "进行健康检查..."
    
    # 检查API
    if curl -s "http://localhost:8000/health" > /dev/null; then
        log_success "API服务运行正常"
    else
        log_error "API服务健康检查失败"
    fi
    
    # 检查前端
    if curl -s "http://localhost:3003" > /dev/null; then
        log_success "前端服务运行正常"
    else
        log_error "前端服务健康检查失败"
    fi
    
    # 显示访问地址
    echo ""
    log_success "🎉 部署完成！"
    echo ""
    echo "访问地址:"
    echo "  前端界面: http://$server_ip:3003"
    echo "  API文档:  http://$server_ip:8000/docs"
    echo "  监控面板: http://localhost:3001 (仅本地访问)"
    echo "  Prometheus: http://localhost:8090 (仅本地访问)"
    echo ""
    log_warning "请确保配置了LLM API密钥后重启服务"
}

# 显示后续步骤
show_next_steps() {
    echo ""
    echo "=========================="
    echo "后续步骤:"
    echo "=========================="
    echo ""
    echo "1. 配置LLM API密钥:"
    echo "   编辑 .env 文件，添加您的API密钥"
    echo "   nano .env"
    echo ""
    echo "2. 重启服务应用配置:"
echo "   docker-compose -f docker-compose.production.yml restart"
echo ""
echo "3. 注册工具到数据库（重要）:"
echo "   python3 scripts/register_all_tools.py"
echo ""
echo "4. 验证部署结果:"
echo "   ./scripts/verify_deployment.sh"
echo ""
echo "5. 查看服务日志:"
echo "   docker-compose -f docker-compose.production.yml logs -f"
echo ""
echo "6. 停止服务:"
echo "   docker-compose -f docker-compose.production.yml down"
echo ""
echo "7. 配置域名（可选）:"
    echo "   如果您有域名，请配置DNS解析到您的服务器IP"
    echo "   然后修改.env中的VITE_API_URL和CORS_ORIGINS"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "🚀 ModelVS3 生产环境部署脚本"
    echo "================================"
    echo ""
    
    # 检查是否在项目根目录
    if [ ! -f "docker-compose.yml" ] && [ ! -f "docker-compose.production.yml" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 检查是否为root用户
    if [ "$EUID" -eq 0 ]; then
        log_warning "建议不要使用root用户运行此脚本"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # 执行部署步骤
    check_requirements
    configure_environment
    
    # 询问是否配置防火墙
    read -p "是否配置防火墙? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        configure_firewall
    fi
    
    deploy_services
    verify_deployment
    show_next_steps
    
    log_success "部署脚本执行完成！"
}

# 执行主函数
main "$@" 
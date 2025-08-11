#!/bin/bash

# ModelVS3 部署验证脚本
# 用途: 验证全新机器上的部署是否正常工作

set -e

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
    echo -e "${GREEN}[✅]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠️]${NC} $1"
}

log_error() {
    echo -e "${RED}[❌]${NC} $1"
}

# 获取服务器IP
get_server_ip() {
    local ip=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || curl -s api.ipify.org 2>/dev/null)
    if [ -z "$ip" ]; then
        ip=$(hostname -I | awk '{print $1}')
    fi
    echo "$ip"
}

# 检查容器状态
check_containers() {
    log_info "1️⃣ 检查容器状态..."
    
    local compose_file="docker-compose.production.yml"
    if [ ! -f "$compose_file" ]; then
        compose_file="docker-compose.yml"
    fi
    
    if ! docker-compose -f "$compose_file" ps | grep -q "Up"; then
        log_error "发现容器未正常运行"
        docker-compose -f "$compose_file" ps
        return 1
    fi
    
    log_success "所有容器运行正常"
    return 0
}

# 检查端口监听
check_ports() {
    log_info "2️⃣ 检查端口监听..."
    
    local ports=("3003" "8000")
    local failed=0
    
    for port in "${ports[@]}"; do
        if netstat -tulpn 2>/dev/null | grep -q ":$port "; then
            log_success "端口 $port 监听正常"
        else
            log_error "端口 $port 未监听"
            failed=1
        fi
    done
    
    return $failed
}

# 检查API健康
check_api_health() {
    log_info "3️⃣ 检查API健康..."
    
    local server_ip=$(get_server_ip)
    
    # 本地健康检查
    if curl -f "http://localhost:8000/health" >/dev/null 2>&1; then
        log_success "API本地健康检查通过"
    else
        log_error "API本地健康检查失败"
        return 1
    fi
    
    # 外部健康检查
    if curl -f "http://$server_ip:8000/health" >/dev/null 2>&1; then
        log_success "API外部健康检查通过"
    else
        log_warning "API外部健康检查失败 (可能是防火墙配置)"
    fi
    
    return 0
}

# 检查API功能
check_api_endpoints() {
    log_info "4️⃣ 检查API功能..."
    
    local endpoints=("models" "tools" "agents")
    local failed=0
    
    for endpoint in "${endpoints[@]}"; do
        if curl -s "http://localhost:8000/api/v1/$endpoint" | python3 -m json.tool >/dev/null 2>&1; then
            log_success "API端点 /$endpoint 正常"
        else
            log_error "API端点 /$endpoint 异常"
            failed=1
        fi
    done
    
    return $failed
}

# 检查前端访问
check_frontend() {
    log_info "5️⃣ 检查前端访问..."
    
    local server_ip=$(get_server_ip)
    
    # 本地前端检查
    if curl -s "http://localhost:3003" | grep -q "html"; then
        log_success "前端本地访问正常"
    else
        log_error "前端本地访问失败"
        return 1
    fi
    
    # 外部前端检查
    if curl -s "http://$server_ip:3003" | grep -q "html"; then
        log_success "前端外部访问正常"
    else
        log_warning "前端外部访问失败 (可能是防火墙配置)"
    fi
    
    # 前端API代理检查
    if curl -s "http://localhost:3003/api/v1/models" | python3 -m json.tool >/dev/null 2>&1; then
        log_success "前端API代理正常"
    else
        log_error "前端API代理异常"
        return 1
    fi
    
    return 0
}

# 检查CORS配置
check_cors() {
    log_info "6️⃣ 检查CORS配置..."
    
    local server_ip=$(get_server_ip)
    
    local http_code=$(curl -H "Origin: http://$server_ip:3003" \
                          -H "Access-Control-Request-Method: GET" \
                          -X OPTIONS \
                          "http://$server_ip:8000/api/v1/models" \
                          -s -o /dev/null -w "%{http_code}" 2>/dev/null)
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "204" ]; then
        log_success "CORS配置正常"
        return 0
    else
        log_warning "CORS配置可能有问题 (HTTP $http_code)"
        return 1
    fi
}

# 检查数据库连接
check_database() {
    log_info "7️⃣ 检查数据库连接..."
    
    local compose_file="docker-compose.production.yml"
    if [ ! -f "$compose_file" ]; then
        compose_file="docker-compose.yml"
    fi
    
    # 检查PostgreSQL连接
    if docker-compose -f "$compose_file" exec -T api python3 -c "
from src.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        print('✅ PostgreSQL连接成功')
except Exception as e:
    print('❌ PostgreSQL连接失败:', e)
    exit(1)
" 2>/dev/null; then
        log_success "PostgreSQL连接正常"
    else
        log_error "PostgreSQL连接失败"
        return 1
    fi
    
    # 检查Redis连接
    if docker-compose -f "$compose_file" exec -T api python3 -c "
import redis
from src.config import settings
try:
    r = redis.from_url(settings.redis_url)
    r.ping()
    print('✅ Redis连接成功')
except Exception as e:
    print('❌ Redis连接失败:', e)
    exit(1)
" 2>/dev/null; then
        log_success "Redis连接正常"
    else
        log_error "Redis连接失败"
        return 1
    fi
    
    return 0
}

# 检查监控服务
check_monitoring() {
    log_info "8️⃣ 检查监控服务..."
    
    # 检查Prometheus
    if curl -s "http://localhost:8090" | grep -q "Prometheus"; then
        log_success "Prometheus监控正常"
    else
        log_warning "Prometheus监控异常 (可能未启用)"
    fi
    
    # 检查Grafana
    if curl -s "http://localhost:3001" | grep -q "Grafana\|login"; then
        log_success "Grafana监控面板正常"
    else
        log_warning "Grafana监控面板异常 (可能未启用)"
    fi
    
    return 0
}

# 功能测试
test_functionality() {
    log_info "9️⃣ 功能测试..."
    
    # 测试创建Agent
    local test_result=$(curl -X POST "http://localhost:8000/api/v1/agents/" \
                            -H "Content-Type: application/json" \
                            -d '{
                              "name": "验证测试Agent",
                              "description": "部署验证自动测试Agent",
                              "model_name": "gpt-3.5-turbo",
                              "system_prompt": "你是一个测试助手",
                              "tools": []
                            }' \
                            -s 2>/dev/null)
    
    if echo "$test_result" | grep -q '"id"'; then
        log_success "Agent创建功能正常"
        
        # 尝试删除测试Agent
        local agent_id=$(echo "$test_result" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
        if [ -n "$agent_id" ]; then
            curl -X DELETE "http://localhost:8000/api/v1/agents/$agent_id" -s >/dev/null 2>&1
        fi
    else
        log_warning "Agent创建功能可能异常 (可能需要API密钥)"
    fi
    
    return 0
}

# 显示访问信息
show_access_info() {
    local server_ip=$(get_server_ip)
    
    echo ""
    echo "🌐 ===================="
    echo "🎉 部署验证完成！"
    echo "🌐 ===================="
    echo ""
    echo "访问地址:"
    echo "  🌐 前端界面: http://$server_ip:3003"
    echo "  📖 API文档:  http://$server_ip:8000/docs"
    echo "  📊 Grafana:  http://localhost:3001 (仅本地)"
    echo "  📈 Prometheus: http://localhost:8090 (仅本地)"
    echo ""
    echo "管理命令:"
    echo "  📄 查看日志: docker-compose -f docker-compose.production.yml logs -f"
    echo "  🔄 重启服务: docker-compose -f docker-compose.production.yml restart"
    echo "  ⏹️  停止服务: docker-compose -f docker-compose.production.yml down"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "🔍 ModelVS3 部署验证脚本"
    echo "========================="
    echo ""
    
    local server_ip=$(get_server_ip)
    log_info "检测到服务器IP: $server_ip"
    echo ""
    
    local total_checks=0
    local passed_checks=0
    
    # 执行检查
    checks=(
        "check_containers"
        "check_ports" 
        "check_api_health"
        "check_api_endpoints"
        "check_frontend"
        "check_cors"
        "check_database"
        "check_monitoring"
        "test_functionality"
    )
    
    for check in "${checks[@]}"; do
        total_checks=$((total_checks + 1))
        if $check; then
            passed_checks=$((passed_checks + 1))
        fi
        echo ""
    done
    
    # 显示结果
    echo "📊 验证结果: $passed_checks/$total_checks 项检查通过"
    
    if [ $passed_checks -eq $total_checks ]; then
        log_success "🎉 所有检查通过！部署成功！"
        show_access_info
        exit 0
    elif [ $passed_checks -ge $((total_checks * 3 / 4)) ]; then
        log_warning "⚠️ 大部分检查通过，部署基本成功，但需要注意警告项"
        show_access_info
        exit 0
    else
        log_error "❌ 多项检查失败，部署可能有问题"
        echo ""
        echo "排查建议:"
        echo "1. 检查服务日志: docker-compose logs"
        echo "2. 重启服务: docker-compose restart"
        echo "3. 查看详细文档: DEPLOYMENT_VERIFICATION.md"
        exit 1
    fi
}

# 执行主函数
main "$@" 
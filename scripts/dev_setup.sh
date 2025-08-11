#!/bin/bash

# ModelVS3 开发环境设置脚本

set -e  # 出错时立即退出

echo "🚀 ModelVS3 开发环境设置开始..."

# 检查 Python 版本
check_python() {
    echo "🐍 检查 Python 版本..."
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 未安装，请先安装 Python 3.8+"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo "✅ Python 版本: $python_version"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        echo "❌ Python 版本过低，需要 3.8+"
        exit 1
    fi
}

# 检查 Node.js 版本
check_nodejs() {
    echo "📦 检查 Node.js 版本..."
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js 未安装，请先安装 Node.js 16+"
        exit 1
    fi
    
    node_version=$(node -v)
    echo "✅ Node.js 版本: $node_version"
}

# 检查 Docker
check_docker() {
    echo "🐳 检查 Docker..."
    if ! command -v docker &> /dev/null; then
        echo "⚠️  Docker 未安装，某些功能可能无法使用"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "⚠️  Docker 未运行，请启动 Docker"
        return 1
    fi
    
    echo "✅ Docker 正常运行"
    return 0
}

# 创建虚拟环境
create_venv() {
    echo "🔧 创建 Python 虚拟环境..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ 虚拟环境已创建"
    else
        echo "ℹ️  虚拟环境已存在"
    fi
}

# 安装 Python 依赖
install_python_deps() {
    echo "📚 安装 Python 依赖..."
    source venv/bin/activate
    
    # 升级 pip
    pip install --upgrade pip
    
    # 安装依赖
    pip install -r requirements.txt
    
    echo "✅ Python 依赖安装完成"
}

# 安装前端依赖
install_frontend_deps() {
    echo "🎨 安装前端依赖..."
    cd frontend
    
    if [ ! -f "package.json" ]; then
        echo "❌ frontend/package.json 不存在"
        cd ..
        return 1
    fi
    
    npm install
    echo "✅ 前端依赖安装完成"
    cd ..
}

# 设置环境变量
setup_env() {
    echo "⚙️  设置环境变量..."
    if [ ! -f ".env" ]; then
        if [ -f "config/env.template" ]; then
            cp config/env.template .env
            echo "✅ 环境变量文件已创建，请编辑 .env 文件"
        else
            echo "❌ 环境变量模板文件不存在"
            return 1
        fi
    else
        echo "ℹ️  .env 文件已存在"
    fi
}

# 启动数据库
start_database() {
    echo "🗄️  启动数据库..."
    if check_docker; then
        if [ -f "docker-compose.yml" ]; then
            docker-compose up -d postgres redis
            echo "✅ 数据库服务已启动"
            
            # 等待数据库启动
            echo "⏳ 等待数据库启动..."
            sleep 5
        else
            echo "❌ docker-compose.yml 不存在"
            return 1
        fi
    else
        echo "⚠️  Docker 不可用，请手动启动 PostgreSQL 和 Redis"
    fi
}

# 初始化数据库
init_database() {
    echo "🔧 初始化数据库..."
    source venv/bin/activate
    
    # 检查 alembic 是否可用
    if ! command -v alembic &> /dev/null; then
        echo "❌ Alembic 未安装，请先安装依赖"
        return 1
    fi
    
    # 运行迁移
    alembic upgrade head
    echo "✅ 数据库迁移完成"
    
    # 填充种子数据
    if [ -f "scripts/seed_data.py" ]; then
        echo "🌱 填充种子数据..."
        python3 scripts/seed_data.py
        echo "✅ 种子数据填充完成"
    fi
}

# 创建必要目录
create_directories() {
    echo "📁 创建必要目录..."
    mkdir -p logs
    mkdir -p data
    mkdir -p uploads
    echo "✅ 目录创建完成"
}

# 运行测试
run_tests() {
    echo "🧪 运行测试..."
    source venv/bin/activate
    
    if [ -f "tests/test_main.py" ]; then
        python3 -m pytest tests/ -v
        echo "✅ 测试完成"
    else
        echo "ℹ️  测试文件不存在，跳过测试"
    fi
}

# 显示启动信息
show_startup_info() {
    echo ""
    echo "🎉 开发环境设置完成！"
    echo ""
    echo "📋 启动服务:"
    echo "  # 激活虚拟环境"
    echo "  source venv/bin/activate"
    echo ""
    echo "  # 启动后端服务器"
    echo "  python3 cli.py server start --reload"
    echo "  # 或者直接使用 uvicorn"
    echo "  uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
    echo "  # 启动前端开发服务器"
    echo "  cd frontend && npm run dev"
    echo ""
    echo "🌐 访问地址:"
    echo "  后端 API: http://localhost:8000"
    echo "  API 文档: http://localhost:8000/docs"
    echo "  前端界面: http://localhost:3000"
    echo "  监控面板: http://localhost:3001"
    echo ""
    echo "🔑 默认账户:"
    echo "  管理员: admin@example.com / admin123"
    echo "  演示用户: demo@example.com / demo123"
    echo ""
    echo "💡 有用的命令:"
    echo "  python3 cli.py --help           # 查看 CLI 帮助"
    echo "  python3 cli.py health           # 健康检查"
    echo "  python3 cli.py agent list       # 列出 Agent"
    echo "  python3 cli.py model list       # 列出模型"
    echo ""
}

# 主函数
main() {
    echo "🌟 欢迎使用 ModelVS3 Agent 平台！"
    echo ""
    
    # 检查系统依赖
    check_python
    check_nodejs
    check_docker
    
    # 设置环境
    create_venv
    install_python_deps
    install_frontend_deps
    setup_env
    create_directories
    
    # 启动数据库
    start_database
    
    # 初始化数据库
    init_database
    
    # 运行测试
    if [ "$1" = "--with-tests" ]; then
        run_tests
    fi
    
    # 显示启动信息
    show_startup_info
}

# 运行主函数
main "$@" 
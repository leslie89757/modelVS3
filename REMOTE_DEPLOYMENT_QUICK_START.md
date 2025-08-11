# 🌐 ModelVS3 远程服务器快速部署指南

## 🎯 **部署概览**

在远程Linux服务器上部署ModelVS3，获得以下服务：
- **前端界面**: `http://您的服务器IP:3003`
- **后端API**: `http://您的服务器IP:8000`
- **监控面板**: `http://localhost:3001` (服务器本地访问)

---

## 🚀 **方式一：一键自动部署（推荐）**

### **1️⃣ 连接到远程服务器**
```bash
ssh your-username@your-server-ip
```

### **2️⃣ 克隆项目**
```bash
# 克隆项目到服务器
git clone <your-repository-url> modelVS3
cd modelVS3

# 或者如果已有项目，更新到最新版本
cd modelVS3
git pull origin main
```

### **3️⃣ 运行一键部署脚本**
```bash
# 给脚本执行权限
chmod +x scripts/deploy_production.sh

# 运行部署脚本
./scripts/deploy_production.sh
```

**脚本会自动完成：**
- ✅ 检查Docker环境
- ✅ 配置生产环境变量
- ✅ 构建并启动所有服务
- ✅ 等待服务就绪
- ✅ 运行健康检查

### **4️⃣ 注册工具到数据库**
```bash
# 注册所有可用工具
python3 scripts/register_all_tools.py

# 或使用快速注册脚本
./scripts/quick_register_tools.sh
```

### **5️⃣ 验证部署**
```bash
# 运行部署验证脚本
./scripts/verify_deployment.sh
```

---

## 🛠️ **方式二：手动部署**

### **1️⃣ 环境准备**
```bash
# 安装Docker和Docker Compose (Ubuntu/Debian)
sudo apt update
sudo apt install -y docker.io docker-compose git

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到docker组
sudo usermod -aG docker $USER
# 需要重新登录或运行: newgrp docker
```

### **2️⃣ 配置环境变量**
```bash
# 复制并编辑生产环境配置
cp config/production.env.template config/production.env

# 编辑配置文件
nano config/production.env
```

**需要配置的关键变量：**
```bash
# 服务器配置
SERVER_IP=您的服务器IP地址
DOMAIN_NAME=您的域名(可选)

# 数据库密码
POSTGRES_PASSWORD=设置一个强密码

# 应用密钥
SECRET_KEY=生成一个随机密钥
JWT_SECRET_KEY=生成一个JWT密钥

# LLM API密钥
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# CORS和前端配置
CORS_ORIGINS=http://您的服务器IP:3003,http://您的域名
VITE_API_URL=http://您的服务器IP:8000
```

### **3️⃣ 启动服务**
```bash
# 使用生产配置启动
docker-compose -f docker-compose.production.yml up -d

# 查看启动日志
docker-compose -f docker-compose.production.yml logs -f
```

### **4️⃣ 等待服务就绪**
```bash
# 等待所有服务启动（通常需要2-3分钟）
sleep 120

# 检查容器状态
docker-compose -f docker-compose.production.yml ps
```

---

## 🔧 **端口配置和防火墙**

### **开放必要端口**
```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 3003/tcp  # 前端界面
sudo ufw allow 8000/tcp  # 后端API
sudo ufw enable

# CentOS/RHEL (Firewalld)
sudo firewall-cmd --permanent --add-port=3003/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### **端口说明**
| 端口 | 服务 | 访问方式 |
|------|------|----------|
| 3003 | 前端界面 | 公网访问 |
| 8000 | 后端API | 公网访问 |
| 3001 | Grafana | 仅本地 |
| 8090 | Prometheus | 仅本地 |

---

## ✅ **部署验证**

### **1️⃣ 检查服务状态**
```bash
# 检查所有容器
docker ps

# 检查特定服务健康
curl http://localhost:8000/health
curl http://localhost:3003
```

### **2️⃣ 访问服务**
- **前端界面**: `http://您的服务器IP:3003`
- **API文档**: `http://您的服务器IP:8000/docs`
- **健康检查**: `http://您的服务器IP:8000/health`

### **3️⃣ 功能测试**
```bash
# 测试API接口
curl http://您的服务器IP:8000/api/v1/models
curl http://您的服务器IP:8000/api/v1/tools
curl http://您的服务器IP:8000/api/v1/agents
```

---

## 🔧 **常用管理命令**

### **服务管理**
```bash
# 启动所有服务
docker-compose -f docker-compose.production.yml up -d

# 停止所有服务
docker-compose -f docker-compose.production.yml down

# 重启特定服务
docker-compose -f docker-compose.production.yml restart api

# 查看日志
docker-compose -f docker-compose.production.yml logs -f api
docker-compose -f docker-compose.production.yml logs -f frontend
```

### **数据管理**
```bash
# 备份数据库
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U postgres modelvs3 > backup.sql

# 查看数据库
docker-compose -f docker-compose.production.yml exec postgres psql -U postgres -d modelvs3

# 重新注册工具
python3 scripts/register_all_tools.py
```

### **监控和调试**
```bash
# 查看系统资源使用
docker stats

# 查看容器详情
docker-compose -f docker-compose.production.yml ps
docker-compose -f docker-compose.production.yml top

# 进入容器调试
docker-compose -f docker-compose.production.yml exec api bash
```

---

## 🚨 **故障排除**

### **常见问题**

**1️⃣ 端口被占用**
```bash
# 查看端口占用
sudo netstat -tulpn | grep :3003
sudo netstat -tulpn | grep :8000

# 停止占用进程
sudo kill -9 <PID>
```

**2️⃣ 容器无法启动**
```bash
# 查看详细错误日志
docker-compose -f docker-compose.production.yml logs

# 清理并重新构建
docker-compose -f docker-compose.production.yml down -v
docker-compose -f docker-compose.production.yml up -d --build
```

**3️⃣ 数据库连接失败**
```bash
# 检查数据库容器
docker-compose -f docker-compose.production.yml exec postgres pg_isready

# 重置数据库
docker-compose -f docker-compose.production.yml down
docker volume rm modelvs3_postgres_data
docker-compose -f docker-compose.production.yml up -d
```

**4️⃣ 无法访问服务**
```bash
# 检查防火墙
sudo ufw status
sudo firewall-cmd --list-ports

# 检查CORS配置
grep CORS_ORIGINS config/production.env

# 测试内部网络
docker-compose -f docker-compose.production.yml exec frontend curl http://api:8000/health
```

---

## 📚 **下一步操作**

部署完成后，您可以：

1. **配置LLM模型** - 在前端界面添加OpenAI、Anthropic等模型
2. **创建AI Agent** - 使用Agent设计器创建智能助手
3. **配置工具** - 启用搜索、计算器、文件读取等工具
4. **设置监控** - 访问Grafana面板监控系统状态
5. **备份数据** - 定期备份数据库和配置文件

**🎉 现在您的ModelVS3平台已在远程服务器上成功运行！** 
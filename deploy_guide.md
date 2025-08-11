# 🐳 ModelVS3 项目Docker全新部署指南

## 📋 项目概述

ModelVS3 是一个现代化的多模型 AI Agent 平台，集成了奇门遁甲引擎，支持多种LLM模型的统一接入和管理。

### 核心服务架构
- **API 服务**: FastAPI 后端 (端口 8000)
- **前端界面**: React/Vite 应用 (端口 3003)  
- **数据库**: PostgreSQL + pgvector (端口 5432)
- **缓存**: Redis (端口 6379)
- **监控**: Prometheus (端口 8090) + Grafana (端口 3001)

## 🚀 全新部署步骤

### 步骤1: 环境准备

```bash
# 1.1 克隆项目
git clone <your-repository-url>
cd modelVS3

# 1.2 设置脚本权限
chmod +x scripts/*.sh

# 1.3 检查Docker环境
docker --version
docker-compose --version
```

### 步骤2: 配置环境变量

```bash
# 2.1 复制环境变量模板
cp config/env.template .env

# 2.2 编辑环境变量（重要！）
vim .env  # 或使用您喜欢的编辑器
```

**关键配置项**：
```bash
# 基础配置
APP_NAME=ModelVS3
DEBUG=false  # 生产环境设为false
SECRET_KEY=your-super-secret-key-32-chars-min

# 数据库（容器内部通信）
DATABASE_URL=postgresql://postgres:password@postgres:5432/modelvs3
REDIS_URL=redis://redis:6379/0

# LLM API Keys（必须配置）
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 安全配置
CORS_ORIGINS=http://localhost:3003,http://your-domain.com
```

### 步骤3: 一键部署（推荐）

```bash
# 3.1 运行自动部署脚本
./scripts/start.sh
```

### 步骤4: 手动部署（高级用户）

```bash
# 4.1 停止可能存在的服务
docker-compose down -v

# 4.2 构建所有镜像
docker-compose build --no-cache

# 4.3 启动所有服务
docker-compose up -d

# 4.4 查看启动状态
docker-compose ps
```

### 步骤5: 验证部署

```bash
# 5.1 检查服务状态
docker-compose ps

# 5.2 查看服务日志
docker-compose logs -f api
docker-compose logs -f frontend

# 5.3 健康检查
curl http://localhost:8000/health
curl http://localhost:3003
```

## 🔧 高级配置

### 数据库初始化

```bash
# 进入API容器
docker-compose exec api bash

# 运行数据库迁移
alembic upgrade head

# 种子数据（可选）
python3 scripts/seed_data.py
```

### SSL/HTTPS 配置

如需启用HTTPS，修改 `docker-compose.yml`:

```yaml
api:
  environment:
    - SSL_CERT_PATH=/app/certs/cert.pem
    - SSL_KEY_PATH=/app/certs/key.pem
  volumes:
    - ./certs:/app/certs:ro
```

### 环境变量详细说明

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `SECRET_KEY` | 应用密钥 | 无 | ✅ |
| `DATABASE_URL` | 数据库连接 | postgres URL | ✅ |
| `OPENAI_API_KEY` | OpenAI密钥 | 无 | 🔶 |
| `DEBUG` | 调试模式 | false | ❌ |
| `CORS_ORIGINS` | 跨域来源 | localhost | ❌ |

## 📊 访问地址

部署成功后，可以通过以下地址访问：

- **🌐 前端界面**: http://localhost:3003
- **📖 API文档**: http://localhost:8000/docs  
- **📊 Grafana监控**: http://localhost:3001 (admin/admin)
- **🔍 Prometheus**: http://localhost:8090
- **🗄️ 数据库**: localhost:5432 (postgres/password)

## 🛠️ 常用管理命令

### 服务管理
```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务  
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f [service-name]
```

### 数据管理
```bash
# 数据库备份
docker-compose exec postgres pg_dump -U postgres modelvs3 > backup.sql

# 数据库恢复
docker-compose exec -T postgres psql -U postgres modelvs3 < backup.sql

# 清理所有数据（谨慎！）
docker-compose down -v
```

### 更新部署
```bash
# 更新代码后重新部署
git pull
docker-compose build --no-cache
docker-compose up -d
```

## 🐛 故障排除

### 常见问题

**1. 端口冲突**
```bash
# 检查端口占用
netstat -tulpn | grep :8000

# 修改端口（在docker-compose.yml中）
ports:
  - "8001:8000"  # 改为8001
```

**2. 权限问题**
```bash
# 设置文件权限
sudo chown -R $USER:$USER .
chmod +x scripts/*.sh
```

**3. 内存不足**
```bash
# 检查系统资源
docker system df
docker system prune -a  # 清理无用资源
```

**4. 数据库连接失败**
```bash
# 检查数据库状态
docker-compose logs postgres

# 重置数据库
docker-compose down -v
docker-compose up -d postgres
```

### 日志查看
```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs -f api
docker-compose logs -f frontend  
docker-compose logs -f postgres

# 实时跟踪日志
docker-compose logs -f --tail=100
```

## 🔐 安全建议

### 生产环境配置

1. **修改默认密码**:
   ```bash
   # 数据库密码
   POSTGRES_PASSWORD=strong-password-here
   
   # Grafana密码  
   GF_SECURITY_ADMIN_PASSWORD=admin-password-here
   ```

2. **启用防火墙**:
   ```bash
   # 只允许必要端口
   ufw allow 80
   ufw allow 443
   ufw deny 5432  # 数据库端口不对外开放
   ```

3. **使用反向代理**:
   ```nginx
   # nginx配置示例
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:3003;
       }
       
       location /api {
           proxy_pass http://localhost:8000;
       }
   }
   ```

## 📈 性能优化

### 资源配置
```yaml
# docker-compose.yml
api:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '1.0'
      reservations:
        memory: 1G
        cpus: '0.5'
```

### 缓存优化
```bash
# Redis配置优化
REDIS_MAXMEMORY=256mb
REDIS_MAXMEMORY_POLICY=allkeys-lru
```

## 🆘 获取帮助

如果遇到问题：

1. 查看项目 [README.md](README.md)
2. 检查 [故障排除](#故障排除) 部分
3. 提交 Issue 到项目仓库
4. 联系技术支持

---

**部署完成后，您的ModelVS3平台就可以开始使用了！** 🎉 
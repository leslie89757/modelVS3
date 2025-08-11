# 🌐 ModelVS3 远程Linux服务器生产部署指南

本指南将帮助您在远程Linux服务器上快速部署ModelVS3 AI Agent平台。

## 📋 **服务架构与IP/域名配置复盘**

### **服务端口映射表**

| 服务 | 容器内端口 | 对外端口 | 访问方式 | 说明 |
|------|------------|----------|----------|------|
| **前端界面** | 3000 | 3003 | 公网访问 | React应用主界面 |
| **后端API** | 8000 | 8000 | 公网访问 | FastAPI服务 |
| **PostgreSQL** | 5432 | 127.0.0.1:5432 | 仅本地 | 主数据库 |
| **Redis** | 6379 | 127.0.0.1:6379 | 仅本地 | 缓存系统 |
| **Prometheus** | 9090 | 127.0.0.1:8090 | 仅本地 | 监控指标 |
| **Grafana** | 3000 | 127.0.0.1:3001 | 仅本地 | 监控面板 |

### **网络通信架构**
```
外部用户 → 服务器IP:3003 (前端) → 容器网络 → api:8000 (后端)
                                              ↓
外部用户 → 服务器IP:8000 (API)            postgres:5432 (数据库)
                                              ↓
                                        redis:6379 (缓存)
```

## 🚀 **快速部署步骤**

### **第一步：环境准备**

1. **连接到您的远程Linux服务器**：
```bash
ssh your-username@your-server-ip
```

2. **安装Docker和Docker Compose**（如果未安装）：
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose git

# CentOS/RHEL
sudo yum install -y docker docker-compose git
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到docker组
sudo usermod -aG docker $USER
# 重新登录使权限生效
```

3. **克隆项目**：
```bash
git clone <your-repository-url>
cd modelVS3
```

### **第二步：一键部署**

运行自动化部署脚本：
```bash
./scripts/deploy_production.sh
```

脚本将自动：
- ✅ 检查系统要求
- ✅ 获取服务器IP地址
- ✅ 生成强密码
- ✅ 配置环境变量
- ✅ 设置防火墙规则
- ✅ 构建并启动所有服务
- ✅ 验证部署状态

### **第三步：配置API密钥**

1. **编辑环境变量文件**：
```bash
nano .env
```

2. **添加您的LLM API密钥**：
```bash
# LLM API 密钥
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key  
GOOGLE_API_KEY=your-google-api-key
```

3. **重启服务应用配置**：
```bash
docker-compose -f docker-compose.production.yml restart
```

### **第四步：访问应用**

部署完成后，您可以通过以下地址访问：

- **🌐 前端界面**: `http://your-server-ip:3003`
- **📖 API文档**: `http://your-server-ip:8000/docs`
- **📊 监控面板**: `http://localhost:3001` (仅本地访问)
- **📈 Prometheus**: `http://localhost:8090` (仅本地访问)

## 🔧 **高级配置**

### **配置域名访问（推荐）**

如果您有域名，建议配置域名访问：

1. **配置DNS解析**：
```
A记录: app.yourdomain.com → your-server-ip
A记录: api.yourdomain.com → your-server-ip
```

2. **修改环境变量**：
```bash
# 编辑 .env 文件
VITE_API_URL=http://api.yourdomain.com
CORS_ORIGINS=http://app.yourdomain.com,https://app.yourdomain.com
```

3. **配置反向代理（Nginx）**：
```nginx
# /etc/nginx/sites-available/modelvs3
server {
    listen 80;
    server_name app.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:3003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **SSL/HTTPS配置**

使用Let's Encrypt免费SSL证书：

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d app.yourdomain.com -d api.yourdomain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🛠️ **管理命令**

### **服务控制**
```bash
# 启动所有服务
docker-compose -f docker-compose.production.yml up -d

# 停止所有服务
docker-compose -f docker-compose.production.yml down

# 重启服务
docker-compose -f docker-compose.production.yml restart

# 查看服务状态
docker-compose -f docker-compose.production.yml ps

# 查看实时日志
docker-compose -f docker-compose.production.yml logs -f
```

### **数据管理**
```bash
# 数据库备份
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U postgres modelvs3 > backup_$(date +%Y%m%d).sql

# 数据库恢复
docker-compose -f docker-compose.production.yml exec -T postgres psql -U postgres modelvs3 < backup.sql

# 查看数据库
docker-compose -f docker-compose.production.yml exec postgres psql -U postgres modelvs3
```

### **系统监控**
```bash
# 查看系统资源使用
docker stats

# 查看磁盘使用
df -h

# 查看内存使用
free -h

# 清理Docker资源
docker system prune -a
```

## 🔒 **安全配置**

### **防火墙设置**
```bash
# Ubuntu UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 3003  # 前端
sudo ufw allow 8000  # API

# CentOS firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http  
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=3003/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### **密码安全**
- ✅ 定期更换数据库密码
- ✅ 使用强密码（已自动生成）
- ✅ 定期更新JWT密钥
- ✅ 监控访问日志

## 🚨 **故障排除**

### **常见问题**

**1. 服务启动失败**
```bash
# 查看详细日志
docker-compose -f docker-compose.production.yml logs [service-name]

# 检查资源使用
docker stats
free -h
df -h
```

**2. 前端无法访问API**
```bash
# 检查CORS配置
grep CORS_ORIGINS .env

# 检查API地址配置
grep VITE_API_URL .env

# 重启前端服务
docker-compose -f docker-compose.production.yml restart frontend
```

**3. 数据库连接失败**
```bash
# 检查数据库状态
docker-compose -f docker-compose.production.yml logs postgres

# 手动连接测试
docker-compose -f docker-compose.production.yml exec postgres psql -U postgres -d modelvs3
```

**4. 端口冲突**
```bash
# 检查端口占用
netstat -tulpn | grep :8000
netstat -tulpn | grep :3003

# 修改端口映射（在docker-compose.production.yml中）
```

### **重置部署**
```bash
# 完全重置（会删除所有数据）
docker-compose -f docker-compose.production.yml down -v
docker system prune -a
./scripts/deploy_production.sh
```

## 📊 **性能优化**

### **资源限制**
编辑 `docker-compose.production.yml` 添加资源限制：
```yaml
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

### **数据库优化**
```sql
-- 连接到数据库
\c modelvs3

-- 查看数据库大小
SELECT pg_size_pretty(pg_database_size('modelvs3'));

-- 优化查询
VACUUM ANALYZE;
```

## 🆘 **获取支持**

如果遇到问题：

1. 📖 查看部署日志
2. 🔍 检查[故障排除](#故障排除)部分
3. 📧 联系技术支持
4. 🐛 提交Issue到项目仓库

---

**🎉 祝您部署成功！** 您的ModelVS3 AI Agent平台现在已在生产环境中运行。 
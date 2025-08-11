# 🔒 ModelVS3 公网IP安全部署指南

## 🎯 **针对公网IP 36.153.25.22 的安全配置**

### **⚡ 快速修复方案（立即执行）**

#### **1. 修复前端API访问**
```bash
# 编辑 .env 文件
cd /path/to/modelvs3
nano .env

# 添加以下配置
VITE_API_URL=http://36.153.25.22:8000
CORS_ORIGINS=http://36.153.25.22:3003,http://36.153.25.22:8000
```

#### **2. 重新部署服务**
```bash
# 停止现有服务
docker-compose -f docker-compose.production.yml down

# 重新构建并启动
docker-compose -f docker-compose.production.yml up --build -d

# 验证服务状态
docker-compose -f docker-compose.production.yml ps
```

#### **3. 验证访问**
```bash
# 测试前端访问
curl -I http://36.153.25.22:3003

# 测试API访问
curl http://36.153.25.22:8000/health

# 验证CORS配置
curl -H "Origin: http://36.153.25.22:3003" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS http://36.153.25.22:8000/api/v1/auth/login
```

---

### **🔒 完整安全方案（推荐后续实施）**

#### **第一步：安装SSL证书**

**方案A：自签名证书（快速测试）**
```bash
# 生成自签名证书
sudo mkdir -p /etc/ssl/certs /etc/ssl/private
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/modelvs3.key \
  -out /etc/ssl/certs/modelvs3.crt \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=ModelVS3/CN=36.153.25.22"

# 设置权限
sudo chmod 600 /etc/ssl/private/modelvs3.key
sudo chmod 644 /etc/ssl/certs/modelvs3.crt
```

**方案B：Let's Encrypt免费证书（推荐）**
```bash
# 安装certbot
sudo apt update
sudo apt install -y certbot nginx

# 获取证书（需要域名）
# 如果您有域名，请替换 example.com
sudo certbot certonly --standalone -d your-domain.com

# 证书路径
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

#### **第二步：配置Nginx反向代理**
```bash
# 安装nginx（如果未安装）
sudo apt install -y nginx

# 复制配置文件
sudo cp nginx-ssl-config.conf /etc/nginx/sites-available/modelvs3
sudo ln -sf /etc/nginx/sites-available/modelvs3 /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重启nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

#### **第三步：修改Docker配置**
```bash
# 修改 docker-compose.production.yml
# 将前端和API端口改为仅本地监听
# ports:
#   - "127.0.0.1:3003:3000"  # 前端仅本地
#   - "127.0.0.1:8000:8000"  # API仅本地
```

#### **第四步：配置防火墙**
```bash
# 重新配置防火墙
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 只开放必要端口
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 关闭直接访问的端口
# sudo ufw deny 3003
# sudo ufw deny 8000

sudo ufw --force enable
```

#### **第五步：更新环境配置**
```bash
# 修改 .env 文件
VITE_API_URL=  # 使用空字符串，通过nginx代理
CORS_ORIGINS=https://36.153.25.22
PUBLIC_SCHEME=https
PUBLIC_PORT=443
```

---

### **🔍 安全检查清单**

#### **部署后验证**
```bash
# 1. SSL证书验证
openssl s_client -connect 36.153.25.22:443 -servername 36.153.25.22

# 2. 端口扫描检查
nmap -p 22,80,443,3003,8000 36.153.25.22

# 3. HTTP重定向测试
curl -I http://36.153.25.22/

# 4. HTTPS访问测试
curl -I https://36.153.25.22/

# 5. API代理测试
curl https://36.153.25.22/api/v1/health
```

#### **安全评估**
- [ ] HTTPS强制跳转
- [ ] SSL证书有效
- [ ] 不必要端口已关闭
- [ ] API通过代理访问
- [ ] 安全头配置正确
- [ ] CORS配置适当

---

### **🚨 风险提示**

#### **当前风险（HTTP部署）**
1. **数据泄露风险**：用户密码、API密钥明文传输
2. **中间人攻击**：恶意用户可以截获和修改请求
3. **会话劫持**：JWT令牌可能被窃取
4. **API滥用**：8000端口直接暴露，易被扫描攻击

#### **迁移到HTTPS的注意事项**
1. **混合内容问题**：确保所有资源都通过HTTPS加载
2. **CORS更新**：需要更新所有HTTP引用为HTTPS
3. **证书续期**：定期更新SSL证书
4. **性能考虑**：HTTPS会增加少量延迟

---

### **📞 紧急情况处理**

#### **如果服务无法访问**
```bash
# 检查nginx状态
sudo systemctl status nginx

# 检查Docker容器
docker-compose -f docker-compose.production.yml ps

# 查看nginx错误日志
sudo tail -f /var/log/nginx/error.log

# 临时禁用SSL重定向
sudo nano /etc/nginx/sites-available/modelvs3
# 注释掉重定向行，重启nginx
```

#### **回滚到HTTP**
```bash
# 停止nginx
sudo systemctl stop nginx

# 恢复Docker端口映射
# 修改 docker-compose.production.yml
# ports:
#   - "3003:3000"
#   - "8000:8000"

# 重启Docker服务
docker-compose -f docker-compose.production.yml restart
```

---

### **📈 后续优化建议**

1. **域名配置**：申请域名并配置DNS
2. **CDN加速**：使用Cloudflare等CDN服务
3. **监控告警**：配置服务监控和告警
4. **备份策略**：定期备份数据和配置
5. **访问日志**：分析用户访问模式和安全威胁
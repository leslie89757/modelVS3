# 🔍 ModelVS3 服务路由关系分析报告

## 📊 **当前服务状态**

### **本机开发环境 (192.168.3.20)**
```
✅ 前端服务: localhost:3003 (Docker: modelvs3-frontend-1)
✅ API服务:  localhost:8000 (Docker: modelvs3-api-1)
✅ 数据库:   localhost:5432 (Docker: modelvs3-postgres-1)
✅ Redis:    localhost:6379 (Docker: modelvs3-redis-1)
✅ Grafana:  localhost:3001
✅ Prometheus: localhost:9090
```

### **远程生产环境 (192.168.3.27)**
```
✅ 前端服务: 192.168.3.27:3003 (可访问)
✅ API服务:  192.168.3.27:8000 (可访问)
🔶 数据库:   192.168.3.27:5432 (内部访问)
🔶 Redis:    192.168.3.27:6379 (内部访问)
```

## 🚨 **发现的路由问题**

### **1. 当前配置分析**
```bash
# 本机前端配置
VITE_API_URL=http://localhost:8000  ✅ 正确指向本机API

# 但存在的问题：
1. 两个服务同时运行可能导致混乱
2. 浏览器可能同时访问两个服务
3. 数据不同步（不同的数据库）
4. 工具注册状态可能不一致
```

### **2. 潜在混乱调用路径**

#### **场景A: 本机前端 → 远程API**
```
浏览器访问: http://localhost:3003
前端尝试调用: http://localhost:8000 (本机API)
但如果本机API不可用，可能误调用远程API
```

#### **场景B: 远程前端 → 本机API**
```
浏览器访问: http://192.168.3.27:3003  
远程前端可能被配置为调用: http://192.168.3.20:8000
导致跨网络的不合理调用
```

#### **场景C: 浏览器直接访问**
```
用户可能在浏览器中：
- 打开 http://localhost:3003 (本机)
- 同时打开 http://192.168.3.27:3003 (远程)
导致数据和状态混乱
```

## 🔧 **解决方案**

### **方案1: 明确环境分离（推荐）**

#### **保留本机作为开发环境**
```bash
# 本机环境配置
前端: http://localhost:3003
API:  http://localhost:8000
用途: 开发和测试

# 停止本机服务命令
docker-compose down
```

#### **远程作为生产环境**
```bash
# 远程环境配置
前端: http://192.168.3.27:3003  
API:  http://192.168.3.27:8000
用途: 生产使用

# 确保远程服务配置正确
VITE_API_URL=http://192.168.3.27:8000
```

### **方案2: 端口隔离**

#### **本机开发环境使用不同端口**
```yaml
# 修改本机 docker-compose.yml
frontend:
  ports:
    - "3004:3000"  # 改为3004端口

api:
  ports:
    - "8001:8000"  # 改为8001端口
```

#### **对应的环境变量修改**
```bash
# 本机 .env
VITE_API_URL=http://localhost:8001
```

### **方案3: 域名绑定**

#### **配置本地域名**
```bash
# 编辑 /etc/hosts
echo "127.0.0.1 dev.modelvs3.local" >> /etc/hosts
echo "192.168.3.27 prod.modelvs3.local" >> /etc/hosts
```

#### **使用域名访问**
```bash
开发环境: http://dev.modelvs3.local:3003
生产环境: http://prod.modelvs3.local:3003
```

## 🎯 **推荐操作步骤**

### **第一步：确认当前使用需求**
```bash
# 确认您当前主要使用哪个环境？
# A. 本机开发测试
# B. 远程生产使用  
# C. 两个都需要
```

### **第二步：停止不需要的服务**

#### **如果主要使用远程服务**
```bash
# 停止本机服务
cd /Users/guzhenqiang/QIGI/modelVS3
docker-compose down

# 只保留远程服务运行
# 访问: http://192.168.3.27:3003
```

#### **如果主要使用本机服务**
```bash
# 保持本机服务运行
# 停止远程服务
ssh user@192.168.3.27
cd /path/to/modelVS3
docker-compose -f docker-compose.production.yml down
```

### **第三步：清理浏览器缓存**
```bash
# 清理可能的缓存混乱
1. 清除浏览器缓存
2. 关闭所有ModelVS3相关标签页
3. 重新访问确定的环境
```

### **第四步：验证路由配置**

#### **检查本机配置**
```bash
# 进入前端容器检查
docker-compose exec frontend printenv | grep API_URL

# 应该看到: VITE_API_URL=http://localhost:8000
```

#### **检查远程配置**
```bash
# SSH到远程服务器
ssh user@192.168.3.27
docker-compose -f docker-compose.production.yml exec frontend printenv | grep API_URL

# 应该看到: VITE_API_URL=http://192.168.3.27:8000
```

### **第五步：数据同步（如需要）**

#### **如果需要数据同步**
```bash
# 从本机导出数据
docker-compose exec postgres pg_dump -U postgres modelvs3 > local_backup.sql

# 传输到远程服务器
scp local_backup.sql user@192.168.3.27:/tmp/

# 在远程服务器导入
ssh user@192.168.3.27
docker-compose -f docker-compose.production.yml exec -T postgres psql -U postgres modelvs3 < /tmp/local_backup.sql
```

## 🔍 **路由验证清单**

### **验证本机服务**
- [ ] 访问 http://localhost:3003 正常加载
- [ ] 前端调用 http://localhost:8000/api/v1/tools 成功
- [ ] 网络请求都指向 localhost
- [ ] 数据库连接本机PostgreSQL

### **验证远程服务**  
- [ ] 访问 http://192.168.3.27:3003 正常加载
- [ ] 前端调用 http://192.168.3.27:8000/api/v1/tools 成功
- [ ] 网络请求都指向 192.168.3.27
- [ ] 数据库连接远程PostgreSQL

### **验证隔离性**
- [ ] 本机服务不会调用远程API
- [ ] 远程服务不会调用本机API
- [ ] 两个环境的数据独立
- [ ] 工具注册状态分别管理

## 📱 **监控和调试**

### **网络请求监控**
```bash
# 本机服务网络请求监控
docker-compose logs frontend | grep -E "GET|POST"

# 远程服务网络请求监控
ssh user@192.168.3.27
docker-compose -f docker-compose.production.yml logs frontend | grep -E "GET|POST"
```

### **实时连接检查**
```bash
# 检查本机API连接
watch "curl -s http://localhost:8000/health | jq .timestamp"

# 检查远程API连接  
watch "curl -s http://192.168.3.27:8000/health | jq .timestamp"
```

## 💡 **最佳实践建议**

1. **环境标识**: 在页面添加环境标识（开发/生产）
2. **端口规范**: 开发和生产使用不同端口
3. **域名区分**: 使用不同域名或子域名
4. **配置管理**: 使用不同的配置文件
5. **监控分离**: 分别监控两个环境的健康状态

---

**请确认您希望采用哪种解决方案，我可以帮您具体实施！** 🚀 
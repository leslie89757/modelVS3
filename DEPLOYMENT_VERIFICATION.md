# 🔍 ModelVS3 部署验证检查清单

本文档提供了在全新机器上部署ModelVS3后的完整验证流程，确保所有服务间通信正常。

## 📋 **部署验证步骤**

### **第一步：基础服务检查**

#### 1.1 **容器状态检查**
```bash
# 检查所有容器状态
docker-compose -f docker-compose.production.yml ps

# 预期结果：所有服务状态为 "Up"
# postgres    Up    healthy
# redis       Up    healthy  
# api         Up
# frontend    Up
# prometheus  Up
# grafana     Up
```

#### 1.2 **端口监听检查**
```bash
# 检查端口是否正确监听
netstat -tulpn | grep -E ":3003|:8000|:8090|:3001"

# 预期结果：
# 0.0.0.0:3003        LISTEN    (前端)
# 0.0.0.0:8000        LISTEN    (API)
# 127.0.0.1:8090      LISTEN    (Prometheus)
# 127.0.0.1:3001      LISTEN    (Grafana)
```

#### 1.3 **服务日志检查**
```bash
# 检查是否有错误日志
docker-compose -f docker-compose.production.yml logs --tail=50 | grep -i error

# 检查API服务启动日志
docker-compose -f docker-compose.production.yml logs api | grep "启动\|healthy\|connected"
```

### **第二步：数据库连接验证**

#### 2.1 **PostgreSQL连接测试**
```bash
# 进入API容器测试数据库连接
docker-compose -f docker-compose.production.yml exec api python3 -c "
from src.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        print('✅ PostgreSQL连接成功:', result.fetchone()[0])
except Exception as e:
    print('❌ PostgreSQL连接失败:', e)
"
```

#### 2.2 **Redis连接测试**
```bash
# 测试Redis连接
docker-compose -f docker-compose.production.yml exec api python3 -c "
import redis
from src.config import settings
try:
    r = redis.from_url(settings.redis_url)
    r.ping()
    print('✅ Redis连接成功')
except Exception as e:
    print('❌ Redis连接失败:', e)
"
```

### **第三步：API服务验证**

#### 3.1 **健康检查**
```bash
# 获取服务器IP
SERVER_IP=$(curl -s ifconfig.me)

# API健康检查
curl -f "http://localhost:8000/health" || echo "❌ API健康检查失败"
curl -f "http://$SERVER_IP:8000/health" || echo "❌ 外部API访问失败"
```

#### 3.2 **API文档访问**
```bash
# 检查API文档是否可访问
curl -s "http://localhost:8000/docs" | grep -q "swagger" && echo "✅ API文档正常" || echo "❌ API文档异常"
```

#### 3.3 **核心API端点测试**
```bash
# 测试模型列表API
curl -s "http://localhost:8000/api/v1/models" | python3 -m json.tool > /dev/null && echo "✅ 模型API正常" || echo "❌ 模型API异常"

# 测试工具列表API  
curl -s "http://localhost:8000/api/v1/tools" | python3 -m json.tool > /dev/null && echo "✅ 工具API正常" || echo "❌ 工具API异常"

# 测试Agent列表API
curl -s "http://localhost:8000/api/v1/agents" | python3 -m json.tool > /dev/null && echo "✅ Agent API正常" || echo "❌ Agent API异常"
```

### **第四步：前端服务验证**

#### 4.1 **前端可访问性**
```bash
# 检查前端首页
curl -s "http://localhost:3003" | grep -q "ModelVS3\|html" && echo "✅ 前端页面正常" || echo "❌ 前端页面异常"

# 外部访问测试
curl -s "http://$SERVER_IP:3003" | grep -q "html" && echo "✅ 外部前端访问正常" || echo "❌ 外部前端访问失败"
```

#### 4.2 **前端API代理测试**
```bash
# 测试前端nginx的API代理
curl -s "http://localhost:3003/api/v1/models" | python3 -m json.tool > /dev/null && echo "✅ 前端API代理正常" || echo "❌ 前端API代理异常"
```

### **第五步：CORS跨域验证**

#### 5.1 **CORS配置检查**
```bash
# 检查CORS配置
docker-compose -f docker-compose.production.yml exec api python3 -c "
from src.config import settings
print('CORS Origins:', settings.cors_origins)
"
```

#### 5.2 **跨域请求测试**
```bash
# 模拟浏览器跨域预检请求
curl -H "Origin: http://$SERVER_IP:3003" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     "http://$SERVER_IP:8000/api/v1/models" \
     -v 2>&1 | grep -q "Access-Control-Allow-Origin" && echo "✅ CORS配置正常" || echo "❌ CORS配置异常"
```

### **第六步：服务间通信验证**

#### 6.1 **容器网络通信**
```bash
# 从API容器ping数据库
docker-compose -f docker-compose.production.yml exec api ping -c 1 postgres && echo "✅ API→数据库网络正常" || echo "❌ API→数据库网络异常"

# 从API容器ping Redis
docker-compose -f docker-compose.production.yml exec api ping -c 1 redis && echo "✅ API→Redis网络正常" || echo "❌ API→Redis网络异常"

# 从前端容器ping API
docker-compose -f docker-compose.production.yml exec frontend wget -qO- http://api:8000/health > /dev/null && echo "✅ 前端→API网络正常" || echo "❌ 前端→API网络异常"
```

### **第七步：监控服务验证**

#### 7.1 **Prometheus监控**
```bash
# 检查Prometheus是否可访问
curl -s "http://localhost:8090" | grep -q "Prometheus" && echo "✅ Prometheus正常" || echo "❌ Prometheus异常"

# 检查指标采集
curl -s "http://localhost:8090/metrics" | grep -q "http_requests_total" && echo "✅ 指标采集正常" || echo "❌ 指标采集异常"
```

#### 7.2 **Grafana监控面板**
```bash
# 检查Grafana是否可访问
curl -s "http://localhost:3001" | grep -q "Grafana\|login" && echo "✅ Grafana正常" || echo "❌ Grafana异常"
```

### **第八步：功能完整性测试**

#### 8.1 **创建测试Agent**
```bash
# 创建一个简单的测试Agent
curl -X POST "http://localhost:8000/api/v1/agents/" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "测试Agent",
       "description": "部署验证测试Agent",
       "model_name": "gpt-3.5-turbo",
       "system_prompt": "你是一个测试助手",
       "tools": []
     }' | grep -q '"id"' && echo "✅ Agent创建功能正常" || echo "❌ Agent创建功能异常"
```

#### 8.2 **前端交互测试**
使用浏览器访问 `http://your-server-ip:3003` 验证：
- [ ] 页面正常加载
- [ ] 导航菜单可用
- [ ] Models页面能显示模型列表
- [ ] Tools页面能显示工具列表
- [ ] Agent页面能显示Agent列表
- [ ] 新建Agent功能正常

## 🛠️ **一键验证脚本**

创建自动化验证脚本：

```bash
#!/bin/bash
# 保存为 verify_deployment.sh

echo "🔍 开始ModelVS3部署验证..."

# 获取服务器IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "localhost")
echo "📍 服务器IP: $SERVER_IP"

# 验证容器状态
echo "1️⃣ 检查容器状态..."
docker-compose -f docker-compose.production.yml ps

# 验证端口监听
echo "2️⃣ 检查端口监听..."
netstat -tulpn | grep -E ":3003|:8000|:8090|:3001"

# 验证API健康
echo "3️⃣ 检查API健康..."
curl -f "http://localhost:8000/health" && echo "✅ API健康检查通过"

# 验证前端访问
echo "4️⃣ 检查前端访问..."
curl -s "http://localhost:3003" | grep -q "html" && echo "✅ 前端访问正常"

# 验证API功能
echo "5️⃣ 检查API功能..."
curl -s "http://localhost:8000/api/v1/models" | python3 -m json.tool > /dev/null && echo "✅ API功能正常"

# 验证CORS
echo "6️⃣ 检查CORS配置..."
curl -H "Origin: http://$SERVER_IP:3003" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     "http://$SERVER_IP:8000/api/v1/models" \
     -s -o /dev/null -w "%{http_code}" | grep -q "200" && echo "✅ CORS配置正常"

echo "✅ 验证完成！"
echo "🌐 访问地址:"
echo "  前端: http://$SERVER_IP:3003"
echo "  API:  http://$SERVER_IP:8000/docs"
```

## 🚨 **常见问题排查**

### **问题1：前端无法访问API**
```bash
# 检查CORS配置
docker-compose -f docker-compose.production.yml exec api printenv | grep CORS

# 解决方案：更新.env文件中的CORS_ORIGINS
echo "CORS_ORIGINS=http://$SERVER_IP:3003" >> .env
docker-compose -f docker-compose.production.yml restart api
```

### **问题2：数据库连接失败**
```bash
# 检查数据库容器状态
docker-compose -f docker-compose.production.yml logs postgres

# 解决方案：等待数据库完全启动
docker-compose -f docker-compose.production.yml restart api
```

### **问题3：容器间网络不通**
```bash
# 检查Docker网络
docker network ls
docker network inspect modelVs3_modelvs3-network

# 解决方案：重新创建网络
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

---

✅ **验证完成后，您的ModelVS3平台就可以在生产环境中正常使用了！** 
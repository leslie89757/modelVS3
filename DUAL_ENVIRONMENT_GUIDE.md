# 🔄 ModelVS3 双环境管理指南

## 🎯 **环境配置成功**

您的ModelVS3现在已成功配置为双环境模式，完美解决了路由混乱问题！

### **📊 当前环境状态**

#### **🔧 开发环境 (本机)**
```
✅ 状态: 运行正常
🌐 前端: http://localhost:3004
🔗 API:  http://localhost:8001
📊 数据库: modelvs3_dev (端口5433)
🔧 用途: 开发和测试
```

#### **🌐 远程生产环境**
```
✅ 状态: 运行正常  
🌐 前端: http://192.168.3.27:3003
🔗 API:  http://192.168.3.27:8000
📊 数据库: modelvs3 (远程)
🚀 用途: 生产使用
```

## 🔧 **环境管理命令**

### **一键管理脚本**
```bash
# 查看所有环境状态
./scripts/manage_environments.sh status

# 启动开发环境
./scripts/manage_environments.sh start-dev

# 启动本机生产环境（如需要）
./scripts/manage_environments.sh start-prod

# 切换环境
./scripts/manage_environments.sh switch-to-dev    # 切换到开发
./scripts/manage_environments.sh switch-to-prod  # 切换到生产

# 停止环境
./scripts/manage_environments.sh stop-dev        # 停止开发
./scripts/manage_environments.sh stop-all        # 停止所有
```

### **工具注册命令**
```bash
# 为开发环境注册工具
python3 scripts/register_all_tools.py --dev

# 为生产环境注册工具
python3 scripts/register_all_tools.py

# 快速注册（自动检测环境）
./scripts/quick_register_tools.sh
```

## 📱 **日常使用流程**

### **开发工作流程**
```bash
# 1. 启动开发环境
./scripts/manage_environments.sh start-dev

# 2. 访问开发环境
浏览器打开: http://localhost:3004

# 3. 查看开发日志
./scripts/manage_environments.sh logs-dev

# 4. 停止开发环境
./scripts/manage_environments.sh stop-dev
```

### **生产使用流程**
```bash
# 直接访问远程生产环境
浏览器打开: http://192.168.3.27:3003

# 无需本机操作，远程服务独立运行
```

## 🔍 **环境差异对比**

| 项目 | 开发环境 | 远程生产环境 |
|------|----------|-------------|
| **前端地址** | http://localhost:3004 | http://192.168.3.27:3003 |
| **API地址** | http://localhost:8001 | http://192.168.3.27:8000 |
| **数据库** | modelvs3_dev (本机5433) | modelvs3 (远程5432) |
| **数据隔离** | ✅ 独立数据 | ✅ 独立数据 |
| **工具注册** | 需要单独注册 | 需要单独注册 |
| **用途** | 开发测试 | 生产使用 |

## 🛠️ **配置文件说明**

### **开发环境配置**
- **Docker配置**: `docker-compose.dev.yml`
- **环境变量**: `config/dev.env`
- **项目名称**: `modelvs3-dev`
- **容器名称**: `modelvs3-dev-*`

### **生产环境配置**
- **本机生产**: `docker-compose.yml`
- **远程生产**: `docker-compose.production.yml`
- **项目名称**: `modelvs3`
- **容器名称**: `modelvs3-*`

## 📊 **监控和调试**

### **实时状态检查**
```bash
# 检查所有环境状态
./scripts/manage_environments.sh status

# 检查特定服务
curl http://localhost:8001/health    # 开发环境API
curl http://192.168.3.27:8000/health # 远程生产API
```

### **日志查看**
```bash
# 开发环境日志
./scripts/manage_environments.sh logs-dev

# 查看特定服务日志
docker-compose -f docker-compose.dev.yml logs api
docker-compose -f docker-compose.dev.yml logs frontend
```

### **数据库连接**
```bash
# 开发环境数据库
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d modelvs3_dev

# 查看开发环境工具
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d modelvs3_dev -c "SELECT name, enabled FROM tools;"
```

## 🔧 **工具管理**

### **开发环境工具**
```bash
# 注册开发环境工具
python3 scripts/register_all_tools.py --dev

# 查看开发环境工具
curl http://localhost:8001/api/v1/tools | jq
```

### **生产环境工具**
```bash
# 查看远程生产环境工具
curl http://192.168.3.27:8000/api/v1/tools | jq
```

## 🚨 **故障排除**

### **问题1: 端口冲突**
```bash
# 检查端口占用
lsof -i :3004,8001  # 开发环境端口
lsof -i :3003,8000  # 生产环境端口

# 解决方案
./scripts/manage_environments.sh stop-all
./scripts/manage_environments.sh start-dev
```

### **问题2: 容器名称冲突**
```bash
# 清理所有容器
docker-compose -f docker-compose.dev.yml down -v
docker-compose down -v

# 重新启动
./scripts/manage_environments.sh start-dev
```

### **问题3: 数据库连接失败**
```bash
# 检查开发环境数据库
docker-compose -f docker-compose.dev.yml logs postgres

# 重启数据库
docker-compose -f docker-compose.dev.yml restart postgres
```

### **问题4: 工具注册失败**
```bash
# 检查API是否正常
curl http://localhost:8001/health

# 重新注册工具
python3 scripts/register_all_tools.py --dev
```

## 💡 **最佳实践**

### **1. 环境隔离**
- ✅ 开发数据和生产数据完全隔离
- ✅ 不同的端口避免冲突
- ✅ 独立的容器和网络

### **2. 开发流程**
- 🔧 开发时使用本机开发环境 (localhost:3004)
- 🚀 测试时使用远程生产环境 (192.168.3.27:3003)
- 📊 两个环境可以同时运行

### **3. 数据管理**
- 📝 开发环境可以随时清空重置
- 🔒 生产环境数据需要谨慎操作
- 💾 定期备份生产环境数据

### **4. 工具配置**
- 🔧 开发环境用于测试新工具
- ✅ 生产环境只使用稳定工具
- 🔄 工具配置需要分别管理

## 🎊 **使用总结**

现在您可以：

✅ **同时使用两个环境而不冲突**
- 开发: http://localhost:3004
- 生产: http://192.168.3.27:3003

✅ **方便地在环境间切换**
- 使用管理脚本一键切换
- 独立的数据和配置

✅ **独立管理工具和数据**
- 开发环境用于测试
- 生产环境用于正式使用

---

**🎉 恭喜！您的ModelVS3双环境配置完成，现在可以高效地进行开发和生产工作了！** 
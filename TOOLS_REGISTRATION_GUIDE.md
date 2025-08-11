# 🔧 工具注册指南

重新部署后，您需要重新注册所有工具到数据库。本指南提供了详细的工具注册方法。

## 🚀 **一键注册所有工具（推荐）**

### **执行统一注册脚本**
```bash
# 进入项目目录
cd modelVS3

# 一键注册所有工具
python3 scripts/register_all_tools.py

# 或者
./scripts/register_all_tools.py
```

**该脚本会注册以下Function Call工具：**
1. ✅ **精确时间工具** - 获取当前精确时间，支持多时区
2. ✅ **万年历工具** - 日期查询、农历转换、节日查询、年龄计算
3. ✅ **奇门遁甲工具** - 奇门起盘和预测分析
4. ✅ **网络搜索工具** - 互联网信息搜索
5. ✅ **计算器工具** - 数学计算和表达式求值
6. ✅ **文件读取工具** - 读取和分析各种文件格式

**注意：** 当前使用Function Call模式，会自动跳过MCP工具注册。

## 📋 **分别注册单个工具**

如果您只想注册特定工具，可以使用以下命令：

### **1. 注册万年历工具**
```bash
python3 scripts/register_calendar_tool.py
```

### **2. 注册精确时间工具**
```bash
python3 scripts/quick_register_time_tool.py
```

### **3. 注册MCP工具**
```bash
python3 scripts/register_mcp_tools.py
```

### **4. 更新所有工具**
```bash
python3 scripts/update_tools_database.py
```

## 🔍 **验证工具注册**

### **检查工具列表**
```bash
# 通过API检查
curl http://localhost:8000/api/v1/tools/ | python3 -m json.tool

# 通过前端界面检查
# 访问: http://your-server-ip:3003/tools
```

### **测试工具功能**
```bash
# 测试精确时间工具
curl -X POST "http://localhost:8000/api/v1/tools/test" \
     -H "Content-Type: application/json" \
     -d '{"tool_name": "precision_time", "parameters": {"timezone": "Asia/Shanghai"}}'
```

## 🐳 **Docker容器内注册**

如果您需要在Docker容器内执行注册：

```bash
# 进入API容器
docker-compose -f docker-compose.production.yml exec api bash

# 在容器内执行注册
python3 scripts/register_all_tools.py

# 退出容器
exit
```

## 🛠️ **手动数据库操作**

### **连接数据库**
```bash
# 进入数据库容器
docker-compose -f docker-compose.production.yml exec postgres psql -U postgres -d modelvs3

# 查看工具表
SELECT id, name, description, enabled, created_at FROM tools;

# 启用所有工具
UPDATE tools SET enabled = true;

# 退出数据库
\q
```

## 🚨 **常见问题解决**

### **问题1：数据库连接失败**
```bash
# 检查数据库是否运行
docker-compose -f docker-compose.production.yml ps postgres

# 重启数据库服务
docker-compose -f docker-compose.production.yml restart postgres

# 等待数据库启动后重试
sleep 10
python3 scripts/register_all_tools.py
```

### **问题2：Python模块导入错误**
```bash
# 检查Python路径
export PYTHONPATH=/app:$PYTHONPATH

# 在项目根目录执行
cd /path/to/modelVS3
python3 scripts/register_all_tools.py
```

### **问题3：权限错误**
```bash
# 检查脚本执行权限
chmod +x scripts/*.py

# 使用python3直接执行
python3 scripts/register_all_tools.py
```

### **问题4：MCP工具注册失败**
```bash
# 检查MCP服务是否运行
ps aux | grep mcp

# 单独注册MCP工具
python3 scripts/register_mcp_tools.py
```

## 📊 **注册后验证**

### **预期结果**
注册成功后，您应该看到：

```
📊 工具注册总结:
   ➕ 新注册工具: X
   🔄 更新工具: Y
   ❌ 失败工具: 0
   📅 总计处理: Z

📝 数据库中的所有工具 (共 Z 个):
   1. ✅ precision_time - 获取当前精确时间
   2. ✅ calendar - 万年历工具
   3. ✅ qimen_dunjia - 奇门遁甲起盘工具
   4. ✅ web_search - 网络搜索工具
   5. ✅ calculator - 数学计算工具
   6. ✅ file_reader - 文件读取工具
   ... (其他工具)
```

### **前端验证**
1. 访问 `http://your-server-ip:3003/tools`
2. 查看工具管理页面
3. 确认所有工具显示正常
4. 测试工具功能

### **Agent配置验证**
1. 创建新的Agent
2. 在工具选择界面看到所有注册的工具
3. 选择工具并测试对话功能

## 🔄 **自动化注册脚本**

创建自动化脚本 `auto_register_tools.sh`：

```bash
#!/bin/bash
echo "🔧 自动注册所有工具..."

# 等待服务启动
sleep 30

# 执行注册
python3 scripts/register_all_tools.py

# 验证注册结果
if [ $? -eq 0 ]; then
    echo "✅ 工具注册成功"
else
    echo "❌ 工具注册失败"
fi
```

## 💡 **最佳实践**

1. **部署后立即注册**: 在成功部署后立即执行工具注册
2. **定期检查**: 定期检查工具状态和可用性
3. **备份配置**: 保存工具配置以便快速恢复
4. **测试功能**: 注册后测试关键工具功能
5. **监控日志**: 关注工具执行日志和错误信息

---

**✅ 工具注册完成后，您的ModelVS3平台就拥有了完整的工具生态系统！** 
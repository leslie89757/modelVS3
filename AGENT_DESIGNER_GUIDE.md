# 🎨 Agent 设计器 - 完整使用指南

## 📋 概述

全新的 Agent 设计器实现了**边设计边调试**的功能，让您能够：
- 🔧 **实时配置**: 左侧面板调整 Agent 参数
- 💬 **即时测试**: 右侧面板立即对话调试
- 🛠️ **工具可视化**: 详细展示工具调用过程
- 💾 **智能保存**: 自动保存配置变更

## 🚀 快速启动

### 方式一：使用启动脚本（推荐）
```bash
# 运行启动脚本
./start_agent_designer.sh
```

### 方式二：手动 Docker 启动
```bash
# 构建并启动所有服务
docker-compose up --build -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 🌐 访问地址

启动成功后，通过以下地址访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| **Agent 设计器** | `http://localhost:3003/agent-designer` | 🎯 **主要功能** |
| 主应用 | `http://localhost:3003` | 完整的管理界面 |
| API 文档 | `http://localhost:8000/docs` | FastAPI 自动生成文档 |
| Grafana | `http://localhost:3001` | 监控面板 (admin/admin) |
| Prometheus | `http://localhost:8090` | 指标收集 |

## 🎯 使用流程

### 1. 基础配置
进入 Agent 设计器后，首先配置基本信息：

```
✅ Agent 名称（必填）
✅ 系统提示词（必填）
📝 描述信息
🏷️ 分类标签
🔐 访问权限
```

### 2. 模型配置
选择和调整 LLM 参数：

```
🤖 主要模型：选择 GPT-4、Claude 等
🌡️ 温度值：0.0-2.0（创意度）
📏 最大令牌：1-8000
⚙️ 其他参数：top_p, frequency_penalty 等
```

### 3. 工具配置
启用所需的工具：

```
☑️ 勾选需要的工具
📋 查看工具参数规范
🔧 配置工具选项
```

### 4. 实时调试
在右侧面板测试 Agent：

```
💬 输入测试消息
🤖 查看 Agent 回复
🛠️ 展开工具调用详情
📊 查看执行统计
```

## 🛠️ 工具调用可视化

Agent 设计器提供了完整的工具调用展示：

### 工具调用卡片
每个工具调用都显示为可展开的卡片：

```
🔧 工具调用: calculator
   ├─ 状态: ✅ success | ❌ error | ⏳ pending
   ├─ 执行时间: 245ms
   └─ 点击展开查看详情
```

### 详细信息
展开后显示完整的调用信息：

```yaml
输入参数:
{
  "expression": "2 + 2 * 3"
}

执行结果:
{
  "result": 8,
  "explanation": "按照运算顺序：2 + (2 * 3) = 8"
}

错误信息:
（如果有错误会显示详细信息）
```

## 📊 调试面板功能

### 消息类型
- 👤 **用户消息**: 蓝色背景，右对齐
- 🤖 **Assistant**: 白色背景，支持 Markdown
- 🛠️ **工具消息**: 紫色背景，显示工具执行
- ⚙️ **系统消息**: 黄色背景，系统提示

### 元数据显示
每条消息都包含丰富的元数据：

```
⏰ 时间戳: 14:30:25
⚡ 执行时间: 1.2s
📊 信心度: 85%
🔧 工具调用: 2 次
```

### 交互功能
- 🧹 **清空会话**: 重置对话历史
- 📜 **滚动到底部**: 自动跟随最新消息
- ⌨️ **快捷键**: Enter 发送，Shift+Enter 换行

## 💾 保存机制

### 自动保存
- ✅ 默认开启自动保存
- ⏱️ 配置变更后 2 秒自动保存
- 🔄 仅在有 Agent 名称时生效

### 手动保存
- 💾 点击"保存"按钮立即保存
- 🚫 关闭自动保存时必须手动保存
- ✅ 保存成功会显示 Toast 提示

### 保存状态
- ✅ **已保存**: 绿色勾号，显示 Agent ID
- ⚠️ **未保存**: 黄色警告，需要先保存才能调试

## 🎨 界面特性

### 响应式布局
- 📱 支持不同屏幕尺寸
- ↔️ 左右等宽双面板设计
- 📜 独立滚动区域

### 主题和样式
- 🎨 现代化 UI 设计
- 🌈 语义化颜色系统
- ✨ 平滑动画过渡
- 🎯 清晰的视觉层次

### 用户体验
- 🍞 Toast 消息提示
- ⏳ 加载状态指示
- 🚫 禁用状态处理
- 🎹 键盘快捷键支持

## 🔧 故障排除

### 常见问题

#### 1. 无法访问 Agent 设计器
```bash
# 检查服务状态
docker-compose ps

# 查看前端日志
docker-compose logs frontend

# 重启前端服务
docker-compose restart frontend
```

#### 2. API 调用失败
```bash
# 检查后端服务
curl http://localhost:8000/docs

# 查看 API 日志
docker-compose logs api

# 重启后端服务
docker-compose restart api
```

#### 3. 数据库连接问题
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready -U postgres

# 查看数据库日志
docker-compose logs postgres

# 重建数据库
docker-compose down -v
docker-compose up -d postgres
```

### 调试技巧

#### 开发者工具
1. 按 `F12` 打开浏览器开发者工具
2. 查看 **Console** 标签页的错误信息
3. 查看 **Network** 标签页的 API 请求
4. 检查 **Application** 标签页的本地存储

#### 日志分析
```bash
# 查看所有服务日志
docker-compose logs

# 实时跟踪日志
docker-compose logs -f api frontend

# 过滤特定错误
docker-compose logs | grep ERROR
```

## 🔗 API 集成

Agent 设计器使用以下 API 端点：

### Agent 管理
```
POST   /api/v1/agents          # 创建 Agent
PATCH  /api/v1/agents/{id}     # 更新 Agent
GET    /api/v1/agents/{id}     # 获取 Agent
```

### 模型和工具
```
GET    /api/v1/models?enabled=true  # 获取可用模型
GET    /api/v1/tools                # 获取可用工具
```

### 调试执行
```
POST   /api/v1/runs            # 执行 Agent 对话
GET    /api/v1/runs/{id}       # 获取执行结果
```

## 🚀 高级功能

### 配置模板
预设常用的 Agent 配置模板（计划功能）：
- 📝 内容创作助手
- 🔍 数据分析专家  
- 💼 商业顾问
- 🛠️ 技术专家

### 版本管理
Agent 配置版本控制（计划功能）：
- 📚 配置历史记录
- 🔄 版本回滚
- 📊 变更对比

### 协作功能
多人协作编辑（计划功能）：
- 👥 团队共享
- 💬 评论系统
- 🔒 权限管理

## 📞 技术支持

遇到问题时：

1. 📖 查看本指南的故障排除部分
2. 🔍 检查 Docker 容器日志
3. 🌐 确认网络连接正常
4. 💾 检查磁盘空间是否充足

---

🎉 **开始使用全新的 Agent 设计器，体验边设计边调试的高效开发流程！**

访问地址：**http://localhost:3003/agent-designer**
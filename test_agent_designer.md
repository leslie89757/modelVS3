# Agent设计器测试指南

## 新功能概述

我已经完成了全新的Agent设计器页面，实现了您要求的"边设计边调试"功能。以下是主要特性：

### 🎨 核心功能

1. **双面板设计**
   - 左侧：Agent配置设计面板
   - 右侧：实时调试对话面板

2. **实时配置与调试**
   - 修改配置后自动保存（可选）
   - 立即在右侧测试Agent响应
   - 无需跳转页面，一站式体验

3. **工具调用可视化**
   - 展开显示工具调用参数
   - 显示工具执行结果
   - 执行时间和状态追踪
   - 错误信息详细展示

4. **配置面板功能**
   - 基本信息配置
   - 模型参数调节
   - 系统提示词编辑
   - 工具选择和配置
   - 知识库设置

5. **调试面板功能**
   - Markdown渲染支持
   - 代码高亮显示
   - 流式输出模拟
   - 消息历史管理
   - 执行统计信息

## 🚀 启动测试

### Docker 部署启动
```bash
# 构建并启动所有服务
docker-compose up --build

# 或者后台运行
docker-compose up -d --build
```

### 访问新页面
浏览器访问：`http://localhost:3003/agent-designer`

### 服务端口说明
- **前端服务**: `http://localhost:3003` (nginx + React)
- **后端API**: `http://localhost:8000` (FastAPI)
- **数据库**: `localhost:5432` (PostgreSQL)
- **Redis**: `localhost:6379`
- **Grafana**: `http://localhost:3001` (监控面板)
- **Prometheus**: `http://localhost:8090` (指标收集)

## 🔧 测试流程

1. **基础配置**
   - 填写Agent名称（必需）
   - 输入系统提示词（必需）
   - 选择主要模型
   - 调整温度参数

2. **工具配置**
   - 选择需要的工具
   - 点击工具名称查看详细参数
   - 启用的工具会在调试中生效

3. **实时调试**
   - 在右侧输入测试消息
   - 观察Agent响应
   - 查看工具调用详情
   - 检查执行时间和状态

4. **迭代优化**
   - 根据调试结果调整配置
   - 修改系统提示词
   - 重新测试验证

## 📋 功能亮点

### 工具调用展示
- 每个工具调用都有独立的展开面板
- 显示输入参数、执行结果、执行时间
- 支持成功/失败状态显示
- 错误信息详细展示

### 自动保存机制
- 可切换自动保存模式
- 修改配置后2秒自动保存
- 手动保存按钮可立即保存
- 保存状态实时反馈

### 响应式设计
- 左右双面板等宽布局
- 内容区域独立滚动
- 移动端友好的响应式适配

### 消息渲染
- Markdown完整支持
- 代码块语法高亮
- 流式输出动画效果
- 消息时间戳和元数据

## 🎯 与现有功能集成

新的Agent设计器完全兼容现有的API架构：

- 使用现有的 `/api/v1/agents` API进行保存
- 调用 `/api/v1/runs` API进行调试
- 兼容现有的Agent配置结构
- 支持所有现有工具和模型

## 📝 技术实现

### 状态管理
- React useState管理配置状态
- 实时同步左右面板数据
- 配置变更自动触发保存

### API集成
- 异步调用后端接口
- 错误处理和用户反馈
- 流式响应支持（预留）

### 用户体验
- 加载状态指示器
- 成功/错误Toast提示
- 键盘快捷键支持
- 自动滚动到最新消息

## 🔍 下一步优化

1. **流式响应**：实现真正的流式调试体验
2. **配置模板**：预设常用Agent配置模板
3. **导入导出**：支持配置文件导入导出
4. **版本管理**：Agent配置版本历史管理
5. **协作功能**：多人协作编辑Agent

## 🐳 Docker 部署说明

### 启动步骤
1. **构建并启动服务**
   ```bash
   docker-compose up --build
   ```

2. **检查服务状态**
   ```bash
   docker-compose ps
   ```

3. **查看日志**
   ```bash
   # 查看所有服务日志
   docker-compose logs
   
   # 查看特定服务日志
   docker-compose logs frontend
   docker-compose logs api
   ```

### 重建前端（如果修改了代码）
```bash
# 停止并重建前端服务
docker-compose stop frontend
docker-compose build frontend
docker-compose up -d frontend
```

### 服务依赖关系
- `frontend` 依赖 `api`
- `api` 依赖 `postgres` 和 `redis`
- 所有服务都有健康检查配置

## 📞 技术支持

如果在测试过程中遇到任何问题，请检查：

1. **Docker 服务状态**
   ```bash
   docker-compose ps
   ```

2. **端口占用情况**
   ```bash
   netstat -tulpn | grep -E ':(3003|8000|5432|6379)'
   ```

3. **容器日志**
   ```bash
   docker-compose logs frontend
   docker-compose logs api
   ```

4. **浏览器控制台**
   - 检查是否有 JavaScript 错误
   - 检查网络请求是否成功
   - 确认 API 调用返回正常

5. **数据库连接**
   ```bash
   docker-compose exec postgres psql -U postgres -d modelvs3 -c "\dt"
   ```

### 常见问题解决

**问题1**: 前端无法访问
- 检查容器是否正常运行：`docker-compose ps`
- 检查端口是否正确映射：前端应该在 `localhost:3003`

**问题2**: API 调用失败
- 检查后端服务状态：`docker-compose logs api`
- 确认数据库连接正常：`docker-compose logs postgres`

**问题3**: 工具调用失败
- 检查工具配置是否正确
- 查看 API 服务日志中的工具执行信息

新的Agent设计器现在已经完全集成到项目中，使用 Docker 部署后访问 `http://localhost:3003/agent-designer` 即可开始测试！

## 🔄 开发模式

如果需要开发模式（代码修改实时更新），可以：

1. **挂载源代码目录**（已在 docker-compose.yml 中配置）
2. **前端开发**：修改 `frontend/src/` 下的文件会自动重建
3. **后端开发**：修改 `src/` 下的文件会自动重载

## 🎯 功能验证清单

- [ ] 页面正常加载 (`http://localhost:3003/agent-designer`)
- [ ] 左侧配置面板功能正常
- [ ] 右侧调试面板可以发送消息
- [ ] Agent 配置可以保存
- [ ] 工具调用结果可以展开查看
- [ ] 自动保存功能工作正常
- [ ] 消息历史正确显示
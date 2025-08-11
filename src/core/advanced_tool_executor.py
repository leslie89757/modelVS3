"""高级工具执行器"""

import json
import time
import asyncio
import httpx
import subprocess
import tempfile
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from ..models_advanced import AdvancedTool

logger = logging.getLogger(__name__)


class AdvancedToolExecutor:
    """高级工具执行器"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self._builtin_tools = self._initialize_builtin_tools()
    
    def _initialize_builtin_tools(self) -> Dict[str, Any]:
        """初始化内置工具"""
        
        return {
            "web_search": {
                "function": self._web_search,
                "schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索查询"},
                        "num_results": {"type": "integer", "default": 5, "description": "返回结果数量"}
                    },
                    "required": ["query"]
                }
            },
            "calculator": {
                "function": self._calculator,
                "schema": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "数学表达式"}
                    },
                    "required": ["expression"]
                }
            },
            "code_executor": {
                "function": self._code_executor,
                "schema": {
                    "type": "object",
                    "properties": {
                        "language": {"type": "string", "enum": ["python", "javascript", "bash"], "description": "编程语言"},
                        "code": {"type": "string", "description": "要执行的代码"},
                        "timeout": {"type": "integer", "default": 30, "description": "超时时间(秒)"}
                    },
                    "required": ["language", "code"]
                }
            },
            "file_manager": {
                "function": self._file_manager,
                "schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["read", "write", "delete", "list"], "description": "文件操作"},
                        "path": {"type": "string", "description": "文件路径"},
                        "content": {"type": "string", "description": "文件内容（写入时使用）"}
                    },
                    "required": ["action", "path"]
                }
            },
            "data_processor": {
                "function": self._data_processor,
                "schema": {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "enum": ["analyze", "transform", "filter", "aggregate"], "description": "数据操作"},
                        "data": {"type": "array", "description": "输入数据"},
                        "parameters": {"type": "object", "description": "操作参数"}
                    },
                    "required": ["operation", "data"]
                }
            },
            "image_generator": {
                "function": self._image_generator,
                "schema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "图像描述提示"},
                        "style": {"type": "string", "enum": ["realistic", "cartoon", "abstract", "artistic"], "default": "realistic"},
                        "size": {"type": "string", "enum": ["512x512", "1024x1024", "1024x768"], "default": "1024x1024"}
                    },
                    "required": ["prompt"]
                }
            },
            "text_analyzer": {
                "function": self._text_analyzer,
                "schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "要分析的文本"},
                        "analysis_type": {"type": "string", "enum": ["sentiment", "summary", "keywords", "entities"], "description": "分析类型"}
                    },
                    "required": ["text", "analysis_type"]
                }
            },
            "api_caller": {
                "function": self._api_caller,
                "schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "API端点URL"},
                        "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"], "default": "GET"},
                        "headers": {"type": "object", "description": "请求头"},
                        "data": {"type": "object", "description": "请求数据"},
                        "timeout": {"type": "integer", "default": 30, "description": "超时时间"}
                    },
                    "required": ["url"]
                }
            }
        }
    
    async def execute_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        agent_id: str = None
    ) -> Dict[str, Any]:
        """执行工具"""
        
        start_time = time.time()
        
        try:
            # 首先检查内置工具
            if tool_name in self._builtin_tools:
                result = await self._execute_builtin_tool(tool_name, parameters)
            else:
                # 检查数据库中的自定义工具
                result = await self._execute_custom_tool(tool_name, parameters, agent_id)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # 更新工具使用统计
            if self.db and agent_id:
                await self._update_tool_stats(tool_name, True, execution_time)
            
            return {
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error(f"工具 {tool_name} 执行失败: {e}")
            
            # 更新工具使用统计
            if self.db and agent_id:
                await self._update_tool_stats(tool_name, False, execution_time)
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _execute_builtin_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """执行内置工具"""
        
        tool_config = self._builtin_tools[tool_name]
        tool_function = tool_config["function"]
        
        # 验证参数
        self._validate_parameters(parameters, tool_config["schema"])
        
        # 执行工具函数
        return await tool_function(parameters)
    
    async def _execute_custom_tool(self, tool_name: str, parameters: Dict[str, Any], agent_id: str = None) -> Any:
        """执行自定义工具"""
        
        if not self.db:
            raise ValueError("数据库连接未初始化，无法执行自定义工具")
        
        # 查询工具配置
        tool = self.db.query(AdvancedTool).filter(
            AdvancedTool.name == tool_name,
            AdvancedTool.enabled == True
        ).first()
        
        if not tool:
            raise ValueError(f"工具 {tool_name} 不存在或未启用")
        
        # 验证参数
        self._validate_parameters(parameters, tool.schema)
        
        # 根据实现类型执行
        implementation = tool.implementation
        impl_type = implementation.get("type", "api")
        
        if impl_type == "api":
            return await self._execute_api_tool(implementation, parameters)
        elif impl_type == "script":
            return await self._execute_script_tool(implementation, parameters)
        elif impl_type == "function":
            return await self._execute_function_tool(implementation, parameters)
        else:
            raise ValueError(f"不支持的工具实现类型: {impl_type}")
    
    async def _execute_api_tool(self, implementation: Dict[str, Any], parameters: Dict[str, Any]) -> Any:
        """执行API工具"""
        
        endpoint = implementation.get("endpoint")
        method = implementation.get("method", "POST")
        headers = implementation.get("headers", {})
        timeout = implementation.get("timeout", 30)
        
        if not endpoint:
            raise ValueError("API工具缺少endpoint配置")
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method.upper() == "GET":
                response = await client.get(endpoint, params=parameters, headers=headers)
            else:
                response = await client.request(method, endpoint, json=parameters, headers=headers)
            
            response.raise_for_status()
            return response.json()
    
    async def _execute_script_tool(self, implementation: Dict[str, Any], parameters: Dict[str, Any]) -> Any:
        """执行脚本工具"""
        
        code = implementation.get("code")
        if not code:
            raise ValueError("脚本工具缺少code配置")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # 添加参数到脚本
            script_content = f"""
import json
import sys

# 参数
parameters = {json.dumps(parameters)}

# 用户代码
{code}
"""
            f.write(script_content)
            temp_file = f.name
        
        try:
            # 执行脚本
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"脚本执行失败: {result.stderr}")
            
            # 尝试解析输出为JSON
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"output": result.stdout.strip()}
                
        finally:
            # 清理临时文件
            os.unlink(temp_file)
    
    async def _execute_function_tool(self, implementation: Dict[str, Any], parameters: Dict[str, Any]) -> Any:
        """执行函数工具"""
        
        # 这里可以实现自定义函数执行逻辑
        # 为安全起见，暂时不支持动态函数执行
        raise NotImplementedError("动态函数执行暂未实现")
    
    def _validate_parameters(self, parameters: Dict[str, Any], schema: Dict[str, Any]):
        """验证参数"""
        
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # 检查必需参数
        for param in required:
            if param not in parameters:
                raise ValueError(f"缺少必需参数: {param}")
        
        # 检查参数类型（简单验证）
        for param, value in parameters.items():
            if param in properties:
                expected_type = properties[param].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    raise ValueError(f"参数 {param} 应为字符串类型")
                elif expected_type == "integer" and not isinstance(value, int):
                    raise ValueError(f"参数 {param} 应为整数类型")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    raise ValueError(f"参数 {param} 应为数字类型")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    raise ValueError(f"参数 {param} 应为布尔类型")
                elif expected_type == "array" and not isinstance(value, list):
                    raise ValueError(f"参数 {param} 应为数组类型")
                elif expected_type == "object" and not isinstance(value, dict):
                    raise ValueError(f"参数 {param} 应为对象类型")
    
    # 内置工具实现
    async def _web_search(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """网页搜索工具"""
        
        query = parameters["query"]
        num_results = parameters.get("num_results", 5)
        
        try:
            # 使用DuckDuckGo搜索API
            search_url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = []
                
                # 添加抽象信息
                if data.get("Abstract"):
                    results.append({
                        "title": "摘要",
                        "content": data["Abstract"],
                        "url": data.get("AbstractURL", "")
                    })
                
                # 添加相关主题
                for topic in data.get("RelatedTopics", [])[:num_results]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        results.append({
                            "title": topic.get("Text", "")[:100],
                            "content": topic.get("Text", ""),
                            "url": topic.get("FirstURL", "")
                        })
                
                return {
                    "query": query,
                    "results": results[:num_results],
                    "total_found": len(results)
                }
                
        except Exception as e:
            raise RuntimeError(f"网页搜索失败: {str(e)}")
    
    async def _calculator(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """计算器工具"""
        
        expression = parameters["expression"]
        
        try:
            # 使用eval进行计算（在实际环境中应使用更安全的方法）
            import ast
            import operator
            
            # 支持的操作符
            ops = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.Mod: operator.mod,
                ast.USub: operator.neg,
            }
            
            def eval_expr(node):
                if isinstance(node, ast.Constant):
                    return node.value
                elif isinstance(node, ast.BinOp):
                    return ops[type(node.op)](eval_expr(node.left), eval_expr(node.right))
                elif isinstance(node, ast.UnaryOp):
                    return ops[type(node.op)](eval_expr(node.operand))
                else:
                    raise TypeError(node)
            
            tree = ast.parse(expression, mode='eval')
            result = eval_expr(tree.body)
            
            return {
                "expression": expression,
                "result": result,
                "type": type(result).__name__
            }
            
        except Exception as e:
            raise RuntimeError(f"计算失败: {str(e)}")
    
    async def _code_executor(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """代码执行工具"""
        
        language = parameters["language"]
        code = parameters["code"]
        timeout = parameters.get("timeout", 30)
        
        if language == "python":
            return await self._execute_python_code(code, timeout)
        elif language == "javascript":
            return await self._execute_javascript_code(code, timeout)
        elif language == "bash":
            return await self._execute_bash_code(code, timeout)
        else:
            raise ValueError(f"不支持的编程语言: {language}")
    
    async def _execute_python_code(self, code: str, timeout: int) -> Dict[str, Any]:
        """执行Python代码"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
            
        finally:
            os.unlink(temp_file)
    
    async def _execute_javascript_code(self, code: str, timeout: int) -> Dict[str, Any]:
        """执行JavaScript代码"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ["node", temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
            
        finally:
            os.unlink(temp_file)
    
    async def _execute_bash_code(self, code: str, timeout: int) -> Dict[str, Any]:
        """执行Bash代码"""
        
        result = subprocess.run(
            ["bash", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    
    async def _file_manager(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """文件管理工具"""
        
        action = parameters["action"]
        path = parameters["path"]
        content = parameters.get("content", "")
        
        # 安全检查：限制在特定目录内
        safe_base = "/tmp/agent_files"
        os.makedirs(safe_base, exist_ok=True)
        
        if not path.startswith(safe_base):
            path = os.path.join(safe_base, path.lstrip("/"))
        
        try:
            if action == "read":
                with open(path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                return {"content": file_content, "size": len(file_content)}
            
            elif action == "write":
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {"success": True, "bytes_written": len(content)}
            
            elif action == "delete":
                os.remove(path)
                return {"success": True, "deleted": path}
            
            elif action == "list":
                if os.path.isdir(path):
                    items = os.listdir(path)
                    return {"items": items, "count": len(items)}
                else:
                    return {"items": [os.path.basename(path)], "count": 1}
            
            else:
                raise ValueError(f"不支持的文件操作: {action}")
                
        except Exception as e:
            raise RuntimeError(f"文件操作失败: {str(e)}")
    
    async def _data_processor(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """数据处理工具"""
        
        operation = parameters["operation"]
        data = parameters["data"]
        params = parameters.get("parameters", {})
        
        try:
            if operation == "analyze":
                return self._analyze_data(data, params)
            elif operation == "transform":
                return self._transform_data(data, params)
            elif operation == "filter":
                return self._filter_data(data, params)
            elif operation == "aggregate":
                return self._aggregate_data(data, params)
            else:
                raise ValueError(f"不支持的数据操作: {operation}")
                
        except Exception as e:
            raise RuntimeError(f"数据处理失败: {str(e)}")
    
    def _analyze_data(self, data: list, params: dict) -> dict:
        """分析数据"""
        
        if not data:
            return {"error": "数据为空"}
        
        result = {
            "count": len(data),
            "data_types": {},
            "sample": data[:5] if len(data) > 5 else data
        }
        
        # 分析数据类型
        for item in data:
            data_type = type(item).__name__
            result["data_types"][data_type] = result["data_types"].get(data_type, 0) + 1
        
        # 如果是数字数据，计算统计信息
        if all(isinstance(x, (int, float)) for x in data):
            result["statistics"] = {
                "min": min(data),
                "max": max(data),
                "average": sum(data) / len(data),
                "sum": sum(data)
            }
        
        return result
    
    def _transform_data(self, data: list, params: dict) -> dict:
        """转换数据"""
        
        transform_type = params.get("type", "uppercase")
        
        if transform_type == "uppercase" and all(isinstance(x, str) for x in data):
            return {"result": [x.upper() for x in data]}
        elif transform_type == "lowercase" and all(isinstance(x, str) for x in data):
            return {"result": [x.lower() for x in data]}
        elif transform_type == "square" and all(isinstance(x, (int, float)) for x in data):
            return {"result": [x ** 2 for x in data]}
        else:
            return {"error": "不支持的转换类型或数据类型不匹配"}
    
    def _filter_data(self, data: list, params: dict) -> dict:
        """过滤数据"""
        
        filter_condition = params.get("condition", "")
        
        if not filter_condition:
            return {"result": data}
        
        # 简单的过滤实现
        filtered = []
        for item in data:
            if isinstance(item, str) and filter_condition.lower() in item.lower():
                filtered.append(item)
            elif isinstance(item, (int, float)) and str(filter_condition) in str(item):
                filtered.append(item)
        
        return {"result": filtered, "original_count": len(data), "filtered_count": len(filtered)}
    
    def _aggregate_data(self, data: list, params: dict) -> dict:
        """聚合数据"""
        
        if all(isinstance(x, (int, float)) for x in data):
            return {
                "sum": sum(data),
                "average": sum(data) / len(data) if data else 0,
                "min": min(data) if data else None,
                "max": max(data) if data else None,
                "count": len(data)
            }
        else:
            # 字符串数据的聚合
            from collections import Counter
            counter = Counter(data)
            return {
                "unique_count": len(counter),
                "most_common": counter.most_common(5),
                "total_count": len(data)
            }
    
    async def _image_generator(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """图像生成工具（模拟实现）"""
        
        prompt = parameters["prompt"]
        style = parameters.get("style", "realistic")
        size = parameters.get("size", "1024x1024")
        
        # 这里应该调用实际的图像生成API，比如DALL-E或Stable Diffusion
        # 为了演示，这里返回一个模拟结果
        
        return {
            "prompt": prompt,
            "style": style,
            "size": size,
            "image_url": f"https://placeholder.com/{size}?text={prompt[:20]}",
            "message": "图像生成功能需要配置实际的AI图像生成服务"
        }
    
    async def _text_analyzer(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """文本分析工具"""
        
        text = parameters["text"]
        analysis_type = parameters["analysis_type"]
        
        try:
            if analysis_type == "sentiment":
                return self._analyze_sentiment(text)
            elif analysis_type == "summary":
                return self._summarize_text(text)
            elif analysis_type == "keywords":
                return self._extract_keywords(text)
            elif analysis_type == "entities":
                return self._extract_entities(text)
            else:
                raise ValueError(f"不支持的分析类型: {analysis_type}")
                
        except Exception as e:
            raise RuntimeError(f"文本分析失败: {str(e)}")
    
    def _analyze_sentiment(self, text: str) -> dict:
        """情感分析（简单实现）"""
        
        positive_words = ["好", "棒", "优秀", "喜欢", "满意", "开心", "快乐", "赞"]
        negative_words = ["差", "糟糕", "讨厌", "不满", "失望", "愤怒", "悲伤", "烦"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = "积极"
            score = 0.6 + (positive_count - negative_count) * 0.1
        elif negative_count > positive_count:
            sentiment = "消极"
            score = 0.4 - (negative_count - positive_count) * 0.1
        else:
            sentiment = "中性"
            score = 0.5
        
        return {
            "sentiment": sentiment,
            "score": max(0.0, min(1.0, score)),
            "positive_indicators": positive_count,
            "negative_indicators": negative_count
        }
    
    def _summarize_text(self, text: str) -> dict:
        """文本摘要（简单实现）"""
        
        sentences = text.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 简单的摘要：取前两句
        summary = '。'.join(sentences[:2])
        if summary and not summary.endswith('。'):
            summary += '。'
        
        return {
            "original_length": len(text),
            "summary": summary,
            "summary_length": len(summary),
            "sentence_count": len(sentences)
        }
    
    def _extract_keywords(self, text: str) -> dict:
        """关键词提取（简单实现）"""
        
        # 简单的关键词提取：统计词频
        import re
        from collections import Counter
        
        # 去除标点符号，分词
        words = re.findall(r'\w+', text)
        words = [w for w in words if len(w) > 1]  # 过滤单字符
        
        word_freq = Counter(words)
        keywords = word_freq.most_common(10)
        
        return {
            "keywords": [{"word": word, "frequency": freq} for word, freq in keywords],
            "total_words": len(words),
            "unique_words": len(word_freq)
        }
    
    def _extract_entities(self, text: str) -> dict:
        """实体抽取（简单实现）"""
        
        import re
        
        # 简单的实体识别
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        phones = re.findall(r'\b\d{3}-\d{3}-\d{4}\b|\b\d{10,11}\b', text)
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        
        return {
            "emails": emails,
            "phone_numbers": phones,
            "urls": urls,
            "entity_count": len(emails) + len(phones) + len(urls)
        }
    
    async def _api_caller(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """API调用工具"""
        
        url = parameters["url"]
        method = parameters.get("method", "GET")
        headers = parameters.get("headers", {})
        data = parameters.get("data", {})
        timeout = parameters.get("timeout", 30)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if data else None
                )
                
                result = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "url": str(response.url)
                }
                
                # 尝试解析JSON响应
                try:
                    result["json"] = response.json()
                except:
                    result["text"] = response.text
                
                return result
                
        except Exception as e:
            raise RuntimeError(f"API调用失败: {str(e)}")
    
    async def _update_tool_stats(self, tool_name: str, success: bool, execution_time: int):
        """更新工具使用统计"""
        
        if not self.db:
            return
        
        try:
            tool = self.db.query(AdvancedTool).filter(AdvancedTool.name == tool_name).first()
            if tool:
                tool.usage_count += 1
                
                # 更新成功率
                total_usage = tool.usage_count
                current_success_rate = tool.success_rate
                if success:
                    tool.success_rate = (current_success_rate * (total_usage - 1) + 1.0) / total_usage
                else:
                    tool.success_rate = (current_success_rate * (total_usage - 1)) / total_usage
                
                # 更新平均执行时间
                current_avg_time = tool.avg_execution_time
                tool.avg_execution_time = (current_avg_time * (total_usage - 1) + execution_time) / total_usage
                
                self.db.commit()
                
        except Exception as e:
            logger.warning(f"更新工具统计失败: {e}")
            self.db.rollback() 
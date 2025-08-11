"""工具执行器"""

import asyncio
import json
import httpx
import sys
import os
from typing import Dict, List, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)

# 添加qimenEngine路径到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
qimen_engine_path = os.path.join(project_root, 'qimenEngine')
if qimen_engine_path not in sys.path:
    sys.path.insert(0, qimen_engine_path)


class ToolExecutor:
    """工具执行器"""
    
    def __init__(self):
        self._tool_registry = {}
        self._init_builtin_tools()
    
    def _init_builtin_tools(self):
        """初始化内置工具"""
        
        # 网页搜索工具
        self._tool_registry["web_search"] = {
            "schema": {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "在互联网上搜索信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索查询"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            "executor": self._web_search
        }
        
        # 计算器工具
        self._tool_registry["calculator"] = {
            "schema": {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "执行数学计算",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "数学表达式"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            },
            "executor": self._calculator
        }
        
        # 文件读取工具
        self._tool_registry["file_reader"] = {
            "schema": {
                "type": "function",
                "function": {
                    "name": "file_reader",
                    "description": "读取文件内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            "executor": self._file_reader
        }
        
        # 奇门遁甲工具
        self._tool_registry["qimen_dunjia"] = {
            "schema": {
                "type": "function",
                "function": {
                    "name": "qimen_dunjia",
                    "description": "奇门遁甲排盘工具，根据当前时间起奇门局进行预测分析",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "要问的问题或求测的事情"
                            }
                        },
                        "required": []
                    }
                }
            },
            "executor": self._qimen_dunjia
        }
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        
        if tool_name not in self._tool_registry:
            raise ValueError(f"未知工具: {tool_name}")
        
        tool_config = self._tool_registry[tool_name]
        executor = tool_config["executor"]
        
        try:
            result = await executor(parameters)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"工具 {tool_name} 执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具 Schema"""
        
        if tool_name in self._tool_registry:
            return self._tool_registry[tool_name]["schema"]
        return None
    
    def register_tool(
        self, 
        tool_name: str, 
        schema: Dict[str, Any], 
        executor: Callable
    ):
        """注册自定义工具"""
        
        self._tool_registry[tool_name] = {
            "schema": schema,
            "executor": executor
        }
    
    async def _qimen_dunjia(self, parameters: Dict[str, Any]) -> str:
        """奇门遁甲工具实现 - 始终使用当前时间"""
        
        # 确保qimenEngine在路径中
        import sys
        import os
        qimen_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'qimenEngine')
        qimen_path = os.path.abspath(qimen_path)
        
        if qimen_path not in sys.path:
            sys.path.insert(0, qimen_path)
        
        # 导入并调用qimen_only模块
        import importlib
        
        # 清理可能存在的旧模块缓存
        modules_to_clear = ['qimen_only', 'qimen_calendar', 'ganzhi', 'ju', 'palace', 'rules', 'zhishi_calculator']
        for module_name in modules_to_clear:
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        try:
            import qimen_only
        except ImportError:
            # 如果直接导入失败，尝试相对导入
            try:
                from ...qimenEngine import qimen_only
            except ImportError:
                # 如果还是失败，尝试从绝对路径导入
                qimen_path = os.path.join(os.path.dirname(__file__), '..', '..', 'qimenEngine')
                qimen_path = os.path.abspath(qimen_path)
                if qimen_path not in sys.path:
                    sys.path.insert(0, qimen_path)
                import qimen_only
        
        # 捕获打印输出
        from io import StringIO
        import contextlib
        
        captured_output = StringIO()
        
        # 总是使用当前时间
        with contextlib.redirect_stdout(captured_output):
            # 调用qimen_now函数
            cal_info, ju_number, is_yang, nine_palace, analysis = qimen_only.qimen_now()
        
        # 获取捕获的输出
        output = captured_output.getvalue()
        
        # 优先返回捕获的输出（包含完整的真太阳时等信息）
        if output.strip():
            return output
        else:
            # 手动构建格式化输出（兼容备用方案，包含真太阳时信息）
            result = f"""🎯 奇门遁甲排盘
{'=' * 50}

📋 历法信息:
   📅 公历: {cal_info['year']}年{cal_info['month']}月{cal_info['day']}日 {cal_info['hour']}时{cal_info['minute']}分
   🕐 时辰: {cal_info['shi_chen']}
   📆 节气: {cal_info['solar_term']}
   🌟 干支: {cal_info['year_gan']}{cal_info['year_zhi']}年 {cal_info['month_gan']}{cal_info['month_zhi']}月 {cal_info['day_gan']}{cal_info['day_zhi']}日 {cal_info['hour_gan']}{cal_info['hour_zhi']}时"""

            # 添加真太阳时信息（如果启用）
            if cal_info.get('use_true_solar_time', False):
                time_diff = cal_info.get('time_difference_minutes', 0)
                true_solar_time = cal_info.get('true_solar_time', '')
                standard_shi_chen = cal_info.get('standard_time_shi_chen', '')
                
                result += f"""

📝 时间对比信息:
   ☀️  真太阳时: {true_solar_time} (用于排盘)
   ⏰ 时间差异: {time_diff:+.1f} 分钟
   📊 对比: 标准时间→{standard_shi_chen} / 真太阳时→{cal_info['shi_chen']}"""
                
                # 如果时辰发生变化，特别标注
                if standard_shi_chen != cal_info['shi_chen']:
                    result += f"""
   🎯 注意: 由于真太阳时影响，时辰从 {standard_shi_chen} 变为 {cal_info['shi_chen']}"""
                
                result += f"""
   💡 说明: 奇门遁甲使用真太阳时确保天文准确性"""

            result += f"""

🏰 奇门局信息:
   🎯 局数: {ju_number}
   ⚊ 阴阳: {'阳遁' if is_yang else '阴遁'}

📊 断事分析:"""
            
            # 添加分析结果
            if analysis:
                for analysis_type, results in analysis.items():
                    if results:
                        result += f"\n   📈 {analysis_type} ({len(results)} 项):"
                        for i, item in enumerate(results, 1):
                            result += f"\n      {i}. {item}"
            
            return result
    


    async def _web_search(self, parameters: Dict[str, Any]) -> str:
        """网页搜索工具实现"""
        
        query = parameters.get("query", "")
        
        try:
            # 使用DuckDuckGo搜索API（免费，无需API key）
            search_url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(search_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 提取搜索结果
                    results = []
                    
                    # 添加抽象文本
                    if data.get("Abstract"):
                        results.append(f"摘要: {data['Abstract']}")
                    
                    # 添加相关主题
                    if data.get("RelatedTopics"):
                        for topic in data["RelatedTopics"][:3]:  # 只取前3个
                            if isinstance(topic, dict) and topic.get("Text"):
                                results.append(f"• {topic['Text']}")
                    
                    # 添加定义
                    if data.get("Definition"):
                        results.append(f"定义: {data['Definition']}")
                    
                    if results:
                        return f"搜索 '{query}' 的结果:\n\n" + "\n\n".join(results)
                    else:
                        return f"搜索 '{query}' 未找到相关结果。"
                else:
                    return f"搜索服务暂时不可用，状态码: {response.status_code}"
                    
        except Exception as e:
            logger.error(f"网页搜索失败: {e}")
            return f"搜索 '{query}' 时发生错误: {str(e)}"
    
    async def _calculator(self, parameters: Dict[str, Any]) -> str:
        """计算器工具实现"""
        
        expression = parameters.get("expression", "")
        
        try:
            # 安全的数学表达式计算
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
                    raise TypeError(f"不支持的操作: {node}")
            
            tree = ast.parse(expression, mode='eval')
            result = eval_expr(tree.body)
            
            return f"{expression} = {result}"
            
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    async def _file_reader(self, parameters: Dict[str, Any]) -> str:
        """文件读取工具实现"""
        
        file_path = parameters.get("file_path", "")
        
        try:
            # 出于安全考虑，限制只能读取特定目录下的文件
            allowed_dirs = ["/tmp", "./data", "./uploads"]
            
            import os
            abs_path = os.path.abspath(file_path)
            
            if not any(abs_path.startswith(os.path.abspath(d)) for d in allowed_dirs):
                return "错误: 文件路径不在允许的目录中"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 限制文件大小
            if len(content) > 10000:
                content = content[:10000] + "\n... (文件被截断)"
            
            return content
            
        except Exception as e:
            return f"文件读取错误: {str(e)}" 
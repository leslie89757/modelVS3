#!/usr/bin/env python3
"""初始化高级工具数据脚本"""

import sys
import uuid
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.database import SessionLocal
from src.models_advanced import AdvancedTool


def create_builtin_tools():
    """创建内置工具"""
    
    db = SessionLocal()
    
    try:
        # 检查是否已存在工具
        existing_tool = db.query(AdvancedTool).first()
        if existing_tool:
            print("工具已存在，跳过初始化")
            return
        
        tools = [
            {
                "name": "web_search",
                "description": "在互联网上搜索信息，支持多种搜索引擎",
                "category": "信息获取",
                "schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询关键词"
                        },
                        "num_results": {
                            "type": "integer",
                            "default": 5,
                            "description": "返回结果数量，最多10个"
                        }
                    },
                    "required": ["query"]
                },
                "implementation": {
                    "type": "function",
                    "timeout": 10
                },
                "required_params": ["query"],
                "optional_params": ["num_results"]
            },
            {
                "name": "calculator",
                "description": "执行数学计算，支持基本算术运算",
                "category": "数学计算",
                "schema": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，如 2+3*4"
                        }
                    },
                    "required": ["expression"]
                },
                "implementation": {
                    "type": "function",
                    "timeout": 5
                },
                "required_params": ["expression"],
                "optional_params": []
            },
            {
                "name": "code_executor",
                "description": "执行代码片段，支持Python、JavaScript、Bash",
                "category": "代码执行",
                "schema": {
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "enum": ["python", "javascript", "bash"],
                            "description": "编程语言"
                        },
                        "code": {
                            "type": "string",
                            "description": "要执行的代码"
                        },
                        "timeout": {
                            "type": "integer",
                            "default": 30,
                            "description": "超时时间（秒）"
                        }
                    },
                    "required": ["language", "code"]
                },
                "implementation": {
                    "type": "function",
                    "timeout": 30
                },
                "required_params": ["language", "code"],
                "optional_params": ["timeout"]
            },
            {
                "name": "file_manager",
                "description": "文件管理工具，支持读取、写入、删除、列表操作",
                "category": "文件操作",
                "schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["read", "write", "delete", "list"],
                            "description": "文件操作类型"
                        },
                        "path": {
                            "type": "string",
                            "description": "文件或目录路径"
                        },
                        "content": {
                            "type": "string",
                            "description": "文件内容（写入时使用）"
                        }
                    },
                    "required": ["action", "path"]
                },
                "implementation": {
                    "type": "function",
                    "timeout": 15
                },
                "required_params": ["action", "path"],
                "optional_params": ["content"]
            },
            {
                "name": "data_processor",
                "description": "数据处理工具，支持分析、转换、过滤、聚合操作",
                "category": "数据处理",
                "schema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["analyze", "transform", "filter", "aggregate"],
                            "description": "数据操作类型"
                        },
                        "data": {
                            "type": "array",
                            "description": "输入数据数组"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "操作参数"
                        }
                    },
                    "required": ["operation", "data"]
                },
                "implementation": {
                    "type": "function",
                    "timeout": 20
                },
                "required_params": ["operation", "data"],
                "optional_params": ["parameters"]
            },
            {
                "name": "text_analyzer",
                "description": "文本分析工具，支持情感分析、摘要、关键词提取、实体识别",
                "category": "文本分析",
                "schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "要分析的文本内容"
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["sentiment", "summary", "keywords", "entities"],
                            "description": "分析类型"
                        }
                    },
                    "required": ["text", "analysis_type"]
                },
                "implementation": {
                    "type": "function",
                    "timeout": 15
                },
                "required_params": ["text", "analysis_type"],
                "optional_params": []
            },
            {
                "name": "api_caller",
                "description": "通用API调用工具，支持各种HTTP方法和参数",
                "category": "网络请求",
                "schema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "API端点URL"
                        },
                        "method": {
                            "type": "string",
                            "enum": ["GET", "POST", "PUT", "DELETE"],
                            "default": "GET",
                            "description": "HTTP方法"
                        },
                        "headers": {
                            "type": "object",
                            "description": "请求头"
                        },
                        "data": {
                            "type": "object",
                            "description": "请求数据"
                        },
                        "timeout": {
                            "type": "integer",
                            "default": 30,
                            "description": "超时时间（秒）"
                        }
                    },
                    "required": ["url"]
                },
                "implementation": {
                    "type": "function",
                    "timeout": 30
                },
                "required_params": ["url"],
                "optional_params": ["method", "headers", "data", "timeout"]
            },
            {
                "name": "image_generator",
                "description": "AI图像生成工具（需要配置实际的图像生成服务）",
                "category": "图像生成",
                "schema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "图像描述提示词"
                        },
                        "style": {
                            "type": "string",
                            "enum": ["realistic", "cartoon", "abstract", "artistic"],
                            "default": "realistic",
                            "description": "图像风格"
                        },
                        "size": {
                            "type": "string",
                            "enum": ["512x512", "1024x1024", "1024x768"],
                            "default": "1024x1024",
                            "description": "图像尺寸"
                        }
                    },
                    "required": ["prompt"]
                },
                "implementation": {
                    "type": "function",
                    "timeout": 60
                },
                "required_params": ["prompt"],
                "optional_params": ["style", "size"]
            }
        ]
        
        # 创建工具记录
        for tool_data in tools:
            tool = AdvancedTool(
                name=tool_data["name"],
                description=tool_data["description"],
                category=tool_data["category"],
                schema=tool_data["schema"],
                implementation=tool_data["implementation"],
                version="1.0.0",
                enabled=True,
                required_params=tool_data["required_params"],
                optional_params=tool_data["optional_params"],
                usage_count=0,
                success_rate=0.0,
                avg_execution_time=0.0
            )
            
            db.add(tool)
        
        db.commit()
        print(f"成功创建了 {len(tools)} 个内置工具")
        
        # 显示创建的工具
        for tool_data in tools:
            print(f"- {tool_data['name']}: {tool_data['description']}")
    
    except Exception as e:
        print(f"创建工具失败: {e}")
        db.rollback()
        
    finally:
        db.close()


if __name__ == "__main__":
    print("开始初始化高级工具数据...")
    create_builtin_tools()
    print("初始化完成！") 
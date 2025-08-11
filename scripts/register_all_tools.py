#!/usr/bin/env python3
"""统一工具注册脚本 - 重新部署后一键注册所有Function Call工具"""

import asyncio
import sys
import os
import json
import traceback
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Tool
from src.database import get_db


class ToolRegistrar:
    """工具注册器"""
    
    def __init__(self, database_url="postgresql://postgres:password@localhost:5432/modelvs3", dev_mode=False):
        if dev_mode:
            database_url = "postgresql://postgres:password@localhost:5433/modelvs3_dev"
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.registered_count = 0
        self.updated_count = 0
        self.failed_count = 0
    
    def get_db_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
    
    def register_or_update_tool(self, name, description, schema, enabled=True):
        """注册或更新工具"""
        try:
            db = self.get_db_session()
            
            # 检查工具是否已存在
            existing_tool = db.query(Tool).filter(Tool.name == name).first()
            
            if existing_tool:
                print(f"   🔄 更新现有工具: {name}")
                existing_tool.description = description
                existing_tool.schema = schema
                existing_tool.enabled = enabled
                self.updated_count += 1
            else:
                print(f"   ➕ 创建新工具: {name}")
                new_tool = Tool(
                    name=name,
                    description=description,
                    schema=schema,
                    enabled=enabled
                )
                db.add(new_tool)
                self.registered_count += 1
            
            db.commit()
            db.close()
            return True
            
        except Exception as e:
            print(f"   ❌ 工具 {name} 注册失败: {e}")
            self.failed_count += 1
            return False
    
    def register_precision_time_tool(self):
        """注册精确时间工具"""
        print("1️⃣ 注册精确时间工具...")
        
        schema = {
            "type": "function",
            "function": {
                "name": "precision_time",
                "description": "获取当前精确时间，支持多种时区和格式化选项",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "时区名称，如 UTC, Asia/Shanghai, America/New_York",
                            "default": "UTC"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["iso", "timestamp", "human", "custom"],
                            "description": "时间格式",
                            "default": "iso"
                        },
                        "custom_format": {
                            "type": "string",
                            "description": "自定义时间格式（当format为custom时使用）"
                        },
                        "locale": {
                            "type": "string",
                            "description": "语言环境，如 zh_CN, en_US",
                            "default": "zh_CN"
                        },
                        "include_milliseconds": {
                            "type": "boolean",
                            "description": "是否包含毫秒",
                            "default": False
                        }
                    },
                    "required": []
                }
            }
        }
        
        return self.register_or_update_tool(
            "precision_time",
            "获取当前精确时间，支持多种时区和格式化选项",
            schema
        )
    
    def register_calendar_tool(self):
        """注册万年历工具"""
        print("2️⃣ 注册万年历工具...")
        
        schema = {
            "type": "function",
            "function": {
                "name": "calendar",
                "description": "万年历工具，提供日期查询、农历转换、节日查询、年龄计算等功能",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["get_date_info", "get_month_calendar", "get_year_info", "calculate_age"],
                            "description": "操作类型",
                            "default": "get_date_info"
                        },
                        "year": {
                            "type": "integer",
                            "description": "年份 (1900-2100)",
                            "minimum": 1900,
                            "maximum": 2100
                        },
                        "month": {
                            "type": "integer",
                            "description": "月份 (1-12)",
                            "minimum": 1,
                            "maximum": 12
                        },
                        "day": {
                            "type": "integer",
                            "description": "日期 (1-31)",
                            "minimum": 1,
                            "maximum": 31
                        },
                        "birth_year": {
                            "type": "integer",
                            "description": "出生年份（用于年龄计算）"
                        },
                        "birth_month": {
                            "type": "integer",
                            "description": "出生月份（用于年龄计算）"
                        },
                        "birth_day": {
                            "type": "integer",
                            "description": "出生日期（用于年龄计算）"
                        },
                        "include_lunar": {
                            "type": "boolean",
                            "description": "是否包含农历信息",
                            "default": True
                        },
                        "include_festivals": {
                            "type": "boolean",
                            "description": "是否包含节日信息",
                            "default": True
                        },
                        "include_zodiac": {
                            "type": "boolean",
                            "description": "是否包含生肖星座信息",
                            "default": True
                        },
                        "locale": {
                            "type": "string",
                            "description": "语言环境",
                            "default": "zh_CN"
                        }
                    },
                    "required": ["action"]
                }
            }
        }
        
        return self.register_or_update_tool(
            "calendar",
            "万年历工具，提供日期查询、农历转换、节日查询、年龄计算等功能",
            schema
        )
    
    def register_qimen_tool(self):
        """注册奇门遁甲工具"""
        print("3️⃣ 注册奇门遁甲工具...")
        
        schema = {
            "type": "function",
            "function": {
                "name": "qimen_dunjia",
                "description": "奇门遁甲起盘工具，可以根据指定时间起奇门局进行预测分析",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "integer",
                            "description": "年份",
                            "minimum": 1900,
                            "maximum": 2100
                        },
                        "month": {
                            "type": "integer",
                            "description": "月份 (1-12)",
                            "minimum": 1,
                            "maximum": 12
                        },
                        "day": {
                            "type": "integer",
                            "description": "日期 (1-31)",
                            "minimum": 1,
                            "maximum": 31
                        },
                        "hour": {
                            "type": "integer",
                            "description": "小时 (0-23)",
                            "minimum": 0,
                            "maximum": 23
                        },
                        "minute": {
                            "type": "integer",
                            "description": "分钟 (0-59)",
                            "minimum": 0,
                            "maximum": 59,
                            "default": 0
                        },
                        "question": {
                            "type": "string",
                            "description": "要问的问题或求测的事项"
                        },
                        "method": {
                            "type": "string",
                            "enum": ["转盘", "飞盘"],
                            "description": "起盘方法",
                            "default": "转盘"
                        },
                        "include_analysis": {
                            "type": "boolean",
                            "description": "是否包含分析解释",
                            "default": True
                        }
                    },
                    "required": ["year", "month", "day", "hour"]
                }
            }
        }
        
        return self.register_or_update_tool(
            "qimen_dunjia",
            "奇门遁甲起盘工具，可以根据指定时间起奇门局进行预测分析",
            schema
        )
    
    def register_web_search_tool(self):
        """注册网络搜索工具"""
        print("4️⃣ 注册网络搜索工具...")
        
        schema = {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "在互联网上搜索信息，获取最新的网络内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询关键词"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "返回结果数量，最多10个",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 5
                        },
                        "language": {
                            "type": "string",
                            "description": "搜索语言",
                            "default": "zh-CN"
                        },
                        "region": {
                            "type": "string",
                            "description": "搜索地区",
                            "default": "CN"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
        
        return self.register_or_update_tool(
            "web_search",
            "在互联网上搜索信息，获取最新的网络内容",
            schema
        )
    
    def register_calculator_tool(self):
        """注册计算器工具"""
        print("5️⃣ 注册计算器工具...")
        
        schema = {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "执行数学计算，支持基本运算、函数运算和复杂表达式",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "要计算的数学表达式，如 '2+3*4', 'sin(0.5)', 'sqrt(16)'"
                        },
                        "precision": {
                            "type": "integer",
                            "description": "小数点精度",
                            "minimum": 0,
                            "maximum": 10,
                            "default": 4
                        }
                    },
                    "required": ["expression"]
                }
            }
        }
        
        return self.register_or_update_tool(
            "calculator",
            "执行数学计算，支持基本运算、函数运算和复杂表达式",
            schema
        )
    
    def register_file_reader_tool(self):
        """注册文件读取工具"""
        print("6️⃣ 注册文件读取工具...")
        
        schema = {
            "type": "function",
            "function": {
                "name": "file_reader",
                "description": "读取和分析文件内容，支持多种文件格式",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "文件路径"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "文件编码",
                            "default": "utf-8"
                        },
                        "max_lines": {
                            "type": "integer",
                            "description": "最大读取行数",
                            "default": 1000
                        },
                        "format": {
                            "type": "string",
                            "enum": ["text", "json", "csv", "auto"],
                            "description": "文件格式",
                            "default": "auto"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        }
        
        return self.register_or_update_tool(
            "file_reader",
            "读取和分析文件内容，支持多种文件格式",
            schema
        )
    

    
    def show_registration_summary(self):
        """显示注册总结"""
        print(f"\n📊 工具注册总结:")
        print(f"   ➕ 新注册工具: {self.registered_count}")
        print(f"   🔄 更新工具: {self.updated_count}")
        print(f"   ❌ 失败工具: {self.failed_count}")
        print(f"   📅 总计处理: {self.registered_count + self.updated_count + self.failed_count}")
        
        # 显示数据库中所有工具
        try:
            db = self.get_db_session()
            all_tools = db.query(Tool).all()
            
            print(f"\n📝 数据库中的所有工具 (共 {len(all_tools)} 个):")
            for i, tool in enumerate(all_tools, 1):
                status = "✅" if tool.enabled else "❌"
                print(f"   {i}. {status} {tool.name} - {tool.description}")
            
            db.close()
            
        except Exception as e:
            print(f"   ❌ 获取工具列表失败: {e}")
    
    async def register_all_tools(self):
        """注册所有工具"""
        print("🚀 开始注册所有工具...")
        print("=" * 60)
        
        # 注册基础工具
        tools = [
            self.register_precision_time_tool,
            self.register_calendar_tool,
            self.register_qimen_tool,
            self.register_web_search_tool,
            self.register_calculator_tool,
            self.register_file_reader_tool,
        ]
        
        for tool_func in tools:
            try:
                tool_func()
                print(f"   ✅ 完成")
            except Exception as e:
                print(f"   ❌ 失败: {e}")
            print()
        
        print(f"   ✅ 所有Function Call工具注册完成")
        
        print("=" * 60)
        self.show_registration_summary()


async def test_tool_api():
    """测试工具API"""
    print("\n🧪 测试工具API...")
    
    try:
        import httpx
        import sys
        
        # 根据模式选择API地址
        dev_mode = "--dev" in sys.argv
        api_url = "http://localhost:8001/api/v1/tools/" if dev_mode else "http://localhost:8000/api/v1/tools/"
        
        # 检查API是否可访问
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url)
            
            if response.status_code == 200:
                tools = response.json()
                print(f"✅ API访问成功，找到 {len(tools)} 个工具")
                
                # 显示前几个工具
                for i, tool in enumerate(tools[:3], 1):
                    print(f"   {i}. {tool['name']} - {tool['description']}")
                
                return True
            else:
                print(f"❌ API访问失败: HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False


async def main():
    """主函数"""
    import sys
    dev_mode = "--dev" in sys.argv
    env_name = "开发环境" if dev_mode else "生产环境"
    
    print(f"🔧 ModelVS3 Function Call工具注册脚本 ({env_name})")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 用途: 为{env_name}注册所有Function Call工具")
    if dev_mode:
        print("🔧 开发模式: 使用端口8001和数据库modelvs3_dev")
    print("=" * 70)
    
    # 创建工具注册器
    registrar = ToolRegistrar(dev_mode=dev_mode)
    
    # 注册所有工具
    await registrar.register_all_tools()
    
    # 测试API
    api_success = await test_tool_api()
    
    # 显示完成信息
    print("\n" + "=" * 70)
    if registrar.failed_count == 0 and api_success:
        print("🎉 所有工具注册成功！")
        print("💡 现在您可以在前端工具管理页面看到所有工具")
        print("🔗 访问: http://localhost:3003/tools")
        print("🤖 Agent可以在配置中选择并使用这些工具")
    else:
        print("⚠️ 部分工具注册可能有问题，请检查日志")
    
    print("=" * 70)


if __name__ == "__main__":
    # 运行主函数
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 用户中断执行")
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        traceback.print_exc()
        sys.exit(1) 
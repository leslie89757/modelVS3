#!/usr/bin/env python3
"""注册万年历工具到数据库"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Tool
import uuid

def register_calendar_tool():
    """注册万年历工具到数据库"""
    
    print("🗓️ 注册万年历工具...")
    
    try:
        # 创建数据库连接
        DATABASE_URL = "postgresql://postgres:password@localhost:5432/modelvs3"
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 检查工具是否已存在
        existing_tool = db.query(Tool).filter(Tool.name == "calendar").first()
        
        if existing_tool:
            print(f"✅ 万年历工具已存在，ID: {existing_tool.id}")
            print(f"   更新现有工具配置...")
            
            # 更新工具配置
            existing_tool.description = "万年历工具，提供日期查询、农历转换、节日查询、年龄计算等功能"
            existing_tool.schema = {
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
                            "target_year": {
                                "type": "integer",
                                "description": "目标年份（用于年龄计算，不填则使用当前日期）"
                            },
                            "target_month": {
                                "type": "integer",
                                "description": "目标月份（用于年龄计算）"
                            },
                            "target_day": {
                                "type": "integer",
                                "description": "目标日期（用于年龄计算）"
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
            existing_tool.enabled = True
            
        else:
            print("➕ 创建新的万年历工具...")
            
            # 创建新工具
            new_tool = Tool(
                name="calendar",
                description="万年历工具，提供日期查询、农历转换、节日查询、年龄计算等功能",
                schema={
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
                                "target_year": {
                                    "type": "integer",
                                    "description": "目标年份（用于年龄计算，不填则使用当前日期）"
                                },
                                "target_month": {
                                    "type": "integer",
                                    "description": "目标月份（用于年龄计算）"
                                },
                                "target_day": {
                                    "type": "integer",
                                    "description": "目标日期（用于年龄计算）"
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
                },
                enabled=True
            )
            db.add(new_tool)
        
        # 提交更改
        db.commit()
        
        # 验证结果
        calendar_tool = db.query(Tool).filter(Tool.name == "calendar").first()
        
        if calendar_tool:
            print("✅ 万年历工具注册成功！")
            print(f"   ID: {calendar_tool.id}")
            print(f"   名称: {calendar_tool.name}")
            print(f"   描述: {calendar_tool.description}")
            print(f"   启用状态: {'✅ 启用' if calendar_tool.enabled else '❌ 禁用'}")
            print(f"   创建时间: {calendar_tool.created_at}")
        
        # 显示所有工具
        all_tools = db.query(Tool).all()
        print(f"\n📝 数据库中的所有工具 (共 {len(all_tools)} 个):")
        for i, tool in enumerate(all_tools, 1):
            status = "✅" if tool.enabled else "❌"
            print(f"   {i}. {status} {tool.name}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 注册失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_calendar_api():
    """测试万年历API"""
    
    print("\n🌐 测试万年历API...")
    
    import requests
    
    try:
        # 获取工具列表
        response = requests.get("http://localhost:8000/api/v1/tools/")
        
        if response.status_code == 200:
            tools = response.json()
            calendar_tool = None
            
            for tool in tools:
                if tool['name'] == 'calendar':
                    calendar_tool = tool
                    break
            
            if calendar_tool:
                print(f"✅ 找到万年历工具: {calendar_tool['name']}")
                
                # 测试工具调用
                print("🧪 测试工具调用...")
                
                test_params = {
                    "action": "get_date_info",
                    "year": 2024,
                    "month": 12,
                    "day": 25
                }
                
                test_response = requests.post(
                    f"http://localhost:8000/api/v1/tools/{calendar_tool['id']}/test",
                    json={"parameters": test_params}
                )
                
                if test_response.status_code == 200:
                    result = test_response.json()
                    print(f"✅ 测试成功: {result.get('success')}")
                    if result.get('result'):
                        print(f"   结果预览: {result['result'][:100]}...")
                else:
                    print(f"❌ 测试失败: {test_response.status_code}")
                    
            else:
                print("❌ 没有找到万年历工具")
                
        else:
            print(f"❌ API访问失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API测试失败: {e}")


if __name__ == "__main__":
    print("🚀 注册万年历工具到数据库")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 注册工具
    success = register_calendar_tool()
    
    if success:
        # 测试API
        test_calendar_api()
        
        print("\n🎉 完成！万年历工具已成功注册")
        print("💡 现在您可以在前端工具管理页面看到万年历工具")
        print("🔗 访问: http://localhost:3003/tools")
        print("\n📖 万年历工具支持的功能:")
        print("   📅 get_date_info - 获取指定日期详细信息")
        print("   📆 get_month_calendar - 获取月历")
        print("   📊 get_year_info - 获取年份信息")
        print("   🎂 calculate_age - 计算年龄")
    else:
        print("\n❌ 万年历工具注册失败")
    
    print("=" * 50) 
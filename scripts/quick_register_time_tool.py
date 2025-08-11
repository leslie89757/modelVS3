#!/usr/bin/env python3
"""快速注册精确时间工具到数据库"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Tool
import uuid

def register_precision_time_tool():
    """注册精确时间工具到数据库"""
    
    print("🔧 快速注册精确时间工具...")
    
    try:
        # 创建数据库连接
        DATABASE_URL = "postgresql://postgres:password@localhost:5432/modelvs3"
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 检查工具是否已存在
        existing_tool = db.query(Tool).filter(Tool.name == "precision_time").first()
        
        if existing_tool:
            print(f"✅ 精确时间工具已存在，ID: {existing_tool.id}")
            print(f"   更新现有工具配置...")
            
            # 更新工具配置
            existing_tool.description = "获取当前精确时间，支持多种时区和格式化选项"
            existing_tool.schema = {
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
                                "description": "时间格式类型",
                                "default": "iso"
                            },
                            "include_microseconds": {
                                "type": "boolean",
                                "description": "是否包含微秒精度",
                                "default": True
                            },
                            "locale": {
                                "type": "string",
                                "description": "语言环境，如 zh_CN, en_US",
                                "default": "zh_CN"
                            },
                            "action": {
                                "type": "string",
                                "enum": ["get_time", "get_timezone_info"],
                                "description": "操作类型：获取时间或获取时区信息",
                                "default": "get_time"
                            }
                        },
                        "required": []
                    }
                }
            }
            existing_tool.enabled = True
            
        else:
            print("➕ 创建新的精确时间工具...")
            
            # 创建新工具
            new_tool = Tool(
                name="precision_time",
                description="获取当前精确时间，支持多种时区和格式化选项",
                schema={
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
                                    "description": "时间格式类型",
                                    "default": "iso"
                                },
                                "include_microseconds": {
                                    "type": "boolean",
                                    "description": "是否包含微秒精度",
                                    "default": True
                                },
                                "locale": {
                                    "type": "string",
                                    "description": "语言环境，如 zh_CN, en_US",
                                    "default": "zh_CN"
                                },
                                "action": {
                                    "type": "string",
                                    "enum": ["get_time", "get_timezone_info"],
                                    "description": "操作类型：获取时间或获取时区信息",
                                    "default": "get_time"
                                }
                            },
                            "required": []
                        }
                    }
                },
                enabled=True
            )
            db.add(new_tool)
        
        # 提交更改
        db.commit()
        
        # 验证结果
        precision_tool = db.query(Tool).filter(Tool.name == "precision_time").first()
        
        if precision_tool:
            print("✅ 精确时间工具注册成功！")
            print(f"   ID: {precision_tool.id}")
            print(f"   名称: {precision_tool.name}")
            print(f"   描述: {precision_tool.description}")
            print(f"   启用状态: {'✅ 启用' if precision_tool.enabled else '❌ 禁用'}")
            print(f"   创建时间: {precision_tool.created_at}")
        
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

def test_api_access():
    """测试API访问"""
    
    print("\n🌐 测试API访问...")
    
    import requests
    
    try:
        # 测试工具列表API
        response = requests.get("http://localhost:8000/api/v1/tools/")
        
        if response.status_code == 200:
            tools = response.json()
            print(f"✅ API访问成功，返回 {len(tools)} 个工具")
            
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
            
            return True
        else:
            print(f"❌ API访问失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 快速注册精确时间工具到数据库")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 注册工具
    success = register_precision_time_tool()
    
    if success:
        # 测试API
        api_success = test_api_access()
        
        if api_success:
            print("\n🎉 完成！精确时间工具已成功注册")
            print("💡 现在您可以在前端工具管理页面看到这个工具")
            print("🔗 访问: http://localhost:3003/tools")
        else:
            print("\n⚠️ 工具注册成功，但API测试失败")
    else:
        print("\n❌ 工具注册失败")
    
    print("=" * 50) 
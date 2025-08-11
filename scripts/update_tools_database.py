#!/usr/bin/env python3
"""更新数据库中的工具，确保所有Function Call工具都被正确注册"""

import asyncio
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from src.database import engine, get_db
from src.models import Tool
from src.core.tool_executor import ToolExecutor


async def update_tools_in_database():
    """更新数据库中的工具"""
    
    print("🔧 开始更新数据库中的工具...")
    
    try:
        # 创建ToolExecutor实例
        tool_executor = ToolExecutor()
        
        # 获取数据库会话
        db = next(get_db())
        
        # 获取所有已注册的工具
        tool_names = ["web_search", "calculator", "file_reader", "qimen_dunjia"]
        
        registered_count = 0
        updated_count = 0
        
        for tool_name in tool_names:
            print(f"\n📦 处理工具: {tool_name}")
            
            # 获取工具schema
            schema = await tool_executor.get_tool_schema(tool_name)
            if not schema:
                print(f"   ❌ 无法获取工具schema: {tool_name}")
                continue
            
            # 检查工具是否已存在
            existing_tool = db.query(Tool).filter(Tool.name == tool_name).first()
            
            if existing_tool:
                # 更新现有工具
                print(f"   🔄 更新现有工具")
                existing_tool.description = schema["function"]["description"]
                existing_tool.schema = schema
                existing_tool.enabled = True
                existing_tool.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # 创建新工具
                print(f"   ➕ 创建新工具")
                new_tool = Tool(
                    name=tool_name,
                    description=schema["function"]["description"],
                    schema=schema,
                    enabled=True
                )
                db.add(new_tool)
                registered_count += 1
        
        # 提交所有更改
        db.commit()
        
        print(f"\n✅ 工具更新完成!")
        print(f"   📊 新注册: {registered_count} 个工具")
        print(f"   🔄 更新: {updated_count} 个工具")
        print(f"   📅 总计: {registered_count + updated_count} 个工具")
        
        # 验证注册结果
        total_tools = db.query(Tool).count()
        enabled_tools = db.query(Tool).filter(Tool.enabled == True).count()
        
        print(f"\n📋 数据库工具统计:")
        print(f"   总工具数: {total_tools}")
        print(f"   启用工具数: {enabled_tools}")
        
        # 显示所有工具列表
        all_tools = db.query(Tool).all()
        print(f"\n📝 当前数据库中的所有工具:")
        for i, tool in enumerate(all_tools, 1):
            status = "✅ 启用" if tool.enabled else "❌ 禁用"
            print(f"   {i}. {tool.name} - {status}")
            print(f"      描述: {tool.description}")
            if tool.created_at:
                print(f"      创建时间: {tool.created_at}")
        
        db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 更新工具失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tools():
    """测试所有工具"""
    
    print("\n🧪 测试所有工具...")
    
    try:
        tool_executor = ToolExecutor()
        
        # 测试计算器
        print("\n--- 测试计算器 ---")
        result = await tool_executor.execute_tool("calculator", {"expression": "2 + 3 * 4"})
        if result["success"]:
            print(f"✅ 计算器测试成功: {result['result']}")
        else:
            print(f"❌ 计算器测试失败: {result['error']}")
        
        # 测试奇门遁甲
        print("\n--- 测试奇门遁甲 ---")
        result = await tool_executor.execute_tool("qimen_dunjia", {})
        if result["success"]:
            print(f"✅ 奇门遁甲测试成功")
            print(f"   结果预览: {result['result'][:200]}...")
        else:
            print(f"❌ 奇门遁甲测试失败: {result['error']}")
        
        # 测试网页搜索
        print("\n--- 测试网页搜索 ---")
        result = await tool_executor.execute_tool("web_search", {"query": "Python"})
        if result["success"]:
            print(f"✅ 网页搜索测试成功")
            print(f"   结果预览: {result['result'][:200]}...")
        else:
            print(f"❌ 网页搜索测试失败: {result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 工具测试失败: {e}")
        return False


if __name__ == "__main__":
    async def main():
        """主函数"""
        print("🚀 工具数据库更新程序")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 步骤1: 更新工具到数据库
        update_success = await update_tools_in_database()
        
        if not update_success:
            print("\n❌ 工具更新失败，退出程序")
            return False
        
        # 步骤2: 测试工具
        test_success = await test_tools()
        
        if not test_success:
            print("\n❌ 工具测试失败")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 所有工具已成功更新到数据库并测试通过！")
        print("💡 现在您可以在前端工具管理界面中看到所有工具")
        print("🔧 Agent可以在配置中选择并使用这些工具")
        
        return True
    
    # 运行主函数
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 
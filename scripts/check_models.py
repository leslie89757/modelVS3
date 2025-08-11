#!/usr/bin/env python3
"""检查系统中配置的模型信息"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Model

def main():
    # 连接数据库
    database_url = "postgresql://postgres:password@postgres:5432/modelvs3"
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 查询所有模型
        models = db.query(Model).all()
        print(f'📊 系统中共有 {len(models)} 个模型配置:')
        print('=' * 80)

        for i, model in enumerate(models, 1):
            print(f'{i}. 📝 模型名称: {model.name}')
            print(f'   🏷️  显示名称: {model.display_name}')
            print(f'   🔧 提供商: {model.provider}')
            print(f'   🌐 API端点: {model.api_base}')
            
            # 安全显示API密钥
            if model.api_key and len(model.api_key) > 14:
                api_key_display = f"{model.api_key[:10]}...{model.api_key[-4:]}"
            else:
                api_key_display = "未配置" if not model.api_key else "密钥过短"
            print(f'   🔑 API密钥: {api_key_display}')
            
            print(f'   📊 状态: {"✅ 启用" if model.enabled else "❌ 禁用"}')
            print(f'   💰 定价: 输入${model.input_price_per_token:.6f}/token, 输出${model.output_price_per_token:.6f}/token')
            print('-' * 80)

        # 检查DeepSeek模型
        deepseek_models = [m for m in models if 'deepseek' in m.name.lower() or 'deepseek' in m.provider.lower()]
        if deepseek_models:
            print(f"\n🤖 发现 {len(deepseek_models)} 个DeepSeek相关模型:")
            for model in deepseek_models:
                print(f"   - {model.name} ({model.provider}) - {'启用' if model.enabled else '禁用'}")
        else:
            print("\n⚠️  未发现DeepSeek相关模型配置")

    except Exception as e:
        print(f"❌ 查询模型失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

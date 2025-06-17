#!/usr/bin/env python3
"""
LlamaIndex配置测试脚本
测试LlamaIndex是否正确使用base_url配置
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.config import settings
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

def test_llamaindex_config():
    """测试LlamaIndex配置"""
    print("🔍 测试LlamaIndex配置...")
    
    print(f"📖 从配置文件读取:")
    print(f"   API Key: {settings.openai_api_key[:10]}...{settings.openai_api_key[-4:]}")
    print(f"   Base URL: {settings.openai_base_url}")
    print(f"   Model: {settings.openai_model}")
    print(f"   Embedding Model: {settings.embedding_model}")
    
    # 配置LlamaIndex
    print("\n🔧 配置LlamaIndex...")
    
    # 设置嵌入模型
    embed_model = OpenAIEmbedding(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.embedding_model
    )
    
    # 设置LLM
    llm = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_model,
        temperature=0.1
    )
    
    # 设置全局配置
    Settings.embed_model = embed_model
    Settings.llm = llm
    
    print("✅ LlamaIndex配置完成")
    
    # 测试嵌入模型
    print("\n🔍 测试嵌入模型...")
    try:
        embeddings = embed_model.get_text_embedding("测试文本")
        print(f"✅ 嵌入模型测试成功")
        print(f"   向量维度: {len(embeddings)}")
    except Exception as e:
        print(f"❌ 嵌入模型测试失败: {e}")
        return False
    
    # 测试LLM
    print("\n🔍 测试LLM...")
    try:
        response = llm.complete("请回复'测试成功'")
        print(f"✅ LLM测试成功")
        print(f"   回复: {response.text}")
    except Exception as e:
        print(f"❌ LLM测试失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                 LlamaIndex 配置测试工具                      ║")
    print("║                                                              ║")
    print("║  🔧 测试LlamaIndex配置                                      ║")
    print("║  🌐 验证base_url设置                                       ║")
    print("║  🤖 测试模型可用性                                         ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    success = test_llamaindex_config()
    
    print("\n" + "="*60)
    if success:
        print("🎉 LlamaIndex配置测试通过！")
    else:
        print("❌ LlamaIndex配置测试失败！")
        print("\n💡 可能的解决方案:")
        print("   1. 检查LlamaIndex版本是否支持base_url参数")
        print("   2. 尝试设置环境变量 OPENAI_BASE_URL")
        print("   3. 检查API密钥和代理地址是否正确")
    print("="*60)

if __name__ == "__main__":
    main()

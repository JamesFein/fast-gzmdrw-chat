#!/usr/bin/env python3
"""
OpenAI API密钥测试脚本
测试API密钥的有效性、余额和可用模型
"""

import os
import sys
import requests
import json
from datetime import datetime
from pathlib import Path

def load_env_file():
    """加载.env文件中的配置"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ 错误: 未找到.env文件")
        return None, None
    
    api_key = None
    base_url = None
    
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('OPENAI_API_KEY='):
                    api_key = line.split('=', 1)[1]
                elif line.startswith('OPENAI_BASE_URL='):
                    base_url = line.split('=', 1)[1]
        
        return api_key, base_url
    except Exception as e:
        print(f"❌ 读取.env文件失败: {e}")
        return None, None

def test_api_connection(api_key, base_url):
    """测试API连接"""
    print("🔍 测试API连接...")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # 测试模型列表接口
    models_url = f"{base_url}/models" if base_url else "https://api.openai.com/v1/models"
    
    try:
        response = requests.get(models_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ API连接成功")
            return True, response.json()
        else:
            print(f"❌ API连接失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   错误信息: {error_data.get('error', {}).get('message', '未知错误')}")
            except:
                print(f"   响应内容: {response.text[:200]}")
            return False, None
            
    except requests.exceptions.Timeout:
        print("❌ API连接超时")
        return False, None
    except requests.exceptions.ConnectionError:
        print("❌ 网络连接错误")
        return False, None
    except Exception as e:
        print(f"❌ API连接异常: {e}")
        return False, None

def test_embedding_model(api_key, base_url):
    """测试嵌入模型"""
    print("🔍 测试嵌入模型...")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    embeddings_url = f"{base_url}/embeddings" if base_url else "https://api.openai.com/v1/embeddings"
    
    data = {
        "model": "text-embedding-3-small",
        "input": "测试文本"
    }
    
    try:
        response = requests.post(embeddings_url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            embedding_length = len(result['data'][0]['embedding'])
            print(f"✅ 嵌入模型测试成功")
            print(f"   模型: text-embedding-3-small")
            print(f"   向量维度: {embedding_length}")
            print(f"   Token使用: {result['usage']['total_tokens']}")
            return True
        else:
            print(f"❌ 嵌入模型测试失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   错误信息: {error_data.get('error', {}).get('message', '未知错误')}")
            except:
                print(f"   响应内容: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 嵌入模型测试异常: {e}")
        return False

def test_chat_model(api_key, base_url):
    """测试聊天模型"""
    print("🔍 测试聊天模型...")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    chat_url = f"{base_url}/chat/completions" if base_url else "https://api.openai.com/v1/chat/completions"
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "请回复'测试成功'"}
        ],
        "max_tokens": 10,
        "temperature": 0
    }
    
    try:
        response = requests.post(chat_url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            reply = result['choices'][0]['message']['content']
            print(f"✅ 聊天模型测试成功")
            print(f"   模型: gpt-4o-mini")
            print(f"   回复: {reply}")
            print(f"   Token使用: {result['usage']['total_tokens']}")
            return True
        else:
            print(f"❌ 聊天模型测试失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   错误信息: {error_data.get('error', {}).get('message', '未知错误')}")
            except:
                print(f"   响应内容: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 聊天模型测试异常: {e}")
        return False

def check_available_models(models_data):
    """检查可用模型"""
    if not models_data or 'data' not in models_data:
        return
    
    print("📋 可用模型列表:")
    
    # 筛选相关模型
    embedding_models = []
    chat_models = []
    
    for model in models_data['data']:
        model_id = model['id']
        if 'embedding' in model_id:
            embedding_models.append(model_id)
        elif any(x in model_id for x in ['gpt', 'chat']):
            chat_models.append(model_id)
    
    if embedding_models:
        print("   📊 嵌入模型:")
        for model in sorted(embedding_models)[:5]:  # 只显示前5个
            print(f"      - {model}")
        if len(embedding_models) > 5:
            print(f"      ... 还有 {len(embedding_models) - 5} 个模型")
    
    if chat_models:
        print("   💬 聊天模型:")
        for model in sorted(chat_models)[:5]:  # 只显示前5个
            print(f"      - {model}")
        if len(chat_models) > 5:
            print(f"      ... 还有 {len(chat_models) - 5} 个模型")

def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                   OpenAI API 密钥测试工具                    ║
║                                                              ║
║  🔑 测试API密钥有效性                                       ║
║  🌐 检查网络连接                                           ║
║  🤖 验证模型可用性                                         ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """主函数"""
    print_banner()
    
    # 加载配置
    print("📖 读取配置文件...")
    api_key, base_url = load_env_file()
    
    if not api_key:
        print("❌ 未找到API密钥")
        print("💡 请在.env文件中设置 OPENAI_API_KEY")
        sys.exit(1)
    
    # 显示配置信息
    print(f"✅ API密钥: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else api_key}")
    print(f"✅ API地址: {base_url or 'https://api.openai.com/v1'}")
    
    print("\n" + "="*60)
    print("🚀 开始测试...")
    print("="*60)
    
    # 测试API连接
    connection_ok, models_data = test_api_connection(api_key, base_url)
    
    if not connection_ok:
        print("\n❌ API连接失败，无法继续测试")
        print("\n💡 可能的解决方案:")
        print("   1. 检查API密钥是否正确")
        print("   2. 检查网络连接")
        print("   3. 检查API地址是否正确")
        print("   4. 确认API密钥有足够余额")
        sys.exit(1)
    
    # 检查可用模型
    check_available_models(models_data)
    
    print("\n" + "-"*60)
    
    # 测试嵌入模型
    embedding_ok = test_embedding_model(api_key, base_url)
    
    print("\n" + "-"*60)
    
    # 测试聊天模型
    chat_ok = test_chat_model(api_key, base_url)
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试结果总结:")
    print("="*60)
    
    print(f"🔗 API连接: {'✅ 成功' if connection_ok else '❌ 失败'}")
    print(f"📊 嵌入模型: {'✅ 可用' if embedding_ok else '❌ 不可用'}")
    print(f"💬 聊天模型: {'✅ 可用' if chat_ok else '❌ 不可用'}")
    
    if connection_ok and embedding_ok and chat_ok:
        print("\n🎉 所有测试通过！API密钥配置正确，可以正常使用RAG应用。")
        print("\n🚀 现在可以运行: python start.py")
    else:
        print("\n⚠️  部分测试失败，请检查配置或联系API提供商。")
    
    print(f"\n⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

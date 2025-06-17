#!/usr/bin/env python3
"""
RAG聊天应用启动脚本
一键启动整个应用，包括环境检查、依赖安装、服务启动等
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def print_banner():
    """打印应用横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    RAG 聊天应用启动器                        ║
║                                                              ║
║  🤖 基于 LlamaIndex + ChromaDB 的智能文档问答系统           ║
║  📁 支持 TXT 文件自动索引和混合检索                         ║
║  💬 提供美观的 Web 聊天界面                                 ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print(f"   当前版本: {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    print(f"✅ Python版本检查通过: {version.major}.{version.minor}.{version.micro}")

def check_env_file():
    """检查环境配置文件"""
    print("🔍 检查环境配置...")
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ 错误: 未找到.env配置文件")
        print("📝 请创建.env文件并配置以下参数:")
        print("""
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://your-proxy-url.com/v1
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
DATA_DIR=./data
STORAGE_DIR=./storage
COLLECTION_NAME=documents

# ChromaDB SQLite配置
CHROMA_DB_IMPL=duckdb+parquet
CHROMA_PERSIST_DIRECTORY=./storage

# CORS配置
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000", "https://chat.example.org"]
        """)
        sys.exit(1)
    
    print("✅ 环境配置文件检查通过")

def check_directories():
    """检查并创建必要的目录"""
    print("🔍 检查项目目录结构...")
    
    directories = [
        "data",
        "storage", 
        "backend/app",
        "backend/config",
        "frontend/static/css",
        "frontend/static/js",
        "frontend/templates"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"📁 创建目录: {directory}")
            dir_path.mkdir(parents=True, exist_ok=True)
        else:
            print(f"✅ 目录已存在: {directory}")

def check_virtual_environment():
    """检查虚拟环境"""
    print("🔍 检查虚拟环境...")
    
    # 检查是否在虚拟环境中
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 已在虚拟环境中")
        return True
    
    # 检查是否存在venv目录
    venv_path = Path("venv")
    if venv_path.exists():
        print("⚠️  检测到虚拟环境目录，但当前未激活")
        print("💡 请先激活虚拟环境:")
        if os.name == 'nt':  # Windows
            print("   venv\\Scripts\\activate")
        else:  # Linux/Mac
            print("   source venv/bin/activate")
        return False
    
    print("⚠️  未检测到虚拟环境")
    create_venv = input("是否创建新的虚拟环境? (y/n): ").lower().strip()
    
    if create_venv == 'y':
        print("📦 创建虚拟环境...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ 虚拟环境创建完成")
        print("💡 请激活虚拟环境后重新运行此脚本:")
        if os.name == 'nt':  # Windows
            print("   venv\\Scripts\\activate")
        else:  # Linux/Mac
            print("   source venv/bin/activate")
        return False
    
    return True

def install_dependencies():
    """安装依赖包"""
    print("🔍 检查依赖包...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ 错误: 未找到requirements.txt文件")
        sys.exit(1)
    
    try:
        # 检查是否已安装主要依赖
        import fastapi
        import uvicorn
        import llama_index
        print("✅ 主要依赖包已安装")
    except ImportError:
        print("📦 安装依赖包...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ 依赖包安装完成")

def check_data_directory():
    """检查数据目录"""
    print("🔍 检查数据目录...")
    
    data_dir = Path("data")
    txt_files = list(data_dir.glob("*.txt"))
    
    if not txt_files:
        print("⚠️  data目录中没有TXT文件")
        print("💡 请将要处理的TXT文件放入data目录中")
        print("📁 示例文件结构:")
        print("   data/")
        print("   ├── document1.txt")
        print("   ├── document2.txt")
        print("   └── ...")
        
        create_sample = input("是否创建示例文档? (y/n): ").lower().strip()
        if create_sample == 'y':
            sample_content = """这是一个示例文档。

RAG（检索增强生成）是一种结合了信息检索和文本生成的AI技术。
它通过检索相关文档片段，然后基于这些片段生成回答。

主要优势：
1. 提高回答的准确性和相关性
2. 减少模型幻觉问题
3. 支持实时更新知识库
4. 可以处理大量文档

技术组件：
- 向量数据库：存储文档的向量表示
- 检索器：根据查询检索相关文档
- 生成器：基于检索结果生成回答
- 混合检索：结合关键词检索和语义检索

应用场景：
- 企业知识库问答
- 文档智能分析
- 客服机器人
- 学术研究助手
"""
            sample_file = data_dir / "sample_document.txt"
            sample_file.write_text(sample_content, encoding='utf-8')
            print(f"✅ 已创建示例文档: {sample_file}")
    else:
        print(f"✅ 找到 {len(txt_files)} 个TXT文件")
        for txt_file in txt_files[:5]:  # 只显示前5个
            print(f"   📄 {txt_file.name}")
        if len(txt_files) > 5:
            print(f"   ... 还有 {len(txt_files) - 5} 个文件")

def start_server():
    """启动服务器"""
    print("🚀 启动RAG聊天应用...")
    
    # 检查端口是否被占用
    import socket
    port = 8000
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('localhost', port)) == 0:
            print(f"⚠️  端口 {port} 已被占用")
            port = 8001
            print(f"🔄 尝试使用端口 {port}")
    
    print(f"🌐 服务器将在 http://localhost:{port} 启动")
    print("📱 浏览器将自动打开...")
    
    # 延迟打开浏览器
    def open_browser():
        time.sleep(3)  # 等待服务器启动
        webbrowser.open(f"http://localhost:{port}")
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # 启动服务器
    try:
        # 设置环境变量
        env = os.environ.copy()
        env['PYTHONPATH'] = os.getcwd()

        # 从.env文件读取OpenAI配置并设置环境变量
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('OPENAI_API_KEY='):
                        env['OPENAI_API_KEY'] = line.split('=', 1)[1]
                    elif line.startswith('OPENAI_BASE_URL='):
                        env['OPENAI_BASE_URL'] = line.split('=', 1)[1]

        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "backend.app.main:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload"
        ], check=True, env=env)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动服务器时发生错误: {e}")
        sys.exit(1)

def main():
    """主函数"""
    try:
        print_banner()
        
        # 环境检查
        check_python_version()
        check_env_file()
        check_directories()
        
        if not check_virtual_environment():
            sys.exit(1)
        
        install_dependencies()
        check_data_directory()
        
        print("\n" + "="*60)
        print("🎉 环境检查完成，准备启动应用...")
        print("="*60)
        
        # 启动服务器
        start_server()
        
    except KeyboardInterrupt:
        print("\n👋 启动已取消")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

# 极简 RAG 聊天应用开发脚本

## 项目概述

**目标**：构建一个极简的 RAG（检索增强生成）聊天应用，用户可以将 TXT 文件放入指定目录，运行脚本后通过网页界面与文档内容进行对话。

**核心功能**：

- 📁 文档处理：自动索引指定目录下的所有 TXT 文件
- 🔍 混合检索：BM25 关键词检索 + 向量相似度检索
- 💬 智能问答：基于检索到的文档内容生成回答
- 🌐 Web 界面：简洁的单页面聊天界面
- 🚀 一键部署：运行脚本即可启动服务

**技术栈**：

- 后端：Python 3.11 + FastAPI + LlamaIndex + ChromaDB
- 前端：HTML + TailwindCSS + Vanilla JavaScript
- LLM：GPT-4o-mini（通过代理 API）
- 向量模型：text-embedding-3-small

## 开发步骤

### 第一步：环境准备

#### 1.1 创建项目目录结构

```bash
mkdir rag-chat-app
cd rag-chat-app

# 创建目录结构
mkdir -p {backend,frontend,data,storage}
mkdir -p backend/{app,config}
mkdir -p frontend/{static/{css,js},templates}
```

#### 1.2 创建 Python 虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 激活虚拟环境 (Linux/Mac)
source venv/bin/activate
```

#### 1.3 安装依赖包

创建 `requirements.txt`：

```txt
fastapi==0.115.13
uvicorn[standard]==0.34.3
llama-index==0.12.42
llama-index-vector-stores-chroma
llama-index-embeddings-openai
llama-index-llms-openai
chromadb==1.0.12
pydantic-settings==2.9.1
python-multipart
python-dotenv
```

安装依赖：

```bash
pip install -r requirements.txt
```

### 第二步：配置管理

#### 2.1 创建环境配置文件

创建 `.env` 文件：

```env
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

# CORS配置
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000", "https://chat.example.org"]
```

#### 2.2 创建配置类

创建 `backend/config/settings.py`：

```python
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # OpenAI配置
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # 应用配置
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    data_dir: str = "./data"
    storage_dir: str = "./storage"
    collection_name: str = "documents"

    # CORS配置
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = False

# 全局配置实例
settings = Settings()
```

### 第三步：后端开发

#### 3.1 创建 RAG 服务核心类

创建 `backend/app/rag_service.py`：

```python
import os
import logging
from typing import List, Optional
from pathlib import Path

import chromadb
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings as LlamaSettings
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.node_parser import SentenceSplitter

from config.settings import settings

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.index = None
        self.query_engine = None
        self._setup_llama_index()
        self._initialize_vector_store()

    def _setup_llama_index(self):
        """配置LlamaIndex全局设置"""
        # 配置LLM
        llm = OpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.1
        )

        # 配置嵌入模型
        embed_model = OpenAIEmbedding(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )

        # 设置全局配置
        LlamaSettings.llm = llm
        LlamaSettings.embed_model = embed_model
        LlamaSettings.node_parser = SentenceSplitter(
            chunk_size=1024,
            chunk_overlap=200
        )

    def _initialize_vector_store(self):
        """初始化向量存储"""
        try:
            # 确保存储目录存在
            os.makedirs(settings.storage_dir, exist_ok=True)

            # 初始化ChromaDB
            chroma_client = chromadb.PersistentClient(
                path=settings.storage_dir
            )

            # 获取或创建集合
            try:
                chroma_collection = chroma_client.get_collection(
                    settings.collection_name
                )
                logger.info(f"加载现有集合: {settings.collection_name}")
            except:
                chroma_collection = chroma_client.create_collection(
                    settings.collection_name
                )
                logger.info(f"创建新集合: {settings.collection_name}")

            # 创建向量存储
            vector_store = ChromaVectorStore(
                chroma_collection=chroma_collection
            )
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )

            # 尝试加载现有索引
            try:
                self.index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store,
                    storage_context=storage_context
                )
                logger.info("成功加载现有索引")
            except:
                # 如果没有现有索引，创建空索引
                self.index = VectorStoreIndex(
                    nodes=[],
                    storage_context=storage_context
                )
                logger.info("创建新的空索引")

            # 创建查询引擎
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=5,
                response_mode="compact"
            )

        except Exception as e:
            logger.error(f"初始化向量存储失败: {e}")
            raise

    def load_documents(self) -> bool:
        """加载数据目录中的文档"""
        try:
            data_path = Path(settings.data_dir)
            if not data_path.exists():
                logger.warning(f"数据目录不存在: {data_path}")
                return False

            # 检查是否有TXT文件
            txt_files = list(data_path.glob("*.txt"))
            if not txt_files:
                logger.warning(f"数据目录中没有找到TXT文件: {data_path}")
                return False

            logger.info(f"找到 {len(txt_files)} 个TXT文件")

            # 读取文档
            reader = SimpleDirectoryReader(
                input_dir=str(data_path),
                required_exts=[".txt"],
                recursive=True
            )
            documents = reader.load_data()

            if not documents:
                logger.warning("没有成功加载任何文档")
                return False

            logger.info(f"成功加载 {len(documents)} 个文档")

            # 重新构建索引
            self.index = VectorStoreIndex.from_documents(
                documents,
                storage_context=self.index.storage_context
            )

            # 更新查询引擎
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=5,
                response_mode="compact"
            )

            logger.info("文档索引构建完成")
            return True

        except Exception as e:
            logger.error(f"加载文档失败: {e}")
            return False

    def query(self, question: str) -> dict:
        """查询RAG系统"""
        try:
            if not self.query_engine:
                return {
                    "success": False,
                    "error": "RAG系统未初始化",
                    "answer": ""
                }

            logger.info(f"处理查询: {question}")

            # 执行查询
            response = self.query_engine.query(question)

            # 提取源文档信息
            source_nodes = getattr(response, 'source_nodes', [])
            sources = []
            for node in source_nodes:
                if hasattr(node, 'metadata') and 'file_name' in node.metadata:
                    sources.append({
                        "file": node.metadata['file_name'],
                        "score": getattr(node, 'score', 0.0)
                    })

            return {
                "success": True,
                "answer": str(response),
                "sources": sources,
                "error": ""
            }

        except Exception as e:
            logger.error(f"查询失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": ""
            }

    def get_status(self) -> dict:
        """获取系统状态"""
        try:
            data_path = Path(settings.data_dir)
            txt_files = list(data_path.glob("*.txt")) if data_path.exists() else []

            return {
                "initialized": self.query_engine is not None,
                "data_dir_exists": data_path.exists(),
                "txt_files_count": len(txt_files),
                "txt_files": [f.name for f in txt_files]
            }
        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return {
                "initialized": False,
                "error": str(e)
            }

# 全局RAG服务实例
rag_service = RAGService()
```

#### 3.2 创建 FastAPI 应用

创建 `backend/app/main.py`：

```python
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from config.settings import settings
from app.rag_service import rag_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="RAG聊天应用",
    description="基于LlamaIndex和ChromaDB的极简RAG聊天应用",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# 请求模型
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    success: bool
    answer: str
    sources: list = []
    error: str = ""

# API路由
@app.get("/")
async def root():
    """根路径，返回聊天页面"""
    return FileResponse("frontend/chat.html")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "RAG聊天应用运行正常"}

@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    try:
        status = rag_service.get_status()
        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/load-documents")
async def load_documents():
    """加载文档到向量数据库"""
    try:
        success = rag_service.load_documents()
        if success:
            return {"success": True, "message": "文档加载成功"}
        else:
            return {"success": False, "message": "文档加载失败，请检查data目录中是否有TXT文件"}
    except Exception as e:
        logger.error(f"加载文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """查询文档"""
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="问题不能为空")

        result = rag_service.query(request.question)
        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("RAG聊天应用启动中...")

    # 尝试自动加载文档
    try:
        rag_service.load_documents()
        logger.info("启动时自动加载文档完成")
    except Exception as e:
        logger.warning(f"启动时自动加载文档失败: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )
```

#### 3.3 创建启动脚本

创建 `backend/run.py`：

```python
#!/usr/bin/env python3
"""
RAG聊天应用启动脚本
"""
import os
import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings

def main():
    """主函数"""
    print("🚀 启动RAG聊天应用...")
    print(f"📍 服务地址: http://{settings.app_host}:{settings.app_port}")
    print(f"📁 数据目录: {settings.data_dir}")
    print(f"💾 存储目录: {settings.storage_dir}")
    print("=" * 50)

    # 确保必要目录存在
    os.makedirs(settings.data_dir, exist_ok=True)
    os.makedirs(settings.storage_dir, exist_ok=True)

    # 启动服务
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
```

### 第四步：前端开发

#### 4.1 创建聊天页面 HTML

创建 `frontend/chat.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>RAG聊天应用</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
      .chat-container {
        height: calc(100vh - 200px);
      }
      .message-bubble {
        max-width: 80%;
        word-wrap: break-word;
      }
      .typing-indicator {
        display: none;
      }
      .typing-indicator.show {
        display: flex;
      }
      .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #9ca3af;
        animation: typing 1.4s infinite ease-in-out;
      }
      .dot:nth-child(1) {
        animation-delay: -0.32s;
      }
      .dot:nth-child(2) {
        animation-delay: -0.16s;
      }
      .dot:nth-child(3) {
        animation-delay: 0s;
      }

      @keyframes typing {
        0%,
        80%,
        100% {
          transform: scale(0);
        }
        40% {
          transform: scale(1);
        }
      }
    </style>
  </head>
  <body class="bg-gray-100">
    <div class="container mx-auto max-w-4xl p-4">
      <!-- 头部 -->
      <header class="bg-white rounded-lg shadow-md p-6 mb-4">
        <h1 class="text-3xl font-bold text-gray-800 text-center">
          🤖 RAG聊天应用
        </h1>
        <p class="text-gray-600 text-center mt-2">
          基于您的文档内容进行智能问答
        </p>

        <!-- 状态栏 -->
        <div class="mt-4 flex justify-between items-center">
          <div id="status-indicator" class="flex items-center">
            <div class="w-3 h-3 rounded-full bg-gray-400 mr-2"></div>
            <span class="text-sm text-gray-600">检查状态中...</span>
          </div>
          <button
            id="load-docs-btn"
            class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm transition-colors"
          >
            📁 重新加载文档
          </button>
        </div>
      </header>

      <!-- 聊天区域 -->
      <div class="bg-white rounded-lg shadow-md">
        <!-- 消息列表 -->
        <div
          id="chat-messages"
          class="chat-container overflow-y-auto p-6 space-y-4"
        >
          <div class="flex justify-center">
            <div class="bg-blue-50 text-blue-800 px-4 py-2 rounded-lg text-sm">
              💡 请在data目录放入TXT文件，然后开始提问吧！
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="border-t p-4">
          <div class="flex space-x-2">
            <input
              type="text"
              id="question-input"
              placeholder="请输入您的问题..."
              class="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              maxlength="500"
            />
            <button
              id="send-btn"
              class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors"
            >
              发送
            </button>
          </div>
          <div class="text-xs text-gray-500 mt-2">
            按Enter发送消息 • 最多500字符
          </div>
        </div>
      </div>
    </div>

    <script src="/static/js/chat.js"></script>
  </body>
</html>
```

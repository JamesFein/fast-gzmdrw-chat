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

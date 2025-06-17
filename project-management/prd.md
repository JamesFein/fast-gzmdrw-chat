# 极简 RAG 聊天应用开发脚本

## 关于开发文档和开发流程

**开发文档不写具体的代码，只写项目的关键性知识**
**开发过程中不断测试**
**开发过程中，代码要在后端的终端和前端的 console 输出尽可能多的调试信息**
**一切从简，用最快最方便稳定的方式实现文档中的目标**
**文档仅供参考，一边开发一边改这个文档**

## 项目概述

**目标**：构建一个极简的 RAG（检索增强生成）聊天应用，用户可以将 TXT 文件放入指定目录，运行脚本后通过网页界面与文档内容进行对话。

**核心功能**：

- 📁 文档处理：自动索引指定目录下的所有 TXT 文件
- 🔍 混合检索：BM25 关键词检索 + 向量相似度检索
- 💬 智能问答：基于检索到的文档内容生成回答
- 🌐 Web 界面：简洁的单页面聊天界面
- 🚀 一键部署：运行脚本即可启动服务

**技术栈**：

- 后端：Python 3.11 + FastAPI + LlamaIndex + ChromaDB (SQLite)
- 前端：HTML + TailwindCSS + Vanilla JavaScript
- 数据库：SQLite（ChromaDB 底层存储）
- LLM：GPT-4o-mini（通过代理 API）
- 向量模型：text-embedding-3-small

## 开发步骤

### 第一步：环境准备

#### 1.1 创建项目目录结构

# 在当前目录创建目录结构

mkdir -p {backend,frontend,data,storage}
mkdir -p backend/{app,config}
mkdir -p frontend/{static/{css,js},templates}

````

#### 1.2 创建 Python 虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 激活虚拟环境 (Linux/Mac)
source venv/bin/activate
````

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

# ChromaDB SQLite配置
CHROMA_DB_IMPL=duckdb+parquet
CHROMA_PERSIST_DIRECTORY=./storage

# CORS配置
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000", "https://chat.example.org"]
```

#### 2.2 创建配置类

创建 `backend/config/settings.py`：

### 第三步：后端开发

#### 3.1 创建 RAG 服务核心类

创建 `backend/app/rag_service.py`：

#### 3.2 创建 FastAPI 应用

创建 `backend/app/main.py`：

#### 3.3 创建启动脚本

创建 `backend/run.py`：

### 第四步：前端开发

#### 4.1 创建聊天页面 HTML

#### 4.2 创建 JavaScript 交互逻辑

创建 `frontend/static/js/chat.js`：

### 第五步：部署和运行

#### 5.1 创建项目启动脚本

创建根目录下的 `start.py`：

#### 5.2 创建 README 文档

创建 `README.md`：

````markdown
# RAG 聊天应用

一个基于 LlamaIndex 和 ChromaDB 的极简 RAG（检索增强生成）聊天应用。

## 功能特点

- 🔍 **智能检索**: 结合 BM25 关键词检索和向量相似度检索
- 💬 **自然对话**: 基于 GPT-4o-mini 的智能问答
- 📁 **简单易用**: 只需将 TXT 文件放入 data 目录即可
- 🌐 **Web 界面**: 美观的单页面聊天界面
- ⚡ **快速部署**: 一键启动，无需复杂配置

## 快速开始

### 1. 环境要求

- Python 3.11+
- OpenAI API 密钥（支持代理）

### 2. 安装和配置

```bash
# 克隆或下载项目
git clone <your-repo-url>
cd rag-chat-app

# 创建.env配置文件
cp .env.example .env
# 编辑.env文件，填入你的OpenAI API配置

# 一键启动
python start.py
```
````

### 3. 使用方法

1. 将 TXT 文档放入 `data/` 目录
2. 访问 http://localhost:8000
3. 点击"重新加载文档"按钮
4. 开始与文档对话！

## 项目结构

```
rag-chat-app/
├── backend/           # 后端代码
│   ├── app/          # FastAPI应用
│   ├── config/       # 配置管理
│   └── run.py        # 启动脚本
├── frontend/         # 前端代码
│   ├── static/       # 静态资源
│   └── chat.html     # 聊天页面
├── data/            # 文档目录（放置TXT文件）
├── storage/         # ChromaDB数据存储目录
│   ├── chroma.sqlite3    # SQLite数据库文件（自动生成）
│   └── [向量数据文件]     # 向量嵌入数据（自动生成）
├── .env             # 环境配置
├── requirements.txt # 依赖包
└── start.py         # 一键启动脚本
```

## API 接口设计

### 1. 页面路由

- `GET /` - 聊天页面（返回 HTML）

### 2. 系统状态接口

- `GET /api/status` - 获取系统状态
  ```json
  Response: {
    "status": "ok",
    "documents_count": 10,
    "storage_size": "2.5MB",
    "last_updated": "2024-01-01T12:00:00Z"
  }
  ```

### 3. 文档管理接口

- `POST /api/load-documents` - 重新加载文档
  ```json
  Request: {} (空请求体)
  Response: {
    "success": true,
    "message": "Documents loaded successfully",
    "documents_processed": 5,
    "chunks_created": 150,
    "processing_time": 2.5,
    "replaced_files": [        # 被替换的同名文件列表
      {
        "filename": "document1.txt",
        "old_chunks": 20,
        "new_chunks": 25
      }
    ],
    "new_files": [             # 新增的文件列表
      "document2.txt",
      "document3.txt"
    ]
  }
  ```

### 4. 查询问答接口

- `POST /api/query` - 查询问答

  ```json
  Request: {
    "query": "用户问题",
    "max_results": 5,        // 可选，默认5
    "similarity_threshold": 0.7  // 可选，默认0.7
  }

  Response: {
    "answer": "AI生成的回答",
    "sources": [
      {
        "filename": "document1.txt",
        "content": "相关文档片段",
        "score": 0.85,
        "chunk_index": 2
      }
    ],
    "processing_time": 1.2,
    "tokens_used": 150
  }
  ```

### 5. 错误响应格式

```json
{
  "error": true,
  "message": "错误描述",
  "code": "ERROR_CODE",
  "details": {} // 可选的详细信息
}
```

## 技术栈

- **后端**: FastAPI + LlamaIndex + ChromaDB
- **数据库**: SQLite（ChromaDB 底层存储，自动管理）
- **前端**: HTML + TailwindCSS + Vanilla JS
- **LLM**: GPT-4o-mini
- **向量模型**: text-embedding-3-small

### 数据存储设计

#### 设计思路

基于 PRD 需求分析，本应用采用极简化的数据存储设计：

1. **无用户系统**: 应用为单用户使用，无需用户认证和会话管理
2. **对话历史前端存储**: 对话历史存储在浏览器 localStorage 中，减少后端复杂度
3. **文档向量化存储**: 使用 ChromaDB 存储文档向量和元数据
4. **文件系统存储**: 原始 TXT 文件直接存储在 data 目录

#### 数据表设计

基于 LlamaIndex 的最佳实践，采用简化的单一存储架构：

##### 1. ChromaDB Collection (documents) - 统一存储

```
Collection Name: documents
Purpose: 存储文档块的向量嵌入和文本内容，支持LlamaIndex内置的混合检索

Document Schema:
- id: string (文档块唯一标识，格式: filename_chunk_index)
- content: string (文档块文本内容)
- metadata: dict {
    "filename": string,        # 原始文件名（唯一标识）
    "file_path": string,       # 文件完整路径
    "chunk_index": int,        # 块索引
    "chunk_size": int,         # 块大小
    "file_size": int,          # 原始文件大小
    "file_modified": string,   # 文件修改时间
    "created_at": string,      # 索引创建时间
    "total_chunks": int        # 该文件的总块数
}
- embedding: vector (768维向量，与text-embedding-3-small模型输出维度严格匹配)
```

**设计说明**：

- LlamaIndex 内置 BM25Retriever，可直接从 VectorStoreIndex 的 docstore 创建
- 无需额外的 SQLite 数据库，简化架构
- 混合检索通过 LlamaIndex 的 QueryFusionRetriever 或内置 hybrid 模式实现

##### 2. 文件系统存储

```
data/
├── document1.txt          # 用户上传的TXT文件
├── document2.txt
└── ...

storage/
├── chroma.sqlite3         # ChromaDB SQLite数据库
├── index/                 # 向量索引文件
└── ...                    # 其他ChromaDB生成的文件
```

##### 4. 前端 localStorage 存储

```javascript
// 对话历史存储结构
localStorage.setItem('chat_history', JSON.stringify([
    {
        id: string,           // 消息唯一ID
        type: 'user' | 'assistant',
        content: string,      // 消息内容
        timestamp: number,    // 时间戳
        sources?: [           // 仅assistant消息包含
            {
                filename: string,
                content: string,
                score: number
            }
        ]
    }
]));

// 应用设置
localStorage.setItem('app_settings', JSON.stringify({
    theme: 'light' | 'dark',
    auto_scroll: boolean,
    max_history: number
}));
```

#### 设计优势

1. **极简架构**: 无需复杂的用户管理和会话系统
2. **混合检索**: 基于 LlamaIndex 内置 BM25Retriever，结合关键词检索和向量语义检索
3. **高性能**:
   - ChromaDB 提供高效的向量检索能力
   - LlamaIndex BM25Retriever 提供优化的关键词检索
   - 单一数据源避免同步开销，支持并发访问
4. **易维护**: SQLite 单文件数据库，便于备份和迁移
5. **前端缓存**: localStorage 存储对话历史，减少服务器压力
6. **文件级更新**: 同名文件完全替换机制，确保数据一致性
7. **并发友好**: 利用 ChromaDB 的 SQLite WAL 模式，支持多读单写并发

#### 增量更新规则（重要）

**核心原则**: 文件名唯一性，同名文件完全替换

1. **文件唯一标识**: 每个文件以文件名作为唯一标识
2. **同名文件处理规则**:

   - 检测到同名文件时，首先删除旧文件的所有相关数据
   - 删除内容包括：
     - ChromaDB 中所有相关的文档块记录和向量嵌入
     - docstore 中所有相关的文档节点
     - 所有相关的元数据信息
   - 删除完成后，重新处理新的同名文件
   - 重新进行文本分块、向量化、存储等完整流程

3. **删除操作流程**:

   ```python
   # 伪代码示例 - LlamaIndex方式删除
   def handle_duplicate_file(filename):
       # 1. 删除ChromaDB中的相关记录
       existing_ids = chroma_collection.get(
           where={"filename": filename}
       )["ids"]
       if existing_ids:
           chroma_collection.delete(ids=existing_ids)

       # 2. 删除docstore中的相关节点
       for doc_id in existing_ids:
           if index.docstore.document_exists(doc_id):
               index.docstore.delete_document(doc_id)

       # 3. 处理新文件
       process_new_file(filename)
   ```

4. **更新检测机制**:
   - 扫描 data 目录中的所有 TXT 文件
   - 对比文件修改时间和数据库记录
   - 发现同名文件时触发完全替换流程

#### 数据流程

1. **文档加载**:

   - 扫描 data 目录
   - 检查同名文件冲突
   - 删除旧文件所有相关数据（如存在）
   - 文本分块 → 向量化 → 存储到 ChromaDB 和 docstore

2. **混合检索查询处理**:

   - 用户问题 → 并行检索：
     - BM25 检索：BM25Retriever.from_defaults(docstore=index.docstore)
     - 向量检索：index.as_retriever() 进行语义相似检索
   - 结果融合：使用 QueryFusionRetriever 或内置 hybrid 模式
   - 重排序 → 选择最佳片段 → LLM 生成回答

3. **对话管理**: 前端 localStorage 管理对话历史，后端无状态处理

### ChromaDB 底层存储说明

本应用使用 ChromaDB 作为向量数据库，ChromaDB 底层使用 SQLite 进行数据持久化：

- **chroma.sqlite3**: 存储集合元数据、文档信息、向量索引
- **向量数据文件**: 存储文档的向量嵌入数据
- **自动管理**: 无需手动操作 SQLite，ChromaDB 自动处理所有数据库操作

#### 重要技术注意事项

**向量维度配置**:

- ChromaDB 集合的向量维度必须与嵌入模型输出维度严格匹配
- text-embedding-3-small 输出 768 维向量
- 数据库配置维度超过 768 会导致：
  - 存储空间浪费（多余维度填充 0 值）
  - 检索性能下降（计算复杂度增加）
  - 潜在的配置错误和数据不一致

```python
# 推荐做法：让ChromaDB自动处理维度
collection = client.create_collection(
    name="documents",
    embedding_function=OpenAIEmbeddingFunction(
        model_name="text-embedding-3-small"
    )
    # 不手动指定dimension，让ChromaDB自动检测
)

# 避免的做法：
# metadata={"dimension": 1536}  # 错误！会导致维度不匹配
```

**混合检索实现**:

```python
# LlamaIndex混合检索的两种实现方式

# 方式1：使用内置hybrid模式
query_engine = index.as_query_engine(
    vector_store_query_mode="hybrid",
    similarity_top_k=5
)

# 方式2：使用QueryFusionRetriever
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever

vector_retriever = index.as_retriever(similarity_top_k=5)
bm25_retriever = BM25Retriever.from_defaults(
    docstore=index.docstore,
    similarity_top_k=5
)

fusion_retriever = QueryFusionRetriever(
    [vector_retriever, bm25_retriever],
    similarity_top_k=5,
    num_queries=1,  # 禁用查询生成
    mode="relative_score",
    use_async=False,
)
```

## 常见问题

**Q: 如何添加新文档？**
A: 将 TXT 文件放入 data 目录，然后点击"重新加载文档"按钮。

**Q: 如果上传同名文件会怎样？**
A: 系统会自动删除旧文件的所有相关数据（包括向量、文本块、元数据等），然后重新处理新文件。这确保了数据的一致性，但旧文件的所有信息将完全丢失。

**Q: 支持哪些文档格式？**
A: 目前只支持 TXT 格式，后续可扩展支持 PDF、Word 等。

**Q: 如何修改模型配置？**
A: 编辑.env 文件中的 OPENAI_MODEL 和 EMBEDDING_MODEL 参数。

**Q: 数据存储在哪里？**
A: 向量数据存储在 `storage/` 目录下的 SQLite 数据库中，包括 `chroma.sqlite3` 等文件。

**Q: 如何清空数据库重新开始？**
A: 删除 `storage/` 目录下的所有文件，重启应用即可自动重建数据库。

**Q: 数据库文件很大怎么办？**
A: ChromaDB 会自动压缩数据，如需手动清理可删除不需要的文档后重新加载。

#### 6.2 性能优化建议

1. **向量数据库优化**：

   - 调整 chunk_size 和 chunk_overlap 参数
   - 使用更高效的嵌入模型
   - 实现增量索引更新

2. **SQLite 数据库优化**：

   - 定期清理无用的向量数据
   - 监控 `storage/` 目录大小
   - 考虑使用 `VACUUM` 命令压缩 SQLite 数据库
   - 备份重要的 `chroma.sqlite3` 文件

3. **检索优化**：

   - 实现混合检索（BM25 + 向量检索）
   - 添加重排序机制
   - 优化相似度阈值

4. **用户体验优化**：
   - 添加流式输出支持
   - 实现对话历史记录
   - 添加文档预览功能

## 总结

通过以上步骤，您可以快速构建一个功能完整的 RAG 聊天应用。这个应用具有以下优势：

1. **简单易用**：一键启动，无需复杂配置
2. **功能完整**：包含文档加载、向量检索、智能问答等核心功能
3. **易于扩展**：模块化设计，便于添加新功能
4. **生产就绪**：包含错误处理、日志记录等生产环境必需功能

您可以根据实际需求对应用进行定制和扩展，比如支持更多文档格式、添加用户认证、实现多轮对话等功能。

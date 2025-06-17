# RAG 聊天应用

一个基于 LlamaIndex 和 ChromaDB 的极简 RAG（检索增强生成）聊天应用。

## 🌟 功能特点

- 🔍 **智能检索**: 结合 BM25 关键词检索和向量相似度检索
- 💬 **自然对话**: 基于 GPT-4o-mini 的智能问答
- 📁 **简单易用**: 只需将 TXT 文件放入 data 目录即可
- 🌐 **Web 界面**: 美观的单页面聊天界面
- ⚡ **快速部署**: 一键启动，无需复杂配置
- 🗄️ **SQLite 存储**: 基于 ChromaDB 的 SQLite 底层存储
- 🔄 **文件替换**: 支持同名文件完全替换机制
- 📱 **响应式设计**: 支持桌面和移动设备

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- OpenAI API 密钥（支持代理）

### 2. 安装和配置

```bash
# 克隆或下载项目
git clone <your-repo-url>
cd fast-gzmdrw-chat

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 创建环境配置文件
cp .env.example .env
# 编辑 .env 文件，填入你的 OpenAI API 配置
```

### 3. 配置 .env 文件

创建 `.env` 文件并配置以下参数：

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
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

### 4. 一键启动

```bash
# 一键启动（推荐）
python start.py
```

启动脚本会自动：
- 检查 Python 版本和虚拟环境
- 安装依赖包
- 检查配置文件
- 创建必要目录
- 启动服务器
- 自动打开浏览器

### 5. 手动启动（可选）

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端服务
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. 使用方法

1. 将 TXT 文档放入 `data/` 目录
2. 访问 http://localhost:8000
3. 点击"重新加载文档"按钮
4. 开始与文档对话！

## 📁 项目结构

```
fast-gzmdrw-chat/
├── backend/                 # 后端代码
│   ├── app/                # FastAPI应用
│   │   ├── __init__.py
│   │   ├── main.py         # 主应用文件
│   │   └── rag_service.py  # RAG服务核心类
│   ├── config/             # 配置管理
│   │   ├── __init__.py
│   │   └── settings.py     # 配置类
│   └── __init__.py
├── frontend/               # 前端代码
│   ├── static/            # 静态资源
│   │   ├── css/
│   │   │   └── style.css  # 样式文件
│   │   └── js/
│   │       └── app.js     # JavaScript交互逻辑
│   └── templates/
│       └── index.html     # 聊天页面
├── data/                  # 文档目录（放置TXT文件）
│   └── sample_document.txt # 示例文档
├── storage/               # ChromaDB数据存储目录
│   ├── chroma.sqlite3     # SQLite数据库文件（自动生成）
│   └── [向量数据文件]      # 向量嵌入数据（自动生成）
├── project-management/    # 项目管理文档
│   └── prd.md            # 产品需求文档
├── .env                  # 环境配置
├── requirements.txt      # 依赖包
├── start.py             # 一键启动脚本
└── README.md            # 项目说明
```

## 🔧 API 接口

### 页面路由
- `GET /` - 聊天页面（返回 HTML）

### 系统状态接口
- `GET /api/status` - 获取系统状态

### 文档管理接口
- `POST /api/load-documents` - 重新加载文档

### 查询问答接口
- `POST /api/query` - 查询问答

详细的 API 文档请参考 [PRD 文档](project-management/prd.md)。

## 🛠️ 技术栈

- **后端**: FastAPI + LlamaIndex + ChromaDB
- **数据库**: SQLite（ChromaDB 底层存储，自动管理）
- **前端**: HTML + TailwindCSS + Vanilla JavaScript
- **LLM**: GPT-4o-mini
- **向量模型**: text-embedding-3-small

## 💾 数据存储设计

### 核心特性

1. **无用户系统**: 单用户使用，无需认证
2. **对话历史前端存储**: 存储在浏览器 localStorage 中
3. **文档向量化存储**: 使用 ChromaDB 存储文档向量和元数据
4. **文件系统存储**: 原始 TXT 文件直接存储在 data 目录

### 数据表设计

基于 LlamaIndex 最佳实践，采用简化的单一存储架构：

#### ChromaDB Collection (documents)
- **Collection Name**: documents
- **Purpose**: 存储文档块的向量嵌入和文本内容
- **Schema**: 
  - id: 文档块唯一标识
  - content: 文档块文本内容
  - metadata: 文件信息和元数据
  - embedding: 768维向量（text-embedding-3-small）

#### 文件替换机制

**核心原则**: 文件名唯一性，同名文件完全替换

1. **检测同名文件**: 以文件名作为唯一标识
2. **完全删除旧数据**: 删除 ChromaDB 中所有相关记录和向量
3. **重新处理新文件**: 完整的文本分块、向量化、存储流程

## 🔍 混合检索

应用采用 LlamaIndex 内置的混合检索机制：

1. **BM25 检索**: 关键词匹配检索
2. **向量检索**: 语义相似度检索  
3. **结果融合**: 使用 QueryFusionRetriever 融合结果
4. **重排序**: 基于相似度分数重新排序

## 📝 使用说明

### 添加文档
1. 将 TXT 文件放入 `data/` 目录
2. 点击"加载文档"按钮
3. 等待处理完成

### 文档更新
- 同名文件会完全替换旧文件的所有数据
- 新文件会自动添加到知识库中
- 删除的文件需要手动清理数据库

### 对话技巧
- 提问要具体明确
- 可以询问文档中的具体内容
- 支持多轮对话和上下文理解

## ❓ 常见问题

**Q: 如何添加新文档？**
A: 将 TXT 文件放入 data 目录，然后点击"重新加载文档"按钮。

**Q: 如果上传同名文件会怎样？**
A: 系统会自动删除旧文件的所有相关数据，然后重新处理新文件。

**Q: 支持哪些文档格式？**
A: 目前只支持 TXT 格式，后续可扩展支持 PDF、Word 等。

**Q: 如何修改模型配置？**
A: 编辑 .env 文件中的 OPENAI_MODEL 和 EMBEDDING_MODEL 参数。

**Q: 数据存储在哪里？**
A: 向量数据存储在 `storage/` 目录下的 SQLite 数据库中。

**Q: 如何清空数据库重新开始？**
A: 删除 `storage/` 目录下的所有文件，重启应用即可。

## 🔧 开发和调试

### 开发模式启动
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 查看日志
应用会在控制台输出详细的调试信息，包括：
- 文档加载进度
- 检索过程
- API 请求响应
- 错误信息

### 性能优化
1. 调整 chunk_size 和 chunk_overlap 参数
2. 使用更高效的嵌入模型
3. 定期清理无用的向量数据
4. 监控 storage 目录大小

## 📄 许可证

本项目采用 MIT 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

如有问题，请提交 Issue 或联系开发者。

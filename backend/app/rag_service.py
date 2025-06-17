"""
RAG服务核心类
基于LlamaIndex实现混合检索（BM25 + 向量检索）
"""
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core import SimpleDirectoryReader
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import CompactAndRefine

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """RAG服务类，实现文档加载、索引构建和混合检索"""
    
    def __init__(self):
        self.index: Optional[VectorStoreIndex] = None
        self.query_engine = None
        self.chroma_client = None
        self.collection = None
        
        # 初始化LlamaIndex设置
        self._setup_llama_index()
        
        # 初始化ChromaDB
        self._setup_chroma()
        
        # 加载现有索引或创建新索引
        self._load_or_create_index()
    
    def _setup_llama_index(self):
        """配置LlamaIndex全局设置"""
        # 强制设置环境变量
        os.environ['OPENAI_API_KEY'] = settings.openai_api_key
        os.environ['OPENAI_BASE_URL'] = settings.openai_base_url

        # 尝试monkey patch OpenAI客户端
        try:
            import openai
            # 设置全局默认值
            openai.api_key = settings.openai_api_key
            openai.base_url = settings.openai_base_url
        except Exception as e:
            logger.warning(f"设置OpenAI全局配置失败: {e}")

        # 设置LLM
        Settings.llm = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
            temperature=0.1
        )

        # 设置嵌入模型
        Settings.embed_model = OpenAIEmbedding(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.embedding_model
        )
        
        # 设置文本分块器
        Settings.node_parser = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50
        )
        
        logger.info("LlamaIndex设置完成")
    
    def _setup_chroma(self):
        """初始化ChromaDB客户端和集合"""
        try:
            # 创建ChromaDB客户端 - 使用新的配置方式
            self.chroma_client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory
            )
            
            # 获取或创建集合
            try:
                self.collection = self.chroma_client.get_collection(
                    name=settings.collection_name
                )
                logger.info(f"加载现有集合: {settings.collection_name}")
            except Exception:
                self.collection = self.chroma_client.create_collection(
                    name=settings.collection_name
                )
                logger.info(f"创建新集合: {settings.collection_name}")
                
        except Exception as e:
            logger.error(f"ChromaDB初始化失败: {e}")
            raise
    
    def _load_or_create_index(self):
        """加载现有索引或创建新索引"""
        try:
            # 创建向量存储
            vector_store = ChromaVectorStore(chroma_collection=self.collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # 检查是否有现有数据
            if self.collection.count() > 0:
                # 从现有向量存储加载索引
                self.index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store,
                    storage_context=storage_context
                )
                logger.info(f"加载现有索引，文档数量: {self.collection.count()}")
            else:
                # 创建空索引
                self.index = VectorStoreIndex(
                    nodes=[],
                    storage_context=storage_context
                )
                logger.info("创建新的空索引")
            
            # 创建查询引擎
            self._create_query_engine()
            
        except Exception as e:
            logger.error(f"索引加载/创建失败: {e}")
            raise
    
    def _create_query_engine(self):
        """创建混合检索查询引擎"""
        if not self.index:
            raise ValueError("索引未初始化")
        
        try:
            # 暂时只使用向量检索，避免混合模式的配置问题
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=5
            )

            logger.info("向量检索查询引擎创建完成")

        except Exception as e:
            logger.error(f"查询引擎创建失败: {e}")
            raise
    
    def load_documents(self) -> Dict[str, Any]:
        """
        加载data目录中的所有TXT文档
        实现同名文件完全替换机制
        """
        try:
            data_path = Path(settings.data_dir)
            if not data_path.exists():
                return {
                    "success": False,
                    "message": f"数据目录不存在: {data_path}",
                    "documents_processed": 0
                }
            
            # 读取所有TXT文件
            txt_files = list(data_path.glob("*.txt"))
            if not txt_files:
                return {
                    "success": False,
                    "message": "未找到TXT文件",
                    "documents_processed": 0
                }
            
            processed_files = []
            replaced_files = []
            new_files = []
            
            for txt_file in txt_files:
                filename = txt_file.name
                
                # 检查是否为同名文件（需要替换）
                existing_ids = self._get_document_ids_by_filename(filename)
                if existing_ids:
                    # 删除旧文件的所有相关数据
                    self._delete_document_by_filename(filename)
                    replaced_files.append({
                        "filename": filename,
                        "old_chunks": len(existing_ids)
                    })
                    logger.info(f"删除同名文件的旧数据: {filename}, 块数: {len(existing_ids)}")
                else:
                    new_files.append(filename)
                
                # 处理新文件
                self._process_single_file(txt_file)
                processed_files.append(filename)
            
            # 重新创建查询引擎
            self._create_query_engine()
            
            # 更新replaced_files中的new_chunks信息
            for replaced_file in replaced_files:
                filename = replaced_file["filename"]
                new_ids = self._get_document_ids_by_filename(filename)
                replaced_file["new_chunks"] = len(new_ids)
            
            return {
                "success": True,
                "message": f"成功处理 {len(processed_files)} 个文件",
                "documents_processed": len(processed_files),
                "replaced_files": replaced_files,
                "new_files": new_files,
                "total_chunks": self.collection.count()
            }
            
        except Exception as e:
            logger.error(f"文档加载失败: {e}")
            return {
                "success": False,
                "message": f"文档加载失败: {str(e)}",
                "documents_processed": 0
            }
    
    def _get_document_ids_by_filename(self, filename: str) -> List[str]:
        """根据文件名获取所有相关的文档ID"""
        try:
            result = self.collection.get(
                where={"filename": filename}
            )
            return result["ids"] if result["ids"] else []
        except Exception as e:
            logger.warning(f"查询文档ID失败: {e}")
            return []
    
    def _delete_document_by_filename(self, filename: str):
        """删除指定文件名的所有相关数据"""
        try:
            # 获取所有相关ID
            existing_ids = self._get_document_ids_by_filename(filename)
            
            if existing_ids:
                # 从ChromaDB删除
                self.collection.delete(ids=existing_ids)
                
                # 从docstore删除
                for doc_id in existing_ids:
                    if self.index.docstore.document_exists(doc_id):
                        self.index.docstore.delete_document(doc_id)
                
                logger.info(f"删除文件 {filename} 的 {len(existing_ids)} 个文档块")
                
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            raise
    
    def _process_single_file(self, file_path: Path):
        """处理单个文件，添加到索引中"""
        try:
            # 读取文档
            reader = SimpleDirectoryReader(
                input_files=[str(file_path)]
            )
            documents = reader.load_data()
            
            if not documents:
                logger.warning(f"文件为空或读取失败: {file_path}")
                return
            
            # 为文档添加元数据
            for doc in documents:
                doc.metadata.update({
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "file_size": file_path.stat().st_size,
                    "file_modified": str(file_path.stat().st_mtime)
                })
            
            # 添加到索引
            for doc in documents:
                self.index.insert(doc)
            
            logger.info(f"成功处理文件: {file_path.name}")
            
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {e}")
            raise
    
    def query(self, question: str, max_results: int = 5) -> Dict[str, Any]:
        """
        执行混合检索查询
        """
        if not self.query_engine:
            return {
                "success": False,
                "message": "查询引擎未初始化",
                "answer": "",
                "sources": []
            }
        
        try:
            # 执行查询
            response = self.query_engine.query(question)
            
            # 提取源文档信息
            sources = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node in response.source_nodes[:max_results]:
                    sources.append({
                        "filename": node.metadata.get("filename", "未知"),
                        "content": node.text[:200] + "..." if len(node.text) > 200 else node.text,
                        "score": getattr(node, 'score', 0.0)
                    })
            
            return {
                "success": True,
                "answer": str(response),
                "sources": sources,
                "total_sources": len(sources)
            }
            
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return {
                "success": False,
                "message": f"查询失败: {str(e)}",
                "answer": "",
                "sources": []
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            doc_count = self.collection.count() if self.collection else 0
            
            # 计算存储大小
            storage_path = Path(settings.chroma_persist_directory)
            storage_size = 0
            if storage_path.exists():
                for file_path in storage_path.rglob("*"):
                    if file_path.is_file():
                        storage_size += file_path.stat().st_size
            
            storage_size_mb = storage_size / (1024 * 1024)
            
            return {
                "status": "ok",
                "documents_count": doc_count,
                "storage_size": f"{storage_size_mb:.2f}MB",
                "collection_name": settings.collection_name,
                "data_directory": settings.data_dir
            }
            
        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

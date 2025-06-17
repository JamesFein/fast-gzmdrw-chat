"""
FastAPI主应用
提供RAG聊天服务的API接口
"""
import logging
import time
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.config import settings
from backend.app.rag_service import RAGService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="RAG聊天应用",
    description="基于LlamaIndex的极简RAG聊天应用",
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

# 全局RAG服务实例
rag_service: RAGService = None


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化RAG服务"""
    global rag_service
    try:
        logger.info("正在初始化RAG服务...")
        rag_service = RAGService()
        logger.info("RAG服务初始化完成")
    except Exception as e:
        logger.error(f"RAG服务初始化失败: {e}")
        raise


# 请求模型
class QueryRequest(BaseModel):
    query: str = Field(..., description="用户问题", min_length=1, max_length=1000)
    max_results: int = Field(5, description="最大返回结果数", ge=1, le=20)
    similarity_threshold: float = Field(0.7, description="相似度阈值", ge=0.0, le=1.0)


class QueryResponse(BaseModel):
    answer: str = Field(..., description="AI生成的回答")
    sources: list = Field(..., description="相关文档片段")
    processing_time: float = Field(..., description="处理时间（秒）")
    total_sources: int = Field(..., description="源文档数量")


class LoadDocumentsResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="处理消息")
    documents_processed: int = Field(..., description="处理的文档数量")
    replaced_files: list = Field(default=[], description="被替换的文件列表")
    new_files: list = Field(default=[], description="新增的文件列表")
    processing_time: float = Field(..., description="处理时间（秒）")


class StatusResponse(BaseModel):
    status: str = Field(..., description="系统状态")
    documents_count: int = Field(..., description="文档数量")
    storage_size: str = Field(..., description="存储大小")
    collection_name: str = Field(..., description="集合名称")
    data_directory: str = Field(..., description="数据目录")


# 静态文件服务
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回聊天页面"""
    try:
        with open("frontend/templates/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>页面未找到</h1><p>请确保前端文件存在</p>",
            status_code=404
        )


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """获取系统状态"""
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG服务未初始化")
        
        status = rag_service.get_status()
        return StatusResponse(**status)
        
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@app.post("/api/load-documents", response_model=LoadDocumentsResponse)
async def load_documents():
    """重新加载文档"""
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG服务未初始化")
        
        start_time = time.time()
        result = rag_service.load_documents()
        processing_time = time.time() - start_time
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        response_data = {
            **result,
            "processing_time": processing_time
        }
        
        return LoadDocumentsResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加载文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"加载文档失败: {str(e)}")


@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """查询问答"""
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG服务未初始化")
        
        start_time = time.time()
        result = rag_service.query(
            question=request.query,
            max_results=request.max_results
        )
        processing_time = time.time() - start_time
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        response_data = {
            "answer": result["answer"],
            "sources": result["sources"],
            "processing_time": processing_time,
            "total_sources": result["total_sources"]
        }
        
        return QueryResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return {
        "error": True,
        "message": "服务器内部错误",
        "detail": str(exc) if settings.app_host == "127.0.0.1" else "请联系管理员"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_level="info"
    )

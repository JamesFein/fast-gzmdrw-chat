"""
应用配置设置
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # OpenAI API配置
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
    
    # ChromaDB配置
    chroma_db_impl: str = "duckdb+parquet"
    chroma_persist_directory: str = "./storage"
    
    # CORS配置
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.data_dir, exist_ok=True)
os.makedirs(settings.storage_dir, exist_ok=True)

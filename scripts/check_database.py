#!/usr/bin/env python3
"""
数据库查询脚本
用于验证文档管理功能的正确性，直接查询ChromaDB和SQLite数据库
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import chromadb
from backend.config import settings


class DatabaseChecker:
    """数据库检查器"""
    
    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.sqlite_path = None
        self.setup_connections()
    
    def setup_connections(self):
        """建立数据库连接"""
        try:
            # 连接ChromaDB
            self.chroma_client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory
            )
            
            # 获取集合
            try:
                self.collection = self.chroma_client.get_collection(
                    name=settings.collection_name
                )
                print(f"✓ 成功连接到ChromaDB集合: {settings.collection_name}")
            except Exception as e:
                print(f"✗ ChromaDB集合不存在: {e}")
                return
            
            # 查找SQLite数据库文件
            storage_path = Path(settings.chroma_persist_directory)
            sqlite_files = list(storage_path.glob("*.sqlite3"))
            if sqlite_files:
                self.sqlite_path = sqlite_files[0]
                print(f"✓ 找到SQLite数据库: {self.sqlite_path}")
            else:
                print("✗ 未找到SQLite数据库文件")
                
        except Exception as e:
            print(f"✗ 数据库连接失败: {e}")
    
    def check_chroma_data(self) -> Dict[str, Any]:
        """检查ChromaDB数据"""
        if not self.collection:
            return {"error": "ChromaDB集合未连接"}
        
        try:
            # 获取所有数据
            result = self.collection.get(include=["metadatas", "documents"])
            
            total_docs = len(result["ids"])
            
            # 按文件名分组统计
            file_stats = {}
            for i, doc_id in enumerate(result["ids"]):
                metadata = result["metadatas"][i] if result["metadatas"] else {}
                filename = metadata.get("filename", "未知文件")
                
                if filename not in file_stats:
                    file_stats[filename] = {
                        "filename": filename,
                        "chunks": [],
                        "total_chunks": 0,
                        "file_size": metadata.get("file_size", 0),
                        "file_path": metadata.get("file_path", ""),
                        "file_modified": metadata.get("file_modified", "")
                    }
                
                file_stats[filename]["chunks"].append({
                    "id": doc_id,
                    "text_length": len(result["documents"][i]) if result["documents"] and result["documents"][i] else 0
                })
                file_stats[filename]["total_chunks"] += 1
            
            return {
                "total_documents": total_docs,
                "unique_files": len(file_stats),
                "files": file_stats
            }
            
        except Exception as e:
            return {"error": f"查询ChromaDB失败: {e}"}
    
    def check_sqlite_data(self) -> Dict[str, Any]:
        """检查SQLite数据"""
        if not self.sqlite_path or not self.sqlite_path.exists():
            return {"error": "SQLite数据库文件不存在"}
        
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            table_info = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                # 获取表结构
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                table_info[table] = {
                    "row_count": count,
                    "columns": columns
                }
            
            conn.close()
            
            return {
                "database_path": str(self.sqlite_path),
                "tables": table_info
            }
            
        except Exception as e:
            return {"error": f"查询SQLite失败: {e}"}
    
    def check_file_consistency(self) -> Dict[str, Any]:
        """检查文件一致性"""
        chroma_data = self.check_chroma_data()
        
        if "error" in chroma_data:
            return {"error": "无法检查一致性，ChromaDB查询失败"}
        
        # 检查data目录中的文件
        data_path = Path(settings.data_dir)
        if not data_path.exists():
            return {"error": f"数据目录不存在: {data_path}"}
        
        txt_files = list(data_path.glob("*.txt"))
        disk_files = {f.name for f in txt_files}
        db_files = set(chroma_data["files"].keys())
        
        # 找出不一致的文件
        only_on_disk = disk_files - db_files
        only_in_db = db_files - disk_files
        common_files = disk_files & db_files
        
        return {
            "disk_files": list(disk_files),
            "database_files": list(db_files),
            "only_on_disk": list(only_on_disk),
            "only_in_database": list(only_in_db),
            "common_files": list(common_files),
            "consistency_ok": len(only_on_disk) == 0 and len(only_in_db) == 0
        }
    
    def print_summary(self):
        """打印数据库摘要"""
        print("\n" + "="*60)
        print("数据库状态检查报告")
        print("="*60)
        
        # ChromaDB数据
        print("\n📊 ChromaDB数据:")
        chroma_data = self.check_chroma_data()
        if "error" in chroma_data:
            print(f"  ✗ {chroma_data['error']}")
        else:
            print(f"  ✓ 总文档块数: {chroma_data['total_documents']}")
            print(f"  ✓ 唯一文件数: {chroma_data['unique_files']}")
            
            if chroma_data['files']:
                print("\n  📁 文件详情:")
                for filename, info in chroma_data['files'].items():
                    print(f"    • {filename}: {info['total_chunks']} 块")
        
        # SQLite数据
        print("\n🗄️ SQLite数据:")
        sqlite_data = self.check_sqlite_data()
        if "error" in sqlite_data:
            print(f"  ✗ {sqlite_data['error']}")
        else:
            print(f"  ✓ 数据库路径: {sqlite_data['database_path']}")
            print(f"  ✓ 表数量: {len(sqlite_data['tables'])}")
            
            for table, info in sqlite_data['tables'].items():
                print(f"    • {table}: {info['row_count']} 行")
        
        # 文件一致性
        print("\n🔍 文件一致性:")
        consistency = self.check_file_consistency()
        if "error" in consistency:
            print(f"  ✗ {consistency['error']}")
        else:
            if consistency['consistency_ok']:
                print("  ✓ 磁盘文件与数据库文件完全一致")
            else:
                print("  ⚠️ 发现不一致:")
                if consistency['only_on_disk']:
                    print(f"    • 仅在磁盘: {consistency['only_on_disk']}")
                if consistency['only_in_database']:
                    print(f"    • 仅在数据库: {consistency['only_in_database']}")
            
            print(f"  📁 磁盘文件数: {len(consistency['disk_files'])}")
            print(f"  🗃️ 数据库文件数: {len(consistency['database_files'])}")
        
        print("\n" + "="*60)
    
    def export_detailed_report(self, output_file: str = "database_report.json"):
        """导出详细报告"""
        report = {
            "timestamp": str(Path().cwd()),
            "chroma_data": self.check_chroma_data(),
            "sqlite_data": self.check_sqlite_data(),
            "consistency": self.check_file_consistency()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已导出到: {output_file}")


def main():
    """主函数"""
    print("🔍 开始检查数据库状态...")
    
    checker = DatabaseChecker()
    checker.print_summary()
    
    # 询问是否导出详细报告
    try:
        export = input("\n是否导出详细报告到JSON文件? (y/N): ").strip().lower()
        if export in ['y', 'yes']:
            checker.export_detailed_report()
    except KeyboardInterrupt:
        print("\n\n👋 检查完成")


if __name__ == "__main__":
    main()

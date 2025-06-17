#!/usr/bin/env python3
"""
文档管理功能测试脚本
测试文档上传、同名文件替换、删除等功能
"""

import os
import sys
import tempfile
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.app.rag_service import RAGService
from scripts.check_database import DatabaseChecker


class DocumentManagementTester:
    """文档管理功能测试器"""
    
    def __init__(self):
        self.rag_service = None
        self.db_checker = None
        self.test_files = {}
        
    def setup(self):
        """初始化测试环境"""
        print("🔧 初始化测试环境...")
        
        try:
            self.rag_service = RAGService()
            self.db_checker = DatabaseChecker()
            print("✓ RAG服务初始化成功")
            
            # 创建测试文件
            self.create_test_files()
            print("✓ 测试文件创建成功")
            
        except Exception as e:
            print(f"✗ 初始化失败: {e}")
            return False
        
        return True
    
    def create_test_files(self):
        """创建测试文件"""
        self.test_files = {
            "test_doc1.txt": "这是第一个测试文档。\n包含一些测试内容用于验证文档管理功能。\n文档管理系统应该能够正确处理这个文件。",
            "test_doc2.txt": "这是第二个测试文档。\n用于测试多文档处理能力。\n系统应该能够同时管理多个文档。",
            "test_doc1_updated.txt": "这是更新后的第一个测试文档。\n内容已经被修改，用于测试同名文件替换功能。\n系统应该完全删除旧数据并重新处理新内容。"
        }
    
    def test_upload_documents(self):
        """测试文档上传功能"""
        print("\n📤 测试文档上传功能...")
        
        # 上传第一个文档
        result1 = self.rag_service.upload_document(
            self.test_files["test_doc1.txt"], 
            "test_doc1.txt"
        )
        
        if result1["success"]:
            print(f"✓ 上传 test_doc1.txt 成功: {result1['new_chunks']} 块")
        else:
            print(f"✗ 上传 test_doc1.txt 失败: {result1['message']}")
            return False
        
        # 上传第二个文档
        result2 = self.rag_service.upload_document(
            self.test_files["test_doc2.txt"], 
            "test_doc2.txt"
        )
        
        if result2["success"]:
            print(f"✓ 上传 test_doc2.txt 成功: {result2['new_chunks']} 块")
        else:
            print(f"✗ 上传 test_doc2.txt 失败: {result2['message']}")
            return False
        
        return True
    
    def test_list_documents(self):
        """测试文档列表功能"""
        print("\n📋 测试文档列表功能...")
        
        result = self.rag_service.get_documents_list()
        
        if result["success"]:
            print(f"✓ 获取文档列表成功: {len(result['documents'])} 个文档")
            for doc in result["documents"]:
                print(f"  • {doc['filename']}: {doc['chunks_count']} 块")
            return True
        else:
            print(f"✗ 获取文档列表失败: {result['message']}")
            return False
    
    def test_replace_document(self):
        """测试同名文件替换功能"""
        print("\n🔄 测试同名文件替换功能...")
        
        # 获取替换前的状态
        before_list = self.rag_service.get_documents_list()
        before_doc1 = None
        for doc in before_list["documents"]:
            if doc["filename"] == "test_doc1.txt":
                before_doc1 = doc
                break
        
        if not before_doc1:
            print("✗ 找不到 test_doc1.txt，无法测试替换功能")
            return False
        
        print(f"  替换前: test_doc1.txt 有 {before_doc1['chunks_count']} 块")
        
        # 上传同名文件（内容不同）
        result = self.rag_service.upload_document(
            self.test_files["test_doc1_updated.txt"], 
            "test_doc1.txt"
        )
        
        if not result["success"]:
            print(f"✗ 替换文档失败: {result['message']}")
            return False
        
        print(f"  替换结果: 旧 {result['old_chunks']} 块 → 新 {result['new_chunks']} 块")
        
        # 验证替换后的状态
        after_list = self.rag_service.get_documents_list()
        after_doc1 = None
        for doc in after_list["documents"]:
            if doc["filename"] == "test_doc1.txt":
                after_doc1 = doc
                break
        
        if not after_doc1:
            print("✗ 替换后找不到 test_doc1.txt")
            return False
        
        print(f"  替换后: test_doc1.txt 有 {after_doc1['chunks_count']} 块")
        
        # 验证文档数量没有增加（只是替换，不是新增）
        if len(before_list["documents"]) == len(after_list["documents"]):
            print("✓ 文档数量保持不变，确认是替换而非新增")
        else:
            print("⚠️ 文档数量发生变化，可能存在问题")
        
        return True
    
    def test_delete_document(self):
        """测试文档删除功能"""
        print("\n🗑️ 测试文档删除功能...")
        
        # 删除 test_doc2.txt
        result = self.rag_service.delete_document("test_doc2.txt")
        
        if result["success"]:
            print(f"✓ 删除 test_doc2.txt 成功: 删除了 {result['deleted_chunks']} 块")
        else:
            print(f"✗ 删除 test_doc2.txt 失败: {result['message']}")
            return False
        
        # 验证删除后的状态
        after_list = self.rag_service.get_documents_list()
        doc2_exists = any(doc["filename"] == "test_doc2.txt" for doc in after_list["documents"])
        
        if not doc2_exists:
            print("✓ 确认 test_doc2.txt 已从数据库中删除")
        else:
            print("✗ test_doc2.txt 仍然存在于数据库中")
            return False
        
        return True
    
    def test_query_functionality(self):
        """测试查询功能"""
        print("\n🔍 测试查询功能...")
        
        # 查询测试
        result = self.rag_service.query("测试文档的内容是什么？")
        
        if result["success"]:
            print(f"✓ 查询成功，找到 {result['total_sources']} 个相关源")
            print(f"  回答: {result['answer'][:100]}...")
        else:
            print(f"✗ 查询失败: {result['message']}")
            return False
        
        return True
    
    def check_database_consistency(self):
        """检查数据库一致性"""
        print("\n🔍 检查数据库一致性...")
        
        consistency = self.db_checker.check_file_consistency()
        chroma_data = self.db_checker.check_chroma_data()
        
        if "error" in consistency:
            print(f"✗ 一致性检查失败: {consistency['error']}")
            return False
        
        if "error" in chroma_data:
            print(f"✗ ChromaDB检查失败: {chroma_data['error']}")
            return False
        
        print(f"✓ ChromaDB中有 {chroma_data['total_documents']} 个文档块")
        print(f"✓ 涉及 {chroma_data['unique_files']} 个唯一文件")
        
        return True
    
    def cleanup(self):
        """清理测试数据"""
        print("\n🧹 清理测试数据...")
        
        # 删除所有测试文档
        docs_list = self.rag_service.get_documents_list()
        if docs_list["success"]:
            for doc in docs_list["documents"]:
                if doc["filename"].startswith("test_"):
                    result = self.rag_service.delete_document(doc["filename"])
                    if result["success"]:
                        print(f"✓ 删除测试文档: {doc['filename']}")
                    else:
                        print(f"✗ 删除失败: {doc['filename']}")
        
        print("✓ 测试数据清理完成")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始文档管理功能测试")
        print("="*50)
        
        if not self.setup():
            return False
        
        tests = [
            ("文档上传", self.test_upload_documents),
            ("文档列表", self.test_list_documents),
            ("同名文件替换", self.test_replace_document),
            ("文档删除", self.test_delete_document),
            ("查询功能", self.test_query_functionality),
            ("数据库一致性", self.check_database_consistency)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} 测试通过")
                else:
                    print(f"❌ {test_name} 测试失败")
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
        
        print("\n" + "="*50)
        print(f"🏁 测试完成: {passed}/{total} 通过")
        
        # 询问是否清理测试数据
        try:
            cleanup = input("\n是否清理测试数据? (Y/n): ").strip().lower()
            if cleanup != 'n':
                self.cleanup()
        except KeyboardInterrupt:
            print("\n跳过清理")
        
        return passed == total


def main():
    """主函数"""
    tester = DocumentManagementTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 所有测试通过！文档管理功能正常工作。")
    else:
        print("\n⚠️ 部分测试失败，请检查系统配置。")


if __name__ == "__main__":
    main()

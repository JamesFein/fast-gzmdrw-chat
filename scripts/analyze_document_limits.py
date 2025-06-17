#!/usr/bin/env python3
"""
文档大小限制分析脚本
分析当前项目对文档大小的支持情况
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.config import settings
from backend.app.rag_service import RAGService


class DocumentLimitAnalyzer:
    """文档大小限制分析器"""
    
    def __init__(self):
        self.rag_service = None
        
    def setup(self):
        """初始化"""
        try:
            self.rag_service = RAGService()
            print("✓ RAG服务初始化成功")
            return True
        except Exception as e:
            print(f"✗ RAG服务初始化失败: {e}")
            return False
    
    def analyze_current_config(self):
        """分析当前配置"""
        print("\n📊 当前配置分析:")
        print("="*50)
        
        # LlamaIndex配置
        print("🔧 LlamaIndex配置:")
        print(f"  • 文本分块大小: 512 tokens")
        print(f"  • 块重叠大小: 50 tokens")
        print(f"  • 嵌入模型: {settings.embedding_model}")
        print(f"  • LLM模型: {settings.openai_model}")
        
        # FastAPI配置
        print("\n🌐 FastAPI配置:")
        print("  • 文件上传大小限制: 无明确限制（使用默认值）")
        print("  • 默认multipart限制: ~1MB per part")
        print("  • 内存文件大小限制: 1MB（超过后写入临时文件）")
        
        # ChromaDB配置
        print("\n🗄️ ChromaDB配置:")
        print("  • 存储类型: SQLite (本地持久化)")
        print("  • 内存限制: 无明确限制")
        print("  • 文件句柄限制: 系统默认")
        
        # 估算理论限制
        print("\n📈 理论限制估算:")
        self.estimate_limits()
    
    def estimate_limits(self):
        """估算理论限制"""
        # 基于当前配置估算
        chunk_size_tokens = 512
        chunk_overlap_tokens = 50
        effective_chunk_size = chunk_size_tokens - chunk_overlap_tokens
        
        # 估算token到字符的比例（中文约1:1.5，英文约1:4）
        chinese_chars_per_token = 1.5
        english_chars_per_token = 4
        
        print(f"  • 每个文档块: ~{chunk_size_tokens} tokens")
        print(f"  • 中文文档块: ~{int(chunk_size_tokens * chinese_chars_per_token)} 字符")
        print(f"  • 英文文档块: ~{int(chunk_size_tokens * english_chars_per_token)} 字符")
        
        # 估算不同大小文档的块数
        doc_sizes = [
            ("小文档", 1024, "1KB"),
            ("中文档", 10240, "10KB"), 
            ("大文档", 102400, "100KB"),
            ("超大文档", 1048576, "1MB"),
            ("巨型文档", 10485760, "10MB")
        ]
        
        print(f"\n  📄 文档大小 vs 文档块数估算（中文）:")
        for name, size_bytes, size_str in doc_sizes:
            # 假设UTF-8编码，中文字符约3字节
            chars = size_bytes // 3
            chunks = max(1, chars // int(chunk_size_tokens * chinese_chars_per_token))
            print(f"    • {name} ({size_str}): ~{chunks} 个文档块")
    
    def test_document_sizes(self):
        """测试不同大小的文档"""
        print("\n🧪 文档大小测试:")
        print("="*50)
        
        test_cases = [
            ("小文档", self.generate_test_content(500)),
            ("中文档", self.generate_test_content(5000)),
            ("大文档", self.generate_test_content(50000)),
            ("超大文档", self.generate_test_content(500000))
        ]
        
        results = []
        
        for name, content in test_cases:
            print(f"\n📝 测试 {name} ({len(content)} 字符)...")
            
            try:
                start_time = time.time()
                
                # 上传文档
                result = self.rag_service.upload_document(content, f"test_{name}.txt")
                
                processing_time = time.time() - start_time
                
                if result["success"]:
                    print(f"  ✓ 上传成功")
                    print(f"  • 处理时间: {processing_time:.2f}秒")
                    print(f"  • 生成块数: {result['new_chunks']}")
                    print(f"  • 平均每块字符数: {len(content) // result['new_chunks']}")
                    
                    results.append({
                        "name": name,
                        "size": len(content),
                        "chunks": result['new_chunks'],
                        "time": processing_time,
                        "success": True
                    })
                    
                    # 清理测试文档
                    self.rag_service.delete_document(f"test_{name}.txt")
                    
                else:
                    print(f"  ✗ 上传失败: {result['message']}")
                    results.append({
                        "name": name,
                        "size": len(content),
                        "success": False,
                        "error": result['message']
                    })
                    
            except Exception as e:
                print(f"  ✗ 测试异常: {e}")
                results.append({
                    "name": name,
                    "size": len(content),
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def generate_test_content(self, target_chars: int) -> str:
        """生成测试内容"""
        base_text = """这是一个测试文档，用于验证系统对不同大小文档的处理能力。
文档包含中文内容，用于测试中文文本的分块和向量化处理。
系统需要能够正确处理各种大小的文档，从小型文档到大型文档。
文档管理系统应该能够高效地处理文本分块、向量嵌入和存储。
"""
        
        # 重复基础文本直到达到目标长度
        content = ""
        while len(content) < target_chars:
            content += base_text
            if len(content) < target_chars:
                content += f"\n\n第{len(content)//len(base_text) + 1}段重复内容:\n"
        
        return content[:target_chars]
    
    def analyze_performance(self, results):
        """分析性能结果"""
        print("\n📊 性能分析:")
        print("="*50)
        
        successful_results = [r for r in results if r["success"]]
        
        if not successful_results:
            print("  ⚠️ 没有成功的测试结果")
            return
        
        print("  📈 成功处理的文档:")
        for result in successful_results:
            chars_per_second = result["size"] / result["time"]
            chunks_per_second = result["chunks"] / result["time"]
            
            print(f"    • {result['name']}: {result['size']:,} 字符")
            print(f"      - 处理时间: {result['time']:.2f}秒")
            print(f"      - 处理速度: {chars_per_second:,.0f} 字符/秒")
            print(f"      - 块生成速度: {chunks_per_second:.1f} 块/秒")
            print(f"      - 文档块数: {result['chunks']}")
        
        # 失败的测试
        failed_results = [r for r in results if not r["success"]]
        if failed_results:
            print("\n  ❌ 失败的测试:")
            for result in failed_results:
                print(f"    • {result['name']}: {result['size']:,} 字符")
                print(f"      - 错误: {result['error']}")
    
    def provide_recommendations(self):
        """提供优化建议"""
        print("\n💡 优化建议:")
        print("="*50)
        
        print("  🔧 配置优化:")
        print("    • 可以调整chunk_size来平衡精度和性能")
        print("    • 当前512 tokens适合大多数场景")
        print("    • 对于超大文档，可以考虑增加chunk_size到1024")
        
        print("\n  📈 性能优化:")
        print("    • 对于大文档，考虑异步处理")
        print("    • 可以实现文档预处理和批量上传")
        print("    • 考虑添加进度显示")
        
        print("\n  🛡️ 限制建议:")
        print("    • 建议设置文件上传大小限制（如10MB）")
        print("    • 对超大文档提供分段上传功能")
        print("    • 添加文档大小预警机制")
        
        print("\n  🔍 监控建议:")
        print("    • 监控处理时间和内存使用")
        print("    • 记录文档大小和块数统计")
        print("    • 设置性能告警阈值")
    
    def run_analysis(self):
        """运行完整分析"""
        print("🔍 文档大小限制分析")
        print("="*60)
        
        if not self.setup():
            return False
        
        # 分析当前配置
        self.analyze_current_config()
        
        # 测试不同大小的文档
        results = self.test_document_sizes()
        
        # 分析性能
        self.analyze_performance(results)
        
        # 提供建议
        self.provide_recommendations()
        
        print("\n" + "="*60)
        print("🏁 分析完成")
        
        return True


def main():
    """主函数"""
    analyzer = DocumentLimitAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()

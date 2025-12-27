import sys
import os
import chromadb
from chromadb.utils import embedding_functions
from typing import Dict, Any

# 添加当前目录到模块搜索路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from base import BaseTool

class LawRetriever(BaseTool):
    name = "LawRetriever"
    description = "根据语义关键词从ChromaDB向量数据库中检索相关法律法规"

    def __init__(self, db_path="./chroma_db"):
        super().__init__()
        # 1. 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(path=db_path)
        
        # 2. 设置 Embedding 函数（默认使用 all-MiniLM-L6-v2）
        # 如果需要更好的中文支持，可更换为 HuggingFaceBgeEmbeddings
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # 3. 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name="china_laws",
            embedding_function=self.emb_fn
        )
        
        # 4. 首次运行初始化数据（将你原来的 Mock 数据写入数据库）
        self._init_database()

    def _init_database(self):
        """将初始法规条文存入向量数据库，确保语义搜索可用"""
        if self.collection.count() == 0:
            laws_to_add = [
                {
                    "id": "law-001",
                    "content": "当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金。约定的违约金过分高于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以适当减少。",
                    "metadata": {"title": "《民法典》第585条", "scene": "违约金"}
                },
                {
                    "id": "law-002",
                    "content": "向人民法院请求保护民事权利的诉讼时效期间为三年。法律另有规定的，依照其规定。",
                    "metadata": {"title": "《民法典》第188条", "scene": "诉讼时效"}
                }
            ]
            
            self.collection.add(
                ids=[l["id"] for l in laws_to_add],
                documents=[l["content"] for l in laws_to_add],
                metadatas=[l["metadata"] for l in laws_to_add]
            )

    def run(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # 提取关键词或合同条款描述
        query_text = input_data.get("keywords", "")
        if not query_text:
            return self._format_error("未提供检索关键词")

        try:
            # 5. 执行向量检索：寻找语义最相似的 2 条法律
            results = self.collection.query(
                query_texts=[query_text],
                n_results=2
            )
            
            # 6. 格式化结果
            laws = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i in range(len(results['documents'][0])):
                    # 只有当距离足够近（相关度高）时才返回，否则可能误导
                    # distance 越小越相似，通常 < 1.0 比较可靠
                    laws.append({
                        "id": results['ids'][0][i],
                        "title": results['metadatas'][0][i].get('title', '未知条文'),
                        "content": results['documents'][0][i],
                        "applicable_scene": results['metadatas'][0][i].get('scene', '通用'),
                        "score": round(1 - results['distances'][0][i], 4) # 相似度分数
                    })
            
            if not laws:
                return self._format_success({"laws": [], "total": 0})

            return self._format_success({
                "laws": laws,
                "total": len(laws)
            })
            
        except Exception as e:
            return self._format_error(f"检索过程发生异常: {str(e)}")
    
    def _format_success(self, data):
        return {
            "status": "success",
            "data": data
        }
    
    def _format_error(self, message, status_code="500"):
        return {
            "status": "error",
            "message": message,
            "status_code": status_code
        }

if __name__ == "__main__":
    # 测试向量检索
    tool = LawRetriever()
    
    # 哪怕关键词不完全一致（如“罚金” vs “违约金”），向量库也能搜到
    print("--- 语义检索测试 ---")
    result = tool.run({"keywords": "合同里的罚金太高了怎么办"}, {})
    print(result)
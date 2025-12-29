"""
法规检索工具（MVP Mock 版）
使用内置规则条目做简单关键词匹配，避免依赖向量库，便于开箱演示。
"""
from typing import Dict, Any, List
from base import BaseTool


class LawRetriever(BaseTool):
    name = "LawRetriever"
    description = "根据关键词检索内置法规条文（MVP Mock，无需向量库）"

    def __init__(self):
        super().__init__()
        # 内置法规数据（可根据需求扩充）
        self.laws: List[Dict[str, Any]] = [
            {
                "id": "law-001",
                "title": "《民法典》第585条",
                "content": "当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金。约定的违约金过分高于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以适当减少。",
                "applicable_scene": "违约金"
            },
            {
                "id": "law-002",
                "title": "《民法典》第188条",
                "content": "向人民法院请求保护民事权利的诉讼时效期间为三年。法律另有规定的，依照其规定。",
                "applicable_scene": "诉讼时效"
            },
            {
                "id": "law-003",
                "title": "《仲裁法》第5条",
                "content": "当事人达成仲裁协议，一方向人民法院起诉的，人民法院不予受理，但仲裁协议无效的除外。",
                "applicable_scene": "争议解决"
            }
        ]

    def run(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        query_text = input_data.get("keywords", "") or ""
        if not query_text.strip():
            return self._format_error("未提供检索关键词")

        # 简单关键词匹配：按包含关系打分
        query_lower = query_text.lower()
        results = []
        for law in self.laws:
            title = law.get("title", "")
            content = law.get("content", "")
            scene = law.get("applicable_scene", "")
            text_blob = f"{title} {content} {scene}".lower()
            if any(k in text_blob for k in self._extract_keywords(query_lower)):
                results.append({**law, "score": 0.9})

        return self._format_success({
            "laws": results,
            "total": len(results)
        })

    def _extract_keywords(self, query: str) -> List[str]:
        # 粗略分词：按空格/逗号/顿号拆分，长度>1保留
        seps = [",", "，", "、", " ", ";", "；"]
        tmp = [query]
        for sep in seps:
            tmp = sum([s.split(sep) for s in tmp], [])
        return [t.strip() for t in tmp if len(t.strip()) > 1]

    def _format_success(self, data):
        return {"status": "success", "data": data}

    def _format_error(self, message, status_code="500"):
        return {"status": "error", "message": message, "status_code": status_code}


if __name__ == "__main__":
    tool = LawRetriever()
    print(tool.run({"keywords": "违约金 上限"}, {}))
"""
简单的 LLM 连通性测试脚本

用法：
    python backend/scripts/test_llm.py

依赖：
    - 已在 backend/.env 配置 DASHSCOPE_API_KEY（或 MODEL_STUDIO_KEY）
    - 可选：DASHSCOPE_REGION (beijing/singapore)，DASHSCOPE_MODEL
"""
import os
import sys
from pathlib import Path

from backend.utils.llm_service import LLMService


def main():
    # 确保可以加载 backend/.env
    backend_dir = Path(__file__).resolve().parents[1]
    env_file = backend_dir / ".env"
    if not env_file.exists():
        print("⚠️ 未找到 backend/.env，优先在 backend/.env 配置 DASHSCOPE_API_KEY")

    region = os.getenv("DASHSCOPE_REGION", "beijing")
    model = os.getenv("DASHSCOPE_MODEL", "qwen-long-latest")

    print("=" * 60)
    print("LLM 连通性测试")
    print("=" * 60)
    print(f"Region: {region}")
    print(f"Model : {model}")
    print("-" * 60)

    llm = LLMService(region=region)
    if not llm.client:
        print("❌ LLM 客户端未初始化，请检查 API Key 配置")
        sys.exit(1)

    try:
        resp = llm.chat("你好，这是一条连通性测试。")
        print("✅ 调用成功，返回：")
        print(resp["response"])
    except Exception as e:
        print(f"❌ 调用失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


"""
LLM 模块使用示例
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import asyncio
from backend.utils.llm import get_llm_client, ChatMessage


async def example_basic():
    """基础使用示例"""
    client = get_llm_client()
    
    # 方式1: 使用 generate 方法（最简单）
    response = await client.generate("你好，请介绍一下你自己")
    print("方式1 - generate:")
    print(f"回复: {response.content}")
    print(f"使用量: {response.usage}")
    print()
    
    # 方式2: 使用 chat_simple 方法（带系统消息）
    response_text = await client.chat_simple(
        user_message="什么是人工智能？",
        system_message="你是一个专业的AI助手，擅长用简洁的语言回答问题。"
    )
    print("方式2 - chat_simple:")
    print(f"回复: {response_text}")
    print()
    
    # 方式3: 使用 chat 方法（完整控制）
    messages = [
        ChatMessage(role="system", content="你是一个专业的合同分析助手。"),
        ChatMessage(role="user", content="请分析一下合同中的关键条款。"),
    ]
    response = await client.chat(messages, temperature=0.5)
    print("方式3 - chat:")
    print(f"回复: {response.content}")
    print(f"模型: {response.model}")
    print(f"完成原因: {response.finish_reason}")
    print()


async def example_multi_turn():
    """多轮对话示例"""
    client = get_llm_client()
    
    messages = [
        ChatMessage(role="system", content="你是一个友好的助手。"),
        ChatMessage(role="user", content="我的名字是张三。"),
    ]
    
    # 第一轮
    response = await client.chat(messages)
    print("用户: 我的名字是张三。")
    print(f"助手: {response.content}")
    print()
    
    # 第二轮（添加助手回复到上下文）
    messages.append(ChatMessage(role="assistant", content=response.content))
    messages.append(ChatMessage(role="user", content="你还记得我的名字吗？"))
    
    response = await client.chat(messages)
    print("用户: 你还记得我的名字吗？")
    print(f"助手: {response.content}")
    print()


async def example_custom_params():
    """自定义参数示例"""
    client = get_llm_client()
    
    # 使用自定义温度参数
    response = await client.generate(
        "写一首关于春天的诗",
        temperature=0.9,  # 更高的温度，更创造性
        max_tokens=500
    )
    print("自定义参数:")
    print(f"回复: {response.content}")
    print()


if __name__ == "__main__":
    print("=== LLM 模块使用示例 ===\n")
    
    try:
        # 运行示例
        asyncio.run(example_basic())
        # asyncio.run(example_multi_turn())
        # asyncio.run(example_custom_params())
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("\n💡 提示:")
        print("  - 对于阿里云：使用 DASHSCOPE_API_KEY 环境变量")
        print("  - 对于 OpenAI：使用 MODEL_STUDIO_KEY 或 OPENAI_API_KEY 环境变量")
        print("  - 请确保在项目根目录创建 .env 文件并配置相应的 API 密钥")
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()


"""
LLM 配置管理模块
从 .env 文件读取配置
"""

import os
from pathlib import Path
from typing import Optional
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 查找项目根目录（包含 .env 文件的目录）
# 从当前文件向上查找，直到找到包含 .env 或项目标识文件的目录
def find_project_root() -> Path:
    """查找项目根目录"""
    current = Path(__file__).resolve()
    # 从当前文件向上查找，最多查找 5 层
    for _ in range(5):
        if (current / ".env").exists() or (current / ".git").exists() or (current / "requirements.txt").exists():
            return current
        parent = current.parent
        if parent == current:  # 已到达根目录
            break
        current = parent
    # 如果找不到，返回当前工作目录
    return Path.cwd()

# 加载 .env 文件（从项目根目录）
project_root = find_project_root()
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)


class ProviderType(str, Enum):
    """模型提供商类型"""
    ALIYUN = "aliyun"
    OPENAI = "openai"


class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: ProviderType = Field(
        default=ProviderType.ALIYUN,
        description="模型提供商: aliyun 或 openai"
    )
    api_key: str = Field(..., description="API 密钥")
    model_name: str = Field(
        default="qwen-long-latest",
        description="模型名称"
    )
    base_url: Optional[str] = Field(
        default=None,
        description="API 基础 URL（用于自定义端点）"
    )
    temperature: float = Field(
        default=0.7,
        description="温度参数，控制输出的随机性"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="最大生成 token 数"
    )
    timeout: int = Field(
        default=60,
        description="请求超时时间（秒）"
    )

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """
        从环境变量加载配置
        
        环境变量：
        - MODEL_PROVIDER: 模型提供商 (aliyun/openai)，默认 openai
        - DASHSCOPE_API_KEY: 阿里云 API 密钥（优先使用，阿里云标准环境变量名）
        - MODEL_STUDIO_KEY: API 密钥（备选，兼容旧配置）
        - MODEL_NAME: 模型名称，默认根据提供商设置
        - MODEL_REGION: 阿里云地域 (beijing/singapore)，默认 beijing
        - MODEL_BASE_URL: API 基础 URL（可选，会覆盖地域设置）
        - MODEL_TEMPERATURE: 温度参数，默认 0.7
        - MODEL_MAX_TOKENS: 最大 token 数（可选）
        - MODEL_TIMEOUT: 超时时间（秒），默认 60
        """
        provider_str = os.getenv("MODEL_PROVIDER", "aliyun").lower()
        
        # 解析提供商
        try:
            provider = ProviderType(provider_str)
        except ValueError:
            raise ValueError(
                f"不支持的模型提供商: {provider_str}。"
                f"支持的提供商: {', '.join([p.value for p in ProviderType])}"
            )
        
        # 根据提供商设置默认模型名称
        default_models = {
            ProviderType.ALIYUN: "qwen-long-latest",
            ProviderType.OPENAI: "gpt-3.5-turbo",
        }
        
        # 获取 API 密钥（优先使用 DASHSCOPE_API_KEY，这是阿里云的标准环境变量名）
        if provider == ProviderType.ALIYUN:
            api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("MODEL_STUDIO_KEY")
        else:
            api_key = os.getenv("MODEL_STUDIO_KEY") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            env_file_path = project_root / ".env"
            default_model = default_models.get(provider, "gpt-3.5-turbo")
            if provider == ProviderType.ALIYUN:
                key_name = "DASHSCOPE_API_KEY (或 MODEL_STUDIO_KEY)"
            else:
                key_name = "MODEL_STUDIO_KEY (或 OPENAI_API_KEY)"
            raise ValueError(
                f"未找到 API 密钥环境变量。\n"
                f"请在项目根目录创建 .env 文件并设置以下配置：\n"
                f"  MODEL_PROVIDER={provider_str}\n"
                f"  {key_name}=your_api_key_here\n"
                f"  MODEL_NAME={default_model}\n"
                f"  MODEL_REGION=beijing  # 仅阿里云需要（beijing/singapore）\n"
                f"\n.env 文件路径: {env_file_path}\n"
                f"项目根目录: {project_root}"
            )
        
        model_name = os.getenv("MODEL_NAME", default_models[provider])
        
        # 阿里云地域配置
        base_url = os.getenv("MODEL_BASE_URL")
        if provider == ProviderType.ALIYUN and not base_url:
            region = os.getenv("MODEL_REGION", "beijing").lower()
            if region == "singapore":
                base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
            else:  # 默认北京地域
                base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        # 解析其他配置
        temperature = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
        max_tokens = os.getenv("MODEL_MAX_TOKENS")
        max_tokens = int(max_tokens) if max_tokens else None
        timeout = int(os.getenv("MODEL_TIMEOUT", "60"))
        
        return cls(
            provider=provider,
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )


# 全局配置实例
_config: Optional[LLMConfig] = None


def get_llm_config() -> LLMConfig:
    """
    获取 LLM 配置（单例模式）
    
    Returns:
        LLMConfig: LLM 配置对象
    """
    global _config
    if _config is None:
        _config = LLMConfig.from_env()
    return _config


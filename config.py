"""
配置管理模块
使用环境变量管理敏感信息
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """应用配置类"""
    
    # ============================================
    # 数据库配置 - PostgreSQL
    # ============================================
    POSTGRES_HOST: str = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'contract_forge')
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'admin')
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD', '')
    
    @classmethod
    def get_database_url(cls) -> str:
        """获取数据库连接 URL"""
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
    
    @classmethod
    def get_database_config(cls) -> dict:
        """获取数据库连接配置（字典格式）"""
        return {
            'host': cls.POSTGRES_HOST,
            'port': cls.POSTGRES_PORT,
            'database': cls.POSTGRES_DB,
            'user': cls.POSTGRES_USER,
            'password': cls.POSTGRES_PASSWORD
        }
    
    # ============================================
    # 缓存配置 - Redis
    # ============================================
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_PASSWORD: Optional[str] = os.getenv('REDIS_PASSWORD', None)
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))
    
    @classmethod
    def get_redis_config(cls) -> dict:
        """获取 Redis 连接配置"""
        config = {
            'host': cls.REDIS_HOST,
            'port': cls.REDIS_PORT,
            'db': cls.REDIS_DB,
            'decode_responses': True
        }
        if cls.REDIS_PASSWORD:
            config['password'] = cls.REDIS_PASSWORD
        return config
    
    # ============================================
    # 应用配置
    # ============================================
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # API 服务
    API_HOST: str = os.getenv('API_HOST', '0.0.0.0')
    API_PORT: int = int(os.getenv('API_PORT', '8000'))
    API_DEBUG: bool = os.getenv('API_DEBUG', 'True').lower() == 'true'
    
    # ============================================
    # 安全配置
    # ============================================
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    JWT_ALGORITHM: str = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRE_MINUTES: int = int(os.getenv('JWT_EXPIRE_MINUTES', '30'))
    
    # ============================================
    # 外部服务配置
    # ============================================
    N8N_HOST: str = os.getenv('N8N_HOST', 'localhost')
    N8N_PORT: int = int(os.getenv('N8N_PORT', '5678'))
    N8N_WEBHOOK_URL: str = os.getenv('N8N_WEBHOOK_URL', f'http://localhost:5678/webhook')
    
    # AI 服务（可选）
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY', None)
    OPENAI_API_BASE: Optional[str] = os.getenv('OPENAI_API_BASE', None)
    
    # ============================================
    # 工具方法
    # ============================================
    @classmethod
    def is_production(cls) -> bool:
        """判断是否为生产环境"""
        return cls.ENVIRONMENT.lower() == 'production'
    
    @classmethod
    def is_development(cls) -> bool:
        """判断是否为开发环境"""
        return cls.ENVIRONMENT.lower() == 'development'
    
    @classmethod
    def is_testing(cls) -> bool:
        """判断是否为测试环境"""
        return cls.ENVIRONMENT.lower() == 'testing'
    
    @classmethod
    def validate(cls) -> list[str]:
        """验证配置，返回错误列表"""
        errors = []
        
        # 检查必需的配置项
        if not cls.POSTGRES_PASSWORD:
            errors.append("POSTGRES_PASSWORD 未设置")
        
        if cls.is_production():
            if cls.SECRET_KEY == 'dev-secret-key-change-me':
                errors.append("生产环境必须设置安全的 SECRET_KEY")
            
            if cls.API_DEBUG:
                errors.append("生产环境不应开启 API_DEBUG")
        
        return errors
    
    @classmethod
    def print_config(cls, show_sensitive: bool = False) -> None:
        """打印当前配置（用于调试）"""
        print("\n" + "=" * 70)
        print("📋 当前配置信息")
        print("=" * 70)
        
        print(f"\n🌍 环境: {cls.ENVIRONMENT}")
        print(f"📊 日志级别: {cls.LOG_LEVEL}")
        
        print(f"\n💾 数据库:")
        print(f"  - Host: {cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}")
        print(f"  - Database: {cls.POSTGRES_DB}")
        print(f"  - User: {cls.POSTGRES_USER}")
        if show_sensitive:
            print(f"  - Password: {cls.POSTGRES_PASSWORD}")
        else:
            print(f"  - Password: {'*' * len(cls.POSTGRES_PASSWORD)}")
        
        print(f"\n⚡ Redis:")
        print(f"  - Host: {cls.REDIS_HOST}:{cls.REDIS_PORT}")
        print(f"  - DB: {cls.REDIS_DB}")
        
        print(f"\n🚀 API 服务:")
        print(f"  - Host: {cls.API_HOST}:{cls.API_PORT}")
        print(f"  - Debug: {cls.API_DEBUG}")
        
        print(f"\n🔐 安全:")
        if show_sensitive:
            print(f"  - Secret Key: {cls.SECRET_KEY}")
        else:
            print(f"  - Secret Key: {'*' * min(20, len(cls.SECRET_KEY))}")
        print(f"  - JWT Algorithm: {cls.JWT_ALGORITHM}")
        print(f"  - JWT Expire: {cls.JWT_EXPIRE_MINUTES} 分钟")
        
        print("\n" + "=" * 70 + "\n")


# ============================================
# 使用示例（测试）
# ============================================
if __name__ == "__main__":
    print("🧪 配置模块测试\n")
    
    # 打印配置
    Config.print_config()
    
    # 验证配置
    errors = Config.validate()
    if errors:
        print("⚠️  配置验证失败：")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ 配置验证通过！")
    
    # 测试数据库连接配置
    print("\n📦 数据库连接配置：")
    print(Config.get_database_config())
    
    print("\n📦 Redis 连接配置：")
    print(Config.get_redis_config())


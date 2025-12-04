"""
测试 PostgreSQL 和 Redis 连接
"""

import psycopg2
import redis
from datetime import datetime
import sys
from pathlib import Path

# 添加项目路径到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger, LoggerManager
from config import Config

# 创建日志记录器
logger = get_logger(__name__)

# ============================================
# 测试 PostgreSQL 连接
# ============================================
def test_postgres():
    print("=" * 70)
    print("测试 PostgreSQL 连接")
    print("=" * 70)
    
    logger.info("开始测试 PostgreSQL 连接")
    
    try:
        # 连接数据库（使用配置模块）
        conn = psycopg2.connect(**Config.get_database_config())
        
        print("✅ PostgreSQL 连接成功！\n")
        logger.info("PostgreSQL 连接成功")
        
        # 创建游标
        cur = conn.cursor()
        
        # 测试查询 - 数据库版本
        cur.execute("SELECT version();")
        version = cur.fetchone()
        if version:
            print(f"📦 数据库版本: PostgreSQL {version[0].split()[1]}\n")
        else:
            print("⚠️  无法获取数据库版本\n")
        
        # 查看所有表
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        print(f"📊 已创建的表 ({len(tables)} 个):")
        for table in tables:
            print(f"  ✓ {table[0]}")
        
        # 查询合同类型数据
        print(f"\n📋 合同类型列表:")
        print("-" * 70)
        cur.execute("""
            SELECT type_code, type_name, default_workflow, is_active 
            FROM contract_types 
            ORDER BY sort_order;
        """)
        types = cur.fetchall()
        
        print(f"{'代码':<15} {'名称':<15} {'默认工作流':<30} {'状态'}")
        print("-" * 70)
        for t in types:
            status = '✅ 启用' if t[3] else '❌ 禁用'
            print(f"{t[0]:<15} {t[1]:<15} {t[2]:<30} {status}")
        
        print(f"\n总计: {len(types)} 种合同类型\n")
        
        # 关闭连接
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL 连接失败: {e}\n")
        logger.error(f"PostgreSQL 连接失败: {e}")
        print("请检查：")
        print("  1. Docker 容器是否正在运行: docker-compose ps")
        print("  2. 端口是否正确: 5432")
        print("  3. 用户名密码是否正确")
        return False


# ============================================
# 测试 Redis 连接
# ============================================
def test_redis():
    print("=" * 70)
    print("测试 Redis 连接")
    print("=" * 70)
    
    logger.info("开始测试 Redis 连接")
    
    try:
        # 连接 Redis（使用配置模块）
        r = redis.Redis(**Config.get_redis_config())
        
        # 测试连接
        r.ping()
        print("✅ Redis 连接成功！\n")
        logger.info("Redis 连接成功")
        
        # 获取 Redis 信息
        info = r.info()  # type: ignore
        print(f"📦 Redis 版本: {info['redis_version']}")  # type: ignore
        print(f"💾 已用内存: {info['used_memory_human']}")  # type: ignore
        print(f"🔌 连接数: {info['connected_clients']}\n")  # type: ignore
        
        # 测试基本操作
        print("测试 Redis 基本操作:")
        print("-" * 70)
        
        # 1. 字符串操作
        r.set('test_key', 'Hello Contract Forge!')
        value = r.get('test_key')
        print(f"  1. ✓ SET/GET: {value}")
        
        # 2. 哈希操作（模拟工作流状态）
        r.hset('workflow:test_001', mapping={
            'status': 'processing',
            'progress': '50',
            'current_step': '法规检索中'
        })
        workflow = r.hgetall('workflow:test_001')
        print(f"  2. ✓ HSET/HGETALL: {workflow}")
        
        # 3. 发布/订阅测试（模拟进度推送）
        r.publish('progress:test_001', 'Progress update: 50%')
        print(f"  3. ✓ PUBLISH: 消息已发布到频道")
        
        # 清理测试数据
        r.delete('test_key', 'workflow:test_001')
        print(f"  4. ✓ 测试数据已清理\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}\n")
        logger.error(f"Redis 连接失败: {e}")
        return False


# ============================================
# 主程序
# ============================================
if __name__ == "__main__":
    print("\n🚀 Contract Forge - 数据库连接测试\n")
    
    # 测试 PostgreSQL
    postgres_ok = test_postgres()
    
    # 测试 Redis
    redis_ok = test_redis()
    
    # 总结
    print("=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    print(f"PostgreSQL: {'✅ 连接正常' if postgres_ok else '❌ 连接失败'}")
    print(f"Redis:      {'✅ 连接正常' if redis_ok else '❌ 连接失败'}")
    
    if postgres_ok and redis_ok:
        print("\n🎉 所有数据库连接正常！")
        print("\n下一步可以：")
        print("  1. 开发后端 API 服务")
        print("  2. 启动前端项目")
        print("  3. 创建第一个工作流")
    else:
        print("\n⚠️  请检查数据库配置和连接")
    
    print("\n" + "=" * 70 + "\n")

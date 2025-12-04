"""
数据库工具模块
Database Utilities
"""

import psycopg2
from contextlib import contextmanager
from typing import Generator
from config import Config


class DatabaseManager:
    """数据库管理器"""
    
    @staticmethod
    def get_connection():
        """获取数据库连接"""
        return psycopg2.connect(**Config.get_database_config())
    
    @staticmethod
    @contextmanager
    def transaction() -> Generator:
        """
        事务上下文管理器
        
        用法:
            with DatabaseManager.transaction() as conn:
                dao = ContractTypeDAO(conn, auto_commit=False)
                dao.create(new_type)
                # 如果没有异常，自动 commit
                # 如果有异常，自动 rollback
        
        Yields:
            数据库连接对象
        """
        conn = psycopg2.connect(**Config.get_database_config())
        try:
            yield conn
            conn.commit()  # 成功时提交
        except Exception as e:
            conn.rollback()  # 失败时回滚
            raise e
        finally:
            conn.close()  # 总是关闭连接
    
    @staticmethod
    @contextmanager
    def get_dao_connection(auto_commit: bool = False) -> Generator:
        """
        获取 DAO 使用的连接（带事务控制）
        
        用法:
            with DatabaseManager.get_dao_connection() as conn:
                dao = ContractTypeDAO(conn, auto_commit=False)
                dao.create(type1)
                dao.update(type2)
                # 自动 commit/rollback
        
        Args:
            auto_commit: 是否自动提交（用于兼容 DAO）
        
        Yields:
            数据库连接对象
        """
        conn = psycopg2.connect(**Config.get_database_config())
        try:
            yield conn
            if not auto_commit:
                conn.commit()  # 手动控制时才在这里提交
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()


# ============================================
# 简化版：单独的事务函数
# ============================================
@contextmanager
def db_transaction() -> Generator:
    """
    简化的事务上下文管理器
    
    用法:
        from utils.database import db_transaction
        
        with db_transaction() as conn:
            dao = ContractTypeDAO(conn, auto_commit=False)
            dao.create(new_type)
    """
    conn = psycopg2.connect(**Config.get_database_config())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================
# 连接池版本（高性能场景）
# ============================================
from psycopg2 import pool

class ConnectionPool:
    """数据库连接池"""
    
    _pool = None
    
    @classmethod
    def initialize(cls, minconn=1, maxconn=10):
        """初始化连接池"""
        if cls._pool is None:
            cls._pool = pool.ThreadedConnectionPool(
                minconn,
                maxconn,
                **Config.get_database_config()
            )
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """从连接池获取连接"""
        if cls._pool is None:
            cls.initialize()
        
        conn = cls._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cls._pool.putconn(conn)
    
    @classmethod
    def close_all(cls):
        """关闭所有连接"""
        if cls._pool:
            cls._pool.closeall()


# ============================================
# 使用示例
# ============================================
if __name__ == "__main__":
    from models.contract_type import ContractType, ContractTypeDAO
    
    print("=" * 70)
    print("数据库工具 - 使用示例")
    print("=" * 70)
    
    # 示例 1: 使用 transaction() 上下文管理器
    print("\n1️⃣  使用 transaction() 创建合同类型：")
    print("-" * 70)
    
    try:
        with DatabaseManager.transaction() as conn:
            dao = ContractTypeDAO(conn, auto_commit=False)
            
            # 创建新类型
            new_type = ContractType(
                type_code='TEST_PROD',
                type_name='生产环境测试',
                description='测试生产代码中的事务管理'
            )
            
            created = dao.create(new_type)
            print(f"✅ 创建成功: {created}")
            
            # 如果这里抛出异常，会自动 rollback
            # raise Exception("模拟错误")
        
        print("✅ 事务已提交")
        
    except Exception as e:
        print(f"❌ 发生错误，已回滚: {e}")
    
    
    # 示例 2: 使用简化的 db_transaction()
    print("\n2️⃣  使用简化的 db_transaction()：")
    print("-" * 70)
    
    with db_transaction() as conn:
        dao = ContractTypeDAO(conn, auto_commit=False)
        types = dao.get_all()
        print(f"查询到 {len(types)} 种合同类型")
    
    
    # 示例 3: 使用连接池（高性能）
    print("\n3️⃣  使用连接池：")
    print("-" * 70)
    
    ConnectionPool.initialize()
    
    with ConnectionPool.get_connection() as conn:
        dao = ContractTypeDAO(conn, auto_commit=False)
        sales = dao.get_by_code('SALES')
        if sales:
            print(f"查询到: {sales}")
    
    ConnectionPool.close_all()
    
    print("\n" + "=" * 70 + "\n")


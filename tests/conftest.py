"""
Pytest 配置文件
提供测试 fixtures 和共享配置
"""

import pytest
import psycopg2
from config import Config


@pytest.fixture(scope="session")
def db_connection():
    """
    数据库连接 fixture（会话级别）
    整个测试会话共享一个连接
    """
    conn = psycopg2.connect(**Config.get_database_config())
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def db_transaction(db_connection):
    """
    数据库事务 fixture（函数级别）
    每个测试函数都会回滚，保证测试隔离
    """
    db_connection.rollback()  # 确保干净的起点
    yield db_connection
    db_connection.rollback()  # 测试后回滚


@pytest.fixture
def sample_contract_type():
    """
    示例合同类型数据
    """
    from models.contract_type import ContractType
    
    return ContractType(
        type_code='TEST_TYPE',
        type_name='测试合同类型',
        description='这是一个测试用的合同类型',
        default_workflow='standard_contract_processing',
        is_active=True,
        sort_order=999
    )


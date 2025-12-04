"""
合同类型模型
Contract Type Model

对应数据库表: contract_types
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class DefaultWorkflow(str, Enum):
    """默认工作流类型"""
    STANDARD = "standard_contract_processing"  # 标准合同处理流程
    QUICK = "quick_approval"                   # 快速审批流程
    STRICT = "strict_approval"                 # 严格审批流程


@dataclass
class ContractType:
    """
    合同类型数据类
    
    Attributes:
        id: 主键ID
        type_code: 合同类型代码（唯一）
        type_name: 合同类型名称
        description: 描述信息
        default_workflow: 默认关联的工作流
        is_active: 是否启用
        sort_order: 排序序号
        created_at: 创建时间
        updated_at: 更新时间
    """
    type_code: str
    type_name: str
    id: Optional[int] = None
    description: Optional[str] = None
    default_workflow: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'ContractType':
        """
        从数据库查询结果创建实例
        
        Args:
            row: 数据库查询返回的元组 (id, type_code, type_name, ...)
            
        Returns:
            ContractType 实例
        """
        return cls(
            id=row[0],
            type_code=row[1],
            type_name=row[2],
            description=row[3] if len(row) > 3 else None,
            default_workflow=row[4] if len(row) > 4 else None,
            is_active=row[5] if len(row) > 5 else True,
            sort_order=row[6] if len(row) > 6 else 0,
            created_at=row[7] if len(row) > 7 else None,
            updated_at=row[8] if len(row) > 8 else None,
        )
    
    def to_dict(self) -> dict:
        """
        转换为字典格式（用于 JSON 序列化）
        
        Returns:
            字典格式的数据
        """
        return {
            'id': self.id,
            'type_code': self.type_code,
            'type_name': self.type_name,
            'description': self.description,
            'default_workflow': self.default_workflow,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"ContractType(id={self.id}, code='{self.type_code}', name='{self.type_name}')"


# ============================================
# 数据访问层（DAO）
# ============================================
class ContractTypeDAO:
    """
    合同类型数据访问对象
    提供数据库操作方法
    """
    
    def __init__(self, db_connection, auto_commit: bool = True):
        """
        初始化 DAO
        
        Args:
            db_connection: psycopg2 数据库连接对象
            auto_commit: 是否自动提交事务（测试时设为 False）
        """
        self.conn = db_connection
        self.auto_commit = auto_commit
    
    def get_all(self, active_only: bool = True) -> list[ContractType]:
        """
        获取所有合同类型
        
        Args:
            active_only: 是否只返回启用的类型
            
        Returns:
            合同类型列表
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT id, type_code, type_name, description, 
                   default_workflow, is_active, sort_order, 
                   created_at, updated_at
            FROM contract_types
        """
        
        if active_only:
            query += " WHERE is_active = TRUE"
        
        query += " ORDER BY sort_order, type_code"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        
        return [ContractType.from_db_row(row) for row in rows]
    
    def get_by_code(self, type_code: str) -> Optional[ContractType]:
        """
        根据类型代码获取合同类型
        
        Args:
            type_code: 合同类型代码
            
        Returns:
            合同类型对象，如果不存在返回 None
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT id, type_code, type_name, description, 
                   default_workflow, is_active, sort_order, 
                   created_at, updated_at
            FROM contract_types
            WHERE type_code = %s
        """
        
        cursor.execute(query, (type_code,))
        row = cursor.fetchone()
        cursor.close()
        
        return ContractType.from_db_row(row) if row else None
    
    def get_by_id(self, id: int) -> Optional[ContractType]:
        """
        根据ID获取合同类型
        
        Args:
            id: 合同类型ID
            
        Returns:
            合同类型对象，如果不存在返回 None
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT id, type_code, type_name, description, 
                   default_workflow, is_active, sort_order, 
                   created_at, updated_at
            FROM contract_types
            WHERE id = %s
        """
        
        cursor.execute(query, (id,))
        row = cursor.fetchone()
        cursor.close()
        
        return ContractType.from_db_row(row) if row else None
    
    def create(self, contract_type: ContractType) -> ContractType:
        """
        创建新的合同类型
        
        Args:
            contract_type: 合同类型对象
            
        Returns:
            创建后的合同类型对象（包含ID）
        """
        cursor = self.conn.cursor()
        
        query = """
            INSERT INTO contract_types 
            (type_code, type_name, description, default_workflow, 
             is_active, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, created_at, updated_at
        """
        
        cursor.execute(query, (
            contract_type.type_code,
            contract_type.type_name,
            contract_type.description,
            contract_type.default_workflow,
            contract_type.is_active,
            contract_type.sort_order,
        ))
        
        id, created_at, updated_at = cursor.fetchone()
        
        if self.auto_commit:
            self.conn.commit()
        
        cursor.close()
        
        contract_type.id = id
        contract_type.created_at = created_at
        contract_type.updated_at = updated_at
        
        return contract_type
    
    def update(self, contract_type: ContractType) -> bool:
        """
        更新合同类型
        
        Args:
            contract_type: 合同类型对象（必须包含ID）
            
        Returns:
            是否更新成功
        """
        if not contract_type.id:
            raise ValueError("Contract type ID is required for update")
        
        cursor = self.conn.cursor()
        
        query = """
            UPDATE contract_types
            SET type_code = %s,
                type_name = %s,
                description = %s,
                default_workflow = %s,
                is_active = %s,
                sort_order = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        cursor.execute(query, (
            contract_type.type_code,
            contract_type.type_name,
            contract_type.description,
            contract_type.default_workflow,
            contract_type.is_active,
            contract_type.sort_order,
            contract_type.id,
        ))
        
        rows_affected = cursor.rowcount
        
        if self.auto_commit:
            self.conn.commit()
        
        cursor.close()
        
        return rows_affected > 0
    
    def delete(self, id: int) -> bool:
        """
        删除合同类型（物理删除）
        
        Args:
            id: 合同类型ID
            
        Returns:
            是否删除成功
        """
        cursor = self.conn.cursor()
        
        query = "DELETE FROM contract_types WHERE id = %s"
        cursor.execute(query, (id,))
        
        rows_affected = cursor.rowcount
        
        if self.auto_commit:
            self.conn.commit()
        
        cursor.close()
        
        return rows_affected > 0
    
    def deactivate(self, id: int) -> bool:
        """
        停用合同类型（软删除）
        
        Args:
            id: 合同类型ID
            
        Returns:
            是否操作成功
        """
        cursor = self.conn.cursor()
        
        query = """
            UPDATE contract_types
            SET is_active = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        cursor.execute(query, (id,))
        rows_affected = cursor.rowcount
        
        if self.auto_commit:
            self.conn.commit()
        
        cursor.close()
        
        return rows_affected > 0


# ============================================
# 使用示例
# ============================================
if __name__ == "__main__":
    """
    使用示例和测试
    """
    import psycopg2
    from config import Config
    
    # 连接数据库
    conn = psycopg2.connect(**Config.get_database_config())
    dao = ContractTypeDAO(conn)
    
    print("=" * 70)
    print("合同类型模型 - 使用示例")
    print("=" * 70)
    
    # 1. 获取所有合同类型
    print("\n1️⃣  获取所有启用的合同类型：")
    print("-" * 70)
    types = dao.get_all(active_only=True)
    for t in types:
        print(f"  {t.type_code:<15} | {t.type_name:<15} | {t.default_workflow}")
    
    # 2. 根据代码查询
    print("\n2️⃣  查询 SALES 类型：")
    print("-" * 70)
    sales = dao.get_by_code("SALES")
    if sales:
        print(f"  {sales}")
        print(f"  描述: {sales.description}")
        print(f"  工作流: {sales.default_workflow}")
    
    # 3. 创建新类型（示例 - 不会实际执行）
    print("\n3️⃣  创建新类型示例（代码演示）：")
    print("-" * 70)
    print("""
    new_type = ContractType(
        type_code='FRANCHISE',
        type_name='特许经营合同',
        description='特许经营权授权合同',
        default_workflow='strict_approval',
        sort_order=10
    )
    # created = dao.create(new_type)
    """)
    
    # 4. 转换为字典
    print("\n4️⃣  转换为字典格式：")
    print("-" * 70)
    if sales:
        print(f"  {sales.to_dict()}")
    
    conn.close()
    print("\n" + "=" * 70 + "\n")


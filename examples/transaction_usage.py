"""
事务管理使用示例
Transaction Usage Examples
"""

from utils.database import DatabaseManager, db_transaction, ConnectionPool
from models.contract_type import ContractType, ContractTypeDAO


# ============================================
# 示例 1: 简单的单个操作
# ============================================
def create_contract_type(type_code: str, type_name: str) -> ContractType:
    """
    创建合同类型（单个操作）
    """
    with db_transaction() as conn:
        dao = ContractTypeDAO(conn, auto_commit=False)
        
        new_type = ContractType(
            type_code=type_code,
            type_name=type_name
        )
        
        return dao.create(new_type)
        # 退出 with 块时自动 commit


# ============================================
# 示例 2: 多个操作（事务一致性）
# ============================================
def batch_create_contract_types(types_data: list[dict]) -> list[ContractType]:
    """
    批量创建合同类型（保证事务一致性）
    要么全部成功，要么全部失败
    """
    created_types = []
    
    with db_transaction() as conn:
        dao = ContractTypeDAO(conn, auto_commit=False)
        
        for data in types_data:
            new_type = ContractType(
                type_code=data['code'],
                type_name=data['name'],
                description=data.get('description')
            )
            
            created = dao.create(new_type)
            created_types.append(created)
        
        # 如果循环中任何一个失败，整个事务回滚
        # 如果全部成功，退出时自动 commit
    
    return created_types


# ============================================
# 示例 3: 复杂业务逻辑（多表操作）
# ============================================
def update_contract_type_with_audit(
    type_id: int, 
    new_name: str,
    user_id: str
) -> bool:
    """
    更新合同类型并记录审计日志
    两个操作在同一事务中
    """
    with DatabaseManager.transaction() as conn:
        dao = ContractTypeDAO(conn, auto_commit=False)
        
        # 1. 更新合同类型
        contract_type = dao.get_by_id(type_id)
        if not contract_type:
            raise ValueError(f"Contract type {type_id} not found")
        
        contract_type.type_name = new_name
        dao.update(contract_type)
        
        # 2. 记录审计日志（假设有审计表）
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (entity_type, entity_id, action, user_id)
            VALUES (%s, %s, %s, %s)
        """, ('contract_type', type_id, 'update', user_id))
        cursor.close()
        
        # 两个操作都成功才提交
        return True


# ============================================
# 示例 4: 错误处理
# ============================================
def safe_create_contract_type(type_code: str, type_name: str) -> tuple[bool, str]:
    """
    安全地创建合同类型（带错误处理）
    
    Returns:
        (成功与否, 消息)
    """
    try:
        with db_transaction() as conn:
            dao = ContractTypeDAO(conn, auto_commit=False)
            
            # 检查是否已存在
            existing = dao.get_by_code(type_code)
            if existing:
                return False, f"Type code {type_code} already exists"
            
            # 创建新类型
            new_type = ContractType(
                type_code=type_code,
                type_name=type_name
            )
            dao.create(new_type)
            
            return True, "Created successfully"
    
    except Exception as e:
        # 事务已自动回滚
        return False, f"Error: {str(e)}"


# ============================================
# 示例 5: 在 API 中使用
# ============================================
def api_create_contract_type(request_data: dict) -> dict:
    """
    API 端点：创建合同类型
    
    Args:
        request_data: {"type_code": "...", "type_name": "..."}
    
    Returns:
        {"success": bool, "data": {...} or "error": "..."}
    """
    try:
        with db_transaction() as conn:
            dao = ContractTypeDAO(conn, auto_commit=False)
            
            new_type = ContractType(
                type_code=request_data['type_code'],
                type_name=request_data['type_name'],
                description=request_data.get('description'),
                default_workflow=request_data.get('workflow', 'standard_contract_processing')
            )
            
            created = dao.create(new_type)
            
            return {
                "success": True,
                "data": created.to_dict()
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================
# 示例 6: 使用连接池（高并发场景）
# ============================================
def high_performance_query() -> list[ContractType]:
    """
    高性能查询（使用连接池）
    适合高并发场景
    """
    # 初始化连接池（通常在应用启动时做一次）
    ConnectionPool.initialize(minconn=5, maxconn=20)
    
    with ConnectionPool.get_connection() as conn:
        dao = ContractTypeDAO(conn, auto_commit=False)
        return dao.get_all()


# ============================================
# 示例 7: 手动控制事务（高级用法）
# ============================================
def manual_transaction_control():
    """
    手动控制事务（不使用上下文管理器）
    适合复杂的流程控制
    """
    conn = DatabaseManager.get_connection()
    
    try:
        dao = ContractTypeDAO(conn, auto_commit=False)
        
        # 操作 1
        type1 = ContractType(type_code='MANUAL_1', type_name='手动控制1')
        dao.create(type1)
        
        # 某些条件判断...
        if should_continue():
            # 操作 2
            type2 = ContractType(type_code='MANUAL_2', type_name='手动控制2')
            dao.create(type2)
            
            conn.commit()  # 手动提交
        else:
            conn.rollback()  # 手动回滚
    
    except Exception as e:
        conn.rollback()
        raise e
    
    finally:
        conn.close()


def should_continue() -> bool:
    """业务逻辑判断"""
    return True


# ============================================
# 在 FastAPI 中使用
# ============================================
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class ContractTypeCreate(BaseModel):
    type_code: str
    type_name: str
    description: str = None

@app.post("/api/contract-types")
def create_type_endpoint(data: ContractTypeCreate):
    '''创建合同类型 API'''
    try:
        with db_transaction() as conn:
            dao = ContractTypeDAO(conn, auto_commit=False)
            
            new_type = ContractType(
                type_code=data.type_code,
                type_name=data.type_name,
                description=data.description
            )
            
            created = dao.create(new_type)
            return {"success": True, "data": created.to_dict()}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"""


# ============================================
# 主程序示例
# ============================================
if __name__ == "__main__":
    print("=" * 70)
    print("事务管理使用示例")
    print("=" * 70)
    
    # 示例 1: 创建单个类型
    print("\n1️⃣  创建单个合同类型：")
    try:
        created = create_contract_type('EXAMPLE_1', '示例类型1')
        print(f"✅ 创建成功: {created}")
    except Exception as e:
        print(f"❌ 创建失败: {e}")
    
    # 示例 2: 批量创建
    print("\n2️⃣  批量创建合同类型：")
    types_data = [
        {'code': 'BATCH_1', 'name': '批量测试1'},
        {'code': 'BATCH_2', 'name': '批量测试2'},
    ]
    try:
        created_types = batch_create_contract_types(types_data)
        print(f"✅ 批量创建成功: {len(created_types)} 个")
    except Exception as e:
        print(f"❌ 批量创建失败（已回滚）: {e}")
    
    # 示例 4: 安全创建（带错误处理）
    print("\n4️⃣  安全创建：")
    success, message = safe_create_contract_type('SAFE_TEST', '安全测试')
    print(f"{'✅' if success else '❌'} {message}")
    
    print("\n" + "=" * 70 + "\n")


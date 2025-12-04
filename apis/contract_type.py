# API 端点 - 合同类型

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from models.contract_type import ContractType, ContractTypeDAO
from utils.logger import get_logger
from utils.database import db_transaction

logger = get_logger(__name__)

# 创建 API 路由器
router = APIRouter(
    prefix="/contract-type",
    tags=["contract-type"],
)


# ============================================
# 请求/响应模型
# ============================================
class ContractTypeCreate(BaseModel):
    """创建合同类型请求"""
    type_code: str
    type_name: str
    description: Optional[str] = None
    default_workflow: str = "standard_contract_processing"


# ============================================
# API 端点
# ============================================

@router.get("/all")
async def get_all_contract_types():
    """
    获取所有合同类型
    
    - 查询操作，不需要事务控制
    - 使用默认的 auto_commit=True
    """
    try:
        with db_transaction() as conn:
            dao = ContractTypeDAO(conn)  # ← 查询用默认值
            contract_types = dao.get_all()
            
            return {
                "success": True,
                "data": [t.to_dict() for t in contract_types],
                "count": len(contract_types)
            }
    
    except Exception as e:
        logger.error(f"Failed to get contract types: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{type_code}")
async def get_contract_type(type_code: str):
    """
    根据代码获取合同类型
    
    - 查询操作
    """
    try:
        with db_transaction() as conn:
            dao = ContractTypeDAO(conn)
            contract_type = dao.get_by_code(type_code)
            
            if not contract_type:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Contract type '{type_code}' not found"
                )
            
            return {
                "success": True,
                "data": contract_type.to_dict()
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get contract type: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_contract_type(data: ContractTypeCreate):
    """
    创建合同类型
    
    - 写入操作，需要事务控制
    - 使用 auto_commit=False，让上下文管理器控制提交
    """
    try:
        with db_transaction() as conn:
            dao = ContractTypeDAO(conn, auto_commit=False)  # ← 写入用 False
            
            # 检查是否已存在
            existing = dao.get_by_code(data.type_code)
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Contract type '{data.type_code}' already exists"
                )
            
            # 创建新类型
            new_type = ContractType(
                type_code=data.type_code,
                type_name=data.type_name,
                description=data.description,
                default_workflow=data.default_workflow
            )
            
            created = dao.create(new_type)
            logger.info(f"Created contract type: {created.type_code}")
            
            return {
                "success": True,
                "message": "Contract type created successfully",
                "data": created.to_dict()
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create contract type: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# API 模块结构说明

## 目录结构

```
backend/api/
├── __init__.py          # 主入口，统一注册所有模块路由
├── tools/               # 工具模块
│   ├── __init__.py
│   └── router.py       # 工具相关的 API 路由
└── [其他模块]/          # 其他功能模块
    ├── __init__.py
    └── router.py
```

## 如何添加新模块

### 1. 创建模块文件夹

在 `backend/api/` 下创建新模块文件夹，例如 `contracts/`：

```bash
mkdir -p backend/api/contracts
```

### 2. 创建模块文件

**`backend/api/contracts/__init__.py`**:
```python
"""合同模块 API"""
from backend.api.contracts.router import router
__all__ = ["router"]
```

**`backend/api/contracts/router.py`**:
```python
from fastapi import APIRouter

router = APIRouter(prefix="/contracts", tags=["Contracts"])

@router.get("")
async def list_contracts():
    """获取合同列表"""
    return {"contracts": []}
```

### 3. 在主路由中注册

在 `backend/api/__init__.py` 中添加：

```python
from backend.api.contracts.router import router as contracts_router

main_router.include_router(contracts_router)
```

## 当前模块

- **tools**: 工具管理相关 API (`/api/tools`)


# 事务管理指南

**测试环境 vs 生产环境的事务管理**

---

## 📊 核心区别对比

| 方面 | 测试环境 | 生产环境 |
|-----|---------|---------|
| **使用场景** | 自动化测试 | 实际业务逻辑 |
| **工具** | Pytest Fixture | 上下文管理器 |
| **定义位置** | `tests/conftest.py` | `utils/database.py` |
| **自动注入** | ✅ pytest 自动 | ❌ 需要手动导入 |
| **事务控制** | 测试后自动回滚 | 成功提交/失败回滚 |
| **数据持久化** | ❌ 不持久化 | ✅ 持久化到数据库 |

---

## 🧪 测试环境：使用 Pytest Fixture

### 定义（`tests/conftest.py`）

```python
import pytest
import psycopg2

@pytest.fixture(scope="function")
def db_transaction(db_connection):
    """测试专用：自动回滚"""
    db_connection.rollback()
    yield db_connection
    db_connection.rollback()  # ← 测试后回滚
```

### 使用

```python
def test_create(self, db_transaction):
    """pytest 自动注入"""
    dao = ContractTypeDAO(db_transaction, auto_commit=False)
    dao.create(new_type)
    # 测试结束后自动回滚，数据不会保存
```

**特点**：
- ✅ 只在测试中可用
- ✅ 自动清理，测试隔离
- ✅ 可重复运行
- ❌ **不能在生产代码中使用**

---

## 🚀 生产环境：使用上下文管理器

### 定义（`utils/database.py`）

```python
from contextlib import contextmanager
import psycopg2

@contextmanager
def db_transaction():
    """生产环境：自动提交"""
    conn = psycopg2.connect(...)
    try:
        yield conn
        conn.commit()  # ← 成功提交
    except Exception:
        conn.rollback()  # ← 失败回滚
        raise
    finally:
        conn.close()
```

### 使用

```python
from utils.database import db_transaction

def create_type_in_production():
    """生产代码"""
    with db_transaction() as conn:
        dao = ContractTypeDAO(conn, auto_commit=False)
        dao.create(new_type)
        # 退出 with 块时自动提交，数据持久化
```

**特点**：
- ✅ 在任何地方都可用
- ✅ 自动提交/回滚
- ✅ 数据持久化
- ✅ 异常安全

---

## 💡 为什么不能混用？

### ❌ 错误示例：在生产代码中使用 pytest fixture

```python
# api/contract_type.py
from tests.conftest import db_transaction  # ❌ 错误！

def create_api():
    with db_transaction() as conn:  # ❌ 不会工作！
        # pytest fixture 只在测试中可用
        pass
```

**问题**：
1. `@pytest.fixture` 装饰器只在 pytest 运行时有效
2. 生产环境没有 pytest 的依赖注入机制
3. 会导致 `ImportError` 或运行时错误

---

## ✅ 正确的做法

### 1. 测试中使用 Fixture

```python
# tests/unit/models/test_contract_type.py

def test_create(self, db_transaction):  # ← pytest fixture
    """测试：数据不持久化"""
    dao = ContractTypeDAO(db_transaction, auto_commit=False)
    dao.create(new_type)
```

### 2. 生产代码使用上下文管理器

```python
# api/contract_type.py
from utils.database import db_transaction  # ← 工具函数

def create_api_handler():
    """API：数据持久化"""
    with db_transaction() as conn:
        dao = ContractTypeDAO(conn, auto_commit=False)
        dao.create(new_type)
```

---

## 🎯 常见使用场景

### 场景 1: 简单的单个操作

```python
from utils.database import db_transaction

def save_contract_type(data):
    with db_transaction() as conn:
        dao = ContractTypeDAO(conn, auto_commit=False)
        return dao.create(data)
```

### 场景 2: 多个操作（事务一致性）

```python
def batch_operation():
    with db_transaction() as conn:
        dao = ContractTypeDAO(conn, auto_commit=False)
        
        dao.create(type1)
        dao.update(type2)
        dao.delete(type3)
        
        # 全部成功才提交，任何一个失败都回滚
```

### 场景 3: 在 FastAPI 中使用

```python
from fastapi import FastAPI
from utils.database import db_transaction

app = FastAPI()

@app.post("/api/contract-types")
def create_type(data: dict):
    with db_transaction() as conn:
        dao = ContractTypeDAO(conn, auto_commit=False)
        created = dao.create(data)
        return {"success": True, "data": created.to_dict()}
```

### 场景 4: 在定时任务中使用

```python
def scheduled_job():
    """定时任务：清理过期数据"""
    with db_transaction() as conn:
        dao = ContractTypeDAO(conn, auto_commit=False)
        
        # 批量处理
        old_types = dao.get_all(active_only=False)
        for t in old_types:
            if is_expired(t):
                dao.delete(t.id)
```

---

## 🔧 高级用法

### 使用连接池（高并发场景）

```python
from utils.database import ConnectionPool

# 应用启动时初始化
ConnectionPool.initialize(minconn=5, maxconn=20)

# 使用连接
def handle_request():
    with ConnectionPool.get_connection() as conn:
        dao = ContractTypeDAO(conn, auto_commit=False)
        return dao.get_all()

# 应用关闭时清理
ConnectionPool.close_all()
```

### 手动控制事务

```python
from utils.database import DatabaseManager

def complex_operation():
    conn = DatabaseManager.get_connection()
    
    try:
        dao = ContractTypeDAO(conn, auto_commit=False)
        
        # 操作 1
        dao.create(type1)
        
        # 业务逻辑判断
        if some_condition():
            dao.create(type2)
            conn.commit()
        else:
            conn.rollback()
    
    except Exception as e:
        conn.rollback()
        raise
    
    finally:
        conn.close()
```

---

## 📝 最佳实践

### ✅ 推荐做法

1. **测试用 pytest fixture**
   ```python
   def test_something(self, db_transaction):
       # 使用 fixture
   ```

2. **生产用上下文管理器**
   ```python
   with db_transaction() as conn:
       # 业务逻辑
   ```

3. **DAO 设置 `auto_commit=False`**
   ```python
   dao = ContractTypeDAO(conn, auto_commit=False)
   # 让上下文管理器控制事务
   ```

4. **异常处理**
   ```python
   try:
       with db_transaction() as conn:
           # 操作
   except Exception as e:
       # 已自动回滚
       logger.error(f"Transaction failed: {e}")
   ```

### ❌ 避免的做法

1. **不要在生产代码中导入 pytest fixture**
   ```python
   from tests.conftest import db_transaction  # ❌
   ```

2. **不要混合使用 auto_commit**
   ```python
   # ❌ 混乱的事务控制
   dao = ContractTypeDAO(conn, auto_commit=True)
   # 上下文管理器也会提交，导致双重提交
   ```

3. **不要忘记异常处理**
   ```python
   # ❌ 没有处理异常
   conn = get_connection()
   dao.create(...)  # 如果失败，连接没有关闭
   ```

---

## 🎓 总结

| 需求 | 使用方案 |
|-----|---------|
| **写测试** | pytest fixture (`db_transaction`) |
| **写 API** | 上下文管理器 (`utils.database.db_transaction`) |
| **批处理** | 上下文管理器 |
| **定时任务** | 上下文管理器 |
| **高并发** | 连接池 (`ConnectionPool`) |

**一句话总结**：
- 测试 = pytest fixture（自动回滚）
- 生产 = 上下文管理器（自动提交）

---

## 📚 相关文件

- `tests/conftest.py` - 测试 fixtures 定义
- `utils/database.py` - 生产环境工具
- `examples/transaction_usage.py` - 使用示例

---

*最后更新: 2025-12-04*


# 测试说明

Contract Forge 项目的测试指南。

---

## 📁 测试目录结构

```
tests/
├── __init__.py
├── conftest.py                    # Pytest 配置和共享 fixtures
├── README.md                      # 本文档
├── unit/                          # 单元测试
│   ├── __init__.py
│   ├── models/                    # 模型层测试
│   │   ├── __init__.py
│   │   └── test_contract_type.py
│   ├── services/                  # 服务层测试（待创建）
│   └── utils/                     # 工具函数测试（待创建）
├── integration/                   # 集成测试（待创建）
│   └── test_database_integration.py
└── fixtures/                      # 测试数据（待创建）
    ├── sample_contracts/
    └── expected_outputs/
```

---

## 🚀 运行测试

### 前置条件

1. **安装测试依赖**：

```bash
pip install pytest pytest-cov
```

2. **确保数据库运行**：

```bash
docker-compose up -d postgres redis
```

3. **初始化数据库**（如果还没有）：

```bash
docker exec -i contract_forge-postgres-1 psql -U contract_user -d contract_forge < database/init.sql
```

### 运行所有测试

```bash
# 在项目根目录运行
pytest
```

### 运行特定测试

```bash
# 运行单个测试文件
pytest tests/unit/models/test_contract_type.py

# 运行特定测试类
pytest tests/unit/models/test_contract_type.py::TestContractType

# 运行特定测试方法
pytest tests/unit/models/test_contract_type.py::TestContractType::test_create_contract_type

# 使用关键字过滤
pytest -k "contract_type"
```

### 运行特定类型的测试

```bash
# 只运行单元测试（快速）
pytest -m unit

# 只运行集成测试
pytest -m integration

# 排除慢速测试
pytest -m "not slow"
```

### 详细输出

```bash
# 显示更详细的输出
pytest -vv

# 显示测试覆盖的变量
pytest -vv -s

# 显示失败时的完整回溯
pytest --tb=long
```

### 代码覆盖率

```bash
# 生成覆盖率报告（终端）
pytest --cov=models --cov=utils

# 生成 HTML 覆盖率报告
pytest --cov=models --cov=utils --cov-report=html

# 查看报告
# 打开 htmlcov/index.html
```

---

## 📝 编写测试

### 测试文件命名规范

- 测试文件必须以 `test_` 开头或以 `_test.py` 结尾
- 测试类必须以 `Test` 开头
- 测试方法必须以 `test_` 开头

### 测试示例

```python
import pytest
from models.contract_type import ContractType

class TestContractType:
    """测试合同类型模型"""
    
    def test_create_instance(self):
        """测试创建实例"""
        ct = ContractType(
            type_code='TEST',
            type_name='测试'
        )
        
        assert ct.type_code == 'TEST'
        assert ct.type_name == '测试'
    
    def test_with_fixture(self, sample_contract_type):
        """使用 fixture 的测试"""
        assert sample_contract_type.type_code == 'TEST_TYPE'
```

### 使用 Fixtures

Fixtures 在 `conftest.py` 中定义，可以在任何测试中使用：

```python
def test_database_operation(db_transaction):
    """使用数据库事务 fixture"""
    # db_transaction 会自动回滚
    # 不会影响数据库实际数据
    pass

def test_sample_data(sample_contract_type):
    """使用示例数据 fixture"""
    assert sample_contract_type is not None
```

### 测试数据库操作

```python
class TestDatabaseOperations:
    """测试数据库操作"""
    
    def test_create_and_query(self, db_transaction):
        """测试创建和查询"""
        dao = ContractTypeDAO(db_transaction)
        
        # 创建
        new_type = ContractType(
            type_code='NEW',
            type_name='新类型'
        )
        created = dao.create(new_type)
        
        # 查询
        found = dao.get_by_code('NEW')
        
        assert found is not None
        assert found.id == created.id
        
        # 测试结束后自动回滚，不影响数据库
```

---

## 🎯 测试类型说明

### 单元测试 (Unit Tests)

- **位置**: `tests/unit/`
- **特点**: 
  - 快速执行（毫秒级）
  - 测试单个函数或类
  - 不依赖外部资源（数据库、网络等）
  - 使用 Mock 模拟外部依赖

**示例**:

```python
def test_to_dict():
    """单元测试：纯逻辑测试，不需要数据库"""
    ct = ContractType(type_code='TEST', type_name='测试')
    result = ct.to_dict()
    assert isinstance(result, dict)
```

### 集成测试 (Integration Tests)

- **位置**: `tests/integration/`
- **特点**:
  - 测试多个组件的交互
  - 需要真实的外部资源（数据库、Redis等）
  - 执行较慢（秒级）
  - 测试完整的业务流程

**示例**:

```python
def test_full_workflow(db_transaction):
    """集成测试：测试完整的 CRUD 流程"""
    dao = ContractTypeDAO(db_transaction)
    # ... 完整的业务流程测试
```

### 性能测试 (Performance Tests)

- **位置**: 任何目录，标记为 `@pytest.mark.performance`
- **特点**:
  - 测试执行效率
  - 验证性能指标
  - 通常较慢

---

## 📊 测试覆盖率目标

| 模块 | 目标覆盖率 | 当前状态 |
|-----|-----------|---------|
| models/ | ≥ 90% | ✅ 已达标 |
| utils/ | ≥ 80% | 📝 待实现 |
| apis/ | ≥ 85% | 🚧 待开发 |
| 总体 | ≥ 80% | 🚧 进行中 |

---

## 🔧 常见问题

### 1. 数据库连接失败

**问题**: `psycopg2.OperationalError: could not connect to server`

**解决**:

```bash
# 确保 Docker 容器运行
docker-compose ps

# 启动容器
docker-compose up -d
```

### 2. 测试数据污染

**问题**: 测试之间互相影响

**解决**: 使用 `db_transaction` fixture，它会自动回滚：

```python
def test_example(db_transaction):  # 使用 db_transaction
    # 测试代码
    pass
```

### 3. 导入模块失败

**问题**: `ModuleNotFoundError: No module named 'models'`

**解决**: 确保在项目根目录运行测试：

```bash
cd /path/to/contract_forge
pytest
```

---

## 🎨 最佳实践

### 1. 测试命名

- **清晰描述**: 测试名称应该清楚说明测试什么
- **使用中文**: 可以使用中文文档字符串

```python
def test_get_by_code_not_exists(self):
    """测试获取不存在的合同类型（应返回 None）"""
    pass
```

### 2. 测试隔离

- 每个测试应该独立运行
- 使用 fixtures 提供测试数据
- 测试后清理数据（或使用事务回滚）

### 3. 断言清晰

```python
# ❌ 不好
assert result

# ✅ 好
assert result is not None
assert result.type_code == 'SALES'
```

### 4. 测试边界情况

```python
def test_edge_cases(self):
    """测试边界情况"""
    # 空字符串
    # None 值
    # 超大数值
    # 特殊字符
    pass
```

### 5. 使用参数化测试

```python
@pytest.mark.parametrize("code,expected", [
    ('SALES', '销售合同'),
    ('PURCHASE', '采购合同'),
    ('SERVICE', '服务合同'),
])
def test_multiple_types(code, expected, db_transaction):
    """参数化测试多种类型"""
    dao = ContractTypeDAO(db_transaction)
    result = dao.get_by_code(code)
    assert result.type_name == expected
```

---

## 📚 相关资源

- [Pytest 官方文档](https://docs.pytest.org/)
- [Pytest 最佳实践](https://docs.pytest.org/en/latest/goodpractices.html)
- [Python 测试指南](https://realpython.com/pytest-python-testing/)

---

## 🔄 持续集成（CI）

测试应该在每次提交时自动运行。配置示例：

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov
```

---

*最后更新: 2025-12-04*


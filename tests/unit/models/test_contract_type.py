"""
合同类型模型测试
Test Contract Type Model
"""

import pytest
from datetime import datetime
from models.contract_type import (
    ContractType,
    ContractTypeDAO,
    DefaultWorkflow
)


# ============================================
# ContractType 数据类测试
# ============================================
class TestContractType:
    """测试 ContractType 数据类"""
    
    def test_create_contract_type(self):
        """测试创建合同类型实例"""
        ct = ContractType(
            type_code='SALES',
            type_name='销售合同',
            description='商品销售合同',
            default_workflow='standard_contract_processing',
            is_active=True,
            sort_order=1
        )
        
        assert ct.type_code == 'SALES'
        assert ct.type_name == '销售合同'
        assert ct.is_active is True
        assert ct.id is None  # 新创建的没有 ID
    
    def test_create_with_defaults(self):
        """测试使用默认值创建"""
        ct = ContractType(
            type_code='TEST',
            type_name='测试'
        )
        
        assert ct.is_active is True
        assert ct.sort_order == 0
        assert ct.description is None
    
    def test_to_dict(self):
        """测试转换为字典"""
        ct = ContractType(
            type_code='SALES',
            type_name='销售合同',
            id=1
        )
        
        result = ct.to_dict()
        
        assert isinstance(result, dict)
        assert result['id'] == 1
        assert result['type_code'] == 'SALES'
        assert result['type_name'] == '销售合同'
        assert 'created_at' in result
    
    def test_to_dict_with_datetime(self):
        """测试包含日期时间的字典转换"""
        now = datetime.now()
        ct = ContractType(
            type_code='SALES',
            type_name='销售合同',
            created_at=now
        )
        
        result = ct.to_dict()
        
        assert result['created_at'] == now.isoformat()
    
    def test_repr(self):
        """测试字符串表示"""
        ct = ContractType(
            type_code='SALES',
            type_name='销售合同',
            id=1
        )
        
        repr_str = repr(ct)
        
        assert 'ContractType' in repr_str
        assert 'SALES' in repr_str
        assert '销售合同' in repr_str
    
    def test_from_db_row(self):
        """测试从数据库行创建实例"""
        row = (
            1,                                  # id
            'SALES',                           # type_code
            '销售合同',                         # type_name
            '商品销售合同',                     # description
            'standard_contract_processing',    # default_workflow
            True,                              # is_active
            1,                                 # sort_order
            datetime(2025, 12, 4, 10, 0, 0),  # created_at
            datetime(2025, 12, 4, 10, 0, 0),  # updated_at
        )
        
        ct = ContractType.from_db_row(row)
        
        assert ct.id == 1
        assert ct.type_code == 'SALES'
        assert ct.type_name == '销售合同'
        assert ct.description == '商品销售合同'
        assert ct.is_active is True
    
    def test_from_db_row_partial(self):
        """测试从部分数据库行创建实例"""
        row = (1, 'SALES', '销售合同')
        
        ct = ContractType.from_db_row(row)
        
        assert ct.id == 1
        assert ct.type_code == 'SALES'
        assert ct.type_name == '销售合同'
        assert ct.description is None


# ============================================
# DefaultWorkflow 枚举测试
# ============================================
class TestDefaultWorkflow:
    """测试工作流枚举"""
    
    def test_workflow_values(self):
        """测试工作流枚举值"""
        assert DefaultWorkflow.STANDARD.value == 'standard_contract_processing'
        assert DefaultWorkflow.QUICK.value == 'quick_approval'
        assert DefaultWorkflow.STRICT.value == 'strict_approval'
    
    def test_workflow_is_string(self):
        """测试工作流枚举是字符串类型"""
        assert isinstance(DefaultWorkflow.STANDARD, str)
        assert isinstance(DefaultWorkflow.QUICK, str)


# ============================================
# ContractTypeDAO 测试（需要数据库连接）
# ============================================
class TestContractTypeDAO:
    """测试 ContractTypeDAO 数据访问对象"""
    
    def test_get_all(self, db_transaction):
        """测试获取所有合同类型"""
        dao = ContractTypeDAO(db_transaction, auto_commit=False)
        
        types = dao.get_all(active_only=True)
        
        assert isinstance(types, list)
        assert len(types) > 0
        assert all(isinstance(t, ContractType) for t in types)
        assert all(t.is_active for t in types)
    
    def test_get_all_including_inactive(self, db_transaction):
        """测试获取所有合同类型（包括未启用的）"""
        dao = ContractTypeDAO(db_transaction, auto_commit=False)
        
        active_types = dao.get_all(active_only=True)
        all_types = dao.get_all(active_only=False)
        
        assert len(all_types) >= len(active_types)
    
    def test_get_by_code(self, db_transaction):
        """测试根据代码获取合同类型"""
        dao = ContractTypeDAO(db_transaction, auto_commit=False)
        
        sales = dao.get_by_code('SALES')
        
        assert sales is not None
        assert sales.type_code == 'SALES'
        assert sales.type_name == '销售合同'
        assert sales.id is not None
    
    def test_get_by_code_not_exists(self, db_transaction):
        """测试获取不存在的合同类型"""
        dao = ContractTypeDAO(db_transaction, auto_commit=False)
        
        result = dao.get_by_code('NOT_EXISTS')
        
        assert result is None
    
    def test_get_by_id(self, db_transaction):
        """测试根据ID获取合同类型"""
        dao = ContractTypeDAO(db_transaction, auto_commit=False)
        
        # 先获取一个已存在的类型
        sales = dao.get_by_code('SALES')
        assert sales is not None
        assert sales.id is not None
        
        # 通过ID再次获取
        result = dao.get_by_id(sales.id)
        
        assert result is not None
        assert result.id == sales.id
        assert result.type_code == sales.type_code
    
    def test_create(self, db_transaction, sample_contract_type):
        """测试创建新的合同类型"""
        dao = ContractTypeDAO(db_transaction, auto_commit=False)
        
        created = dao.create(sample_contract_type)
        
        assert created.id is not None
        assert created.type_code == sample_contract_type.type_code
        assert created.created_at is not None
        assert created.updated_at is not None
        
        # 验证可以查询到
        found = dao.get_by_code(created.type_code)
        assert found is not None
        assert found.id == created.id
    
    def test_update(self, db_transaction, sample_contract_type):
        """测试更新合同类型"""
        dao = ContractTypeDAO(db_transaction, auto_commit=False)
        
        # 先创建
        created = dao.create(sample_contract_type)
        
        # 修改
        created.type_name = '更新后的名称'
        created.description = '更新后的描述'
        
        # 更新
        success = dao.update(created)
        
        assert success is True
        assert created.id is not None
        
        # 验证更新成功
        updated = dao.get_by_id(created.id)
        assert updated is not None
        assert updated.type_name == '更新后的名称'
        assert updated.description == '更新后的描述'
    
    def test_update_without_id(self, sample_contract_type):
        """测试更新没有ID的对象（应该失败）"""
        dao = ContractTypeDAO(None)  # 不需要实际连接
        
        with pytest.raises(ValueError, match="Contract type ID is required"):
            dao.update(sample_contract_type)
    
    def test_deactivate(self, db_transaction, sample_contract_type):
        """测试停用合同类型（软删除）"""
        dao = ContractTypeDAO(db_transaction, auto_commit=False)
        
        # 先创建
        created = dao.create(sample_contract_type)
        assert created.is_active is True
        assert created.id is not None
        
        # 停用
        success = dao.deactivate(created.id)
        
        assert success is True
        
        # 验证已停用
        deactivated = dao.get_by_id(created.id)
        assert deactivated is not None
        assert deactivated.is_active is False
        
        # 验证在 active_only=True 时查询不到
        active_types = dao.get_all(active_only=True)
        assert created.id not in [t.id for t in active_types]
    
    def test_delete(self, db_transaction, sample_contract_type):
        """测试删除合同类型（物理删除）"""
        dao = ContractTypeDAO(db_transaction, auto_commit=False)
        
        # 先创建
        created = dao.create(sample_contract_type)
        assert created.id is not None
        created_id = created.id
        
        # 删除
        success = dao.delete(created_id)
        
        assert success is True
        
        # 验证已删除
        deleted = dao.get_by_id(created_id)
        assert deleted is None
    
    def test_delete_not_exists(self, db_transaction):
        """测试删除不存在的记录"""
        dao = ContractTypeDAO(db_transaction, auto_commit=False)
        
        success = dao.delete(99999)  # 不存在的ID
        
        assert success is False


# ============================================
# 集成测试（完整流程）
# ============================================
class TestContractTypeIntegration:
    """集成测试：完整的 CRUD 流程"""
    
    def test_full_crud_workflow(self, db_transaction):
        """测试完整的 CRUD 工作流"""
        dao = ContractTypeDAO(db_transaction, auto_commit=False)
        
        # 1. 创建
        new_type = ContractType(
            type_code='INTEGRATION_TEST',
            type_name='集成测试类型',
            description='用于集成测试',
            default_workflow='quick_approval',
            sort_order=888
        )
        
        created = dao.create(new_type)
        assert created.id is not None
        
        # 2. 读取
        found = dao.get_by_code('INTEGRATION_TEST')
        assert found is not None
        assert found.type_name == '集成测试类型'
        assert found.id is not None
        
        # 3. 更新
        found.type_name = '更新后的集成测试类型'
        dao.update(found)
        
        updated = dao.get_by_id(found.id)
        assert updated is not None
        assert updated.type_name == '更新后的集成测试类型'
        
        # 4. 停用
        dao.deactivate(found.id)
        
        deactivated = dao.get_by_id(found.id)
        assert deactivated is not None
        assert deactivated.is_active is False
        
        # 5. 删除
        dao.delete(found.id)
        
        deleted = dao.get_by_id(found.id)
        assert deleted is None
    
    def test_sorting_and_filtering(self, db_transaction):
        """测试排序和过滤"""
        dao = ContractTypeDAO(db_transaction, auto_commit=False)
        
        # 创建多个测试类型
        for i in range(3):
            ct = ContractType(
                type_code=f'SORT_TEST_{i}',
                type_name=f'排序测试 {i}',
                sort_order=i * 10,
                is_active=(i != 1)  # 中间的一个设为不启用
            )
            dao.create(ct)
        
        # 测试排序
        all_types = dao.get_all(active_only=False)
        test_types = [t for t in all_types if t.type_code.startswith('SORT_TEST_')]
        
        assert len(test_types) == 3
        
        # 测试过滤
        active_types = dao.get_all(active_only=True)
        active_test_types = [t for t in active_types if t.type_code.startswith('SORT_TEST_')]
        
        assert len(active_test_types) == 2  # 只有2个启用的


# ============================================
# 性能测试（可选）
# ============================================
class TestContractTypePerformance:
    """性能测试"""
    
    def test_batch_query_performance(self, db_transaction):
        """测试批量查询性能"""
        import time
        
        dao = ContractTypeDAO(db_transaction, auto_commit=False)
        
        start_time = time.time()
        
        # 执行100次查询
        for _ in range(100):
            dao.get_all(active_only=True)
        
        elapsed_time = time.time() - start_time
        
        # 100次查询应该在1秒内完成
        assert elapsed_time < 1.0, f"查询太慢: {elapsed_time:.2f}秒"


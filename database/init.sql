-- 智能合同处理系统 - 数据库初始化脚本
-- 创建时间: 2025-12-04
-- 说明: 合同类型表（字典表）

-- ============================================
-- 合同类型表
-- ============================================
CREATE TABLE IF NOT EXISTS contract_types (
    id SERIAL PRIMARY KEY,
    type_code VARCHAR(50) UNIQUE NOT NULL,
    type_name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- 关联的工作流
    default_workflow VARCHAR(100),
    
    -- 是否启用
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 排序
    sort_order INTEGER DEFAULT 0,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_contract_types_code ON contract_types(type_code);
CREATE INDEX IF NOT EXISTS idx_contract_types_active ON contract_types(is_active);

-- ============================================
-- 插入常见合同类型
-- ============================================
INSERT INTO contract_types (type_code, type_name, description, default_workflow, sort_order) VALUES
    ('SALES', '销售合同', '商品销售相关的合同', 'standard_contract_processing', 1),
    ('PURCHASE', '采购合同', '商品采购相关的合同', 'standard_contract_processing', 2),
    ('SERVICE', '服务合同', '服务提供相关的合同', 'quick_approval', 3),
    ('LEASE', '租赁合同', '房屋、设备等租赁合同', 'standard_contract_processing', 4),
    ('EMPLOYMENT', '劳动合同', '员工雇佣合同', 'strict_approval', 5),
    ('PARTNERSHIP', '合作协议', '企业间合作协议', 'strict_approval', 6),
    ('NDA', '保密协议', '保密协议/NDA', 'quick_approval', 7),
    ('OTHER', '其他', '其他类型合同', 'standard_contract_processing', 99)
ON CONFLICT (type_code) DO NOTHING;

-- ============================================
-- 完成提示
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '==============================================';
    RAISE NOTICE '✅ 数据库初始化完成！';
    RAISE NOTICE '📊 已创建 contract_types 表';
    RAISE NOTICE '📝 已插入 8 种合同类型';
    RAISE NOTICE '🚀 可以开始开发了！';
    RAISE NOTICE '==============================================';
END $$;

"""
合规规则检查工具使用示例

运行方式：
    python -m backend.utils.langdock.compliance_example
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import asyncio
from backend.utils.langdock import get_registry
from backend.utils.langdock.initialize import initialize_default_tools


async def example_signing_subject_compliance():
    """规则1：签署主体合规校验示例"""
    print("=== 规则1：签署主体合规校验 ===\n")
    
    registry = get_registry()
    tool = registry.get("signing_subject_compliance")
    
    if not tool:
        print("签署主体合规校验工具未注册")
        return
    
    # 测试用例1：企业主体（合规）
    contract_text1 = """
    甲方：XX有限公司
    统一社会信用代码：91110000MA01234567
    乙方：张三
    身份证号：110101199001011234
    
    本合同由甲方和乙方签订...
    """
    
    result = await tool.run({"contract_text": contract_text1})
    
    if result.success:
        print("测试用例1 - 企业主体（合规）:")
        print(f"合规状态: {result.data.get('compliance_status')}")
        print(f"风险等级: {result.data.get('risk_level')}")
        print(f"签署方: {result.data.get('parties')}")
        if result.data.get('violations'):
            print(f"违规项: {result.data.get('violations')}")
        print()
    
    # 测试用例2：企业主体缺少信用代码（违规）
    contract_text2 = """
    甲方：YY科技公司
    乙方：李四
    
    本合同由甲方和乙方签订...
    """
    
    result = await tool.run({"contract_text": contract_text2})
    
    if result.success:
        print("测试用例2 - 企业主体缺少信用代码（违规）:")
        print(f"合规状态: {result.data.get('compliance_status')}")
        print(f"风险等级: {result.data.get('risk_level')}")
        if result.data.get('violations'):
            for violation in result.data.get('violations', []):
                print(f"  - {violation.get('type')}: {violation.get('description')}")
                print(f"    建议: {violation.get('suggestion')}")
        print()


async def example_core_clauses_completeness():
    """规则2：核心条款完整性校验示例"""
    print("=== 规则2：核心条款完整性校验 ===\n")
    
    registry = get_registry()
    tool = registry.get("core_clauses_completeness")
    
    if not tool:
        print("核心条款完整性校验工具未注册")
        return
    
    # 测试用例1：完整条款（合规）
    contract_text1 = """
    合同标的：XX型号设备，数量10台
    合同价款：人民币100万元
    履行期限：2025年1月1日至2025年12月31日
    违约责任：逾期付款按日0.05%支付违约金
    """
    
    result = await tool.run({"contract_text": contract_text1})
    
    if result.success:
        print("测试用例1 - 完整条款（合规）:")
        print(f"合规状态: {result.data.get('compliance_status')}")
        print(f"风险等级: {result.data.get('risk_level')}")
        print(f"必备条款检查:")
        for clause, status in result.data.get('required_clauses', {}).items():
            print(f"  - {clause}: {status}")
        print()
    
    # 测试用例2：缺失核心条款（违规）
    contract_text2 = """
    合同标的：XX型号设备
    合同价款：人民币100万元
    （缺少履行期限和违约责任）
    """
    
    result = await tool.run({"contract_text": contract_text2})
    
    if result.success:
        print("测试用例2 - 缺失核心条款（违规）:")
        print(f"合规状态: {result.data.get('compliance_status')}")
        print(f"风险等级: {result.data.get('risk_level')}")
        print(f"缺失条款: {result.data.get('missing_clauses')}")
        print(f"缺失核心条款: {result.data.get('missing_core_clauses')}")
        print(f"后续行动: {result.data.get('next_action')}")
        print()


async def example_legal_conflict_compliance():
    """规则3：法规冲突校验示例"""
    print("=== 规则3：法规冲突校验 ===\n")
    
    registry = get_registry()
    tool = registry.get("legal_conflict_compliance")
    
    if not tool:
        print("法规冲突校验工具未注册")
        return
    
    # 测试用例1：违约金冲突
    contract_text1 = """
    合同总金额：人民币100万元
    违约金：如一方违约，需支付合同总金额的35%作为违约金
    """
    
    result = await tool.run({"contract_text": contract_text1})
    
    if result.success:
        print("测试用例1 - 违约金冲突:")
        print(f"合规状态: {result.data.get('compliance_status')}")
        print(f"风险等级: {result.data.get('risk_level')}")
        if result.data.get('conflicts'):
            for conflict in result.data.get('conflicts', []):
                print(f"  - {conflict.get('type')}: {conflict.get('description')}")
                print(f"    法规依据: {conflict.get('law_reference')}")
                print(f"    建议: {conflict.get('suggestion')}")
        print()
    
    # 测试用例2：争议解决方式冲突
    contract_text2 = """
    争议解决：双方发生争议时，可向仲裁委员会申请仲裁或向人民法院提起诉讼
    """
    
    result = await tool.run({"contract_text": contract_text2})
    
    if result.success:
        print("测试用例2 - 争议解决方式冲突:")
        print(f"合规状态: {result.data.get('compliance_status')}")
        print(f"风险等级: {result.data.get('risk_level')}")
        if result.data.get('conflicts'):
            for conflict in result.data.get('conflicts', []):
                print(f"  - {conflict.get('type')}: {conflict.get('description')}")
                print(f"    法规依据: {conflict.get('law_reference')}")
                print(f"    建议: {conflict.get('suggestion')}")
        print()


async def example_full_compliance_check():
    """完整合规检查工作流示例"""
    print("=== 完整合规检查工作流 ===\n")
    
    registry = get_registry()
    
    # 模拟合同文本
    contract_text = """
    甲方：XX有限公司
    统一社会信用代码：91110000MA01234567
    乙方：张三
    身份证号：110101199001011234
    
    合同标的：XX型号设备，数量10台
    合同价款：人民币100万元
    履行期限：2025年1月1日至2025年12月31日
    违约责任：逾期付款按日0.05%支付违约金
    
    争议解决：双方发生争议时，可向仲裁委员会申请仲裁或向人民法院提起诉讼
    """
    
    print("执行完整合规检查...\n")
    
    # 1. 签署主体合规校验
    print("1. 签署主体合规校验:")
    tool1 = registry.get("signing_subject_compliance")
    if tool1:
        result1 = await tool1.run({"contract_text": contract_text})
        if result1.success:
            print(f"   状态: {result1.data.get('compliance_status')}")
            print(f"   风险: {result1.data.get('risk_level')}")
    print()
    
    # 2. 核心条款完整性校验
    print("2. 核心条款完整性校验:")
    tool2 = registry.get("core_clauses_completeness")
    if tool2:
        result2 = await tool2.run({"contract_text": contract_text})
        if result2.success:
            print(f"   状态: {result2.data.get('compliance_status')}")
            print(f"   风险: {result2.data.get('risk_level')}")
            print(f"   缺失条款: {result2.data.get('missing_clauses')}")
    print()
    
    # 3. 法规冲突校验
    print("3. 法规冲突校验:")
    tool3 = registry.get("legal_conflict_compliance")
    if tool3:
        result3 = await tool3.run({"contract_text": contract_text})
        if result3.success:
            print(f"   状态: {result3.data.get('compliance_status')}")
            print(f"   风险: {result3.data.get('risk_level')}")
            if result3.data.get('conflicts'):
                print(f"   冲突数量: {len(result3.data.get('conflicts', []))}")
    print()


if __name__ == "__main__":
    # 初始化工具
    initialize_default_tools()
    
    print("=" * 50)
    print("合规规则检查工具使用示例")
    print("=" * 50)
    print()
    
    # 运行示例
    asyncio.run(example_signing_subject_compliance())
    asyncio.run(example_core_clauses_completeness())
    asyncio.run(example_legal_conflict_compliance())
    # asyncio.run(example_full_compliance_check())


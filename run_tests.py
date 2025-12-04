#!/usr/bin/env python
"""
测试运行脚本
提供便捷的测试命令
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd: list[str], description: str):
    """运行命令并显示结果"""
    print(f"\n{'='*70}")
    print(f"🚀 {description}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode != 0:
        print(f"\n❌ {description} 失败")
        sys.exit(1)
    else:
        print(f"\n✅ {description} 成功")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════════════╗
║  Contract Forge - 测试运行器                                  ║
╚══════════════════════════════════════════════════════════════╝

使用方法:
    python run_tests.py <command>

可用命令:
    all             - 运行所有测试
    unit            - 只运行单元测试
    integration     - 只运行集成测试
    coverage        - 运行测试并生成覆盖率报告
    model           - 只测试模型层
    quick           - 快速测试（跳过慢速测试）
    watch           - 监视模式（文件变化时自动运行）
    
示例:
    python run_tests.py all
    python run_tests.py coverage
    python run_tests.py model

或直接使用 pytest:
    pytest                                    # 运行所有测试
    pytest tests/unit/                        # 运行单元测试
    pytest -k "contract_type"                 # 运行特定测试
    pytest --cov=models --cov-report=html     # 覆盖率报告
        """)
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    # 命令映射
    commands = {
        'all': (
            ['pytest', '-v'],
            "运行所有测试"
        ),
        'unit': (
            ['pytest', '-v', 'tests/unit/'],
            "运行单元测试"
        ),
        'integration': (
            ['pytest', '-v', 'tests/integration/'],
            "运行集成测试"
        ),
        'coverage': (
            ['pytest', '--cov=models', '--cov=utils',
             '--cov-report=html', '--cov-report=term-missing'],
            "生成测试覆盖率报告"
        ),
        'model': (
            ['pytest', '-v', 'tests/unit/models/'],
            "测试模型层"
        ),
        'quick': (
            ['pytest', '-v', '-m', 'not slow'],
            "快速测试（跳过慢速测试）"
        ),
        'watch': (
            ['pytest-watch', '--', '-v'],
            "监视模式"
        ),
    }
    
    if command not in commands:
        print(f"❌ 未知命令: {command}")
        print("运行 'python run_tests.py' 查看帮助")
        sys.exit(1)
    
    cmd, description = commands[command]
    run_command(cmd, description)
    
    # 如果是覆盖率报告，提示打开报告
    if command == 'coverage':
        print("\n" + "="*70)
        print("📊 覆盖率报告已生成")
        print("="*70)
        print("\n查看报告:")
        print("  HTML: htmlcov/index.html")
        print("  终端: 上方已显示")


if __name__ == "__main__":
    main()


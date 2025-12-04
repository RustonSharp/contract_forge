"""
测试 API 响应格式
验证所有响应都符合统一的格式
"""

import requests

BASE_URL = "http://localhost:8001"


def test_success_response():
    """测试成功响应的格式"""
    print("\n1️⃣  测试成功响应格式:")
    print("-" * 70)
    
    response = requests.get(f"{BASE_URL}/api/contract-type/all")
    data = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {data}")
    
    # 验证格式
    assert "success" in data, "❌ 缺少 'success' 字段"
    assert data["success"] is True, "❌ success 应该是 True"
    assert "data" in data, "❌ 缺少 'data' 字段"
    assert isinstance(data["data"], list), "❌ data 应该是列表"
    
    print("✅ 成功响应格式正确")


def test_404_response():
    """测试 404 错误响应的格式"""
    print("\n2️⃣  测试 404 错误响应格式:")
    print("-" * 70)
    
    response = requests.get(f"{BASE_URL}/api/contract-type/NOT_EXISTS")
    data = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {data}")
    
    # 验证格式
    assert response.status_code == 404, "❌ 状态码应该是 404"
    assert "success" in data, "❌ 缺少 'success' 字段"
    assert data["success"] is False, "❌ success 应该是 False"
    assert "error" in data, "❌ 缺少 'error' 字段"
    assert "NOT_EXISTS" in data["error"], "❌ error 消息应包含类型代码"
    
    print("✅ 404 响应格式正确")
    print(f"   错误信息: {data['error']}")


def test_400_response():
    """测试 400 错误响应的格式（重复创建）"""
    print("\n3️⃣  测试 400 错误响应格式:")
    print("-" * 70)
    
    # 尝试创建已存在的类型
    response = requests.post(
        f"{BASE_URL}/api/contract-type/",
        json={
            "type_code": "SALES",  # 已存在的类型
            "type_name": "测试",
        }
    )
    data = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {data}")
    
    # 验证格式
    assert response.status_code == 400, "❌ 状态码应该是 400"
    assert "success" in data, "❌ 缺少 'success' 字段"
    assert data["success"] is False, "❌ success 应该是 False"
    assert "error" in data, "❌ 缺少 'error' 字段"
    assert "already exists" in data["error"], "❌ error 消息应提示已存在"
    
    print("✅ 400 响应格式正确")
    print(f"   错误信息: {data['error']}")


def test_500_response():
    """测试 500 错误响应的格式"""
    print("\n4️⃣  测试 500 错误响应格式:")
    print("-" * 70)
    print("   (需要后端模拟错误，跳过此测试)")
    # 实际测试需要在后端代码中触发异常


def test_response_format_consistency():
    """测试所有端点的响应格式一致性"""
    print("\n5️⃣  测试响应格式一致性:")
    print("-" * 70)
    
    endpoints = [
        ("GET", "/api/contract-type/all", None),
        ("GET", "/api/contract-type/SALES", None),
    ]
    
    for method, path, body in endpoints:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{path}")
        else:
            response = requests.post(f"{BASE_URL}{path}", json=body)
        
        data = response.json()
        
        # 所有响应都应该有 success 字段
        assert "success" in data, f"❌ {path} 缺少 'success' 字段"
        
        if data["success"]:
            assert "data" in data, f"❌ {path} 成功响应缺少 'data' 字段"
        else:
            assert "error" in data, f"❌ {path} 失败响应缺少 'error' 字段"
        
        print(f"   ✅ {method} {path} - 格式正确")


if __name__ == "__main__":
    print("=" * 70)
    print("API 响应格式测试")
    print("=" * 70)
    print("⚠️  请确保后端已启动: python main.py")
    print("=" * 70)
    
    try:
        # 测试连接
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ 后端服务器连接成功\n")
        else:
            print("⚠️  后端服务器响应异常\n")
    except Exception as e:
        print(f"❌ 无法连接到后端服务器: {e}")
        print("   请先启动后端: python main.py")
        exit(1)
    
    try:
        # 运行测试
        test_success_response()
        test_404_response()
        test_400_response()
        test_500_response()
        test_response_format_consistency()
        
        print("\n" + "=" * 70)
        print("✅ 所有测试通过！")
        print("=" * 70)
        print("\n前端现在可以正确处理所有响应格式 🎉\n")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}\n")
        exit(1)
    except Exception as e:
        print(f"\n❌ 测试错误: {e}\n")
        exit(1)


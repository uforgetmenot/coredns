#!/usr/bin/env python3
"""
OAuth2 认证功能测试脚本
测试与外部认证服务的集成
"""

import requests
import sys


def test_oauth2_server():
    """测试 OAuth2 服务器是否可访问"""
    print("=" * 60)
    print("测试 OAuth2 服务器连接")
    print("=" * 60)

    server_url = "http://core.seadee.com.cn:8099"

    try:
        response = requests.get(f"{server_url}/docs", timeout=5)
        if response.status_code == 200:
            print(f"✅ OAuth2 服务器可访问: {server_url}")
            return True
        else:
            print(f"❌ OAuth2 服务器返回状态码: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ 无法连接到 OAuth2 服务器: {e}")
        return False


def test_login():
    """测试登录功能"""
    print("\n" + "=" * 60)
    print("测试登录流程")
    print("=" * 60)

    server_url = "http://core.seadee.com.cn:8099"

    # 步骤 1: 获取 Token
    print("\n步骤 1: 使用密码模式获取 Token")
    token_url = f"{server_url}/auth/token"
    # OAuth2 标准使用 form-urlencoded 格式
    login_data = {
        "username": "admin",
        "password": "Admin123",
        "grant_type": "password"
    }

    try:
        response = requests.post(token_url, data=login_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False

        token_data = response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        print(f"✅ 登录成功!")
        print(f"   Access Token (前50字符): {access_token[:50]}...")
        print(f"   Refresh Token (前50字符): {refresh_token[:50]}...")

        # 步骤 2: 获取用户信息
        print("\n步骤 2: 获取用户信息")
        userinfo_url = f"{server_url}/auth/me"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(userinfo_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ 获取用户信息失败: {response.status_code}")
            return False

        user_info = response.json()
        print(f"✅ 成功获取用户信息:")
        print(f"   用户名: {user_info.get('username')}")
        print(f"   全名: {user_info.get('full_name')}")
        print(f"   是否超级用户: {user_info.get('is_superuser')}")
        print(f"   是否激活: {user_info.get('is_active')}")

        if not user_info.get("is_superuser"):
            print("⚠️  警告: 该用户不是超级用户，将无法登录 CoreDNS Manager")

        # 步骤 3: 刷新 Token
        print("\n步骤 3: 刷新 Token")
        refresh_url = f"{server_url}/auth/refresh"
        # OAuth2 标准使用 form-urlencoded 格式
        refresh_data = {"refresh_token": refresh_token}

        response = requests.post(refresh_url, data=refresh_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ 刷新 Token 失败: {response.status_code}")
            return False

        new_token_data = response.json()
        new_access_token = new_token_data.get("access_token")
        print(f"✅ Token 刷新成功!")
        print(f"   New Access Token (前50字符): {new_access_token[:50]}...")

        return True

    except requests.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False


def test_local_app():
    """测试本地应用的 API 端点"""
    print("\n" + "=" * 60)
    print("测试本地应用 API")
    print("=" * 60)

    app_url = "http://localhost:8000"

    try:
        # 测试健康检查
        print("\n测试健康检查端点")
        response = requests.get(f"{app_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ 应用健康检查通过: {response.json()}")
        else:
            print(f"❌ 应用健康检查失败: {response.status_code}")
            return False

        # 测试登录 API
        print("\n测试登录 API")
        login_data = {
            "username": "admin",
            "password": "Admin123"
        }
        response = requests.post(f"{app_url}/api/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ 登录 API 测试成功")
                print(f"   用户: {result.get('user', {}).get('username')}")
                return True
            else:
                print(f"❌ 登录失败: {result.get('message')}")
                return False
        else:
            print(f"❌ 登录 API 返回状态码: {response.status_code}")
            return False

    except requests.RequestException as e:
        print(f"⚠️  本地应用未启动或无法访问: {e}")
        print("   提示: 运行 ./run.sh dev 启动应用")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("CoreDNS Manager - OAuth2 认证功能测试")
    print("=" * 60)

    # 测试 OAuth2 服务器
    if not test_oauth2_server():
        print("\n❌ OAuth2 服务器测试失败，请检查网络连接和服务器地址")
        sys.exit(1)

    # 测试登录流程
    if not test_login():
        print("\n❌ 登录流程测试失败")
        sys.exit(1)

    # 测试本地应用
    test_local_app()

    print("\n" + "=" * 60)
    print("✅ OAuth2 认证功能测试完成")
    print("=" * 60)
    print("\n提示:")
    print("1. 确保在 .env 文件中设置 OAUTH2_ENABLED=True")
    print("2. 运行 ./run.sh dev 启动应用")
    print("3. 访问 http://localhost:8000/login 进行登录")
    print("4. 查看 http://localhost:8000/docs 了解 API 文档")


if __name__ == "__main__":
    main()

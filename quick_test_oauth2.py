#!/usr/bin/env python3
"""
快速验证 OAuth2 认证是否正常工作
"""

import requests

def quick_test():
    """快速测试登录"""
    print("🔍 快速验证 OAuth2 认证...")

    url = "http://core.seadee.com.cn:8099/auth/token"

    # 使用正确的 form-urlencoded 格式
    data = {
        "username": "admin",
        "password": "Admin123",
        "grant_type": "password"
    }

    try:
        response = requests.post(url, data=data, timeout=10)

        if response.status_code == 200:
            token_data = response.json()
            print("✅ OAuth2 认证成功!")
            print(f"   Access Token: {token_data.get('access_token', '')[:50]}...")
            print(f"   Token Type: {token_data.get('token_type', 'bearer')}")
            return True
        else:
            print(f"❌ 认证失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    exit(0 if success else 1)

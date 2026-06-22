"""API端点全面测试"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestAuthEndpoints:
    """认证端点测试"""

    def test_login_success(self):
        """测试登录成功"""
        response = client.post(
            "/api/auth/login",
            json={"username": "test_user", "password": "correct_password"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_failure(self):
        """测试登录失败"""
        response = client.post(
            "/api/auth/login",
            json={"username": "test_user", "password": "wrong_password"},
        )
        assert response.status_code == 401

    def test_token_refresh(self):
        """测试Token刷新"""
        # 先登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "test_user", "password": "correct_password"},
        )
        token = login_resp.json()["access_token"]

        # 刷新token
        refresh_resp = client.post(
            "/api/auth/refresh", headers={"Authorization": f"Bearer {token}"}
        )
        assert refresh_resp.status_code == 200
        assert "new_token" in refresh_resp.json()


class TestRuoxiStateEndpoints:
    """若曦状态端点测试"""

    def test_get_biological_state(self):
        """获取生物状态"""
        response = client.get("/api/state/biological")
        assert response.status_code == 200
        data = response.json()
        assert "hormones" in data
        assert "heart_rate" in data
        assert "circadian_phase" in data

    def test_get_emotional_state(self):
        """获取情感状态"""
        response = client.get("/api/state/emotional")
        assert response.status_code == 200
        data = response.json()
        assert "attachment_level" in data
        assert "trust_index" in data
        assert "current_mood" in data

    def test_get_memory_summary(self):
        """获取记忆摘要"""
        response = client.get("/api/memory/summary")
        assert response.status_code == 200
        data = response.json()
        assert "memory_count" in data
        assert "emotional_highlights" in data


class TestChatEndpoints:
    """聊天端点测试"""

    def test_send_message(self):
        """测试发送消息"""
        response = client.post(
            "/api/chat", json={"message": "你好，若曦", "context": {}}
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "response_time_ms" in data
        assert data["response_time_ms"] < 100

    def test_get_chat_history(self):
        """获取聊天历史"""
        response = client.get("/api/chat/history?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

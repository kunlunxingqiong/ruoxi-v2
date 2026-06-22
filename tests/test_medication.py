"""
🌸 若曦V2 - 用药管理API测试
"""

from datetime import date, datetime, time

import pytest


class TestMedicationAPI:
    """用药API测试"""

    def test_create_medication_success(self, client, auth_headers):
        """测试成功创建用药"""
        response = client.post(
            "/api/v1/medications",
            headers=auth_headers,
            json={
                "name": "降压药",
                "dosage": "5mg",
                "frequency": "daily",
                "purpose": "高血压",
                "reminder_time": "08:00:00",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "降压药"
        assert data["data"]["is_active"] is True

    def test_create_medication_missing_name(self, client, auth_headers):
        """测试缺少药名"""
        response = client.post(
            "/api/v1/medications",
            headers=auth_headers,
            json={"dosage": "5mg", "frequency": "daily"},
        )

        assert response.status_code == 422

    def test_get_medications_list(self, client, auth_headers, test_medication):
        """测试获取用药列表"""
        response = client.get("/api/v1/medications", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_medication_detail(self, client, auth_headers, test_medication):
        """测试获取用药详情"""
        response = client.get(
            f"/api/v1/medications/{test_medication.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_medication.id
        assert data["name"] == test_medication.name

    def test_update_medication(self, client, auth_headers, test_medication):
        """测试更新用药"""
        response = client.put(
            f"/api/v1/medications/{test_medication.id}",
            headers=auth_headers,
            json={"name": "更新后药名", "dosage": "10mg"},
        )

        assert response.status_code == 200
        data = response.json()
        # 验证更新生效
        get_response = client.get(
            f"/api/v1/medications/{test_medication.id}", headers=auth_headers
        )
        get_data = get_response.json()
        assert get_data["dosage"] == "10mg"

    def test_delete_medication(self, client, auth_headers, test_medication):
        """测试删除用药"""
        response = client.delete(
            f"/api/v1/medications/{test_medication.id}", headers=auth_headers
        )

        assert response.status_code == 200

        # 验证已删除
        get_response = client.get(
            f"/api/v1/medications/{test_medication.id}", headers=auth_headers
        )
        assert get_response.status_code == 404


class TestMedicationLogAPI:
    """用药记录API测试"""

    def test_log_medication_taken(self, client, auth_headers, test_medication):
        """测试记录服药"""
        response = client.post(
            f"/api/v1/medications/{test_medication.id}/logs",
            headers=auth_headers,
            json={"status": "taken", "note": "按时服用"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "taken"

    def test_log_medication_skipped(self, client, auth_headers, test_medication):
        """测试记录跳过服药"""
        response = client.post(
            f"/api/v1/medications/{test_medication.id}/logs",
            headers=auth_headers,
            json={"status": "skipped", "note": "忘记带药"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["status"] == "skipped"

    def test_get_medication_logs(self, client, auth_headers, test_medication):
        """测试获取用药记录"""
        # 先记录几次服药
        for _ in range(3):
            client.post(
                f"/api/v1/medications/{test_medication.id}/logs",
                headers=auth_headers,
                json={"status": "taken"},
            )

        response = client.get(
            f"/api/v1/medications/{test_medication.id}/logs", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3

    def test_get_medication_adherence(self, client, auth_headers, test_medication):
        """测试获取依从性统计"""
        # 记录服药
        client.post(
            f"/api/v1/medications/{test_medication.id}/logs",
            headers=auth_headers,
            json={"status": "taken"},
        )

        response = client.get(
            f"/api/v1/medications/{test_medication.id}/adherence", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "adherence_rate" in data["data"]


class TestMedicationScheduleAPI:
    """用药计划API测试"""

    def test_get_today_schedule(self, client, auth_headers, test_medication):
        """测试获取今日用药计划"""
        response = client.get(
            "/api/v1/medications/schedule/today", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_medication_reminders(self, client, auth_headers):
        """测试获取用药提醒"""
        response = client.get("/api/v1/medications/reminders", headers=auth_headers)

        assert response.status_code == 200
        # 可能为空列表或提醒列表
        assert isinstance(response.json(), list)


class TestMedicationInteractions:
    """药物相互作用API测试"""

    def test_check_interactions_success(self, client, auth_headers, test_medication):
        """测试检查药物相互作用"""
        # 创建第二个药物
        client.post(
            "/api/v1/medications",
            headers=auth_headers,
            json={"name": "感冒药", "dosage": "1片", "frequency": "daily"},
        )

        response = client.post(
            "/api/v1/medications/interactions/check",
            headers=auth_headers,
            json={"medication_names": ["降压药", "感冒药"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "interactions" in data


class TestMedicationSmartSuggestions:
    """智能建议API测试"""

    def test_get_smart_suggestions(self, client, auth_headers):
        """测试获取智能用药建议"""
        response = client.get(
            "/api/v1/medications/smart/suggestions", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "suggestions" in data

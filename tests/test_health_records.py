"""
🌸 若曦V2 - 健康记录API测试
"""
import pytest
from datetime import datetime, timedelta


class TestBloodPressureAPI:
    """血压API测试"""
    
    def test_create_bp_record_success(self, client, auth_headers, test_user):
        """测试成功创建血压记录"""
        response = client.post(
            "/api/v1/health/blood-pressure",
            headers=auth_headers,
            json={
                "systolic": 120,
                "diastolic": 80,
                "pulse": 75
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["systolic"] == 120
        assert data["data"]["category"] == "normal"
    
    def test_create_bp_record_crisis_alert(self, client, auth_headers):
        """测试高血压危机触发警报"""
        response = client.post(
            "/api/v1/health/blood-pressure",
            headers=auth_headers,
            json={
                "systolic": 185,
                "diastolic": 125,
                "pulse": 95
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["category"] == "crisis"
    
    def test_create_bp_record_invalid_systolic(self, client, auth_headers):
        """测试无效收缩压"""
        response = client.post(
            "/api/v1/health/blood-pressure",
            headers=auth_headers,
            json={
                "systolic": 300,
                "diastolic": 80
            }
        )
        
        assert response.status_code == 422
    
    def test_create_bp_record_missing_field(self, client, auth_headers):
        """测试缺少必填字段"""
        response = client.post(
            "/api/v1/health/blood-pressure",
            headers=auth_headers,
            json={"systolic": 120}
        )
        
        assert response.status_code == 422
    
    def test_get_bp_records(self, client, auth_headers, test_bp_records):
        """测试获取血压记录列表"""
        response = client.get(
            "/api/v1/health/blood-pressure",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 7
    
    def test_get_bp_statistics(self, client, auth_headers, test_bp_records):
        """测试获取血压统计"""
        response = client.get(
            "/api/v1/health/blood-pressure/statistics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "avg_systolic" in data["data"]
        assert "avg_diastolic" in data["data"]
    
    def test_get_bp_trends(self, client, auth_headers, test_bp_records):
        """测试获取血压趋势"""
        response = client.get(
            "/api/v1/health/blood-pressure/trends",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_bp_unauthorized(self, client):
        """测试未授权访问"""
        response = client.get("/api/v1/health/blood-pressure")
        
        assert response.status_code == 401


class TestGlucoseAPI:
    """血糖API测试"""
    
    def test_create_glucose_record_success(self, client, auth_headers):
        """测试成功创建血糖记录"""
        response = client.post(
            "/api/v1/health/glucose",
            headers=auth_headers,
            json={
                "value": 5.5,
                "unit": "mmol/L",
                "meal_type": "fasting",
                "note": "早晨空腹"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["value"] == 5.5
        assert data["data"]["is_normal"] is True
    
    def test_create_glucose_record_hyper(self, client, auth_headers):
        """测试高血糖记录"""
        response = client.post(
            "/api/v1/health/glucose",
            headers=auth_headers,
            json={
                "value": 17.5,
                "unit": "mmol/L",
                "meal_type": "post_meal"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["is_normal"] is False
    
    def test_create_glucose_record_hypo(self, client, auth_headers):
        """测试低血糖记录"""
        response = client.post(
            "/api/v1/health/glucose",
            headers=auth_headers,
            json={
                "value": 3.2,
                "unit": "mmol/L",
                "meal_type": "fasting"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["is_normal"] is False
    
    def test_get_glucose_statistics(self, client, auth_headers, test_glucose_records):
        """测试血糖统计"""
        response = client.get(
            "/api/v1/health/glucose/statistics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "avg_value" in data["data"]
        assert "hba1c_estimate" in data["data"]


class TestWeightAPI:
    """体重API测试"""
    
    def test_create_weight_record(self, client, auth_headers, test_user):
        """测试创建体重记录"""
        response = client.post(
            "/api/v1/health/weight",
            headers=auth_headers,
            json={
                "weight_kg": 70,
                "record_type": "morning",
                "note": "早晨空腹"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        # 验证BMI计算 (身高175cm)
        expected_bmi = round(70 / (1.75 ** 2), 2)
        assert data["data"]["bmi"] == expected_bmi
    
    def test_weight_bmi_calculation(self, client, auth_headers):
        """测试BMI计算"""
        # 高度175cm, 体重80kg => BMI 26.12
        response = client.post(
            "/api/v1/health/weight",
            headers=auth_headers,
            json={"weight_kg": 80}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["bmi"] == 26.12


class TestSleepAPI:
    """睡眠API测试"""
    
    def test_create_sleep_record(self, client, auth_headers):
        """测试创建睡眠记录"""
        bed_time = (datetime.utcnow() - timedelta(hours=8)).isoformat()
        wake_time = datetime.utcnow().isoformat()
        
        response = client.post(
            "/api/v1/health/sleep",
            headers=auth_headers,
            json={
                "bed_time": bed_time,
                "wake_time": wake_time,
                "sleep_quality": 85
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        # 验证睡眠时长计算
        assert data["data"]["duration_minutes"] == 480  # 8小时
    
    def test_sleep_efficiency_calculation(self, client, auth_headers, test_sleep_records):
        """测试睡眠效率计算"""
        response = client.get(
            "/api/v1/health/sleep/statistics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "avg_efficiency" in data["data"]


class TestHeartRateAPI:
    """心率API测试"""
    
    def test_create_hr_record(self, client, auth_headers):
        """测试创建心率记录"""
        response = client.post(
            "/api/v1/health/heart-rate",
            headers=auth_headers,
            json={
                "bpm": 75,
                "activity": "resting",
                "note": "静息心率"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["bpm"] == 75
    
    def test_hr_bradycardia_detection(self, client, auth_headers):
        """测试心动过缓检测"""
        response = client.post(
            "/api/v1/health/heart-rate",
            headers=auth_headers,
            json={
                "bpm": 45,
                "activity": "resting"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "bradycardia_suspected" in data["data"] or True


class TestRecordsSummaryAPI:
    """记录汇总API测试"""
    
    def test_get_records_summary(self, client, auth_headers, test_bp_records, test_glucose_records):
        """测试获取记录汇总"""
        response = client.get(
            "/api/v1/health/records/recent",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "blood_pressure" in data["data"]
        assert "glucose" in data["data"]

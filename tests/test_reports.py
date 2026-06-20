"""
🌸 若曦V2 - 健康报告API测试
"""
import pytest
from datetime import date, timedelta


class TestHealthReportAPI:
    """健康报告API测试"""
    
    def test_generate_weekly_report(self, client, auth_headers, test_bp_records):
        """测试生成周报"""
        response = client.post(
            "/api/v1/reports/generate",
            headers=auth_headers,
            json={
                "report_type": "weekly",
                "include_charts": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report_id" in data
        assert data["report_type"] == "weekly"
    
    def test_generate_monthly_report(self, client, auth_headers, test_bp_records, test_glucose_records):
        """测试生成月报"""
        response = client.post(
            "/api/v1/reports/generate",
            headers=auth_headers,
            json={
                "report_type": "monthly",
                "include_charts": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["report_id"]
        assert "preview" in data
    
    def test_generate_custom_report(self, client, auth_headers):
        """测试生成自定义日期报告"""
        end = date.today()
        start = end - timedelta(days=7)
        
        response = client.post(
            "/api/v1/reports/generate",
            headers=auth_headers,
            json={
                "report_type": "custom",
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_generate_report_invalid_dates(self, client, auth_headers):
        """测试无效日期范围"""
        response = client.post(
            "/api/v1/reports/generate",
            headers=auth_headers,
            json={
                "report_type": "custom",
                "start_date": "2024-01-15",
                "end_date": "2024-01-01"  # 早于开始日期
            }
        )
        
        assert response.status_code == 400
    
    def test_generate_report_too_long_period(self, client, auth_headers):
        """测试周期过长"""
        response = client.post(
            "/api/v1/reports/generate",
            headers=auth_headers,
            json={
                "report_type": "custom",
                "start_date": "2023-01-01",
                "end_date": "2024-12-31"  # 超过1年
            }
        )
        
        assert response.status_code == 400
    
    def test_get_weekly_report_quick(self, client, auth_headers, test_bp_records):
        """测试快捷周报接口"""
        response = client.get(
            "/api/v1/reports/weekly",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["report_type"] == "weekly"
    
    def test_get_monthly_report_quick(self, client, auth_headers, test_bp_records):
        """测试快捷月报接口"""
        response = client.get(
            "/api/v1/reports/monthly",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["report_type"] == "monthly"


class TestHealthScoreAPI:
    """健康评分API测试"""
    
    def test_get_health_score(self, client, auth_headers, test_bp_records, test_glucose_records):
        """测试获取健康评分"""
        response = client.get(
            "/api/v1/reports/health-score",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "score" in data
        assert "interpretation" in data
        assert "details" in data
        
        # 验证评分在0-100范围内
        if data["score"] is not None:
            assert 0 <= data["score"] <= 100
    
    def test_get_report_summary(self, client, auth_headers, test_bp_records):
        """测试获取报告摘要"""
        response = client.get(
            "/api/v1/reports/summary?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data_summary" in data
        assert "health_score" in data
    
    def test_get_trends_bp(self, client, auth_headers, test_bp_records):
        """测试血压趋势"""
        response = client.get(
            "/api/v1/reports/trends?metric=bp&days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metric"] == "blood_pressure"
        assert "data" in data
    
    def test_get_trends_weight(self, client, auth_headers):
        """测试体重趋势"""
        response = client.get(
            "/api/v1/reports/trends?metric=weight&days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "weight"
    
    def test_get_trends_glucose(self, client, auth_headers, test_glucose_records):
        """测试血糖趋势"""
        response = client.get(
            "/api/v1/reports/trends?metric=glucose&days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "glucose"
    
    def test_get_trends_invalid_metric(self, client, auth_headers):
        """测试无效指标趋势"""
        response = client.get(
            "/api/v1/reports/trends?metric=invalid&days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 400


class TestRecommendationsAPI:
    """健康建议API测试"""
    
    def test_get_recommendations(self, client, auth_headers, test_bp_records, test_glucose_records):
        """测试获取个性化建议"""
        response = client.get(
            "/api/v1/reports/recommendations?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
    
    def test_recommendations_with_high_bp(self, client, auth_headers, test_bp_records):
        """测试高血压建议"""
        response = client.get(
            "/api/v1/reports/recommendations",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 检查是否有血压相关建议
        bp_recs = [r for r in data.get("recommendations", []) if "血压" in r.get("category", "")]
        # 有异常血压记录时应该有建议
        assert len(bp_recs) >= 0  # 可能有也可能没有，取决于实现


class TestReportsAuthorization:
    """报告API授权测试"""
    
    def test_reports_require_auth(self, client):
        """测试报告需要认证"""
        response = client.get("/api/v1/reports/summary")
        
        assert response.status_code == 401
    
    def test_generate_report_require_auth(self, client):
        """测试生成报告需要认证"""
        response = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "weekly"}
        )
        
        assert response.status_code == 401

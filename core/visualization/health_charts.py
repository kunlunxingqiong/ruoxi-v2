"""
🌸 若曦V2 - 健康数据可视化
生成健康趋势图表
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class HealthChartGenerator:
    """
    健康图表生成器

    生成血压、血糖、睡眠等健康指标的可视化图表
    """

    def __init__(self, output_dir: str = "data/charts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_bp_chart_data(self, readings: List[Dict], days: int = 7) -> Dict:
        """
        生成血压图表数据

        Returns ECharts格式的数据
        """
        # 过滤最近N天的数据
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [
            r
            for r in readings
            if datetime.fromisoformat(r.get("timestamp", "2000-01-01")) > cutoff
        ]

        dates = []
        systolic_data = []
        diastolic_data = []

        for r in sorted(recent, key=lambda x: x.get("timestamp", "")):
            date_str = datetime.fromisoformat(r.get("timestamp")).strftime("%m-%d")

            dates.append(date_str)
            systolic_data.append(r.get("systolic", 0))
            diastolic_data.append(r.get("diastolic", 0))

        return {
            "title": {
                "text": "血压趋势",
                "left": "center",
                "textStyle": {"color": "#e34d75"},
            },
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["收缩压", "舒张压"], "bottom": 0},
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "15%",
                "containLabel": True,
            },
            "xAxis": {"type": "category", "boundaryGap": False, "data": dates},
            "yAxis": {"type": "value", "name": "mmHg", "min": 50, "max": 200},
            "series": [
                {
                    "name": "收缩压",
                    "type": "line",
                    "smooth": True,
                    "data": systolic_data,
                    "itemStyle": {"color": "#e34d75"},
                    "markLine": {
                        "data": [
                            {"yAxis": 120, "name": "正常上限"},
                            {"yAxis": 140, "name": "高血压界限"},
                        ]
                    },
                },
                {
                    "name": "舒张压",
                    "type": "line",
                    "smooth": True,
                    "data": diastolic_data,
                    "itemStyle": {"color": "#8b5cf6"},
                    "markLine": {
                        "data": [
                            {"yAxis": 80, "name": "正常上限"},
                            {"yAxis": 90, "name": "高血压界限"},
                        ]
                    },
                },
            ],
        }

    def generate_glucose_chart_data(self, readings: List[Dict], days: int = 7) -> Dict:
        """生成血糖图表数据"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [
            r
            for r in readings
            if datetime.fromisoformat(r.get("timestamp", "2000-01-01")) > cutoff
        ]

        dates = []
        values = []

        for r in sorted(recent, key=lambda x: x.get("timestamp", "")):
            date_str = datetime.fromisoformat(r.get("timestamp")).strftime("%m-%d")
            dates.append(date_str)
            values.append(r.get("value", 0))

        return {
            "title": {
                "text": "血糖趋势",
                "left": "center",
                "textStyle": {"color": "#e34d75"},
            },
            "tooltip": {"trigger": "axis"},
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "10%",
                "containLabel": True,
            },
            "xAxis": {"type": "category", "data": dates},
            "yAxis": {"type": "value", "name": "mmol/L", "min": 3, "max": 15},
            "series": [
                {
                    "name": "血糖",
                    "type": "line",
                    "smooth": True,
                    "areaStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0,
                            "y": 0,
                            "x2": 0,
                            "y2": 1,
                            "colorStops": [
                                {"offset": 0, "color": "rgba(227,77,117,0.3)"},
                                {"offset": 1, "color": "rgba(227,77,117,0.05)"},
                            ],
                        }
                    },
                    "data": values,
                    "itemStyle": {"color": "#e34d75"},
                    "markLine": {
                        "data": [
                            {"yAxis": 6.1, "name": "空腹正常上限"},
                            {"yAxis": 7.0, "name": "糖尿病诊断"},
                        ]
                    },
                }
            ],
        }

    def generate_sleep_chart_data(self, readings: List[Dict], days: int = 7) -> Dict:
        """生成睡眠图表数据"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [
            r
            for r in readings
            if datetime.fromisoformat(r.get("timestamp", "2000-01-01")) > cutoff
        ]

        dates = []
        durations = []
        efficiencies = []

        for r in sorted(recent, key=lambda x: x.get("timestamp", "")):
            date_str = datetime.fromisoformat(r.get("timestamp")).strftime("%m-%d")
            dates.append(date_str)
            durations.append(r.get("duration_hours", 0))
            efficiencies.append(r.get("efficiency", 0))

        return {
            "title": {
                "text": "睡眠分析",
                "left": "center",
                "textStyle": {"color": "#e34d75"},
            },
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["睡眠时长", "睡眠效率"], "bottom": 0},
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "15%",
                "containLabel": True,
            },
            "xAxis": {"type": "category", "data": dates},
            "yAxis": [
                {"type": "value", "name": "小时", "min": 0, "max": 12},
                {"type": "value", "name": "%", "min": 0, "max": 100},
            ],
            "series": [
                {
                    "name": "睡眠时长",
                    "type": "bar",
                    "data": durations,
                    "itemStyle": {"color": "#e34d75"},
                },
                {
                    "name": "睡眠效率",
                    "type": "line",
                    "yAxisIndex": 1,
                    "data": efficiencies,
                    "itemStyle": {"color": "#8b5cf6"},
                },
            ],
        }

    def generate_emotion_chart_data(self, emotion_summary: Dict[str, int]) -> Dict:
        """生成情绪分布图表"""
        emotions = {
            "开心": emotion_summary.get("happy", 0),
            "平静": emotion_summary.get("calm", 0),
            "疲惫": emotion_summary.get("tired", 0),
            "焦虑": emotion_summary.get("anxious", 0),
            "难过": emotion_summary.get("sad", 0),
            "生气": emotion_summary.get("angry", 0),
        }

        colors = {
            "开心": "#fbbf24",
            "平静": "#8b5cf6",
            "疲惫": "#6b7280",
            "焦虑": "#f59e0b",
            "难过": "#3b82f6",
            "生气": "#ef4444",
        }

        data = [
            {"value": v, "name": k, "itemStyle": {"color": colors[k]}}
            for k, v in emotions.items()
            if v > 0
        ]

        return {
            "title": {
                "text": "情绪分布",
                "left": "center",
                "textStyle": {"color": "#e34d75"},
            },
            "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
            "series": [
                {
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "avoidLabelOverlap": False,
                    "itemStyle": {
                        "borderRadius": 10,
                        "borderColor": "#fff",
                        "borderWidth": 2,
                    },
                    "label": {"show": True, "formatter": "{b}\n{c}次"},
                    "data": data,
                }
            ],
        }

    def generate_comprehensive_dashboard(
        self, health_data: Dict, emotion_data: Dict
    ) -> Dict:
        """生成综合健康仪表盘数据"""
        return {
            "bp_chart": self.generate_bp_chart_data(
                health_data.get("blood_pressure", []), days=7
            ),
            "glucose_chart": self.generate_glucose_chart_data(
                health_data.get("blood_glucose", []), days=7
            ),
            "sleep_chart": self.generate_sleep_chart_data(
                health_data.get("sleep", []), days=7
            ),
            "emotion_chart": self.generate_emotion_chart_data(
                emotion_data.get("emotion_summary", {})
            ),
            "summary": {
                "bp_avg": self._calc_avg(
                    health_data.get("blood_pressure", []), "systolic"
                ),
                "glucose_avg": self._calc_avg(
                    health_data.get("blood_glucose", []), "value"
                ),
                "sleep_avg": self._calc_avg(
                    health_data.get("sleep", []), "duration_hours"
                ),
                "emotion_dominant": (
                    max(
                        emotion_data.get("emotion_summary", {}).items(),
                        key=lambda x: x[1],
                    )[0]
                    if emotion_data.get("emotion_summary")
                    else "neutral"
                ),
            },
        }

    def _calc_avg(self, data: List[Dict], field: str) -> Optional[float]:
        """计算平均值"""
        if not data:
            return None
        values = [d.get(field, 0) for d in data if d.get(field)]
        if not values:
            return None
        return round(sum(values) / len(values), 1)

    def save_chart_data(self, chart_data: Dict, user_id: str, chart_type: str) -> str:
        """保存图表数据到文件"""
        filename = f"{user_id}_{chart_type}_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)

        return str(filepath)


# 全局图表生成器
chart_generator = HealthChartGenerator()

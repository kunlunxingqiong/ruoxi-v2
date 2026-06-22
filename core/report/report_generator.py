"""
🌸 若曦V2 - 报告生成器
生成PDF/HTML/Word健康报告
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional


class ReportFormat(Enum):
    """报告格式"""

    PDF = auto()
    HTML = auto()
    MARKDOWN = auto()
    JSON = auto()


class ReportPeriod(Enum):
    """报告周期"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class HealthReportData:
    """健康报告数据"""

    user_id: str
    period: ReportPeriod
    start_date: datetime
    end_date: datetime

    # 血压数据
    bp_avg_systolic: Optional[float] = None
    bp_avg_diastolic: Optional[float] = None
    bp_readings: List[Dict] = None
    bp_trend: str = "stable"  # rising, falling, stable

    # 血糖数据
    glucose_avg: Optional[float] = None
    glucose_readings: List[Dict] = None
    glucose_trend: str = "stable"

    # 睡眠数据
    sleep_avg_duration: Optional[float] = None  # hours
    sleep_efficiency: Optional[float] = None
    sleep_readings: List[Dict] = None

    # 情绪数据
    emotion_summary: Dict[str, int] = None
    emotion_trend: str = "stable"

    # AI分析
    ai_summary: str = ""
    ai_recommendations: List[str] = None
    ai_risk_factors: List[str] = None

    def __post_init__(self):
        if self.bp_readings is None:
            self.bp_readings = []
        if self.glucose_readings is None:
            self.glucose_readings = []
        if self.sleep_readings is None:
            self.sleep_readings = []
        if self.emotion_summary is None:
            self.emotion_summary = {}
        if self.ai_recommendations is None:
            self.ai_recommendations = []
        if self.ai_risk_factors is None:
            self.ai_risk_factors = []


class ReportGenerator:
    """
    报告生成器

    功能:
    - 多格式报告导出
    - 可视化图表
    - AI智能总结
    - 个性化建议
    """

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    async def generate_report(
        self,
        user_id: str,
        health_data: Dict,
        emotion_data: Dict,
        period: ReportPeriod,
        format: ReportFormat = ReportFormat.HTML,
    ) -> str:
        """生成报告"""

        # 解析数据
        report_data = await self._parse_health_data(
            user_id, health_data, emotion_data, period
        )

        # 生成AI总结
        await self._generate_ai_insights(report_data)

        # 根据格式生成
        if format == ReportFormat.HTML:
            return await self._generate_html(report_data)
        elif format == ReportFormat.MARKDOWN:
            return await self._generate_markdown(report_data)
        elif format == ReportFormat.JSON:
            return await self._generate_json(report_data)
        else:
            return await self._generate_html(report_data)  # 默认HTML

    async def _parse_health_data(
        self, user_id: str, health_data: Dict, emotion_data: Dict, period: ReportPeriod
    ) -> HealthReportData:
        """解析健康数据"""

        end_date = datetime.utcnow()

        if period == ReportPeriod.DAILY:
            start_date = end_date - timedelta(days=1)
        elif period == ReportPeriod.WEEKLY:
            start_date = end_date - timedelta(days=7)
        elif period == ReportPeriod.MONTHLY:
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)

        # 解析血压
        bp_readings = health_data.get("blood_pressure", [])
        bp_avg_sys = None
        bp_avg_dia = None
        if bp_readings:
            bp_avg_sys = sum(r.get("systolic", 0) for r in bp_readings) / len(
                bp_readings
            )
            bp_avg_dia = sum(r.get("diastolic", 0) for r in bp_readings) / len(
                bp_readings
            )

        # 解析血糖
        glucose_readings = health_data.get("blood_glucose", [])
        glucose_avg = None
        if glucose_readings:
            glucose_avg = sum(r.get("value", 0) for r in glucose_readings) / len(
                glucose_readings
            )

        # 解析睡眠
        sleep_readings = health_data.get("sleep", [])
        sleep_avg = None
        sleep_eff = None
        if sleep_readings:
            sleep_avg = sum(r.get("duration_hours", 0) for r in sleep_readings) / len(
                sleep_readings
            )
            sleep_eff = sum(r.get("efficiency", 0) for r in sleep_readings) / len(
                sleep_readings
            )

        # 解析情绪
        emotion_summary = emotion_data.get("emotion_summary", {})

        return HealthReportData(
            user_id=user_id,
            period=period,
            start_date=start_date,
            end_date=end_date,
            bp_avg_systolic=bp_avg_sys,
            bp_avg_diastolic=bp_avg_dia,
            bp_readings=bp_readings,
            glucose_avg=glucose_avg,
            glucose_readings=glucose_readings,
            sleep_avg_duration=sleep_avg,
            sleep_efficiency=sleep_eff,
            sleep_readings=sleep_readings,
            emotion_summary=emotion_summary,
        )

    async def _generate_ai_insights(self, data: HealthReportData):
        """生成AI洞察"""
        insights = []
        risks = []

        # 血压分析
        if data.bp_avg_systolic:
            if data.bp_avg_systolic >= 140:
                insights.append("平均血压偏高，建议关注")
                risks.append("高血压风险")
            elif data.bp_avg_systolic >= 120:
                insights.append("血压处于正常高值，注意监测")

        # 血糖分析
        if data.glucose_avg:
            if data.glucose_avg >= 6.1:
                insights.append("空腹血糖接近临界值")
                risks.append("血糖波动")

        # 睡眠分析
        if data.sleep_avg_duration:
            if data.sleep_avg_duration < 6:
                insights.append("睡眠时长不足，影响健康")
                risks.append("睡眠不足")
            elif data.sleep_avg_duration > 8.5:
                insights.append("睡眠充足，休息较好")

        # 情绪分析
        if data.emotion_summary:
            negative = data.emotion_summary.get("sad", 0) + data.emotion_summary.get(
                "anxious", 0
            )
            if negative > 3:
                insights.append("近期情绪波动较大，建议放松")

        data.ai_summary = "、".join(insights) if insights else "整体健康状况良好"
        data.ai_recommendations = self._generate_recommendations(data)
        data.ai_risk_factors = risks

    def _generate_recommendations(self, data: HealthReportData) -> List[str]:
        """生成建议"""
        recommendations = []

        if data.bp_avg_systolic and data.bp_avg_systolic >= 120:
            recommendations.extend(
                ["减少盐摄入，每天不超过6克", "每周运动150分钟", "监测血压，记录趋势"]
            )

        if data.sleep_avg_duration and data.sleep_avg_duration < 6:
            recommendations.extend(
                ["提前30分钟上床", "睡前避免使用电子设备", "尝试冥想或深呼吸"]
            )

        if not recommendations:
            recommendations = ["保持当前健康习惯", "定期体检，预防为主", "保持积极心态"]

        return recommendations

    async def _generate_html(self, data: HealthReportData) -> str:
        """生成HTML报告"""

        # 简单的HTML模板
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>若曦健康报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #fff5f7 0%, #f8f5ff 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 24px;
            box-shadow: 0 10px 40px rgba(227,77,117,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #e34d75 0%, #8b5cf6 100%);
            padding: 40px;
            text-align: center;
            color: white;
        }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .content {{ padding: 40px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{
            color: #e34d75;
            font-size: 1.5em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: #fff5f7;
            padding: 20px;
            border-radius: 16px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #e34d75;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
        .insight-box {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            padding: 20px;
            border-radius: 16px;
            margin: 20px 0;
        }}
        .recommendations {{
            list-style: none;
        }}
        .recommendations li {{
            padding: 10px 0;
            padding-left: 30px;
            position: relative;
        }}
        .recommendations li::before {{
            content: "💜";
            position: absolute;
            left: 0;
        }}
        .footer {{
            text-align: center;
            padding: 30px;
            color: #999;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌸 若曦健康报告</h1>
            <p>{data.start_date.strftime('%Y年%m月%d日')} - {data.end_date.strftime('%Y年%m月%d日')}</p>
        </div>
        
        <div class="content">
            <!-- AI摘要 -->
            <div class="section">
                <h2>💜 AI健康洞察</h2>
                <div class="insight-box">
                    <p>{data.ai_summary}</p>
                </div>
            </div>
            
            <!-- 健康指标 -->
            <div class="section">
                <h2>📊 健康指标</h2>
                <div class="metric-grid">
                    {self._render_bp_card(data)}
                    {self._render_glucose_card(data)}
                    {self._render_sleep_card(data)}
                </div>
            </div>
            
            <!-- 情绪概览 -->
            <div class="section">
                <h2>💕 情绪记录</h2>
                <p>记录次数: {sum(data.emotion_summary.values())} 次</p>
            </div>
            
            <!-- AI建议 -->
            <div class="section">
                <h2>🌟 健康建议</h2>
                <ul class="recommendations">
                    {"".join(f"<li>{r}</li>" for r in self._generate_recommendations(data))}
                </ul>
            </div>
            
            <!-- 生活方式 -->
            <div class="section">
                <h2>🏃 生活方式</h2>
                <p>运动记录: {len(data.exercise_records)} 次</p>
                <p>睡眠平均: {data.sleep_avg_duration:.1f} 小时/天</p>
            </div>
        </div>
        
        <div class="footer">
            <p>🌸 若曦健康助手 · {datetime.now().strftime("%Y年%m月%d日 %H:%M")} 生成</p>
            <p>本报告仅供参考，不构成医疗建议</p>
        </div>
    </div>
</body>
</html>"""
        return html

    def _render_bp_card(self, data: HealthReportData) -> str:
        """渲染血压卡片"""
        if not data.bp_avg_systolic:
            return '<div class="metric-card"><div class="metric-value">--</div><div class="metric-label">血压</div></div>'
        return f"""<div class="metric-card">
            <div class="metric-value">{data.bp_avg_systolic}/{data.bp_avg_diastolic}</div>
            <div class="metric-label">血压 (mmHg)</div>
        </div>"""

    def _render_glucose_card(self, data: HealthReportData) -> str:
        """渲染血糖卡片"""
        if not data.glucose_avg_fasting:
            return '<div class="metric-card"><div class="metric-value">--</div><div class="metric-label">血糖</div></div>'
        return f"""<div class="metric-card">
            <div class="metric-value">{data.glucose_avg_fasting:.1f}</div>
            <div class="metric-label">空腹血糖 (mmol/L)</div>
        </div>"""

    def _render_sleep_card(self, data: HealthReportData) -> str:
        """渲染睡眠卡片"""
        if not data.sleep_avg_duration:
            return '<div class="metric-card"><div class="metric-value">--</div><div class="metric-label">睡眠</div></div>'
        return f"""<div class="metric-card">
            <div class="metric-value">{data.sleep_avg_duration:.1f}h</div>
            <div class="metric-label">平均睡眠</div>
        </div>"""

    async def _generate_markdown(self, data: HealthReportData) -> str:
        """生成Markdown报告"""
        lines = [
            f"# 🌸 若曦健康报告",
            f"**{data.start_date.strftime('%Y年%m月%d日')} - {data.end_date.strftime('%Y年%m月%d日')}**",
            "",
            "## 💜 AI健康洞察",
            data.ai_summary or "暂无AI洞察",
            "",
            "## 📊 健康指标",
        ]

        if data.bp_avg_systolic:
            lines.append(f"- 血压: {data.bp_avg_systolic}/{data.bp_avg_diastolic} mmHg")
        if data.glucose_avg_fasting:
            lines.append(f"- 空腹血糖: {data.glucose_avg_fasting:.1f} mmol/L")
        if data.sleep_avg_duration:
            lines.append(f"- 平均睡眠: {data.sleep_avg_duration:.1f} 小时")
        if data.exercise_records:
            lines.append(f"- 运动记录: {len(data.exercise_records)} 次")

        if data.emotion_summary:
            lines.append("")
            lines.append("## 💕 情绪记录")
            for emotion, count in data.emotion_summary.items():
                lines.append(f"- {emotion}: {count} 次")

        lines.append("")
        lines.append("## 🌟 健康建议")
        for r in self._generate_recommendations(data):
            lines.append(f"- {r}")

        lines.append("")
        lines.append("---")
        lines.append("*🌸 若曦健康助手 · 本报告仅供参考，不构成医疗建议*")

        return "\n".join(lines)

    async def _generate_json(self, data: HealthReportData) -> str:
        """生成JSON报告"""
        report_dict = {
            "title": "若曦健康报告",
            "period": {
                "start": data.start_date.isoformat(),
                "end": data.end_date.isoformat(),
            },
            "ai_summary": data.ai_summary,
            "metrics": {
                "bp_avg_systolic": data.bp_avg_systolic,
                "bp_avg_diastolic": data.bp_avg_diastolic,
                "glucose_avg_fasting": data.glucose_avg_fasting,
                "sleep_avg_duration": data.sleep_avg_duration,
            },
            "emotion_summary": data.emotion_summary,
            "exercise_count": (
                len(data.exercise_records) if data.exercise_records else 0
            ),
            "recommendations": self._generate_recommendations(data),
            "generated_at": datetime.now().isoformat(),
        }
        return json.dumps(report_dict, ensure_ascii=False, indent=2)

    async def _save_report(self, content: str, filename: str) -> str:
        """保存报告到文件"""
        output_path = Path(self.output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(output_path)

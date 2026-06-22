"""
🌸 若曦V2 - 健康时间线引擎
时间线数据聚合与可视化引擎
可视化健康数据时间序列，支持多种图表类型
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ChartType(Enum):
    """图表类型"""

    LINE = "line"  # 折线图
    BAR = "bar"  # 柱状图
    AREA = "area"  # 面积图
    SCATTER = "scatter"  # 散点图
    CANDLESTICK = "candle"  # K线图 (OHLC)
    HEATMAP = "heatmap"  # 热力图


class TimeRange(Enum):
    """时间范围"""

    DAY = "1d"  # 1天
    WEEK = "1w"  # 1周
    MONTH = "1m"  # 1月
    QUARTER = "3m"  # 3月
    HALF_YEAR = "6m"  # 半年
    YEAR = "1y"  # 1年
    ALL = "all"  # 全部


@dataclass
class TimelineDataPoint:
    """时间线数据点"""

    timestamp: datetime
    value: float
    label: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "label": self.label,
            "metadata": self.metadata,
        }


@dataclass
class TimelineSeries:
    """时间线数据系列"""

    id: str
    name: str
    color: str
    unit: str
    data: List[TimelineDataPoint]
    chart_type: ChartType = ChartType.LINE

    # 统计值
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None
    latest_value: Optional[float] = None

    def calculate_stats(self):
        """计算统计值"""
        if not self.data:
            return

        values = [dp.value for dp in self.data]
        self.min_value = min(values)
        self.max_value = max(values)
        self.avg_value = sum(values) / len(values)
        self.latest_value = values[-1] if values else None


@dataclass
class TimelineEvent:
    """时间线事件"""

    id: str
    timestamp: datetime
    type: str
    title: str
    description: str
    importance: str = "normal"  # low, normal, high, critical
    icon: Optional[str] = None
    color: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "importance": self.importance,
            "icon": self.icon,
            "color": self.color,
            "metadata": self.metadata,
        }


@dataclass
class TimelineView:
    """时间线视图配置"""

    id: str
    name: str
    description: str
    time_range: TimeRange
    series_ids: List[str]
    chart_type: ChartType
    aggregation: str = "raw"  # raw, daily_avg, weekly_avg, monthly_avg
    compare_with: Optional[str] = None  # 对比视图ID

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "time_range": self.time_range.value,
            "series_ids": self.series_ids,
            "chart_type": self.chart_type.value,
            "aggregation": self.aggregation,
        }


class TimelineEngine:
    """
    健康时间线引擎

    功能：
    1. 聚合多源健康数据
    2. 生成时间序列图表
    3. 检测趋势变化
    4. 生成事件标记
    """

    def __init__(self):
        self.views: Dict[str, TimelineView] = {}
        self._init_default_views()

    def _init_default_views(self):
        """初始化默认视图"""
        default_views = [
            TimelineView(
                id="bp_weekly",
                name="血压趋势(周)",
                description="最近一周血压变化趋势",
                time_range=TimeRange.WEEK,
                series_ids=["systolic", "diastolic"],
                chart_type=ChartType.LINE,
                aggregation="daily_avg",
            ),
            TimelineView(
                id="bp_monthly",
                name="血压趋势(月)",
                description="最近一月血压变化趋势",
                time_range=TimeRange.MONTH,
                series_ids=["systolic", "diastolic"],
                chart_type=ChartType.LINE,
                aggregation="daily_avg",
            ),
            TimelineView(
                id="glucose_daily",
                name="血糖记录",
                description="每日血糖测量记录",
                time_range=TimeRange.WEEK,
                series_ids=["glucose_fasting", "glucose_postprandial"],
                chart_type=ChartType.SCATTER,
            ),
            TimelineView(
                id="weight_trend",
                name="体重趋势",
                description="体重变化趋势",
                time_range=TimeRange.MONTH,
                series_ids=["weight", "bmi"],
                chart_type=ChartType.AREA,
                aggregation="daily_avg",
            ),
            TimelineView(
                id="sleep_heatmap",
                name="睡眠热力图",
                description="睡眠质量热力分布",
                time_range=TimeRange.MONTH,
                series_ids=["sleep_duration", "sleep_quality"],
                chart_type=ChartType.HEATMAP,
            ),
            TimelineView(
                id="heart_rate",
                name="心率分析",
                description="静息心率趋势",
                time_range=TimeRange.WEEK,
                series_ids=["resting_hr", "max_hr"],
                chart_type=ChartType.LINE,
            ),
            TimelineView(
                id="steps_weekly",
                name="步数统计",
                description="每日步数",
                time_range=TimeRange.WEEK,
                series_ids=["steps", "active_calories"],
                chart_type=ChartType.BAR,
                aggregation="daily_sum",
            ),
        ]

        for view in default_views:
            self.views[view.id] = view

    async def get_timeline_data(
        self,
        user_id: str,
        view_id: str,
        custom_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> Dict:
        """
        获取时间线数据

        Args:
            user_id: 用户ID
            view_id: 视图ID
            custom_range: 自定义时间范围 (start, end)

        Returns:
            时间线数据，包含series和events
        """
        view = self.views.get(view_id)
        if not view:
            raise ValueError(f"视图不存在: {view_id}")

        # 计算时间范围
        if custom_range:
            start_date, end_date = custom_range
        else:
            start_date, end_date = self._calculate_date_range(view.time_range)

        # 获取各个系列的数据
        series_list = []
        for series_id in view.series_ids:
            series = await self._fetch_series_data(
                user_id=user_id,
                series_id=series_id,
                start_date=start_date,
                end_date=end_date,
                aggregation=view.aggregation,
            )
            if series:
                series.calculate_stats()
                series_list.append(series)

        # 获取事件标记
        events = await self._fetch_events(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

        # 生成摘要
        summary = self._generate_summary(series_list, events)

        return {
            "view": view.to_dict(),
            "time_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "series": [
                {
                    "id": s.id,
                    "name": s.name,
                    "color": s.color,
                    "unit": s.unit,
                    "chart_type": s.chart_type.value,
                    "stats": {
                        "min": s.min_value,
                        "max": s.max_value,
                        "avg": round(s.avg_value, 2) if s.avg_value else None,
                        "latest": s.latest_value,
                    },
                    "data": [dp.to_dict() for dp in s.data],
                }
                for s in series_list
            ],
            "events": [e.to_dict() for e in events],
            "summary": summary,
        }

    async def _fetch_series_data(
        self,
        user_id: str,
        series_id: str,
        start_date: datetime,
        end_date: datetime,
        aggregation: str,
    ) -> Optional[TimelineSeries]:
        """
        获取数据系列

        TODO: 实际应从数据库查询
        这里是模拟数据
        """
        # 模拟数据映射
        series_configs = {
            "systolic": {
                "name": "收缩压",
                "color": "#ef4444",
                "unit": "mmHg",
                "chart_type": ChartType.LINE,
            },
            "diastolic": {
                "name": "舒张压",
                "color": "#3b82f6",
                "unit": "mmHg",
                "chart_type": ChartType.LINE,
            },
            "glucose_fasting": {
                "name": "空腹血糖",
                "color": "#10b981",
                "unit": "mmol/L",
                "chart_type": ChartType.SCATTER,
            },
            "glucose_postprandial": {
                "name": "餐后血糖",
                "color": "#f59e0b",
                "unit": "mmol/L",
                "chart_type": ChartType.SCATTER,
            },
            "weight": {
                "name": "体重",
                "color": "#8b5cf6",
                "unit": "kg",
                "chart_type": ChartType.LINE,
            },
            "bmi": {
                "name": "BMI",
                "color": "#ec4899",
                "unit": "",
                "chart_type": ChartType.LINE,
            },
            "sleep_duration": {
                "name": "睡眠时长",
                "color": "#6366f1",
                "unit": "h",
                "chart_type": ChartType.BAR,
            },
            "sleep_quality": {
                "name": "睡眠质量",
                "color": "#14b8a6",
                "unit": "分",
                "chart_type": ChartType.LINE,
            },
            "resting_hr": {
                "name": "静息心率",
                "color": "#f43f5e",
                "unit": "bpm",
                "chart_type": ChartType.LINE,
            },
            "max_hr": {
                "name": "最大心率",
                "color": "#fb7185",
                "unit": "bpm",
                "chart_type": ChartType.SCATTER,
            },
            "steps": {
                "name": "步数",
                "color": "#22c55e",
                "unit": "步",
                "chart_type": ChartType.BAR,
            },
            "active_calories": {
                "name": "活动卡路里",
                "color": "#f97316",
                "unit": "kcal",
                "chart_type": ChartType.LINE,
            },
        }

        config = series_configs.get(series_id)
        if not config:
            return None

        # 生成模拟数据
        data_points = self._generate_mock_data(
            series_id=series_id,
            start_date=start_date,
            end_date=end_date,
            aggregation=aggregation,
        )

        return TimelineSeries(
            id=series_id,
            name=config["name"],
            color=config["color"],
            unit=config["unit"],
            data=data_points,
            chart_type=config["chart_type"],
        )

    def _generate_mock_data(
        self, series_id: str, start_date: datetime, end_date: datetime, aggregation: str
    ) -> List[TimelineDataPoint]:
        """生成模拟数据"""
        import random

        # 基础值范围
        base_ranges = {
            "systolic": (110, 130),
            "diastolic": (70, 85),
            "glucose_fasting": (4.5, 6.5),
            "glucose_postprandial": (5.5, 8.5),
            "weight": (60, 70),
            "bmi": (20, 24),
            "sleep_duration": (6, 9),
            "sleep_quality": (60, 95),
            "resting_hr": (60, 80),
            "max_hr": (120, 160),
            "steps": (3000, 12000),
            "active_calories": (200, 800),
        }

        min_val, max_val = base_ranges.get(series_id, (0, 100))

        data_points = []
        current = start_date

        while current <= end_date:
            # 添加一些随机波动和趋势
            base = (min_val + max_val) / 2
            trend = 0

            # 体重和睡眠可能有轻微下降趋势
            if series_id in ["weight", "bmi"]:
                days_since_start = (current - start_date).days
                trend = -0.02 * days_since_start  # 轻微下降

            value = base + random.uniform(-5, 5) + trend
            value = max(min_val, min(max_val, value))

            data_points.append(
                TimelineDataPoint(timestamp=current, value=round(value, 1), label=None)
            )

            if aggregation == "daily_avg":
                current += timedelta(days=1)
            elif aggregation == "weekly_avg":
                current += timedelta(weeks=1)
            else:
                current += timedelta(days=1)

        return data_points

    async def _fetch_events(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> List[TimelineEvent]:
        """获取事件标记"""
        # 模拟事件数据
        # 实际应从数据库查询：用药提醒、异常指标、体检记录等

        events = []

        # 示例事件
        example_events = [
            {
                "timestamp": start_date + timedelta(days=2),
                "type": "medication",
                "title": "开始服用新药物",
                "description": "医生开具了新的降压药物",
                "importance": "high",
            },
            {
                "timestamp": start_date + timedelta(days=5),
                "type": "alert",
                "title": "血压异常提醒",
                "description": "检测到收缩压超过140mmHg",
                "importance": "critical",
            },
            {
                "timestamp": start_date + timedelta(days=7),
                "type": "checkup",
                "title": "体检日期",
                "description": "季度健康检查",
                "importance": "normal",
            },
        ]

        for i, evt in enumerate(example_events):
            if start_date <= evt["timestamp"] <= end_date:
                events.append(
                    TimelineEvent(
                        id=f"evt_{i}",
                        timestamp=evt["timestamp"],
                        type=evt["type"],
                        title=evt["title"],
                        description=evt["description"],
                        importance=evt["importance"],
                        icon="🔔" if evt["type"] == "alert" else "💊",
                    )
                )

        return events

    def _calculate_date_range(self, time_range: TimeRange) -> Tuple[datetime, datetime]:
        """计算时间范围"""
        end = datetime.now()

        ranges = {
            TimeRange.DAY: timedelta(days=1),
            TimeRange.WEEK: timedelta(weeks=1),
            TimeRange.MONTH: timedelta(days=30),
            TimeRange.QUARTER: timedelta(days=90),
            TimeRange.HALF_YEAR: timedelta(days=180),
            TimeRange.YEAR: timedelta(days=365),
            TimeRange.ALL: timedelta(days=365 * 10),  # 10年
        }

        delta = ranges.get(time_range, timedelta(days=30))
        start = end - delta

        return start, end

    def _generate_summary(
        self, series_list: List[TimelineSeries], events: List[TimelineEvent]
    ) -> Dict:
        """生成时间线摘要"""

        # 统计事件
        event_counts = {}
        for evt in events:
            event_counts[evt.type] = event_counts.get(evt.type, 0) + 1

        # 找出关键变化
        key_changes = []
        for series in series_list:
            if len(series.data) >= 2:
                first = series.data[0].value
                last = series.data[-1].value
                change = last - first
                change_pct = (change / first * 100) if first != 0 else 0

                key_changes.append(
                    {
                        "series": series.name,
                        "change": round(change, 2),
                        "change_pct": round(change_pct, 1),
                        "trend": (
                            "up" if change > 0 else "down" if change < 0 else "stable"
                        ),
                    }
                )

        return {
            "data_points_total": sum(len(s.data) for s in series_list),
            "series_count": len(series_list),
            "event_count": len(events),
            "event_breakdown": event_counts,
            "key_changes": key_changes,
            "critical_events": [e.title for e in events if e.importance == "critical"],
        }

    def get_available_views(self) -> List[Dict]:
        """获取可用视图列表"""
        return [view.to_dict() for view in self.views.values()]

    async def compare_periods(
        self,
        user_id: str,
        series_id: str,
        period1: Tuple[datetime, datetime],
        period2: Tuple[datetime, datetime],
    ) -> Dict:
        """
        对比两个时间段

        Returns:
            对比分析结果
        """
        series1 = await self._fetch_series_data(
            user_id, series_id, period1[0], period1[1], "raw"
        )
        series2 = await self._fetch_series_data(
            user_id, series_id, period2[0], period2[1], "raw"
        )

        if not series1 or not series2:
            return {"error": "数据不足"}

        series1.calculate_stats()
        series2.calculate_stats()

        return {
            "series_name": series1.name,
            "period1": {
                "start": period1[0].isoformat(),
                "end": period1[1].isoformat(),
                "avg": series1.avg_value,
                "min": series1.min_value,
                "max": series1.max_value,
            },
            "period2": {
                "start": period2[0].isoformat(),
                "end": period2[1].isoformat(),
                "avg": series2.avg_value,
                "min": series2.min_value,
                "max": series2.max_value,
            },
            "comparison": {
                "avg_change": round(series2.avg_value - series1.avg_value, 2),
                "avg_change_pct": (
                    round(
                        (series2.avg_value - series1.avg_value)
                        / series1.avg_value
                        * 100,
                        1,
                    )
                    if series1.avg_value
                    else 0
                ),
                "trend": (
                    "improved"
                    if self._is_improved(
                        series1.name, series2.avg_value, series1.avg_value
                    )
                    else (
                        "worsened"
                        if series2.avg_value != series1.avg_value
                        else "stable"
                    )
                ),
            },
        }

    def _is_improved(self, series_name: str, new_val: float, old_val: float) -> bool:
        """判断指标是否改善"""
        # 越低越好的指标
        lower_is_better = ["收缩压", "舒张压", "空腹血糖", "餐后血糖", "BMI", "体重"]

        if series_name in lower_is_better:
            return new_val < old_val
        else:
            # 越高越好或越稳定越好
            return new_val > old_val


# 全局引擎实例
timeline_engine = TimelineEngine()

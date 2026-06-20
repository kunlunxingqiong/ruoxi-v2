"""
🌸 若曦V2 - 健康时间线组件
基于ECharts的时间序列可视化
"""

import React, { useState, useEffect, useRef } from 'react';
import { 
  LineChart, BarChart, Line, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Area, AreaChart, ReferenceLine, Cell
} from 'recharts';
import { 
  Calendar, TrendingUp, Activity, Filter, Download,
  ChevronLeft, ChevronRight, Maximize2, Info
} from 'lucide-react';

// 视图配置
interface ViewConfig {
  id: string;
  name: string;
  description: string;
  time_range: string;
  series_ids: string[];
  chart_type: string;
  aggregation: string;
}

// 数据系列
interface TimelineSeries {
  id: string;
  name: string;
  color: string;
  unit: string;
  chart_type: string;
  stats: {
    min: number;
    max: number;
    avg: number;
    latest: number;
  };
  data: Array<{
    timestamp: string;
    value: number;
    label?: string;
  }>;
}

// 时间线事件
interface TimelineEvent {
  id: string;
  timestamp: string;
  type: string;
  title: string;
  description: string;
  importance: string;
  icon?: string;
  color?: string;
}

// 时间线数据
interface TimelineData {
  view: ViewConfig;
  time_range: {
    start: string;
    end: string;
  };
  series: TimelineSeries[];
  events: TimelineEvent[];
  summary: {
    data_points_total: number;
    series_count: number;
    event_count: number;
    event_breakdown: Record<string, number>;
    key_changes: Array<{
      series: string;
      change: number;
      change_pct: number;
      trend: string;
    }>;
    critical_events: string[];
  };
}

interface HealthTimelineProps {
  apiBaseUrl: string;
  userToken: string;
}

export const HealthTimeline: React.FC<HealthTimelineProps> = ({
  apiBaseUrl,
  userToken
}) => {
  const [availableViews, setAvailableViews] = useState<ViewConfig[]>([]);
  const [selectedView, setSelectedView] = useState<string>('bp_weekly');
  const [timelineData, setTimelineData] = useState<TimelineData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [showEvents, setShowEvents] = useState(true);

  // 获取可用视图
  useEffect(() => {
    fetchAvailableViews();
  }, []);

  // 获取时间线数据
  useEffect(() => {
    fetchTimelineData();
  }, [selectedView, dateRange]);

  const fetchAvailableViews = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/timeline/views`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      const data = await response.json();
      if (data.success) {
        setAvailableViews(data.views);
      }
    } catch (error) {
      console.error('获取视图失败:', error);
    }
  };

  const fetchTimelineData = async () => {
    setIsLoading(true);
    
    try {
      const params = new URLSearchParams();
      if (dateRange.start) params.append('start_date', dateRange.start);
      if (dateRange.end) params.append('end_date', dateRange.end);
      
      const response = await fetch(
        `${apiBaseUrl}/api/v1/timeline/data/${selectedView}?${params}`,
        {
          headers: { 'Authorization': `Bearer ${userToken}` }
        }
      );
      
      const data = await response.json();
      if (data.success) {
        setTimelineData(data.data);
      }
    } catch (error) {
      console.error('获取时间线数据失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 准备图表数据
  const prepareChartData = () => {
    if (!timelineData || !timelineData.series.length) return [];
    
    // 合并多个系列的数据
    const timestamps = timelineData.series[0].data.map(d => d.timestamp);
    
    return timestamps.map((ts, idx) => {
      const point: any = {
        timestamp: new Date(ts).toLocaleDateString('zh-CN'),
        fullTimestamp: ts
      };
      
      timelineData.series.forEach(series => {
        const dataPoint = series.data[idx];
        if (dataPoint) {
          point[series.id] = dataPoint.value;
        }
      });
      
      return point;
    });
  };

  // 渲染图表
  const renderChart = () => {
    const data = prepareChartData();
    if (!data.length) return <div className="text-center text-gray-400 py-20">暂无数据</div>;
    
    const chartType = timelineData?.view.chart_type || 'line';
    
    // 根据图表类型选择组件
    const ChartComponent = chartType === 'bar' ? BarChart : 
                           chartType === 'area' ? AreaChart : LineChart;
    
    return (
      <ResponsiveContainer width="100%" height={400}>
        <ChartComponent data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="timestamp" 
            stroke="#9ca3af"
            fontSize={12}
            tickLine={false}
          />
          <YAxis 
            stroke="#9ca3af"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'white', 
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '12px'
            }}
            labelStyle={{ color: '#374151', fontWeight: 600 }}
          />
          <Legend 
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="circle"
          />
          
          {timelineData?.series.map((series) => (
            chartType === 'bar' ? (
              <Bar 
                key={series.id}
                type="monotone" 
                dataKey={series.id} 
                name={`${series.name} (${series.unit})`}
                stroke={series.color}
                fill={series.color}
                fillOpacity={0.6}
                strokeWidth={2}
                radius={[4, 4, 0, 0]}
              />
            ) : chartType === 'area' ? (
              <Area
                key={series.id}
                type="monotone"
                dataKey={series.id}
                name={`${series.name} (${series.unit})`}
                stroke={series.color}
                fill={series.color}
                fillOpacity={0.2}
                strokeWidth={2}
              />
            ) : (
              <Line
                key={series.id}
                type="monotone"
                dataKey={series.id}
                name={`${series.name} (${series.unit})`}
                stroke={series.color}
                strokeWidth={2}
                dot={{ fill: series.color, strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, strokeWidth: 0 }}
              />
            )
          ))}
          
          {/* 参考线 */}
          {selectedView.includes('bp') && (
            <>
              <ReferenceLine y={120} stroke="#10b981" strokeDasharray="5 5" label="正常上限" />
              <ReferenceLine y={140} stroke="#f59e0b" strokeDasharray="5 5" label="警戒线" />
            </>
          )}
        </ChartComponent>
      </ResponsiveContainer>
    );
  };

  // 渲染统计卡片
  const renderStats = () => {
    if (!timelineData) return null;
    
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {timelineData.series.map((series) => (
          <div key={series.id} className="bg-white rounded-xl p-4 border border-gray-100">
            <div className="flex items-center gap-2 mb-2">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: series.color }}
              />
              <span className="text-sm text-gray-600">{series.name}</span>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">最新</span>
                <span className="font-medium">{series.stats.latest}{series.unit}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">平均</span>
                <span className="font-medium">{series.stats.avg}{series.unit}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">范围</span>
                <span className="font-medium">{series.stats.min}-{series.stats.max}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  // 渲染事件时间线
  const renderEvents = () => {
    if (!timelineData?.events.length || !showEvents) return null;
    
    return (
      <div className="mt-6 bg-gray-50 rounded-xl p-4">
        <h4 className="font-medium text-gray-800 mb-3 flex items-center gap-2">
          <Activity className="w-4 h-4" />
          相关事件
        </h4>
        <div className="space-y-3">
          {timelineData.events.map((event) => (
            <div 
              key={event.id}
              className={`flex items-start gap-3 p-3 rounded-lg ${
                event.importance === 'critical' ? 'bg-red-50 border border-red-100' :
                event.importance === 'high' ? 'bg-yellow-50 border border-yellow-100' :
                'bg-white border border-gray-100'
              }`}
            >
              <span className="text-xl">{event.icon || '🔔'}</span>
              <div className="flex-1">
                <p className="font-medium text-sm">{event.title}</p>
                <p className="text-xs text-gray-500">{event.description}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(event.timestamp).toLocaleString('zh-CN')}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // 渲染关键变化
  const renderKeyChanges = () => {
    if (!timelineData?.summary.key_changes.length) return null;
    
    return (
      <div className="mt-6 bg-gradient-to-r from-pink-50 to-purple-50 rounded-xl p-4">
        <h4 className="font-medium text-gray-800 mb-3 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-pink-500" />
          关键变化
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {timelineData.summary.key_changes.map((change, idx) => (
            <div key={idx} className="flex items-center gap-3 bg-white rounded-lg p-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                change.trend === 'up' ? 'bg-green-100 text-green-600' :
                change.trend === 'down' ? 'bg-red-100 text-red-600' :
                'bg-gray-100 text-gray-600'
              }`}>
                {change.trend === 'up' ? '↑' : change.trend === 'down' ? '↓' : '→'}
              </div>
              <div>
                <p className="text-sm font-medium">{change.series}</p>
                <p className="text-xs text-gray-500">
                  {change.change > 0 ? '+' : ''}{change.change} 
                  ({change.change_pct > 0 ? '+' : ''}{change.change_pct}%)
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      {/* 头部 */}
      <div className="bg-gradient-to-r from-pink-500 to-purple-600 p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Activity className="w-6 h-6" />
              健康时间线
            </h2>
            <p className="text-pink-100 mt-1">
              {timelineData?.view.description || '追踪您的健康变化趋势'}
            </p>
          </div>
          <button 
            onClick={() => {}}
            className="p-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
          >
            <Download className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="p-6">
        {/* 控制栏 */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
          {/* 视图选择 */}
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-gray-500 mb-1">数据视图</label>
            <select
              value={selectedView}
              onChange={(e) => setSelectedView(e.target.value)}
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-pink-300 text-sm"
            >
              {availableViews.map((view) => (
                <option key={view.id} value={view.id}>
                  {view.name}
                </option>
              ))}
            </select>
          </div>

          {/* 日期范围 */}
          <div className="flex gap-2">
            <div>
              <label className="block text-xs text-gray-500 mb-1">开始</label>
              <input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
                className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-pink-300"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">结束</label>
              <input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
                className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-pink-300"
              />
            </div>
          </div>

          {/* 事件开关 */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="showEvents"
              checked={showEvents}
              onChange={(e) => setShowEvents(e.target.checked)}
              className="rounded border-gray-300 text-pink-500 focus:ring-pink-500"
            />
            <label htmlFor="showEvents" className="text-sm text-gray-600 cursor-pointer">
              显示事件
            </label>
          </div>
        </div>

        {/* 加载状态 */}
        {isLoading ? (
          <div className="text-center py-20">
            <div className="animate-spin w-8 h-8 border-3 border-pink-500 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-gray-500">加载中...</p>
          </div>
        ) : (
          <>
            {/* 统计卡片 */}
            {renderStats()}

            {/* 图表 */}
            <div className="bg-gray-50 rounded-xl p-4">
              {renderChart()}
            </div>

            {/* 关键变化 */}
            {renderKeyChanges()}

            {/* 事件时间线 */}
            {renderEvents()}

            {/* 数据摘要 */}
            {timelineData?.summary && (
              <div className="mt-6 flex flex-wrap items-center gap-4 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <Info className="w-4 h-4" />
                  共 {timelineData.summary.data_points_total} 个数据点
                </span>
                <span>
                  {timelineData.summary.event_count} 个事件标记
                </span>
                <span>
                  时间范围: {new Date(timelineData.time_range.start).toLocaleDateString('zh-CN')} 
                  ~ {new Date(timelineData.time_range.end).toLocaleDateString('zh-CN')}
                </span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default HealthTimeline;

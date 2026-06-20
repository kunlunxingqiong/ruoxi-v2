"""
🌸 若曦V2 - 个人健康仪表盘组件
展示用户健康概览和快捷操作
"""

import React, { useState, useEffect } from 'react';
import {
  Activity, Droplet, Scale, Moon, Heart,
  Trophy, Flame, CheckCircle, AlertCircle,
  ChevronRight, Plus, Bell, Calendar,
  TrendingUp, TrendingDown, Minus,
  Pill, Target, FileText, Zap,
  RefreshCw, Settings
} from 'lucide-react';

// 数据类型
interface DashboardData {
  user_summary: {
    username: string;
    avatar?: string;
    health_score: number;
    streak_days: number;
  };
  today_overview: {
    date: string;
    records: {
      blood_pressure?: number;
      glucose?: number;
      weight?: number;
      sleep_duration?: number;
      sleep_quality?: number;
    };
    medication: {
      total: number;
      taken: number;
      completion_rate: number;
    };
    completion_status: string;
  };
  today_tasks: Array<{
    id: string;
    type: string;
    title: string;
    description: string;
    priority: string;
    completed: boolean;
  }>;
  health_trends: {
    blood_pressure?: any;
    weight?: any;
    glucose?: any;
    sleep?: any;
  };
  goal_progress: Array<{
    id: number;
    title: string;
    progress_percentage: number;
    current_value: number;
    target_value: number;
    unit: string;
  }>;
  recent_records: Array<{
    type: string;
    title: string;
    value: any;
    unit: string;
    time: string;
  }>;
  health_alerts: Array<{
    type: string;
    title: string;
    message: string;
    priority: string;
  }>;
  insights: Array<{
    type: string;
    title: string;
    message: string;
  }>;
}

interface PersonalDashboardProps {
  apiBaseUrl: string;
  userToken: string;
}

export const PersonalDashboard: React.FC<PersonalDashboardProps> = ({
  apiBaseUrl,
  userToken
}) => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'tasks' | 'trends'>('overview');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/dashboard/`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      
      if (res.ok) {
        const result = await res.json();
        setData(result.data);
      }
    } catch (e) {
      console.error('获取仪表盘数据失败:', e);
    } finally {
      setLoading(false);
    }
  };

  // 获取健康评分颜色
  const getHealthScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    return 'text-red-500';
  };

  // 获取趋势图标
  const getTrendIcon = (trend?: string) => {
    if (trend === 'improving' || trend === 'decreasing') return <TrendingDown className="w-4 h-4 text-green-500" />;
    if (trend === 'worsening' || trend === 'increasing') return <TrendingUp className="w-4 h-4 text-orange-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-3 text-gray-600">加载中...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500">暂无数据，请开始记录健康数据</p>
      </div>
    );
  }

  const { user_summary, today_overview, today_tasks, health_trends, goal_progress, recent_records, health_alerts, insights } = data;

  return (
    <div className="space-y-6">
      {/* 顶部欢迎区 */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-3xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-1">
              你好，{user_summary.username}！
            </h1>
            <p className="text-indigo-100">
              {new Date().toLocaleDateString('zh-CN', { weekday: 'long', month: 'long', day: 'numeric' })}
            </p>
          </div>
          <div className="text-center">
            <div className={`text-5xl font-bold ${getHealthScoreColor(user_summary.health_score)}`}>
              {user_summary.health_score}
            </div>
            <div className="text-sm text-indigo-100">健康评分</div>
          </div>
        </div>
        
        {/* 连续记录天数 */}
        {user_summary.streak_days > 0 && (
          <div className="mt-4 flex items-center gap-2 bg-white/10 rounded-xl p-3">
            <Flame className="w-5 h-5 text-orange-400" />
            <span className="text-sm">
              已连续记录 <strong>{user_summary.streak_days}</strong> 天，继续保持！
            </span>
          </div>
        )}
      </div>

      {/* 快捷操作 */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { icon: Activity, label: '血压', color: 'bg-red-100 text-red-600', action: '/bp' },
          { icon: Droplet, label: '血糖', color: 'bg-blue-100 text-blue-600', action: '/glucose' },
          { icon: Scale, label: '体重', color: 'bg-green-100 text-green-600', action: '/weight' },
          { icon: Moon, label: '睡眠', color: 'bg-purple-100 text-purple-600', action: '/sleep' }
        ].map((item, idx) => (
          <button
            key={idx}
            onClick={() => window.location.href = item.action}
            className={`${item.color} rounded-2xl p-4 flex flex-col items-center gap-2 hover:shadow-lg transition-all`}
          >
            <item.icon className="w-6 h-6" />
            <span className="text-sm font-medium">{item.label}</span>
          </button>
        ))}
      </div>

      {/* 今日概览 */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800">今日概览</h3>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
            today_overview.completion_status === 'completed' ? 'bg-green-100 text-green-700' :
            today_overview.completion_status === 'good' ? 'bg-yellow-100 text-yellow-700' :
            'bg-gray-100 text-gray-600'
          }`}>
            {today_overview.completion_status === 'completed' ? '今日完成' :
             today_overview.completion_status === 'good' ? '进行中' : '待记录'}
          </span>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* 血压 */}
          <div className="bg-gray-50 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-5 h-5 text-red-500" />
              <span className="text-sm text-gray-600">血压记录</span>
            </div>
            <div className="text-2xl font-bold text-gray-800">
              {today_overview.records.blood_pressure || 0}
            </div>
            <div className="text-xs text-gray-500">次</div>
          </div>
          
          {/* 血糖 */}
          <div className="bg-gray-50 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Droplet className="w-5 h-5 text-blue-500" />
              <span className="text-sm text-gray-600">血糖记录</span>
            </div>
            <div className="text-2xl font-bold text-gray-800">
              {today_overview.records.glucose || 0}
            </div>
            <div className="text-xs text-gray-500">次</div>
          </div>
          
          {/* 体重 */}
          <div className="bg-gray-50 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Scale className="w-5 h-5 text-green-500" />
              <span className="text-sm text-gray-600">体重</span>
            </div>
            <div className="text-2xl font-bold text-gray-800">
              {today_overview.records.weight ? today_overview.records.weight.toFixed(1) : '--'}
            </div>
            <div className="text-xs text-gray-500">kg</div>
          </div>
          
          {/* 用药 */}
          <div className="bg-gray-50 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Pill className="w-5 h-5 text-orange-500" />
              <span className="text-sm text-gray-600">用药</span>
            </div>
            <div className="text-2xl font-bold text-gray-800">
              {today_overview.medication.completion_rate}%
            </div>
            <div className="text-xs text-gray-500">
              {today_overview.medication.taken}/{today_overview.medication.total}
            </div>
          </div>
        </div>
      </div>

      {/* AI健康洞察 */}
      {insights && insights.length > 0 && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-indigo-500" />
            AI健康洞察
          </h3>
          <div className="space-y-3">
            {insights.map((insight, idx) => (
              <div key={idx} className="flex items-start gap-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  insight.type === 'positive' ? 'bg-green-100 text-green-600' :
                  insight.type === 'achievement' ? 'bg-yellow-100 text-yellow-600' :
                  'bg-blue-100 text-blue-600'
                }`}>
                  {insight.type === 'positive' ? <TrendingDown className="w-4 h-4" /> :
                   insight.type === 'achievement' ? <Trophy className="w-4 h-4" /> :
                   <Zap className="w-4 h-4" />}
                </div>
                <div>
                  <div className="font-medium text-gray-800">{insight.title}</div>
                  <div className="text-sm text-gray-600">{insight.message}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 任务列表 */}
      {today_tasks && today_tasks.length > 0 && (
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-blue-500" />
            今日待办
            <span className="text-sm text-gray-500 font-normal">
              ({today_tasks.filter(t => t.completed).length}/{today_tasks.length})
            </span>
          </h3>
          <div className="space-y-3">
            {today_tasks.slice(0, 5).map((task, idx) => (
              <div
                key={idx}
                className={`flex items-center gap-3 p-3 rounded-xl border ${
                  task.completed ? 'bg-gray-50 border-gray-100' : 'bg-white border-gray-200'
                }`}
              >
                <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                  task.completed ? 'bg-green-500 border-green-500' : 'border-gray-300'
                }`}>
                  {task.completed && <CheckCircle className="w-3 h-3 text-white" />}
                </div>
                <div className="flex-1">
                  <div className={`font-medium ${task.completed ? 'text-gray-500 line-through' : 'text-gray-800'}`}>
                    {task.title}
                  </div>
                  <div className="text-sm text-gray-500">{task.description}</div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs ${
                  task.priority === 'high' ? 'bg-red-100 text-red-700' :
                  task.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {task.priority === 'high' ? '高' : task.priority === 'medium' ? '中' : '低'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 目标进度 */}
      {goal_progress && goal_progress.length > 0 && (
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <Target className="w-5 h-5 text-purple-500" />
              目标进度
            </h3>
            <a href="/goals" className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1">
              查看全部 <ChevronRight className="w-4 h-4" />
            </a>
          </div>
          <div className="space-y-4">
            {goal_progress.map((goal, idx) => (
              <div key={idx} className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-800">{goal.title}</span>
                  <span className="text-sm text-gray-600">
                    {goal.current_value}/{goal.target_value} {goal.unit}
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                    style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
                  />
                </div>
                <div className="text-right text-xs text-gray-500 mt-1">
                  {goal.progress_percentage}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 近期趋势 */}
      {health_trends && (
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">近期趋势</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {health_trends.blood_pressure?.has_data && (
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-red-500" /> 血压
                  </span>
                  {getTrendIcon(health_trends.blood_pressure.trend)}
                </div>
                <div className="text-lg font-bold text-gray-800">
                  {health_trends.blood_pressure.avg_systolic}/{health_trends.blood_pressure.avg_diastolic}
                </div>
                <div className="text-xs text-gray-500">mmHg (7天平均)</div>
              </div>
            )}
            
            {health_trends.weight?.has_data && (
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600 flex items-center gap-2">
                    <Scale className="w-4 h-4 text-green-500" /> 体重
                  </span>
                  {getTrendIcon(health_trends.weight.trend)}
                </div>
                <div className="text-lg font-bold text-gray-800">
                  {health_trends.weight.current_weight} kg
                </div>
                <div className={`text-xs ${
                  health_trends.weight.change_kg < 0 ? 'text-green-600' :
                  health_trends.weight.change_kg > 0 ? 'text-orange-600' : 'text-gray-500'
                }`}>
                  7天变化: {health_trends.weight.change_kg > 0 ? '+' : ''}{health_trends.weight.change_kg} kg
                </div>
              </div>
            )}
            
            {health_trends.glucose?.has_data && (
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600 flex items-center gap-2">
                    <Droplet className="w-4 h-4 text-blue-500" /> 血糖
                  </span>
                </div>
                <div className="text-lg font-bold text-gray-800">
                  {health_trends.glucose.avg_value} mmol/L
                </div>
                <div className="text-xs text-gray-500">7天平均</div>
              </div>
            )}
            
            {health_trends.sleep?.has_data && (
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600 flex items-center gap-2">
                    <Moon className="w-4 h-4 text-purple-500" /> 睡眠
                  </span>
                </div>
                <div className="text-lg font-bold text-gray-800">
                  {health_trends.sleep.avg_duration} 小时
                </div>
                <div className="text-xs text-gray-500">7天平均</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 健康警报 */}
      {health_alerts && health_alerts.length > 0 && (
        <div className="bg-red-50 rounded-2xl p-6 border border-red-100">
          <h3 className="text-lg font-semibold text-red-800 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            健康提醒
          </h3>
          <div className="space-y-3">
            {health_alerts.map((alert, idx) => (
              <div key={idx} className="flex items-start gap-3 bg-white rounded-xl p-4">
                <AlertCircle className={`w-5 h-5 mt-0.5 ${
                  alert.priority === 'high' ? 'text-red-500' : 'text-orange-500'
                }`} />
                <div>
                  <div className="font-medium text-gray-800">{alert.title}</div>
                  <div className="text-sm text-gray-600">{alert.message}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PersonalDashboard;

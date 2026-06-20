"""
🌸 若曦V2 - 主仪表盘页面
Next.js App Router页面
"""

'use client';

import React, { useState, useEffect } from 'react';
import { 
  Heart, Activity, Moon, Scale, Pill, MessageCircle, 
  TrendingUp, Calendar, Bell, Settings, User 
} from 'lucide-react';
import { ChatInterface } from '@/components/ChatInterface';

// 健康指标卡片
interface HealthMetric {
  id: string;
  name: string;
  value: string;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  status: 'normal' | 'warning' | 'alert';
  lastUpdated: string;
  icon: React.ReactNode;
  color: string;
}

// 快捷操作
interface QuickAction {
  id: string;
  name: string;
  icon: React.ReactNode;
  href: string;
  color: string;
}

export default function DashboardPage() {
  const [activeSection, setActiveSection] = useState<'overview' | 'chat'>('overview');
  const [unreadNotifications, setUnreadNotifications] = useState(3);
  const [greeting, setGreeting] = useState('');
  
  // 根据时间生成问候语
  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 6) setGreeting('夜深了');
    else if (hour < 11) setGreeting('早上好');
    else if (hour < 14) setGreeting('中午好');
    else if (hour < 18) setGreeting('下午好');
    else setGreeting('晚上好');
  }, []);
  
  // 健康指标数据 (模拟)
  const healthMetrics: HealthMetric[] = [
    {
      id: 'bp',
      name: '血压',
      value: '118/78',
      unit: 'mmHg',
      trend: 'stable',
      status: 'normal',
      lastUpdated: '2小时前',
      icon: <Activity className="w-5 h-5" />,
      color: 'blue'
    },
    {
      id: 'glucose',
      name: '血糖',
      value: '5.6',
      unit: 'mmol/L',
      trend: 'stable',
      status: 'normal',
      lastUpdated: '今晨',
      icon: <TrendingUp className="w-5 h-5" />,
      color: 'green'
    },
    {
      id: 'weight',
      name: '体重',
      value: '65.2',
      unit: 'kg',
      trend: 'down',
      status: 'normal',
      lastUpdated: '昨天',
      icon: <Scale className="w-5 h-5" />,
      color: 'purple'
    },
    {
      id: 'sleep',
      name: '睡眠',
      value: '7.5',
      unit: '小时',
      trend: 'up',
      status: 'normal',
      lastUpdated: '今天',
      icon: <Moon className="w-5 h-5" />,
      color: 'indigo'
    },
    {
      id: 'heart',
      name: '心率',
      value: '72',
      unit: 'bpm',
      trend: 'stable',
      status: 'normal',
      lastUpdated: '现在',
      icon: <Heart className="w-5 h-5" />,
      color: 'red'
    },
    {
      id: 'medication',
      name: '用药',
      value: '2/3',
      unit: '次',
      trend: 'stable',
      status: 'warning',
      lastUpdated: '今天',
      icon: <Pill className="w-5 h-5" />,
      color: 'amber'
    }
  ];
  
  // 快捷操作
  const quickActions: QuickAction[] = [
    { id: 'log-bp', name: '记血压', icon: <Activity className="w-5 h-5" />, href: '/health/bp', color: 'blue' },
    { id: 'log-glucose', name: '记血糖', icon: <TrendingUp className="w-5 h-5" />, href: '/health/glucose', color: 'green' },
    { id: 'emotion', name: '情绪打卡', icon: <Heart className="w-5 h-5" />, href: '/chat/emotion', color: 'pink' },
    { id: 'import', name: '导入数据', icon: <TrendingUp className="w-5 h-5 rotate-180" />, href: '/data/import', color: 'purple' },
    { id: 'report', name: '健康报告', icon: <Calendar className="w-5 h-5" />, href: '/reports', color: 'indigo' },
    { id: 'settings', name: '设置', icon: <Settings className="w-5 h-5" />, href: '/settings', color: 'gray' }
  ];
  
  // 状态颜色映射
  const statusColors = {
    normal: 'bg-green-100 text-green-700 border-green-200',
    warning: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    alert: 'bg-red-100 text-red-700 border-red-200'
  };
  
  const trendIcons = {
    up: '↑',
    down: '↓',
    stable: '→'
  };
  
  const trendColors = {
    up: 'text-green-500',
    down: 'text-red-500',
    stable: 'text-gray-400'
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {/* 顶部导航 */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-300 to-purple-400 flex items-center justify-center">
                <span className="text-xl">🌸</span>
              </div>
              <div>
                <h1 className="font-bold text-gray-800">若曦</h1>
                <p className="text-xs text-gray-500">AI医生朋友</p>
              </div>
            </div>
            
            {/* 导航项 */}
            <nav className="hidden md:flex items-center gap-1">
              <button
                onClick={() => setActiveSection('overview')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeSection === 'overview' 
                    ? 'bg-pink-100 text-pink-700' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                概览
              </button>
              <button
                onClick={() => setActiveSection('chat')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 ${
                  activeSection === 'chat' 
                    ? 'bg-pink-100 text-pink-700' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <MessageCircle className="w-4 h-4" />
                和若曦聊聊
              </button>
            </nav>
            
            {/* 右侧工具 */}
            <div className="flex items-center gap-3">
              <button className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors">
                <Bell className="w-5 h-5 text-gray-600" />
                {unreadNotifications > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                    {unreadNotifications}
                  </span>
                )}
              </button>
              <button className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
              </button>
            </div>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeSection === 'overview' ? (
          <div className="space-y-8">
            {/* 欢迎区 */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-800">
                    {greeting}，欢迎回来 👋
                  </h2>
                  <p className="text-gray-500 mt-1">
                    今天你的健康状态看起来不错，继续保持！
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-400">
                    {new Date().toLocaleDateString('zh-CN', { 
                      weekday: 'long', 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </p>
                </div>
              </div>
            </div>
            
            {/* 健康指标卡片 */}
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-pink-500" />
                健康指标
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {healthMetrics.map((metric) => (
                  <div 
                    key={metric.id}
                    className={`bg-white rounded-xl p-4 border-2 transition-all hover:shadow-md cursor-pointer ${
                      statusColors[metric.status]
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className={`p-2 rounded-lg bg-${metric.color}-100`}>
                        {React.cloneElement(metric.icon as React.ReactElement, {
                          className: `w-4 h-4 text-${metric.color}-600`
                        })}
                      </div>
                      <span className={`text-xs ${trendColors[metric.trend]}`}>
                        {trendIcons[metric.trend]}
                      </span>
                    </div>
                    <p className="text-xs opacity-70">{metric.name}</p>
                    <p className="text-xl font-bold mt-1">
                      {metric.value}
                      <span className="text-xs font-normal ml-1">{metric.unit}</span>
                    </p>
                    <p className="text-xs opacity-60 mt-1">{metric.lastUpdated}</p>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* 快捷操作 */}
              <div className="lg:col-span-1">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                  快捷操作
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {quickActions.map((action) => (
                    <a
                      key={action.id}
                      href={action.href}
                      className={`flex flex-col items-center p-4 bg-white rounded-xl border border-gray-100 hover:border-${action.color}-300 hover:shadow-md transition-all`}
                    >
                      <div className={`w-10 h-10 rounded-lg bg-${action.color}-100 flex items-center justify-center mb-2`}>
                        {React.cloneElement(action.icon as React.ReactElement, {
                          className: `w-5 h-5 text-${action.color}-600`
                        })}
                      </div>
                      <span className="text-sm text-gray-700 text-center">{action.name}</span>
                    </a>
                  ))}
                </div>
              </div>
              
              {/* 最近活动 */}
              <div className="lg:col-span-2">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                  最近活动
                </h3>
                <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                  <div className="divide-y divide-gray-100">
                    {[
                      { time: '10分钟前', content: '记录了血压 118/78 mmHg', type: 'health' },
                      { time: '1小时前', content: '完成了情绪打卡', type: 'emotion' },
                      { time: '今天 08:30', content: '服用了维生素C', type: 'medication' },
                      { time: '今天 07:00', content: '同步了睡眠数据 7.5小时', type: 'sleep' },
                      { time: '昨天', content: '导出了周健康报告', type: 'report' }
                    ].map((activity, idx) => (
                      <div key={idx} className="p-4 flex items-start gap-3 hover:bg-gray-50 transition-colors">
                        <div className={`w-2 h-2 rounded-full mt-2 ${
                          activity.type === 'health' ? 'bg-blue-500' :
                          activity.type === 'emotion' ? 'bg-pink-500' :
                          activity.type === 'medication' ? 'bg-amber-500' :
                          activity.type === 'sleep' ? 'bg-indigo-500' :
                          'bg-gray-400'
                        }`} />
                        <div className="flex-1">
                          <p className="text-sm text-gray-700">{activity.content}</p>
                          <p className="text-xs text-gray-400 mt-1">{activity.time}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* 聊天界面 */
          <div className="h-[calc(100vh-8rem)]">
            <ChatInterface 
              userId="user_001"
              apiBaseUrl="http://localhost:8000"
              wsBaseUrl="ws://localhost:8000"
            />
          </div>
        )}
      </main>
    </div>
  );
}

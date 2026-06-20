"""
🌸 若曦V2 - 用户偏好设置组件
管理用户的个性化设置
"""

import React, { useState, useEffect } from 'react';
import {
  Settings, Bell, Moon, Sun, Globe,
  Layout, Shield, CheckCircle, RefreshCw,
  ChevronRight, ToggleLeft, ToggleRight,
  Mail, MessageSquare, Smartphone
} from 'lucide-react';

interface Preferences {
  theme: string;
  language: string;
  data_display_days: number;
  chart_type: string;
  notification_email: boolean;
  notification_push: boolean;
  notification_sms: boolean;
  daily_summary_time: string;
  weekly_report_day: string;
  share_anonymous_data: boolean;
  allow_ai_analysis: boolean;
  dashboard_cards: string[];
}

interface PreferenceSettingsProps {
  apiBaseUrl: string;
  userToken: string;
}

export const PreferenceSettings: React.FC<PreferenceSettingsProps> = ({
  apiBaseUrl,
  userToken
}) => {
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'general' | 'notifications' | 'privacy' | 'dashboard'>('general');
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  useEffect(() => {
    fetchPreferences();
  }, []);

  const fetchPreferences = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/preferences/`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      
      if (res.ok) {
        const result = await res.json();
        setPrefs(result.preferences);
      }
    } catch (e) {
      console.error('获取偏好设置失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const updatePreference = async (key: string, value: any) => {
    setSaving(true);
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/preferences/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${userToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ [key]: value })
      });
      
      if (res.ok) {
        setPrefs({ ...prefs!, [key]: value });
        setMessage({ type: 'success', text: '设置已保存' });
        setTimeout(() => setMessage(null), 3000);
      }
    } catch (e) {
      setMessage({ type: 'error', text: '保存失败' });
    } finally {
      setSaving(false);
    }
  };

  const resetPreferences = async () => {
    if (!confirm('确定要重置所有设置为默认值吗？')) return;
    
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/preferences/reset-all`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      
      if (res.ok) {
        fetchPreferences();
        setMessage({ type: 'success', text: '设置已重置' });
      }
    } catch (e) {
      setMessage({ type: 'error', text: '重置失败' });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!prefs) {
    return <div className="text-center py-12 text-gray-500">加载失败</div>;
  }

  const Toggle = ({ label, value, onChange, description }: any) => (
    <div className="flex items-center justify-between py-4 border-b border-gray-100 last:border-0">
      <div>
        <div className="font-medium text-gray-800">{label}</div>
        {description && <div className="text-sm text-gray-500">{description}</div>}
      </div>
      <button
        onClick={() => onChange(!value)}
        className={`relative w-14 h-8 rounded-full transition-colors ${
          value ? 'bg-blue-500' : 'bg-gray-300'
        }`}
      >
        <div className={`absolute top-1 w-6 h-6 bg-white rounded-full transition-transform ${
          value ? 'translate-x-7' : 'translate-x-1'
        }`} />
      </button>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* 头部 */}
      <div className="bg-gradient-to-r from-gray-800 to-gray-900 rounded-2xl p-6 text-white">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Settings className="w-6 h-6" />
          偏好设置
        </h2>
        <p className="text-gray-400 mt-1">个性化您的使用体验</p>
      </div>

      {/* 消息提示 */}
      {message && (
        <div className={`rounded-xl p-4 flex items-center gap-3 ${
          message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
        }`}>
          <CheckCircle className="w-5 h-5" />
          {message.text}
        </div>
      )}

      {/* 标签页 */}
      <div className="flex gap-2 bg-gray-100 p-1 rounded-xl">
        {[
          { id: 'general', label: '通用', icon: Settings },
          { id: 'notifications', label: '通知', icon: Bell },
          { id: 'privacy', label: '隐私', icon: Shield },
          { id: 'dashboard', label: '仪表板', icon: Layout }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg font-medium transition-all ${
              activeTab === tab.id 
                ? 'bg-white text-blue-600 shadow-sm' 
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* 通用设置 */}
      {activeTab === 'general' && (
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">通用设置</h3>
          
          {/* 主题 */}
          <div className="mb-6">
            <label className="block font-medium text-gray-700 mb-3">界面主题</label>
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => updatePreference('theme', 'light')}
                className={`p-4 rounded-xl border-2 text-center transition-all ${
                  prefs.theme === 'light' 
                    ? 'border-blue-500 bg-blue-50 text-blue-700' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <Sun className="w-6 h-6 mx-auto mb-2" />
                <div className="font-medium">浅色</div>
              </button>
              <button
                onClick={() => updatePreference('theme', 'dark')}
                className={`p-4 rounded-xl border-2 text-center transition-all ${
                  prefs.theme === 'dark' 
                    ? 'border-blue-500 bg-blue-50 text-blue-700' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <Moon className="w-6 h-6 mx-auto mb-2" />
                <div className="font-medium">深色</div>
              </button>
            </div>
          </div>

          {/* 语言 */}
          <div className="mb-6">
            <label className="block font-medium text-gray-700 mb-3">语言</label>
            <select
              value={prefs.language}
              onChange={(e) => updatePreference('language', e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="zh-CN">简体中文</option>
              <option value="zh-TW">繁體中文</option>
              <option value="en">English</option>
            </select>
          </div>

          {/* 数据显示天数 */}
          <div className="mb-6">
            <label className="block font-medium text-gray-700 mb-3">
              默认显示天数: {prefs.data_display_days}天
            </label>
            <input
              type="range"
              min="7"
              max="90"
              step="7"
              value={prefs.data_display_days}
              onChange={(e) => updatePreference('data_display_days', parseInt(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>7天</span>
              <span>90天</span>
            </div>
          </div>
        </div>
      )}

      {/* 通知设置 */}
      {activeTab === 'notifications' && (
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">通知设置</h3>
          
          <Toggle
            label="邮件通知"
            description="接收健康报告和提醒邮件"
            value={prefs.notification_email}
            onChange={(v: boolean) => updatePreference('notification_email', v)}
          />
          
          <Toggle
            label="推送通知"
            description="接收实时推送提醒"
            value={prefs.notification_push}
            onChange={(v: boolean) => updatePreference('notification_push', v)}
          />
          
          <Toggle
            label="短信通知"
            description="重要健康警报通过短信发送"
            value={prefs.notification_sms}
            onChange={(v: boolean) => updatePreference('notification_sms', v)}
          />

          <div className="mt-6 pt-6 border-t border-gray-100">
            <label className="block font-medium text-gray-700 mb-3">每日摘要推送时间</label>
            <input
              type="time"
              value={prefs.daily_summary_time}
              onChange={(e) => updatePreference('daily_summary_time', e.target.value)}
              className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      )}

      {/* 隐私设置 */}
      {activeTab === 'privacy' && (
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">隐私设置</h3>
          
          <Toggle
            label="匿名数据分享"
            description="匿名分享数据用于改善AI分析算法"
            value={prefs.share_anonymous_data}
            onChange={(v: boolean) => updatePreference('share_anonymous_data', v)}
          />
          
          <Toggle
            label="允许AI分析"
            description="允许AI分析您的健康数据生成洞察"
            value={prefs.allow_ai_analysis}
            onChange={(v: boolean) => updatePreference('allow_ai_analysis', v)}
          />

          <div className="mt-6 p-4 bg-blue-50 rounded-xl">
            <div className="flex items-start gap-3">
              <Shield className="w-5 h-5 text-blue-500 mt-0.5" />
              <div className="text-sm text-blue-700">
                <p className="font-medium mb-1">数据安全</p>
                <p>您的健康数据经过加密存储，只有您可以访问。我们不会将您的个人数据出售给第三方。</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 仪表板设置 */}
      {activeTab === 'dashboard' && (
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">仪表板卡片</h3>
          <p className="text-gray-600 mb-4">选择要在仪表板显示的卡片</p>
          
          <div className="space-y-3">
            {[
              { id: 'health_summary', label: '健康摘要', icon: '❤️' },
              { id: 'quick_actions', label: '快捷操作', icon: '⚡' },
              { id: 'today_medications', label: '今日用药', icon: '💊' },
              { id: 'recent_records', label: '最近记录', icon: '📝' },
              { id: 'goal_progress', label: '目标进度', icon: '🎯' },
              { id: 'ai_insights', label: 'AI洞察', icon: '🔮' }
            ].map(card => (
              <div
                key={card.id}
                onClick={() => {
                  const newCards = prefs.dashboard_cards.includes(card.id)
                    ? prefs.dashboard_cards.filter(c => c !== card.id)
                    : [...prefs.dashboard_cards, card.id];
                  updatePreference('dashboard_cards', newCards);
                }}
                className={`flex items-center justify-between p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  prefs.dashboard_cards.includes(card.id)
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{card.icon}</span>
                  <span className="font-medium text-gray-800">{card.label}</span>
                </div>
                {prefs.dashboard_cards.includes(card.id) && (
                  <CheckCircle className="w-5 h-5 text-blue-500" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 重置按钮 */}
      <button
        onClick={resetPreferences}
        className="w-full py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
      >
        重置所有设置为默认值
      </button>
    </div>
  );
};

export default PreferenceSettings;

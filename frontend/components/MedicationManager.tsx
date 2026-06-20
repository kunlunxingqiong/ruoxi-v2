"""
🌸 若曦V2 - 用药管理组件
React组件用于管理用药记录和查看提醒
"""

import React, { useState, useEffect } from 'react';
import {
  Plus, Pill, Clock, CheckCircle, XCircle, Calendar,
  AlertCircle, TrendingUp, ChevronRight, MoreVertical
} from 'lucide-react';

// 用药数据结构
interface Medication {
  id: number;
  name: string;
  dosage: string;
  frequency: string;
  purpose?: string;
  reminder_time?: string;
  reminder_enabled: boolean;
  is_active: boolean;
  start_date?: string;
  end_date?: string;
}

interface MedicationLog {
  id: number;
  taken_at: string;
  skipped: boolean;
  skip_reason?: string;
  dosage_taken?: string;
}

interface ScheduleItem {
  medication_id: number;
  name: string;
  dosage: string;
  frequency: string;
  reminder_time?: string;
  purpose?: string;
  status: 'pending' | 'taken' | 'skipped';
  taken_at?: string;
  log_id?: number;
}

interface MedicationSummary {
  active_medications: number;
  today_schedule: {
    total: number;
    pending: number;
    taken: number;
    skipped: number;
    completion_rate: number;
  };
  adherence: {
    adherence_rate: number;
    status: string;
    recommendation: string;
  };
  recent_missed_count: number;
}

interface MedicationManagerProps {
  apiBaseUrl: string;
  userToken: string;
}

export const MedicationManager: React.FC<MedicationManagerProps> = ({
  apiBaseUrl,
  userToken
}) => {
  const [medications, setMedications] = useState<Medication[]>([]);
  const [todaySchedule, setTodaySchedule] = useState<ScheduleItem[]>([]);
  const [summary, setSummary] = useState<MedicationSummary | null>(null);
  const [activeTab, setActiveTab] = useState<'today' | 'all' | 'history'>('today');
  const [isLoading, setIsLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);

  // 表单状态
  const [newMed, setNewMed] = useState({
    name: '',
    dosage: '',
    frequency: '每日1次',
    purpose: '',
    reminder_time: '08:00',
    reminder_enabled: true
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      // 获取今日计划
      const scheduleRes = await fetch(`${apiBaseUrl}/api/v1/medications/schedule/today`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      const scheduleData = await scheduleRes.json();
      if (scheduleData.success) {
        setTodaySchedule(scheduleData.schedule);
        setSummary(prev => prev ? {...prev, today_schedule: scheduleData.summary} : null);
      }

      // 获取所有用药
      const medsRes = await fetch(`${apiBaseUrl}/api/v1/medications?active_only=true`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      const medsData = await medsRes.json();
      setMedications(medsData);

      // 获取摘要
      const summaryRes = await fetch(`${apiBaseUrl}/api/v1/medications/summary`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      const summaryData = await summaryRes.json();
      if (summaryData.success) {
        setSummary(summaryData.summary);
      }
    } catch (error) {
      console.error('获取用药数据失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTakeMedication = async (medicationId: number) => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/medications/${medicationId}/take`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${userToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (res.ok) {
        fetchData(); // 刷新数据
      }
    } catch (error) {
      console.error('记录服药失败:', error);
    }
  };

  const handleSkipMedication = async (medicationId: number, reason?: string) => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/medications/${medicationId}/skip`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${userToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ reason })
      });
      
      if (res.ok) {
        fetchData();
      }
    } catch (error) {
      console.error('记录跳过失败:', error);
    }
  };

  const handleAddMedication = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/medications`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${userToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newMed)
      });
      
      if (res.ok) {
        setShowAddForm(false);
        setNewMed({
          name: '',
          dosage: '',
          frequency: '每日1次',
          purpose: '',
          reminder_time: '08:00',
          reminder_enabled: true
        });
        fetchData();
      }
    } catch (error) {
      console.error('添加用药失败:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-pink-300 border-t-pink-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* 头部卡片 */}
      <div className="bg-gradient-to-r from-pink-100 to-purple-100 rounded-2xl p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <Pill className="w-6 h-6 text-pink-500" />
              用药管理
            </h2>
            <p className="text-gray-600 mt-1">
              {summary ? `当前${summary.active_medications}种用药，今日${summary.today_schedule?.completion_rate || 0}%已服用` : '管理您的日常用药'}
            </p>
          </div>
          <button
            onClick={() => setShowAddForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600 transition-colors"
          >
            <Plus className="w-4 h-4" />
            添加用药
          </button>
        </div>

        {/* 今日进度 */}
        {summary?.today_schedule && (
          <div className="mt-4 pt-4 border-t border-pink-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-800">{summary.today_schedule.total}</p>
                  <p className="text-xs text-gray-500">今日计划</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">{summary.today_schedule.taken}</p>
                  <p className="text-xs text-gray-500">已服用</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-orange-500">{summary.today_schedule.pending}</p>
                  <p className="text-xs text-gray-500">待服用</p>
                </div>
              </div>
              
              {/* 依从性 */}
              {summary.adherence && (
                <div className="flex items-center gap-3">
                  <TrendingUp className={`w-5 h-5 ${
                    summary.adherence.adherence_rate >= 80 ? 'text-green-500' : 
                    summary.adherence.adherence_rate >= 50 ? 'text-yellow-500' : 'text-red-500'
                  }`} />
                  <div>
                    <p className="text-sm font-medium">
                      依从性 {summary.adherence.adherence_rate}%
                    </p>
                    <p className="text-xs text-gray-500">
                      {summary.adherence.status === 'excellent' ? '优秀' :
                       summary.adherence.status === 'good' ? '良好' :
                       summary.adherence.status === 'fair' ? '一般' : '需改善'}
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* 进度条 */}
            <div className="mt-3 h-2 bg-white rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-green-400 to-green-500 transition-all duration-500"
                style={{ width: `${summary.today_schedule.completion_rate}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* 标签切换 */}
      <div className="flex gap-2 mb-6">
        {(['today', 'all', 'history'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === tab 
                ? 'bg-pink-500 text-white' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {tab === 'today' && '今日计划'}
            {tab === 'all' && '所有用药'}
            {tab === 'history' && '历史记录'}
          </button>
        ))}
      </div>

      {/* 今日计划 */}
      {activeTab === 'today' && (
        <div className="space-y-3">
          {todaySchedule.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <Pill className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>今日没有用药计划</p>
              <button 
                onClick={() => setShowAddForm(true)}
                className="mt-4 text-pink-500 hover:underline"
              >
                添加用药提醒
              </button>
            </div>
          ) : (
            todaySchedule.map((item) => (
              <MedicationScheduleCard
                key={item.medication_id}
                item={item}
                onTake={() => handleTakeMedication(item.medication_id)}
                onSkip={() => handleSkipMedication(item.medication_id)}
              />
            ))
          )}
        </div>
      )}

      {/* 所有用药 */}
      {activeTab === 'all' && (
        <div className="space-y-3">
          {medications.map((med) => (
            <MedicationCard key={med.id} medication={med} />
          ))}
        </div>
      )}

      {/* 添加用药弹窗 */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md m-4">
            <h3 className="text-lg font-bold mb-4">添加新用药</h3>
            <form onSubmit={handleAddMedication} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">药物名称</label>
                <input
                  type="text"
                  value={newMed.name}
                  onChange={(e) => setNewMed({...newMed, name: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-pink-500 outline-none"
                  placeholder="如：阿司匹林"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">剂量</label>
                <input
                  type="text"
                  value={newMed.dosage}
                  onChange={(e) => setNewMed({...newMed, dosage: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-pink-500 outline-none"
                  placeholder="如：100mg"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">频次</label>
                <select
                  value={newMed.frequency}
                  onChange={(e) => setNewMed({...newMed, frequency: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-pink-500 outline-none"
                >
                  <option>每日1次</option>
                  <option>每日2次</option>
                  <option>每日3次</option>
                  <option>每周1次</option>
                  <option>每周2次</option>
                  <option>每2天1次</option>
                  <option>按需服用</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">提醒时间</label>
                <input
                  type="time"
                  value={newMed.reminder_time}
                  onChange={(e) => setNewMed({...newMed, reminder_time: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-pink-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">用途（可选）</label>
                <input
                  type="text"
                  value={newMed.purpose}
                  onChange={(e) => setNewMed({...newMed, purpose: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-pink-500 outline-none"
                  placeholder="如：降血压"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600"
                >
                  添加
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// 今日用药计划卡片
const MedicationScheduleCard: React.FC<{
  item: ScheduleItem;
  onTake: () => void;
  onSkip: () => void;
}> = ({ item, onTake, onSkip }) => {
  const isOverdue = item.status === 'pending' && item.reminder_time && 
    new Date().toTimeString().slice(0, 5) > item.reminder_time;

  return (
    <div className={`p-4 rounded-xl border-2 transition-all ${
      item.status === 'taken' ? 'bg-green-50 border-green-200' :
      item.status === 'skipped' ? 'bg-gray-50 border-gray-200' :
      isOverdue ? 'bg-red-50 border-red-200' :
      'bg-white border-gray-200 hover:border-pink-300'
    }`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
            item.status === 'taken' ? 'bg-green-500 text-white' :
            item.status === 'skipped' ? 'bg-gray-400 text-white' :
            isOverdue ? 'bg-red-500 text-white' :
            'bg-pink-100 text-pink-500'
          }`}>
            {item.status === 'taken' ? <CheckCircle className="w-5 h-5" /> :
             item.status === 'skipped' ? <XCircle className="w-5 h-5" /> :
             <Pill className="w-5 h-5" />}
          </div>
          <div>
            <p className="font-medium text-gray-800">{item.name}</p>
            <p className="text-sm text-gray-500">{item.dosage} · {item.frequency}</p>
            {item.purpose && (
              <p className="text-xs text-gray-400 mt-0.5">{item.purpose}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="flex items-center gap-1 text-sm">
              <Clock className="w-4 h-4" />
              <span className={isOverdue ? 'text-red-500 font-medium' : 'text-gray-600'}>
                {item.reminder_time || '--:--'}
              </span>
            </div>
            {item.status === 'taken' && item.taken_at && (
              <p className="text-xs text-green-600">
                已服用 {new Date(item.taken_at).toLocaleTimeString('zh-CN', {hour: '2-digit', minute:'2-digit'})}
              </p>
            )}
          </div>

          {item.status === 'pending' && (
            <div className="flex gap-2">
              <button
                onClick={onTake}
                className="px-4 py-2 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 transition-colors"
              >
                服用
              </button>
              <button
                onClick={onSkip}
                className="px-4 py-2 bg-gray-200 text-gray-600 rounded-lg text-sm hover:bg-gray-300 transition-colors"
              >
                跳过
              </button>
            </div>
          )}
        </div>
      </div>

      {isOverdue && (
        <div className="mt-3 flex items-center gap-2 text-red-600 text-sm">
          <AlertCircle className="w-4 h-4" />
          <span>已错过提醒时间</span>
        </div>
      )}
    </div>
  );
};

// 用药信息卡片
const MedicationCard: React.FC<{ medication: Medication }> = ({ medication }) => {
  return (
    <div className="p-4 bg-white rounded-xl border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
            <Pill className="w-5 h-5 text-blue-500" />
          </div>
          <div>
            <p className="font-medium text-gray-800">{medication.name}</p>
            <p className="text-sm text-gray-500">{medication.dosage} · {medication.frequency}</p>
            {medication.purpose && (
              <p className="text-xs text-gray-400 mt-0.5">用途：{medication.purpose}</p>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {medication.reminder_enabled && medication.reminder_time && (
            <span className="flex items-center gap-1 px-2 py-1 bg-pink-50 text-pink-600 rounded-full text-xs">
              <Clock className="w-3 h-3" />
              {medication.reminder_time}
            </span>
          )}
          <button className="p-2 hover:bg-gray-100 rounded-lg">
            <MoreVertical className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between text-sm">
        <div className="flex items-center gap-4 text-gray-500">
          <span className="flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            开始：{medication.start_date || '未设置'}
          </span>
          {medication.end_date && (
            <span className="flex items-center gap-1">
              结束：{medication.end_date}
            </span>
          )}
        </div>
        <button className="flex items-center gap-1 text-pink-500 hover:text-pink-600">
          查看历史
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default MedicationManager;

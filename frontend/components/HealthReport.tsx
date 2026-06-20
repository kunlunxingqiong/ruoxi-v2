"""
🌸 若曦V2 - 健康报告组件
生成和导出健康报告
"""

import React, { useState, useEffect } from 'react';
import { 
  FileText, Download, Calendar, TrendingUp, 
  Activity, Heart, Scale, Moon, Pill, Target,
  ChevronLeft, ChevronRight, RefreshCw, CheckCircle,
  AlertCircle, Loader2
} from 'lucide-react';

// 报告类型
interface ReportType {
  key: string;
  label: string;
  days: number;
  icon: React.ReactNode;
  description: string;
}

const REPORT_TYPES: ReportType[] = [
  { 
    key: 'daily', 
    label: '日报', 
    days: 1, 
    icon: <Calendar className="w-5 h-5" />,
    description: '今日健康快照'
  },
  { 
    key: 'weekly', 
    label: '周报', 
    days: 7, 
    icon: <Calendar className="w-5 h-5" />,
    description: '本周健康总结'
  },
  { 
    key: 'monthly', 
    label: '月报', 
    days: 30, 
    icon: <Calendar className="w-5 h-5" />,
    description: '月度健康趋势'
  },
  { 
    key: 'quarterly', 
    label: '季报', 
    days: 90, 
    icon: <TrendingUp className="w-5 h-5" />,
    description: '季度健康分析'
  }
];

// 健康评分
interface HealthScore {
  overall: number;
  interpretation: string;
  details: Record<string, number>;
}

// 报告数据
interface ReportData {
  health_score?: HealthScore;
  data_summary?: {
    blood_pressure_records: number;
    glucose_records: number;
    weight_records: number;
    sleep_records: number;
    heart_rate_records: number;
    total_data_points: number;
  };
  recommendations?: Array<{
    category: string;
    priority: string;
    message: string;
    actions: string[];
  }>;
}

interface HealthReportProps {
  apiBaseUrl: string;
  userToken: string;
}

export const HealthReport: React.FC<HealthReportProps> = ({
  apiBaseUrl,
  userToken
}) => {
  const [selectedType, setSelectedType] = useState<ReportType>(REPORT_TYPES[1]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [healthScore, setHealthScore] = useState<HealthScore | null>(null);
  const [activeTab, setActiveTab] = useState<'generate' | 'preview'>('generate');
  const [recommendations, setRecommendations] = useState<any[]>([]);

  // 获取健康评分
  useEffect(() => {
    fetchHealthScore();
    fetchRecommendations();
  }, []);

  const fetchHealthScore = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/reports/health-score`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setHealthScore(data.score);
      }
    } catch (e) {
      console.error('获取健康评分失败:', e);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/reports/recommendations?days=30`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setRecommendations(data.recommendations || []);
      }
    } catch (e) {
      console.error('获取建议失败:', e);
    }
  };

  const generateReport = async () => {
    setIsGenerating(true);
    try {
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - selectedType.days + 1);

      const res = await fetch(`${apiBaseUrl}/api/v1/reports/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`
        },
        body: JSON.stringify({
          report_type: selectedType.key,
          include_charts: true,
          include_recommendations: true
        })
      });

      if (res.ok) {
        const data = await res.json();
        setReportData(data.full_data);
        setActiveTab('preview');
      }
    } catch (e) {
      console.error('生成报告失败:', e);
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadPDF = async () => {
    // 模拟PDF下载
    alert('PDF生成功能开发中，可先查看JSON数据预览');
  };

  // 获取评分颜色
  const getScoreColor = (score: number) => {
    if (score >= 90) return '#4caf50';
    if (score >= 80) return '#8bc34a';
    if (score >= 70) return '#ff9800';
    if (score >= 60) return '#ff5722';
    return '#f44336';
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <FileText className="w-6 h-6 text-blue-500" />
          健康报告
        </h2>
        <p className="text-gray-600 mt-2">
          生成专业健康报告，追踪您的健康趋势
        </p>
      </div>

      {/* 健康评分卡片 */}
      {healthScore && (
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex items-center gap-6">
            <div 
              className="w-32 h-32 rounded-full flex items-center justify-center"
              style={{ 
                background: `conic-gradient(${getScoreColor(healthScore.overall || 0)} ${(healthScore.overall || 0) * 3.6}deg, #e0e0e0 0deg)`
              }}
            >
              <div className="w-28 h-28 bg-white rounded-full flex flex-col items-center justify-center">
                <span className="text-4xl font-bold" style={{ color: getScoreColor(healthScore.overall || 0) }}>
                  {healthScore.overall}
                </span>
                <span className="text-xs text-gray-500">健康评分</span>
              </div>
            </div>
            <div className="flex-1">
              <h4 className="text-xl font-semibold mb-2">{healthScore.interpretation}</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                {Object.entries(healthScore.details || {}).map(([key, score]) => (
                  <div key={key} className="bg-gray-50 rounded-lg p-3">
                    <div className="text-xs text-gray-500 capitalize">
                      {key === 'blood_pressure' && '血压'}
                      {key === 'glucose' && '血糖'}
                      {key === 'weight' && '体重'}
                      {key === 'sleep' && '睡眠'}
                      {key === 'heart_rate' && '心率'}
                    </div>
                    <div className="text-lg font-semibold" style={{ color: getScoreColor(score) }}>
                      {Math.round(score)}分
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab切换 */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('generate')}
          className={`px-6 py-3 rounded-xl font-medium transition-colors ${
            activeTab === 'generate' 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          生成报告
        </button>
        <button
          onClick={() => setActiveTab('preview')}
          className={`px-6 py-3 rounded-xl font-medium transition-colors ${
            activeTab === 'preview' 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          报告预览
        </button>
      </div>

      {activeTab === 'generate' ? (
        <div className="space-y-6">
          {/* 报告类型选择 */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4">选择报告类型</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {REPORT_TYPES.map(type => (
                <button
                  key={type.key}
                  onClick={() => setSelectedType(type)}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    selectedType.key === type.key
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${
                    selectedType.key === type.key ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {type.icon}
                  </div>
                  <div className="font-semibold">{type.label}</div>
                  <div className="text-sm text-gray-500">{type.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* 生成按钮 */}
          <button
            onClick={generateReport}
            disabled={isGenerating}
            className="w-full py-4 bg-blue-500 text-white rounded-xl font-semibold hover:bg-blue-600 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                生成中...
              </>
            ) : (
              <>
                <FileText className="w-5 h-5" />
                生成{selectedType.label}
              </>
            )}
          </button>

          {/* 个性化建议预览 */}
          {recommendations.length > 0 && (
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-500" />
                当前建议
              </h3>
              <div className="space-y-3">
                {recommendations.slice(0, 3).map((rec, idx) => (
                  <div 
                    key={idx}
                    className={`p-4 rounded-xl border-l-4 ${
                      rec.priority === 'high' ? 'bg-red-50 border-red-500' :
                      rec.priority === 'medium' ? 'bg-orange-50 border-orange-500' :
                      'bg-green-50 border-green-500'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-medium text-gray-800">{rec.category}</div>
                        <p className="text-sm text-gray-600 mt-1">{rec.message}</p>
                        {rec.actions && (
                          <div className="flex gap-2 mt-2">
                            {rec.actions.map((action: string, i: number) => (
                              <span key={i} className="text-xs bg-white px-2 py-1 rounded">
                                {action}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <span className={`text-xs px-2 py-1 rounded ${
                        rec.priority === 'high' ? 'bg-red-100 text-red-600' :
                        rec.priority === 'medium' ? 'bg-orange-100 text-orange-600' :
                        'bg-green-100 text-green-600'
                      }`}>
                        {rec.priority === 'high' ? '高优先级' : 
                         rec.priority === 'medium' ? '中优先级' : '低优先级'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          {/* 报告预览 */}
          {reportData ? (
            <>
              {/* 数据概览 */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">数据概览</h3>
                  <button
                    onClick={downloadPDF}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg flex items-center gap-2 hover:bg-blue-600"
                  >
                    <Download className="w-4 h-4" />
                    导出PDF
                  </button>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-red-50 rounded-xl p-4 text-center">
                    <Activity className="w-8 h-8 mx-auto mb-2 text-red-500" />
                    <div className="text-2xl font-bold text-red-600">
                      {reportData.data_summary?.blood_pressure_records || 0}
                    </div>
                    <div className="text-sm text-gray-600">血压记录</div>
                  </div>
                  <div className="bg-blue-50 rounded-xl p-4 text-center">
                    <Heart className="w-8 h-8 mx-auto mb-2 text-blue-500" />
                    <div className="text-2xl font-bold text-blue-600">
                      {reportData.data_summary?.glucose_records || 0}
                    </div>
                    <div className="text-sm text-gray-600">血糖记录</div>
                  </div>
                  <div className="bg-green-50 rounded-xl p-4 text-center">
                    <Scale className="w-8 h-8 mx-auto mb-2 text-green-500" />
                    <div className="text-2xl font-bold text-green-600">
                      {reportData.data_summary?.weight_records || 0}
                    </div>
                    <div className="text-sm text-gray-600">体重记录</div>
                  </div>
                  <div className="bg-purple-50 rounded-xl p-4 text-center">
                    <Moon className="w-8 h-8 mx-auto mb-2 text-purple-500" />
                    <div className="text-2xl font-bold text-purple-600">
                      {reportData.data_summary?.sleep_records || 0}
                    </div>
                    <div className="text-sm text-gray-600">睡眠记录</div>
                  </div>
                </div>
              </div>

              {/* 健康评分详情 */}
              {reportData.health_score && (
                <div className="bg-white rounded-2xl shadow-lg p-6">
                  <h3 className="text-lg font-semibold mb-4">健康评分详情</h3>
                  <div className="text-center mb-6">
                    <div className="inline-block">
                      <div className="text-5xl font-bold" style={{ 
                        color: getScoreColor(reportData.health_score.overall || 0) 
                      }}>
                        {reportData.health_score.overall}
                      </div>
                      <div className="text-gray-500 mt-2">{reportData.health_score.interpretation}</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(reportData.health_score.details || {}).map(([key, score]) => (
                      <div key={key} className="text-center p-4 bg-gray-50 rounded-xl">
                        <div className="text-xs text-gray-500 mb-1 capitalize">
                          {key === 'blood_pressure' && '血压'}
                          {key === 'glucose' && '血糖'}
                          {key === 'weight' && '体重'}
                          {key === 'sleep' && '睡眠'}
                          {key === 'heart_rate' && '心率'}
                        </div>
                        <div className="text-xl font-bold" style={{ color: getScoreColor(score) }}>
                          {Math.round(score)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 健康建议 */}
              {reportData.recommendations && reportData.recommendations.length > 0 && (
                <div className="bg-white rounded-2xl shadow-lg p-6">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-blue-500" />
                    健康建议
                  </h3>
                  <div className="space-y-3">
                    {reportData.recommendations.map((rec, idx) => (
                      <div 
                        key={idx}
                        className={`p-4 rounded-xl ${
                          rec.priority === 'high' ? 'bg-red-50' :
                          rec.priority === 'medium' ? 'bg-orange-50' :
                          'bg-green-50'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <span className={`text-xs px-2 py-1 rounded ${
                              rec.priority === 'high' ? 'bg-red-100 text-red-600' :
                              rec.priority === 'medium' ? 'bg-orange-100 text-orange-600' :
                              'bg-green-100 text-green-600'
                            }`}>
                              {rec.priority === 'high' ? '高优先级' : 
                               rec.priority === 'medium' ? '中优先级' : '低优先级'}
                            </span>
                            <div className="font-medium mt-2">{rec.category}</div>
                            <p className="text-sm text-gray-600 mt-1">{rec.message}</p>
                          </div>
                        </div>
                        {rec.actions && (
                          <div className="flex gap-2 mt-3">
                            {rec.actions.map((action: string, i: number) => (
                              <span key={i} className="text-xs bg-white px-3 py-1.5 rounded-lg shadow-sm">
                                {action}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="bg-white rounded-2xl shadow-lg p-12 text-center text-gray-500">
              <FileText className="w-16 h-16 mx-auto mb-4 opacity-30" />
              <p>暂无报告数据</p>
              <button
                onClick={() => setActiveTab('generate')}
                className="mt-4 px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                生成报告
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default HealthReport;

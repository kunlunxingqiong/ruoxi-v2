"""
🌸 若曦V2 - 健康预测组件
展示AI预测的健康趋势
"""

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, Minus, AlertCircle,
  Activity, Heart, Scale, Moon, Brain,
  ChevronRight, ChevronLeft, RefreshCw, Info
} from 'lucide-react';

// 预测数据类型
interface Prediction {
  metric: string;
  current_value: number | string;
  predicted_7d: number | string;
  predicted_30d: number | string;
  confidence_7d: number;
  confidence_30d: number;
  trend_direction: 'increasing' | 'decreasing' | 'stable';
  risk_level: 'low' | 'medium' | 'high' | 'critical';
}

interface HealthPredictionsProps {
  apiBaseUrl: string;
  userToken: string;
}

export const HealthPredictions: React.FC<HealthPredictionsProps> = ({
  apiBaseUrl,
  userToken
}) => {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<'7d' | '30d'>('7d');

  useEffect(() => {
    fetchPredictions();
  }, []);

  const fetchPredictions = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/ai/analysis/predictions`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        const predArray = Object.entries(data.predictions || {}).map(
          ([key, value]: [string, any]) => ({
            metric: key,
            ...value
          })
        );
        setPredictions(predArray);
      }
    } catch (e) {
      console.error('获取预测失败:', e);
    } finally {
      setLoading(false);
    }
  };

  // 获取指标图标
  const getMetricIcon = (metric: string) => {
    switch (metric) {
      case 'blood_pressure': return <Activity className="w-6 h-6 text-red-500" />;
      case 'glucose': return <Heart className="w-6 h-6 text-blue-500" />;
      case 'weight': return <Scale className="w-6 h-6 text-green-500" />;
      case 'sleep': return <Moon className="w-6 h-6 text-purple-500" />;
      case 'heart_rate': return <Heart className="w-6 h-6 text-pink-500" />;
      default: return <Brain className="w-6 h-6 text-gray-500" />;
    }
  };

  // 获取指标中文名称
  const getMetricName = (metric: string) => {
    const names: { [key: string]: string } = {
      'blood_pressure': '血压',
      'glucose': '血糖',
      'weight': '体重',
      'sleep': '睡眠',
      'heart_rate': '心率'
    };
    return names[metric] || metric;
  };

  // 获取趋势图标
  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'increasing': return <TrendingUp className="w-5 h-5 text-orange-500" />;
      case 'decreasing': return <TrendingDown className="w-5 h-5 text-blue-500" />;
      default: return <Minus className="w-5 h-5 text-gray-500" />;
    }
  };

  // 获取风险颜色
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-100 text-red-700';
      case 'high': return 'bg-orange-100 text-orange-700';
      case 'medium': return 'bg-yellow-100 text-yellow-700';
      default: return 'bg-green-100 text-green-700';
    }
  };

  // 格式化预测值
  const formatValue = (metric: string, value: number | string) => {
    if (metric === 'blood_pressure' && typeof value === 'string' && value.includes('/')) {
      return value;
    }
    return typeof value === 'number' ? value.toFixed(1) : value;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-6 flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-3 text-gray-600">AI分析中...</span>
      </div>
    );
  }

  if (predictions.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
        <Brain className="w-16 h-16 mx-auto mb-4 text-gray-300" />
        <h3 className="text-lg font-semibold text-gray-700">暂无预测数据</h3>
        <p className="text-gray-500 mt-2">需要至少7天的连续健康数据才能生成预测</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 头部 */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              <Brain className="w-6 h-6 text-indigo-500" />
              AI健康预测
            </h2>
            <p className="text-gray-600 mt-1">
              基于历史数据趋势预测未来健康状况
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setSelectedPeriod('7d')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedPeriod === '7d' 
                  ? 'bg-indigo-500 text-white' 
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              7天预测
            </button>
            <button
              onClick={() => setSelectedPeriod('30d')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedPeriod === '30d' 
                  ? 'bg-indigo-500 text-white' 
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              30天预测
            </button>
          </div>
        </div>
      </div>

      {/* 预测卡片网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {predictions.map((pred, idx) => {
          const predictedValue = selectedPeriod === '7d' ? pred.predicted_7d : pred.predicted_30d;
          const confidence = selectedPeriod === '7d' ? pred.confidence_7d : pred.confidence_30d;
          
          return (
            <div key={idx} className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              {/* 头部 */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-gray-50 flex items-center justify-center">
                    {getMetricIcon(pred.metric)}
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-800">{getMetricName(pred.metric)}</h4>
                    <div className="flex items-center gap-2 mt-1">
                      {getTrendIcon(pred.trend_direction)}
                      <span className="text-sm text-gray-500 capitalize">
                        {pred.trend_direction === 'increasing' ? '上升' : 
                         pred.trend_direction === 'decreasing' ? '下降' : '稳定'}
                      </span>
                    </div>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRiskColor(pred.risk_level)}`}>
                  {pred.risk_level === 'critical' ? '危险' : 
                   pred.risk_level === 'high' ? '高风险' : 
                   pred.risk_level === 'medium' ? '中风险' : '正常'}
                </span>
              </div>

              {/* 数值对比 */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-gray-50 rounded-xl p-4">
                  <div className="text-sm text-gray-500 mb-1">当前值</div>
                  <div className="text-2xl font-bold text-gray-800">
                    {formatValue(pred.metric, pred.current_value)}
                  </div>
                </div>
                <div className="bg-indigo-50 rounded-xl p-4">
                  <div className="text-sm text-indigo-600 mb-1">
                    {selectedPeriod === '7d' ? '7天预测' : '30天预测'}
                  </div>
                  <div className="text-2xl font-bold text-indigo-700">
                    {formatValue(pred.metric, predictedValue)}
                  </div>
                </div>
              </div>

              {/* 置信度条 */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">预测置信度</span>
                  <span className="font-medium text-gray-700">{(confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-indigo-400 to-purple-500 rounded-full transition-all"
                    style={{ width: `${confidence * 100}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 说明 */}
      <div className="bg-blue-50 rounded-2xl p-4 flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
        <div className="text-sm text-blue-700">
          <p className="font-medium mb-1">关于AI预测</p>
          <p>预测基于历史数据统计模型，仅供参考，不能替代专业医疗建议。如有健康疑虑，请咨询医生。</p>
        </div>
      </div>
    </div>
  );
};

export default HealthPredictions;

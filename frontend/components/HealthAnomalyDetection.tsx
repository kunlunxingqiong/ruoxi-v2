"""
🌸 若曦V2 - 健康异常检测组件
展示AI检测的健康异常
"""

import React, { useState, useEffect } from 'react';
import { 
  Bell, AlertTriangle, AlertCircle, Info,
  Activity, Heart, Scale, Moon, Thermometer,
  ChevronRight, RefreshCw, X, CheckCircle
} from 'lucide-react';

// 异常类型
interface Anomaly {
  metric: string;
  detected: boolean;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  current_value: number;
  expected_range: [number, number];
  deviation_percentage: number;
  recommendation: string;
}

interface HealthAnomalyDetectionProps {
  apiBaseUrl: string;
  userToken: string;
}

export const HealthAnomalyDetection: React.FC<HealthAnomalyDetectionProps> = ({
  apiBaseUrl,
  userToken
}) => {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    critical: 0,
    warning: 0
  });
  const [loading, setLoading] = useState(true);
  const [dismissedAnomalies, setDismissedAnomalies] = useState<string[]>([]);

  useEffect(() => {
    fetchAnomalies();
  }, []);

  const fetchAnomalies = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/ai/analysis/anomalies`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setAnomalies(data.anomalies?.detected_anomalies || []);
        setStats({
          total: data.alert_summary?.total || 0,
          critical: data.alert_summary?.critical || 0,
          warning: data.alert_summary?.warning || 0
        });
      }
    } catch (e) {
      console.error('获取异常检测失败:', e);
    } finally {
      setLoading(false);
    }
  };

  // 获取指标图标
  const getMetricIcon = (metric: string) => {
    switch (metric) {
      case 'blood_pressure': return <Activity className="w-5 h-5 text-red-500" />;
      case 'glucose': return <Heart className="w-5 h-5 text-blue-500" />;
      case 'weight': return <Scale className="w-5 h-5 text-green-500" />;
      case 'heart_rate': return <Thermometer className="w-5 h-5 text-pink-500" />;
      default: return <Activity className="w-5 h-5 text-gray-500" />;
    }
  };

  // 获取指标中文名称
  const getMetricName = (metric: string) => {
    const names: { [key: string]: string } = {
      'blood_pressure': '血压',
      'glucose': '血糖',
      'weight': '体重',
      'heart_rate': '心率'
    };
    return names[metric] || metric;
  };

  // 获取严重程度图标
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <AlertTriangle className="w-6 h-6 text-red-600" />;
      case 'warning': return <AlertCircle className="w-6 h-6 text-orange-500" />;
      default: return <Info className="w-6 h-6 text-blue-500" />;
    }
  };

  // 获取严重程度样式
  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'critical': 
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          badge: 'bg-red-100 text-red-700'
        };
      case 'warning': 
        return {
          bg: 'bg-orange-50',
          border: 'border-orange-200',
          badge: 'bg-orange-100 text-orange-700'
        };
      default: 
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          badge: 'bg-blue-100 text-blue-700'
        };
    }
  };

  // 忽略异常
  const dismissAnomaly = (index: number) => {
    setDismissedAnomalies([...dismissedAnomalies, index.toString()]);
  };

  const activeAnomalies = anomalies.filter((_, idx) => !dismissedAnomalies.includes(idx.toString()));

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-6 flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-3 text-gray-600">AI分析中...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 头部 */}
      <div className="bg-gradient-to-r from-red-50 to-orange-50 rounded-2xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              <Bell className="w-6 h-6 text-red-500" />
              健康异常警报
            </h2>
            <p className="text-gray-600 mt-1">
              AI自动检测健康指标异常
            </p>
          </div>
          <div className="flex gap-4">
            {stats.critical > 0 && (
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-1">
                  <span className="text-xl font-bold text-red-600">{stats.critical}</span>
                </div>
                <span className="text-sm text-red-600">严重</span>
              </div>
            )}
            {stats.warning > 0 && (
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center mx-auto mb-1">
                  <span className="text-xl font-bold text-orange-600">{stats.warning}</span>
                </div>
                <span className="text-sm text-orange-600">警告</span>
              </div>
            )}
            {stats.total === 0 && (
              <div className="flex items-center gap-2 text-green-600">
                <CheckCircle className="w-6 h-6" />
                <span>一切正常</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 异常列表 */}
      {activeAnomalies.length > 0 ? (
        <div className="space-y-4">
          {activeAnomalies.map((anomaly, idx) => {
            const style = getSeverityStyle(anomaly.severity);
            
            return (
              <div 
                key={idx}
                className={`${style.bg} border ${style.border} rounded-2xl p-5 transition-all hover:shadow-lg`}
              >
                <div className="flex items-start gap-4">
                  {/* 图标 */}
                  <div className="flex-shrink-0">
                    {getSeverityIcon(anomaly.severity)}
                  </div>

                  {/* 内容 */}
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getMetricIcon(anomaly.metric)}
                        <span className="font-semibold text-gray-800">
                          {getMetricName(anomaly.metric)}
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${style.badge}`}>
                          {anomaly.severity === 'critical' ? '严重' : 
                           anomaly.severity === 'warning' ? '警告' : '提示'}
                        </span>
                      </div>
                      <button 
                        onClick={() => dismissAnomaly(idx)}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>

                    {/* 异常信息 */}
                    <p className="text-gray-700 mb-3">{anomaly.message}</p>

                    {/* 数值详情 */}
                    <div className="bg-white rounded-xl p-3 mb-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-500">当前值</span>
                        <span className="font-semibold text-gray-800">
                          {anomaly.current_value}
                          {anomaly.deviation_percentage > 0 && (
                            <span className="text-red-500 ml-1">
                              (+{anomaly.deviation_percentage.toFixed(1)}%)
                            </span>
                          )}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm mt-1">
                        <span className="text-gray-500">正常范围</span>
                        <span className="text-gray-700">
                          {anomaly.expected_range[0]} - {anomaly.expected_range[1]}
                        </span>
                      </div>
                    </div>

                    {/* 建议 */}
                    <div className="flex items-start gap-2">
                      <CheckCircle className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-600">{anomaly.recommendation}</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-10 h-10 text-green-500" />
          </div>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">未发现健康异常</h3>
          <p className="text-gray-500 max-w-md mx-auto">
            AI已完成近期数据分析，您的健康指标在可接受范围内。请继续保持健康的生活方式！
          </p>
        </div>
      )}
    </div>
  );
};

export default HealthAnomalyDetection;

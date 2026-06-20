"""
🌸 若曦V2 - 疾病风险评估组件
展示AI评估的疾病风险
"""

import React, { useState, useEffect } from 'react';
import { 
  Shield, AlertTriangle, AlertCircle, CheckCircle,
  Heart, Activity, Scale, Stethoscope,
  ChevronDown, ChevronUp, RefreshCw, Info
} from 'lucide-react';

// 风险类型
interface RiskFactor {
  name: string;
  value: number;
  contribution: number;
}

interface DiseaseRisk {
  disease_name: string;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'very_high';
  contributing_factors: RiskFactor[];
  protective_factors: string[];
  recommendations: string[];
  screening_recommendations: string[];
}

interface HealthRiskAssessmentProps {
  apiBaseUrl: string;
  userToken: string;
}

export const HealthRiskAssessment: React.FC<HealthRiskAssessmentProps> = ({
  apiBaseUrl,
  userToken
}) => {
  const [risks, setRisks] = useState<DiseaseRisk[]>([]);
  const [overallRisk, setOverallRisk] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [expandedRisk, setExpandedRisk] = useState<string | null>(null);

  useEffect(() => {
    fetchRisks();
  }, []);

  const fetchRisks = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/ai/analysis/risks`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setRisks(data.risks || []);
        setOverallRisk(data.overall_risk);
      }
    } catch (e) {
      console.error('获取风险评估失败:', e);
    } finally {
      setLoading(false);
    }
  };

  // 获取风险图标
  const getRiskIcon = (disease: string) => {
    if (disease.includes('血压') || disease.includes('心血管')) {
      return <Heart className="w-6 h-6 text-red-500" />;
    } else if (disease.includes('糖尿')) {
      return <Activity className="w-6 h-6 text-blue-500" />;
    } else if (disease.includes('代谢')) {
      return <Scale className="w-6 h-6 text-green-500" />;
    }
    return <Stethoscope className="w-6 h-6 text-gray-500" />;
  };

  // 获取预警图标
  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'very_high': return <AlertTriangle className="w-6 h-6 text-red-600" />;
      case 'high': return <AlertCircle className="w-6 h-6 text-orange-500" />;
      case 'medium': return <Info className="w-6 h-6 text-yellow-500" />;
      default: return <CheckCircle className="w-6 h-6 text-green-500" />;
    }
  };

  // 获取风险颜色
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'very_high': return 'bg-red-100 text-red-700 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      default: return 'bg-green-100 text-green-700 border-green-200';
    }
  };

  // 获取风险等级文字
  const getRiskLevelText = (level: string) => {
    switch (level) {
      case 'very_high': return '极高风险';
      case 'high': return '高风险';
      case 'medium': return '中等风险';
      default: return '低风险';
    }
  };

  // 风险分数颜色
  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-red-600';
    if (score >= 50) return 'text-orange-600';
    if (score >= 25) return 'text-yellow-600';
    return 'text-green-600';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-6 flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-3 text-gray-600">评估中...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 头部总览 */}
      <div className="bg-gradient-to-r from-red-50 to-orange-50 rounded-2xl p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              <Shield className="w-6 h-6 text-red-500" />
              疾病风险评估
            </h2>
            <p className="text-gray-600 mt-1">
              基于您的健康数据，AI评估的患病风险
            </p>
          </div>
          {overallRisk && (
            <div className="text-right">
              <div className="text-sm text-gray-500 mb-1">综合风险评分</div>
              <div className={`text-4xl font-bold ${getScoreColor(overallRisk.average_score || 0)}`}>
                {Math.round(overallRisk.average_score || 0)}
              </div>
              <div className="text-sm text-gray-500">/ 100</div>
            </div>
          )}
        </div>
      </div>

      {/* 风险卡片列表 */}
      <div className="space-y-4">
        {risks.map((risk, idx) => (
          <div 
            key={idx}
            className="bg-white rounded-2xl shadow-lg overflow-hidden"
          >
            {/* 卡片头部 */}
            <div 
              className="p-6 cursor-pointer"
              onClick={() => setExpandedRisk(expandedRisk === risk.disease_name ? null : risk.disease_name)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-xl bg-gray-50 flex items-center justify-center">
                    {getRiskIcon(risk.disease_name)}
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-800 text-lg">{risk.disease_name}</h4>
                    <div className="flex items-center gap-2 mt-1">
                      {getAlertIcon(risk.risk_level)}
                      <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getRiskColor(risk.risk_level)}`}>
                        {getRiskLevelText(risk.risk_level)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  {/* 风险分数圆环 */}
                  <div className="relative w-16 h-16">
                    <svg className="w-full h-full transform -rotate-90">
                      <circle
                        cx="32"
                        cy="32"
                        r="28"
                        stroke="#f3f4f6"
                        strokeWidth="6"
                        fill="none"
                      />
                      <circle
                        cx="32"
                        cy="32"
                        r="28"
                        stroke={risk.risk_score >= 75 ? '#dc2626' : risk.risk_score >= 50 ? '#f97316' : risk.risk_score >= 25 ? '#eab308' : '#22c55e'}
                        strokeWidth="6"
                        fill="none"
                        strokeDasharray={`${(risk.risk_score / 100) * 176} 176`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-lg font-bold text-gray-800">
                        {Math.round(risk.risk_score)}
                      </span>
                    </div>
                  </div>

                  {/* 展开/收起图标 */}
                  {expandedRisk === risk.disease_name ? (
                    <ChevronUp className="w-6 h-6 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-6 h-6 text-gray-400" />
                  )}
                </div>
              </div>
            </div>

            {/* 展开的详细信息 */}
            {expandedRisk === risk.disease_name && (
              <div className="border-t border-gray-100 p-6 bg-gray-50">
                {/* 风险因子 */}
                {risk.contributing_factors && risk.contributing_factors.length > 0 && (
                  <div className="mb-6">
                    <h5 className="font-semibold text-gray-700 mb-3">风险因子</h5>
                    <div className="space-y-3">
                      {risk.contributing_factors.map((factor, fidx) => (
                        <div key={fidx} className="bg-white rounded-xl p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-gray-700">{factor.name}</span>
                            <span className="text-sm text-gray-500">
                              贡献度: {factor.contribution.toFixed(1)}%
                            </span>
                          </div>
                          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-orange-400 rounded-full"
                              style={{ width: `${factor.contribution}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 保护因素 */}
                {risk.protective_factors && risk.protective_factors.length > 0 && (
                  <div className="mb-6">
                    <h5 className="font-semibold text-gray-700 mb-3">保护因素 ✅</h5>
                    <div className="flex flex-wrap gap-2">
                      {risk.protective_factors.map((factor, pidx) => (
                        <span 
                          key={pidx}
                          className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm"
                        >
                          {factor}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* 建议 */}
                {risk.recommendations && risk.recommendations.length > 0 && (
                  <div className="mb-6">
                    <h5 className="font-semibold text-gray-700 mb-3">行动建议</h5>
                    <ul className="space-y-2">
                      {risk.recommendations.map((rec, ridx) => (
                        <li key={ridx} className="flex items-start gap-2">
                          <CheckCircle className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                          <span className="text-gray-700">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 筛查建议 */}
                {risk.screening_recommendations && risk.screening_recommendations.length > 0 && (
                  <div>
                    <h5 className="font-semibold text-gray-700 mb-3">筛查建议</h5>
                    <ul className="space-y-2">
                      {risk.screening_recommendations.map((screen, sidx) => (
                        <li key={sidx} className="flex items-start gap-2">
                          <Stethoscope className="w-5 h-5 text-purple-500 mt-0.5 flex-shrink-0" />
                          <span className="text-gray-700">{screen}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 免责声明 */}
      <div className="bg-gray-50 rounded-2xl p-4 flex items-start gap-3">
        <Info className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
        <div className="text-sm text-gray-600">
          <p className="font-medium mb-1">免责声明</p>
          <p>风险评估基于统计数据和医学模型，仅供参考。实际患病风险可能因个体差异而不同。如有健康疑虑，请咨询专业医生。</p>
        </div>
      </div>
    </div>
  );
};

export default HealthRiskAssessment;

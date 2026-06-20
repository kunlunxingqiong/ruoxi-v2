"""
🌸 若曦V2 - AI模型选择器组件
让用户选择和查看AI模型
"""

import React, { useState, useEffect } from 'react';
import { 
  Cpu, Zap, Globe, Server, CheckCircle, AlertCircle,
  ChevronDown, Settings, Info
} from 'lucide-react';

// 模型信息
interface ModelInfo {
  provider: string;
  model_id: string;
  display_name: string;
  capabilities: string[];
  max_tokens: number;
  context_window: number;
  is_free: boolean;
  rate_limit: {
    rpm: number;
    rpd: number;
  };
}

interface ModelSelectorProps {
  apiBaseUrl: string;
  userToken: string;
  selectedModel: string;
  onModelChange: (modelId: string) => void;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  apiBaseUrl,
  userToken,
  selectedModel,
  onModelChange
}) => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [modelHealth, setModelHealth] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    fetchModels();
    fetchHealthStatus();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/ai/models`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      const data = await response.json();
      if (data.success) {
        setModels(data.models);
      }
    } catch (error) {
      console.error('获取模型列表失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchHealthStatus = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/ai/health`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      const data = await response.json();
      if (data.success) {
        setModelHealth(data.health_status);
      }
    } catch (error) {
      console.error('获取健康状态失败:', error);
    }
  };

  // 获取提供商图标
  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'gemini':
        return <Zap className="w-4 h-4 text-blue-500" />;
      case 'groq':
        return <Cpu className="w-4 h-4 text-green-500" />;
      case 'ollama':
        return <Server className="w-4 h-4 text-purple-500" />;
      default:
        return <Globe className="w-4 h-4 text-gray-500" />;
    }
  };

  // 获取提供商名称
  const getProviderName = (provider: string) => {
    const names: Record<string, string> = {
      'gemini': 'Google',
      'groq': 'Groq',
      'ollama': '本地'
    };
    return names[provider] || provider;
  };

  // 获取能力标签
  const getCapabilityLabel = (capability: string) => {
    const labels: Record<string, string> = {
      'chat': '对话',
      'streaming': '流式',
      'vision': '视觉',
      'function': '函数',
      'long_context': '长文'
    };
    return labels[capability] || capability;
  };

  const selectedModelInfo = models.find(m => m.model_id === selectedModel);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg">
        <div className="w-4 h-4 border-2 border-gray-300 border-t-pink-500 rounded-full animate-spin" />
        <span className="text-sm text-gray-500">加载模型...</span>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* 选择器按钮 */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg hover:border-pink-300 transition-colors"
      >
        {selectedModelInfo && (
          <>
            {getProviderIcon(selectedModelInfo.provider)}
            <span className="text-sm font-medium">{selectedModelInfo.display_name}</span>
            {modelHealth[selectedModel] ? (
              <CheckCircle className="w-3 h-3 text-green-500" />
            ) : (
              <AlertCircle className="w-3 h-3 text-yellow-500" />
            )}
          </>
        )}
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
      </button>

      {/* 下拉菜单 */}
      {isExpanded && (
        <>
          <div 
            className="fixed inset-0 z-40"
            onClick={() => setIsExpanded(false)}
          />
          <div className="absolute top-full left-0 mt-1 w-80 bg-white rounded-xl shadow-xl border border-gray-100 z-50 overflow-hidden">
            {/* 头部 */}
            <div className="px-4 py-3 bg-gradient-to-r from-pink-50 to-purple-50 border-b border-gray-100">
              <h4 className="font-medium text-gray-800">选择AI模型</h4>
              <p className="text-xs text-gray-500">选择最适合您需求的模型</p>
            </div>

            {/* 推荐区 */}
            <div className="p-3 border-b border-gray-100">
              <p className="text-xs text-gray-400 mb-2">推荐</p>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    onModelChange('gemini-2.0-flash');
                    setIsExpanded(false);
                  }}
                  className="flex-1 px-3 py-2 bg-blue-50 hover:bg-blue-100 rounded-lg text-center transition-colors"
                >
                  <Zap className="w-4 h-4 text-blue-500 mx-auto mb-1" />
                  <span className="text-xs font-medium text-blue-700">快速</span>
                </button>
                <button
                  onClick={() => {
                    onModelChange('llama-3.3-70b-versatile');
                    setIsExpanded(false);
                  }}
                  className="flex-1 px-3 py-2 bg-green-50 hover:bg-green-100 rounded-lg text-center transition-colors"
                >
                  <Cpu className="w-4 h-4 text-green-500 mx-auto mb-1" />
                  <span className="text-xs font-medium text-green-700">强力</span>
                </button>
                <button
                  onClick={() => {
                    onModelChange('llama3.1');
                    setIsExpanded(false);
                  }}
                  className="flex-1 px-3 py-2 bg-purple-50 hover:bg-purple-100 rounded-lg text-center transition-colors"
                >
                  <Server className="w-4 h-4 text-purple-500 mx-auto mb-1" />
                  <span className="text-xs font-medium text-purple-700">本地</span>
                </button>
              </div>
            </div>

            {/* 模型列表 */}
            <div className="max-h-80 overflow-y-auto">
              {/* Gemini模型 */}
              {models.filter(m => m.provider === 'gemini').length > 0 && (
                <div className="p-3">
                  <p className="text-xs text-gray-400 mb-2 flex items-center gap-1">
                    <Zap className="w-3 h-3" />
                    Google Gemini
                    <span className="text-blue-500">免费</span>
                  </p>
                  {models
                    .filter(m => m.provider === 'gemini')
                    .map(model => (
                      <button
                        key={model.model_id}
                        onClick={() => {
                          onModelChange(model.model_id);
                          setIsExpanded(false);
                        }}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                          selectedModel === model.model_id
                            ? 'bg-blue-50 border border-blue-200'
                            : 'hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex-1 text-left">
                          <p className="text-sm font-medium">{model.display_name}</p>
                          <div className="flex items-center gap-2 mt-1">
                            {model.capabilities.slice(0, 3).map(cap => (
                              <span 
                                key={cap}
                                className="text-xs px-1.5 py-0.5 bg-gray-100 rounded"
                              >
                                {getCapabilityLabel(cap)}
                              </span>
                            ))}
                            {modelHealth[model.model_id] ? (
                              <CheckCircle className="w-3 h-3 text-green-500 ml-auto" />
                            ) : (
                              <AlertCircle className="w-3 h-3 text-gray-300 ml-auto" />
                            )}
                          </div>
                        </div>
                      </button>
                    ))}
                </div>
              )}

              {/* Groq模型 */}
              {models.filter(m => m.provider === 'groq').length > 0 && (
                <div className="p-3 border-t border-gray-100">
                  <p className="text-xs text-gray-400 mb-2 flex items-center gap-1">
                    <Cpu className="w-3 h-3" />
                    Groq
                    <span className="text-green-500">免费</span>
                  </p>
                  {models
                    .filter(m => m.provider === 'groq')
                    .map(model => (
                      <button
                        key={model.model_id}
                        onClick={() => {
                          onModelChange(model.model_id);
                          setIsExpanded(false);
                        }}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                          selectedModel === model.model_id
                            ? 'bg-green-50 border border-green-200'
                            : 'hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex-1 text-left">
                          <p className="text-sm font-medium">{model.display_name}</p>
                          <p className="text-xs text-gray-400">
                            {model.context_window >= 100000 ? '长上下文' : '标准上下文'}
                          </p>
                        </div>
                        {modelHealth[model.model_id] ? (
                          <CheckCircle className="w-3 h-3 text-green-500" />
                        ) : (
                          <AlertCircle className="w-3 h-3 text-gray-300" />
                        )}
                      </button>
                    ))}
                </div>
              )}

              {/* Ollama本地模型 */}
              {models.filter(m => m.provider === 'ollama').length > 0 && (
                <div className="p-3 border-t border-gray-100">
                  <p className="text-xs text-gray-400 mb-2 flex items-center gap-1">
                    <Server className="w-3 h-3" />
                    Ollama 本地
                    <span className="text-purple-500">无限制</span>
                  </p>
                  {models
                    .filter(m => m.provider === 'ollama')
                    .map(model => (
                      <button
                        key={model.model_id}
                        onClick={() => {
                          onModelChange(model.model_id);
                          setIsExpanded(false);
                        }}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                          selectedModel === model.model_id
                            ? 'bg-purple-50 border border-purple-200'
                            : 'hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex-1 text-left">
                          <p className="text-sm font-medium">{model.display_name}</p>
                          <p className="text-xs text-gray-400">本地部署，无需联网</p>
                        </div>
                        {modelHealth[model.model_id] ? (
                          <CheckCircle className="w-3 h-3 text-green-500" />
                        ) : (
                          <AlertCircle className="w-3 h-3 text-gray-300" />
                        )}
                      </button>
                    ))}
                </div>
              )}
            </div>

            {/* 底部信息 */}
            <div className="p-3 bg-gray-50 border-t border-gray-100">
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Info className="w-3 h-3" />
                <span>所有模型均可免费使用</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ModelSelector;

"""
🌸 若曦V2 - Apple Health数据导入组件
上传和导入Apple Health导出文件
"""

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, FileText, CheckCircle, AlertCircle, 
  Activity, Heart, Scale, Moon, Droplet, Footprints,
  ChevronRight, RefreshCw, Trash2
} from 'lucide-react';

// 支持的数据类型
interface SupportedType {
  key: string;
  name: string;
  icon: React.ReactNode;
  color: string;
  unit: string;
}

const SUPPORTED_TYPES: SupportedType[] = [
  { key: 'blood_pressure', name: '血压', icon: <Activity className="w-4 h-4" />, color: 'text-red-500', unit: 'mmHg' },
  { key: 'heart_rate', name: '心率', icon: <Heart className="w-4 h-4" />, color: 'text-pink-500', unit: 'bpm' },
  { key: 'weight', name: '体重', icon: <Scale className="w-4 h-4" />, color: 'text-green-500', unit: 'kg' },
  { key: 'sleep', name: '睡眠', icon: <Moon className="w-4 h-4" />, color: 'text-indigo-500', unit: 'duration' },
  { key: 'glucose', name: '血糖', icon: <Droplet className="w-4 h-4" />, color: 'text-blue-500', unit: 'mmol/L' },
  { key: 'steps', name: '步数', icon: <Footprints className="w-4 h-4" />, color: 'text-orange-500', unit: 'count' },
];

// 预览数据结构
interface PreviewData {
  total_records: number;
  by_type: Record<string, number>;
  date_range: {
    earliest: string;
    latest: string;
  };
  sample_records: Array<{
    type: string;
    value: number;
    unit: string;
    date: string;
    source?: string;
  }>;
}

interface AppleHealthImportProps {
  apiBaseUrl: string;
  userToken: string;
  onImportComplete?: () => void;
}

export const AppleHealthImport: React.FC<AppleHealthImportProps> = ({
  apiBaseUrl,
  userToken,
  onImportComplete
}) => {
  const [uploadState, setUploadState] = useState<'idle' | 'uploading' | 'preview' | 'importing' | 'complete' | 'error'>('idle');
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [importResult, setImportResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [skipDuplicates, setSkipDuplicates] = useState(true);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    if (!file.name.endsWith('.xml')) {
      setError('请上传XML格式的文件 (export.xml)');
      setUploadState('error');
      return;
    }

    setSelectedFile(file);
    setUploadState('uploading');
    setError(null);

    try {
      // 先预览
      const previewFormData = new FormData();
      previewFormData.append('file', file);

      const previewRes = await fetch(`${apiBaseUrl}/api/v1/import/apple-health/preview`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${userToken}`
        },
        body: previewFormData
      });

      if (!previewRes.ok) {
        throw new Error('预览失败');
      }

      const preview = await previewRes.json();
      setPreviewData(preview);
      setUploadState('preview');
    } catch (err) {
      setError('文件解析失败，请确保是有效的Apple Health导出文件');
      setUploadState('error');
    }
  }, [apiBaseUrl, userToken]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/xml': ['.xml']
    },
    multiple: false
  });

  const handleImport = async () => {
    if (!selectedFile) return;

    setUploadState('importing');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const res = await fetch(
        `${apiBaseUrl}/api/v1/import/apple-health/upload?skip_duplicates=${skipDuplicates}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${userToken}`
          },
          body: formData
        }
      );

      if (!res.ok) {
        throw new Error('导入失败');
      }

      const result = await res.json();
      setImportResult(result);
      setUploadState('complete');
      
      if (onImportComplete) {
        onImportComplete();
      }
    } catch (err) {
      setError('导入过程中出现错误');
      setUploadState('error');
    }
  };

  const handleReset = () => {
    setUploadState('idle');
    setPreviewData(null);
    setImportResult(null);
    setError(null);
    setSelectedFile(null);
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Upload className="w-6 h-6 text-blue-500" />
          Apple Health 数据导入
        </h2>
        <p className="text-gray-600 mt-2">
          从iPhone导出健康数据并导入到若曦，自动同步你的健康记录
        </p>
      </div>

      {/* 上传区域 */}
      {uploadState === 'idle' && (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-colors ${
            isDragActive 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p className="text-lg text-gray-600 mb-2">
            {isDragActive ? '放开以上传文件' : '拖拽或点击上传 export.xml'}
          </p>
          <p className="text-sm text-gray-400">
            支持从 Apple Health App 导出的 XML 文件
          </p>
        </div>
      )}

      {/* 上传中 */}
      {uploadState === 'uploading' && (
        <div className="text-center py-12">
          <div className="w-12 h-12 border-2 border-blue-300 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">正在解析文件...</p>
        </div>
      )}

      {/* 预览 */}
      {uploadState === 'preview' && previewData && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-500" />
              数据预览
            </h3>
            
            {/* 统计卡片 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-gray-800">{previewData.total_records}</p>
                <p className="text-sm text-gray-500">总记录数</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-gray-800">{Object.keys(previewData.by_type).length}</p>
                <p className="text-sm text-gray-500">数据类型</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <p className="text-sm font-bold text-gray-800">
                  {previewData.date_range.earliest ? new Date(previewData.date_range.earliest).toLocaleDateString('zh-CN') : '-'}
                </p>
                <p className="text-xs text-gray-500">最早日期</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <p className="text-sm font-bold text-gray-800">
                  {previewData.date_range.latest ? new Date(previewData.date_range.latest).toLocaleDateString('zh-CN') : '-'}
                </p>
                <p className="text-xs text-gray-500">最晚日期</p>
              </div>
            </div>

            {/* 数据类型分布 */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-600 mb-3">数据类型分布</h4>
              <div className="space-y-2">
                {SUPPORTED_TYPES.map(type => {
                  const count = previewData.by_type[type.key] || 0;
                  if (count === 0) return null;
                  
                  const percent = (count / previewData.total_records * 100).toFixed(1);
                  
                  return (
                    <div key={type.key} className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center ${type.color}`}>
                        {type.icon}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">{type.name}</span>
                          <span className="text-sm text-gray-500">{count} 条 ({percent}%)</span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-blue-500 rounded-full transition-all"
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 示例数据 */}
            {previewData.sample_records.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-600 mb-3">示例数据</h4>
                <div className="bg-gray-50 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="px-4 py-2 text-left">类型</th>
                        <th className="px-4 py-2 text-left">数值</th>
                        <th className="px-4 py-2 text-left">日期</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.sample_records.slice(0, 5).map((record, idx) => (
                        <tr key={idx} className="border-t border-gray-200">
                          <td className="px-4 py-2">
                            {SUPPORTED_TYPES.find(t => t.key === record.type)?.name || record.type}
                          </td>
                          <td className="px-4 py-2 font-medium">{record.value} {record.unit}</td>
                          <td className="px-4 py-2 text-gray-500">
                            {record.date ? new Date(record.date).toLocaleString('zh-CN') : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* 导入选项 */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h4 className="font-medium mb-4">导入选项</h4>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={skipDuplicates}
                onChange={(e) => setSkipDuplicates(e.target.checked)}
                className="w-5 h-5 rounded border-gray-300 text-blue-500"
              />
              <div>
                <p className="font-medium">跳过重复记录</p>
                <p className="text-sm text-gray-500">如果数据已存在则跳过，避免重复导入</p>
              </div>
            </label>
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-4">
            <button
              onClick={handleReset}
              className="flex-1 px-6 py-3 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors"
            >
              重新选择
            </button>
            <button
              onClick={handleImport}
              className="flex-1 px-6 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors flex items-center justify-center gap-2"
            >
              开始导入
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* 导入中 */}
      {uploadState === 'importing' && (
        <div className="text-center py-12">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-lg text-gray-600">正在导入数据...</p>
          <p className="text-sm text-gray-400 mt-2">这可能需要几分钟，取决于数据量</p>
        </div>
      )}

      {/* 完成 */}
      {uploadState === 'complete' && importResult && (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
          <h3 className="text-xl font-bold text-gray-800 mb-2">导入成功！</h3>
          
          {importResult.import_counts && (
            <div className="bg-gray-50 rounded-xl p-6 mt-6 max-w-md mx-auto">
              <div className="space-y-2">
                {Object.entries(importResult.import_counts).map(([type, count]) => (
                  count > 0 && (
                    <div key={type} className="flex items-center justify-between">
                      <span className="text-gray-600">
                        {type === 'blood_pressure' && '血压'}
                        {type === 'heart_rate' && '心率'}
                        {type === 'weight' && '体重'}
                        {type === 'sleep' && '睡眠'}
                        {type === 'glucose' && '血糖'}
                      </span>
                      <span className="font-bold text-gray-800">{count as number} 条</span>
                    </div>
                  )
                ))}
              </div>
              <div className="border-t mt-4 pt-4">
                <div className="flex items-center justify-between">
                  <span className="font-medium">总计导入</span>
                  <span className="text-xl font-bold text-blue-500">
                    {importResult.total_imported || importResult.imported_records} 条
                  </span>
                </div>
              </div>
            </div>
          )}

          <button
            onClick={handleReset}
            className="mt-8 px-8 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors flex items-center gap-2 mx-auto"
          >
            <RefreshCw className="w-5 h-5" />
            导入更多数据
          </button>
        </div>
      )}

      {/* 错误 */}
      {uploadState === 'error' && (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h3 className="text-lg font-bold text-gray-800 mb-2">导入失败</h3>
          <p className="text-gray-600 mb-6">{error || '未知错误'}</p>
          <button
            onClick={handleReset}
            className="px-8 py-3 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors"
          >
            重试
          </button>
        </div>
      )}

      {/* 使用说明 */}
      <div className="mt-8 bg-gray-50 rounded-xl p-6">
        <h4 className="font-medium text-gray-800 mb-4">如何从 iPhone 导出健康数据</h4>
        <ol className="space-y-3 text-sm text-gray-600">
          <li className="flex gap-3">
            <span className="flex-shrink-0 w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center text-xs font-medium">1</span>
            <span>打开 iPhone 上的「健康」App</span>
          </li>
          <li className="flex gap-3">
            <span className="flex-shrink-0 w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center text-xs font-medium">2</span>
            <span>点击右上角头像，选择「导出所有健康数据」</span>
          </li>
          <li className="flex gap-3">
            <span className="flex-shrink-0 w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center text-xs font-medium">3</span>
            <span>等待导出完成（可能需要几分钟）</span>
          </li>
          <li className="flex gap-3">
            <span className="flex-shrink-0 w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center text-xs font-medium">4</span>
            <span>将文件传输到电脑，上传到此页面</span>
          </li>
        </ol>
      </div>
    </div>
  );
};

export default AppleHealthImport;

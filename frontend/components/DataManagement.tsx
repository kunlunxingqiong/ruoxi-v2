"""
🌸 若曦V2 - 数据管理组件
提供数据导出、导入、备份恢复功能
"""

import React, { useState, useEffect } from 'react';
import { 
  Download, Upload, Archive, Database, Trash2, AlertTriangle,
  FileJson, FileSpreadsheet, FileArchive, CheckCircle, X,
  RefreshCw, ChevronDown, ChevronUp, Calendar, Info
} from 'lucide-react';

// 统计类型
interface DataStats {
  health_records: {
    blood_pressure: number;
    glucose: number;
    weight: number;
    heart_rate: number;
    sleep: number;
  };
  medications: number;
  medication_logs: number;
  goals: number;
  total_records: number;
  data_span: {
    first_record: string | null;
    last_record: string | null;
  };
}

interface DataManagementProps {
  apiBaseUrl: string;
  userToken: string;
}

export const DataManagement: React.FC<DataManagementProps> = ({
  apiBaseUrl,
  userToken
}) => {
  const [stats, setStats] = useState<DataStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'export' | 'import' | 'backup'>('export');
  const [exportFormat, setExportFormat] = useState<'json' | 'csv' | 'zip'>('json');
  const [dateRange, setDateRange] = useState({
    start: '',
    end: ''
  });
  const [importType, setImportType] = useState('blood_pressure');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/data/stats`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (e) {
      console.error('获取统计失败:', e);
    } finally {
      setLoading(false);
    }
  };

  // 导出数据
  const handleExport = async () => {
    setIsProcessing(true);
    try {
      const params = new URLSearchParams({
        format: exportFormat,
        download: 'true'
      });
      
      if (dateRange.start) params.append('start_date', dateRange.start);
      if (dateRange.end) params.append('end_date', dateRange.end);
      
      const res = await fetch(`${apiBaseUrl}/api/v1/data/export?${params}`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ruoxi_export_${new Date().toISOString().slice(0, 10)}.${exportFormat === 'json' ? 'json' : 'zip'}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        
        setMessage({ type: 'success', text: '导出成功！文件已下载' });
      } else {
        setMessage({ type: 'error', text: '导出失败' });
      }
    } catch (e) {
      setMessage({ type: 'error', text: '导出出错' });
    } finally {
      setIsProcessing(false);
    }
  };

  // 导入数据
  const handleImport = async () => {
    if (!uploadedFile) {
      setMessage({ type: 'error', text: '请先选择文件' });
      return;
    }
    
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      
      const res = await fetch(`${apiBaseUrl}/api/v1/data/import/csv?record_type=${importType}`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${userToken}`
        },
        body: formData
      });
      
      const data = await res.json();
      setImportResult(data);
      
      if (data.success) {
        setMessage({ type: 'success', text: data.message });
        fetchStats(); // 刷新统计
      } else {
        setMessage({ type: 'error', text: data.message });
      }
    } catch (e) {
      setMessage({ type: 'error', text: '导入出错' });
    } finally {
      setIsProcessing(false);
    }
  };

  // 创建备份
  const handleBackup = async () => {
    setIsProcessing(true);
    try {
      // 直接调用导出API，格式为zip
      const res = await fetch(`${apiBaseUrl}/api/v1/data/export?format=zip&download=true`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ruoxi_backup_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.zip`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        
        setMessage({ type: 'success', text: '备份创建成功！' });
      }
    } catch (e) {
      setMessage({ type: 'error', text: '备份失败' });
    } finally {
      setIsProcessing(false);
    }
  };

  // 恢复备份
  const handleRestore = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await fetch(`${apiBaseUrl}/api/v1/data/restore`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${userToken}`
        },
        body: formData
      });
      
      const data = await res.json();
      
      if (data.success) {
        setMessage({ type: 'success', text: data.message });
        fetchStats();
      } else {
        setMessage({ type: 'error', text: data.message });
      }
    } catch (err) {
      setMessage({ type: 'error', text: '恢复失败' });
    } finally {
      setIsProcessing(false);
    }
  };

  // 下载模板
  const downloadTemplate = async (type: string) => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/data/export/template/${type}`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${type}_template.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      }
    } catch (e) {
      console.error('下载模板失败:', e);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8 flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-3 text-gray-600">加载中...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 头部统计 */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Database className="w-6 h-6 text-blue-500" />
            数据管理
          </h2>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">总记录数:</span>
            <span className="text-2xl font-bold text-blue-600">{stats?.total_records || 0}</span>
          </div>
        </div>
        
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl p-4">
              <div className="text-sm text-gray-500">血压记录</div>
              <div className="text-xl font-bold text-gray-800">{stats.health_records.blood_pressure}</div>
            </div>
            <div className="bg-white rounded-xl p-4">
              <div className="text-sm text-gray-500">血糖记录</div>
              <div className="text-xl font-bold text-gray-800">{stats.health_records.glucose}</div>
            </div>
            <div className="bg-white rounded-xl p-4">
              <div className="text-sm text-gray-500">体重记录</div>
              <div className="text-xl font-bold text-gray-800">{stats.health_records.weight}</div>
            </div>
            <div className="bg-white rounded-xl p-4">
              <div className="text-sm text-gray-500">睡眠记录</div>
              <div className="text-xl font-bold text-gray-800">{stats.health_records.sleep}</div>
            </div>
          </div>
        )}
      </div>

      {/* 标签页 */}
      <div className="flex gap-2 bg-gray-100 p-1 rounded-xl">
        {[
          { id: 'export', label: '数据导出', icon: Download },
          { id: 'import', label: '数据导入', icon: Upload },
          { id: 'backup', label: '备份恢复', icon: Archive }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id as any);
              setMessage(null);
            }}
            className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-medium transition-all ${
              activeTab === tab.id 
                ? 'bg-white text-blue-600 shadow-sm' 
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <tab.icon className="w-5 h-5" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* 消息提示 */}
      {message && (
        <div className={`rounded-xl p-4 flex items-center gap-3 ${
          message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <AlertTriangle className="w-5 h-5" />
          )}
          {message.text}
          <button onClick={() => setMessage(null)} className="ml-auto">
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* 导出面板 */}
      {activeTab === 'export' && (
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">导出数据</h3>
          
          {/* 格式选择 */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">导出格式</label>
            <div className="grid grid-cols-3 gap-4">
              {[
                { id: 'json', label: 'JSON', desc: '完整数据', icon: FileJson },
                { id: 'csv', label: 'CSV', desc: '表格格式', icon: FileSpreadsheet },
                { id: 'zip', label: 'ZIP', desc: '完整备份', icon: FileArchive }
              ].map(fmt => (
                <button
                  key={fmt.id}
                  onClick={() => setExportFormat(fmt.id as any)}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    exportFormat === fmt.id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <fmt.icon className={`w-6 h-6 mb-2 ${
                    exportFormat === fmt.id ? 'text-blue-500' : 'text-gray-400'
                  }`} />
                  <div className="font-medium text-gray-800">{fmt.label}</div>
                  <div className="text-xs text-gray-500">{fmt.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* 日期范围 */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">日期范围（可选）</label>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">开始日期</label>
                <input
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">结束日期</label>
                <input
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <p className="text-sm text-gray-500 mt-2">
              不选择日期将导出所有历史数据
            </p>
          </div>

          {/* 导出按钮 */}
          <button
            onClick={handleExport}
            disabled={isProcessing}
            className="w-full py-3 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isProcessing ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Download className="w-5 h-5" />
            )}
            {isProcessing ? '处理中...' : '开始导出'}
          </button>
        </div>
      )}

      {/* 导入面板 */}
      {activeTab === 'import' && (
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">导入数据</h3>
          
          {/* 类型选择 */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">数据类型</label>
            <select
              value={importType}
              onChange={(e) => setImportType(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="blood_pressure">血压记录</option>
              <option value="glucose">血糖记录</option>
              <option value="weight">体重记录</option>
              <option value="heart_rate">心率记录</option>
              <option value="sleep">睡眠记录</option>
            </select>
          </div>

          {/* 下载模板 */}
          <div className="mb-6 p-4 bg-blue-50 rounded-xl">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-500 mt-0.5" />
              <div>
                <p className="text-sm text-blue-700 mb-2">
                  请先下载CSV模板，按模板格式填写数据后上传
                </p>
                <button
                  onClick={() => downloadTemplate(importType)}
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  下载 {importType} 模板 →
                </button>
              </div>
            </div>
          </div>

          {/* 文件上传 */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">选择CSV文件</label>
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center">
              <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                className="hidden"
                id="csv-upload"
              />
              <label 
                htmlFor="csv-upload"
                className="text-blue-600 hover:text-blue-800 cursor-pointer font-medium"
              >
                点击选择文件
              </label>
              <p className="text-sm text-gray-500 mt-2">
                或拖拽文件到此处
              </p>
              {uploadedFile && (
                <p className="text-sm text-green-600 mt-2">
                  已选择: {uploadedFile.name}
                </p>
              )}
            </div>
          </div>

          {/* 导入按钮 */}
          <button
            onClick={handleImport}
            disabled={isProcessing || !uploadedFile}
            className="w-full py-3 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isProcessing ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Upload className="w-5 h-5" />
            )}
            {isProcessing ? '导入中...' : '开始导入'}
          </button>

          {/* 导入结果 */}
          {importResult && (
            <div className="mt-4 p-4 bg-gray-50 rounded-xl">
              <h4 className="font-medium text-gray-800 mb-2">导入结果</h4>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="bg-white rounded-lg p-3">
                  <div className="text-2xl font-bold text-green-600">
                    {importResult.import_result?.success_count || 0}
                  </div>
                  <div className="text-xs text-gray-500">成功</div>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <div className="text-2xl font-bold text-yellow-600">
                    {importResult.import_result?.skip_count || 0}
                  </div>
                  <div className="text-xs text-gray-500">跳过</div>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <div className="text-2xl font-bold text-red-600">
                    {importResult.import_result?.error_count || 0}
                  </div>
                  <div className="text-xs text-gray-500">失败</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 备份恢复面板 */}
      {activeTab === 'backup' && (
        <div className="space-y-6">
          {/* 创建备份 */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Archive className="w-5 h-5" />
              创建完整备份
            </h3>
            <p className="text-gray-600 mb-4">
              创建包含所有数据的完整备份包，建议每周备份一次
            </p>
            <button
              onClick={handleBackup}
              disabled={isProcessing}
              className="w-full py-3 bg-green-500 text-white rounded-xl font-medium hover:bg-green-600 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isProcessing ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <Archive className="w-5 h-5" />
              )}
              {isProcessing ? '创建中...' : '创建完整备份'}
            </button>
          </div>

          {/* 恢复备份 */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Upload className="w-5 h-5" />
              从备份恢复
            </h3>
            <div className="p-4 bg-yellow-50 rounded-xl mb-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div className="text-sm text-yellow-800">
                  <p className="font-medium mb-1">恢复前请注意</p>
                  <p>恢复操作会合并备份数据到现有数据，不会删除现有记录。</p>
                  <p>建议在恢复前创建新的备份。</p>
                </div>
              </div>
            </div>
            
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center">
              <Archive className="w-10 h-10 text-gray-400 mx-auto mb-3" />
              <input
                type="file"
                accept=".zip"
                onChange={handleRestore}
                disabled={isProcessing}
                className="hidden"
                id="backup-restore"
              />
              <label 
                htmlFor="backup-restore"
                className={`font-medium ${isProcessing ? 'text-gray-400' : 'text-blue-600 hover:text-blue-800 cursor-pointer'}`}
              >
                {isProcessing ? '处理中...' : '选择备份文件 (.zip)'}
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataManagement;

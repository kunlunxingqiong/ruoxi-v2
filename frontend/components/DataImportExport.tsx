"""
🌸 若曦V2 - 数据导入导出组件
支持健康数据的上传和下载
"""

import React, { useState, useRef } from 'react';
import { 
  Upload, Download, FileSpreadsheet, FileJson, FileText, 
  Eye, CheckCircle, AlertCircle, Loader2, ChevronDown 
} from 'lucide-react';

// 数据类型
interface DataType {
  id: string;
  name: string;
  description: string;
  example: string;
}

// 导入预览
interface ImportPreview {
  data_type: string;
  columns: string[];
  sample_rows: Record<string, any>[];
  total_rows: number;
  validation_errors: string[];
}

// 导入结果
interface ImportResult {
  success: boolean;
  total_rows: number;
  imported_rows: number;
  skipped_rows: number;
  errors: Array<{row: number; error: string}>;
  warnings: string[];
}

interface DataImportExportProps {
  apiBaseUrl: string;
  userToken: string;
}

export const DataImportExport: React.FC<DataImportExportProps> = ({
  apiBaseUrl,
  userToken
}) => {
  const [activeTab, setActiveTab] = useState<'import' | 'export'>('import');
  const [selectedDataType, setSelectedDataType] = useState<string>('blood_pressure');
  const [isLoading, setIsLoading] = useState(false);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [exportFormat, setExportFormat] = useState<string>('excel');
  const [exportTemplate, setExportTemplate] = useState<string>('raw_data');
  const [dateRange, setDateRange] = useState({
    from: '',
    to: ''
  });
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 数据类型列表
  const dataTypes: DataType[] = [
    { id: 'blood_pressure', name: '血压', description: '收缩压/舒张压/脉搏', example: '120/80/72' },
    { id: 'blood_glucose', name: '血糖', description: '血糖数值及时间', example: '5.6 mmol/L' },
    { id: 'weight', name: '体重', description: '体重记录', example: '65.5 kg' },
    { id: 'sleep', name: '睡眠', description: '睡眠时长和质量', example: '8小时 / 深睡2小时' },
    { id: 'heart_rate', name: '心率', description: '心率记录', example: '72 bpm' },
    { id: 'steps', name: '步数', description: '每日步数', example: '8000步' },
    { id: 'medication', name: '用药', description: '服药记录', example: '阿司匹林 100mg' }
  ];

  // 处理文件选择
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreview(null);
      setImportResult(null);
    }
  };

  // 预览导入数据
  const handlePreview = async () => {
    if (!selectedFile) return;
    
    setIsLoading(true);
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/data/import/preview?data_type=${selectedDataType}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${userToken}`
          },
          body: formData
        }
      );
      
      const data = await response.json();
      
      if (data.success) {
        setPreview(data.preview);
      } else {
        alert('预览失败: ' + data.message);
      }
    } catch (error) {
      console.error('预览错误:', error);
      alert('预览失败，请检查网络');
    } finally {
      setIsLoading(false);
    }
  };

  // 执行导入
  const handleImport = async () => {
    if (!selectedFile) return;
    
    setIsLoading(true);
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/data/import?data_type=${selectedDataType}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${userToken}`
          },
          body: formData
        }
      );
      
      const data = await response.json();
      
      if (data.success) {
        setImportResult(data.import);
      } else {
        alert('导入失败');
      }
    } catch (error) {
      console.error('导入错误:', error);
      alert('导入失败，请检查网络');
    } finally {
      setIsLoading(false);
    }
  };

  // 下载模板
  const handleDownloadTemplate = async () => {
    const format = exportFormat === 'json' ? 'csv' : exportFormat;
    
    window.open(
      `${apiBaseUrl}/api/v1/data/import/templates/${selectedDataType}?format=${format}`,
      '_blank'
    );
  };

  // 导出数据
  const handleExport = async () => {
    setIsLoading(true);
    
    try {
      const params = new URLSearchParams({
        data_type: selectedDataType,
        export_format: exportFormat,
        template: exportTemplate
      });
      
      if (dateRange.from) params.append('date_from', dateRange.from);
      if (dateRange.to) params.append('date_to', dateRange.to);
      
      const response = await fetch(
        `${apiBaseUrl}/api/v1/data/export?${params}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${userToken}`
          }
        }
      );
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${selectedDataType}_${exportTemplate}.${exportFormat === 'excel' ? 'xlsx' : exportFormat}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        alert('导出失败');
      }
    } catch (error) {
      console.error('导出错误:', error);
      alert('导出失败，请检查网络');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      {/* 标签页切换 */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('import')}
          className={`flex-1 py-4 text-center font-medium transition-colors ${
            activeTab === 'import'
              ? 'text-pink-500 border-b-2 border-pink-500 bg-pink-50'
              : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
          }`}
        >
          <Upload className="w-5 h-5 inline mr-2" />
          导入数据
        </button>
        <button
          onClick={() => setActiveTab('export')}
          className={`flex-1 py-4 text-center font-medium transition-colors ${
            activeTab === 'export'
              ? 'text-pink-500 border-b-2 border-pink-500 bg-pink-50'
              : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
          }`}
        >
          <Download className="w-5 h-5 inline mr-2" />
          导出数据
        </button>
      </div>

      <div className="p-6">
        {/* 数据类型选择 */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            选择数据类型
          </label>
          <select
            value={selectedDataType}
            onChange={(e) => {
              setSelectedDataType(e.target.value);
              setPreview(null);
              setImportResult(null);
            }}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-300 focus:border-pink-300"
          >
            {dataTypes.map((type) => (
              <option key={type.id} value={type.id}>
                {type.name} - {type.description}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">
            示例: {dataTypes.find(t => t.id === selectedDataType)?.example}
          </p>
        </div>

        {activeTab === 'import' ? (
          // 导入界面
          <div className="space-y-6">
            {/* 文件上传 */}
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-pink-400 hover:bg-pink-50 transition-all"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls,.json"
                onChange={handleFileSelect}
                className="hidden"
              />
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">
                {selectedFile ? selectedFile.name : '点击选择文件上传'}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                支持 CSV, Excel, JSON 格式
              </p>
            </div>

            {/* 下载模板 */}
            <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center">
                <FileSpreadsheet className="w-5 h-5 text-blue-500 mr-2" />
                <span className="text-sm text-blue-700">没有数据文件？先下载模板</span>
              </div>
              <button
                onClick={handleDownloadTemplate}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors"
              >
                下载模板
              </button>
            </div>

            {/* 预览按钮 */}
            {selectedFile && !preview && (
              <button
                onClick={handlePreview}
                disabled={isLoading}
                className="w-full py-3 bg-pink-500 text-white rounded-lg hover:bg-pink-600 transition-colors flex items-center justify-center"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    正在预览...
                  </>
                ) : (
                  <>
                    <Eye className="w-5 h-5 mr-2" />
                    预览数据
                  </>
                )}
              </button>
            )}

            {/* 预览结果 */}
            {preview && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium mb-3">数据预览</h4>
                
                {preview.validation_errors.length > 0 ? (
                  <div className="space-y-2">
                    {preview.validation_errors.map((error, idx) => (
                      <div key={idx} className="flex items-center text-red-600">
                        <AlertCircle className="w-4 h-4 mr-2" />
                        <span className="text-sm">{error}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center text-green-600">
                      <CheckCircle className="w-4 h-4 mr-2" />
                      <span className="text-sm">数据格式验证通过</span>
                    </div>
                    <p className="text-sm text-gray-600">
                      共 {preview.total_rows} 行数据，{preview.columns.length} 列
                    </p>
                    
                    {/* 简单表格预览 */}
                    {preview.sample_rows.length > 0 && (
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-xs">
                          <thead className="bg-gray-100">
                            <tr>
                              {preview.columns.map((col) => (
                                <th key={col} className="px-2 py-1 text-left font-medium">
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {preview.sample_rows.map((row, idx) => (
                              <tr key={idx} className="border-b">
                                {preview.columns.map((col) => (
                                  <td key={col} className="px-2 py-1">
                                    {String(row[col] || '').slice(0, 20)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                    
                    <button
                      onClick={handleImport}
                      disabled={isLoading}
                      className="w-full py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center justify-center"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                          正在导入...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-5 h-5 mr-2" />
                          确认导入
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* 导入结果 */}
            {importResult && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 className="font-medium text-green-800 mb-2">导入完成</h4>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="bg-white rounded-lg p-3">
                    <p className="text-2xl font-bold text-gray-800">{importResult.total_rows}</p>
                    <p className="text-xs text-gray-500">总行数</p>
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <p className="text-2xl font-bold text-green-600">{importResult.imported_rows}</p>
                    <p className="text-xs text-gray-500">成功导入</p>
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <p className="text-2xl font-bold text-yellow-600">{importResult.skipped_rows}</p>
                    <p className="text-xs text-gray-500">跳过</p>
                  </div>
                </div>
                
                {importResult.warnings.length > 0 && (
                  <div className="mt-3 space-y-1">
                    {importResult.warnings.map((warning, idx) => (
                      <p key={idx} className="text-xs text-yellow-600">
                        ⚠️ {warning}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          // 导出界面
          <div className="space-y-6">
            {/* 导出格式 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                导出格式
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'csv', name: 'CSV', icon: FileText },
                  { id: 'excel', name: 'Excel', icon: FileSpreadsheet },
                  { id: 'json', name: 'JSON', icon: FileJson }
                ].map((fmt) => (
                  <button
                    key={fmt.id}
                    onClick={() => setExportFormat(fmt.id)}
                    className={`flex flex-col items-center p-4 rounded-lg border-2 transition-all ${
                      exportFormat === fmt.id
                        ? 'border-pink-500 bg-pink-50 text-pink-600'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <fmt.icon className="w-6 h-6 mb-2" />
                    <span className="text-sm font-medium">{fmt.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* 导出模板 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                导出模板
              </label>
              <select
                value={exportTemplate}
                onChange={(e) => setExportTemplate(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-300"
              >
                <option value="raw_data">原始数据 - 完整记录</option>
                <option value="daily_summary">每日汇总 - 按日统计</option>
                <option value="weekly_report">周报 - 周趋势分析</option>
                <option value="monthly_report">月报 - 月度综合</option>
                <option value="for_doctor">医生格式 - 专业标准</option>
              </select>
            </div>

            {/* 日期范围 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                日期范围 (可选)
              </label>
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="date"
                  value={dateRange.from}
                  onChange={(e) => setDateRange({...dateRange, from: e.target.value})}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-300"
                  placeholder="开始日期"
                />
                <input
                  type="date"
                  value={dateRange.to}
                  onChange={(e) => setDateRange({...dateRange, to: e.target.value})}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-300"
                  placeholder="结束日期"
                />
              </div>
            </div>

            {/* 导出按钮 */}
            <button
              onClick={handleExport}
              disabled={isLoading}
              className="w-full py-3 bg-pink-500 text-white rounded-lg hover:bg-pink-600 transition-colors flex items-center justify-center"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  正在导出...
                </>
              ) : (
                <>
                  <Download className="w-5 h-5 mr-2" />
                  导出数据
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default DataImportExport;

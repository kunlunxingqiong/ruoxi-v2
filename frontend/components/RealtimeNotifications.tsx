"""
🌸 若曦V2 - 实时通知组件
WebSocket连接管理和实时通知展示
"""

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Bell, X, Heart, AlertTriangle, AlertCircle, 
  CheckCircle, Info, Pill, Trophy, Wifi, WifiOff,
  ChevronRight, Clock
} from 'lucide-react';

// 通知类型定义
interface Notification {
  id: string;
  type: 'health_alert' | 'medication_reminder' | 'goal_achieved' | 'appointment' | 'system';
  severity: 'info' | 'warning' | 'critical' | 'emergency';
  title: string;
  message: string;
  timestamp: string;
  data?: any;
  actions?: Array<{ label: string; action: string }>;
  read: boolean;
}

// WebSocket配置
interface WebSocketConfig {
  baseUrl: string;
  token: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

// 通知类型图标映射
const notificationIcons = {
  health_alert: {
    emergency: <AlertCircle className="w-6 h-6 text-red-500" />,
    critical: <AlertTriangle className="w-6 h-6 text-orange-500" />,
    warning: <AlertTriangle className="w-6 h-6 text-yellow-500" />,
    info: <Info className="w-6 h-6 text-blue-500" />
  },
  medication_reminder: <Pill className="w-6 h-6 text-blue-500" />,
  goal_achieved: <Trophy className="w-6 h-6 text-yellow-500" />,
  appointment: <Clock className="w-6 h-6 text-purple-500" />,
  system: <Info className="w-6 h-6 text-gray-500" />
};

// 严重程度样式
const severityStyles = {
  emergency: 'bg-red-50 border-red-200 text-red-800',
  critical: 'bg-orange-50 border-orange-200 text-orange-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800'
};

interface RealtimeNotificationsProps {
  config: WebSocketConfig;
  onNotification?: (notification: Notification) => void;
  onAction?: (action: string, notification: Notification) => void;
}

export const RealtimeNotifications: React.FC<RealtimeNotificationsProps> = ({
  config,
  onNotification,
  onAction
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [showPanel, setShowPanel] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null);

  // WebSocket URL
  const wsUrl = `${config.baseUrl.replace(/^http/, 'ws')}/ws/health?token=${config.token}`;

  // 连接WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        
        // 启动心跳
        if (heartbeatTimerRef.current) {
          clearInterval(heartbeatTimerRef.current);
        }
        heartbeatTimerRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);

        // 订阅健康监控频道
        ws.send(JSON.stringify({
          type: 'subscribe',
          channels: ['health_alerts', 'medication_reminders', 'goal_achievements']
        }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleMessage(data);
        } catch (e) {
          console.error('解析WebSocket消息失败:', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        setConnectionStatus('disconnected');
        
        // 清理心跳
        if (heartbeatTimerRef.current) {
          clearInterval(heartbeatTimerRef.current);
        }

        // 尝试重连
        if (reconnectAttemptsRef.current < (config.maxReconnectAttempts || 5)) {
          const delay = Math.min(
            (config.reconnectInterval || 3000) * Math.pow(2, reconnectAttemptsRef.current),
            30000
          );
          
          reconnectTimerRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        setConnectionStatus('disconnected');
      };
    } catch (e) {
      console.error('WebSocket连接失败:', e);
      setConnectionStatus('disconnected');
    }
  }, [wsUrl, config]);

  // 断开连接
  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
    }
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // 处理消息
  const handleMessage = (data: any) => {
    if (data.type === 'pong') {
      return;
    }

    if (data.type === 'connection_established') {
      console.log('WebSocket连接已建立:', data.data);
      return;
    }

    if (data.type === 'notification') {
      const notification: Notification = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        type: data.notification_type,
        severity: data.severity,
        title: data.title,
        message: data.message,
        timestamp: data.timestamp,
        data: data.data,
        actions: data.actions,
        read: false
      };

      setNotifications(prev => [notification, ...prev]);
      setUnreadCount(prev => prev + 1);

      // 触发回调
      if (onNotification) {
        onNotification(notification);
      }

      // 严重警报自动弹出
      if (data.severity === 'emergency' || data.severity === 'critical') {
        setShowPanel(true);
      }
    }

    if (data.type === 'subscribed') {
      console.log('已订阅频道:', data.channels);
    }
  };

  // 标记已读
  const markAsRead = (notificationId: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
    
    // 发送已读确认
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'mark_read',
        notification_id: notificationId
      }));
    }
  };

  // 标记全部已读
  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnreadCount(0);
  };

  // 删除通知
  const deleteNotification = (notificationId: string) => {
    setNotifications(prev => prev.filter(n => n.id !== notificationId));
  };

  // 处理操作
  const handleAction = (action: string, notification: Notification) => {
    // 执行操作
    if (onAction) {
      onAction(action, notification);
    }

    // 根据操作类型处理
    if (action.startsWith('take_medication:')) {
      // 标记服药
      const medId = action.split(':')[1];
      console.log('标记用药:', medId);
    } else if (action.startsWith('skip_medication:')) {
      // 跳过用药
      const medId = action.split(':')[1];
      console.log('跳过用药:', medId);
    } else if (action === 'view_record') {
      // 查看记录
      console.log('查看记录:', notification.data);
    } else if (action === 'view_goal') {
      // 查看目标
      console.log('查看目标');
    }

    // 标记已读
    markAsRead(notification.id);
  };

  // 获取图标
  const getIcon = (notification: Notification) => {
    if (notification.type === 'health_alert') {
      return notificationIcons.health_alert[notification.severity as keyof typeof notificationIcons.health_alert];
    }
    return notificationIcons[notification.type as keyof typeof notificationIcons] || <Info className="w-6 h-6 text-gray-500" />;
  };

  // 格式化时间
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) {
      return '刚刚';
    } else if (diff < 3600000) {
      return `${Math.floor(diff / 60000)}分钟前`;
    } else if (diff < 86400000) {
      return `${Math.floor(diff / 3600000)}小时前`;
    } else {
      return date.toLocaleDateString('zh-CN');
    }
  };

  // 初始化连接
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return (
    <>
      {/* 通知铃铛按钮 */}
      <button
        onClick={() => setShowPanel(!showPanel)}
        className="fixed top-4 right-4 z-50 w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center hover:shadow-xl transition-shadow"
      >
        <div className="relative">
          <Bell className="w-6 h-6 text-gray-600" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center animate-pulse">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </div>
      </button>

      {/* 连接状态指示器 */}
      <div className="fixed top-4 right-20 z-40">
        {connectionStatus === 'connected' ? (
          <div className="flex items-center gap-1 text-green-500 text-sm bg-green-50 px-2 py-1 rounded">
            <Wifi className="w-4 h-4" />
            <span>实时</span>
          </div>
        ) : connectionStatus === 'connecting' ? (
          <div className="flex items-center gap-1 text-yellow-500 text-sm bg-yellow-50 px-2 py-1 rounded">
            <div className="w-4 h-4 border-2 border-yellow-300 border-t-yellow-500 rounded-full animate-spin" />
            <span>连接中</span>
          </div>
        ) : (
          <div className="flex items-center gap-1 text-gray-400 text-sm bg-gray-50 px-2 py-1 rounded">
            <WifiOff className="w-4 h-4" />
            <span>离线</span>
          </div>
        )}
      </div>

      {/* 通知面板 */}
      {showPanel && (
        <div className="fixed top-20 right-4 z-50 w-96 max-h-[80vh] bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* 面板头部 */}
          <div className="flex items-center justify-between p-4 border-b">
            <h3 className="font-bold text-lg">通知中心</h3>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-blue-500 hover:text-blue-600"
                >
                  全部已读
                </button>
              )}
              <button
                onClick={() => setShowPanel(false)}
                className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* 通知列表 */}
          <div className="overflow-y-auto max-h-[60vh]">
            {notifications.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <Bell className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>暂无通知</p>
              </div>
            ) : (
              <div className="divide-y">
                {notifications.map(notification => (
                  <div
                    key={notification.id}
                    className={`p-4 transition-colors hover:bg-gray-50 ${
                      !notification.read ? 'bg-blue-50/30' : ''
                    }`}
                  >
                    <div className="flex gap-3">
                      {/* 图标 */}
                      <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                        severityStyles[notification.severity]?.split(' ')[0] || 'bg-gray-100'
                      }`}>
                        {getIcon(notification)}
                      </div>

                      {/* 内容 */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <h4 className={`font-semibold text-sm ${
                            !notification.read ? 'text-gray-900' : 'text-gray-600'
                          }`}>
                            {notification.title}
                          </h4>
                          <span className="text-xs text-gray-400 flex-shrink-0">
                            {formatTime(notification.timestamp)}
                          </span>
                        </div>
                        <p className={`text-sm mt-1 ${
                          !notification.read ? 'text-gray-700' : 'text-gray-500'
                        }`}>
                          {notification.message}
                        </p>

                        {/* 操作按钮 */}
                        {notification.actions && notification.actions.length > 0 && (
                          <div className="flex gap-2 mt-2">
                            {notification.actions.map((action, idx) => (
                              <button
                                key={idx}
                                onClick={() => handleAction(action.action, notification)}
                                className="text-xs px-3 py-1.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                              >
                                {action.label}
                              </button>
                            ))}
                          </div>
                        )}

                        {/* 底部操作 */}
                        <div className="flex items-center justify-between mt-2">
                          {!notification.read && (
                            <button
                              onClick={() => markAsRead(notification.id)}
                              className="text-xs text-blue-500 hover:text-blue-600"
                            >
                              标为已读
                            </button>
                          )}
                          <button
                            onClick={() => deleteNotification(notification.id)}
                            className="text-xs text-gray-400 hover:text-gray-600 ml-auto"
                          >
                            删除
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 面板底部 */}
          <div className="p-3 border-t bg-gray-50 text-center">
            <button
              onClick={() => setNotifications([])}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              清空所有通知
            </button>
          </div>
        </div>
      )}

      {/* 紧急通知弹窗 (重要警报自动显示) */}
      {notifications.filter(n => 
        (n.severity === 'emergency' || n.severity === 'critical') && !n.read
      ).map(notification => (
        <div
          key={`modal-${notification.id}`}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4"
          onClick={() => markAsRead(notification.id)}
        >
          <div 
            className={`max-w-md w-full rounded-2xl p-6 ${
              notification.severity === 'emergency' 
                ? 'bg-red-50 border-2 border-red-200' 
                : 'bg-orange-50 border-2 border-orange-200'
            }`}
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 mb-4">
              {notificationIcons.health_alert[notification.severity as keyof typeof notificationIcons.health_alert]}
              <h3 className="text-xl font-bold">{notification.title}</h3>
            </div>
            <p className="text-lg mb-6">{notification.message}</p>
            
            {notification.data?.recommendation && (
              <div className="bg-white/70 rounded-lg p-3 mb-4">
                <p className="font-medium">建议:</p>
                <p>{notification.data.recommendation}</p>
              </div>
            )}
            
            <div className="flex gap-3">
              {notification.actions?.map((action, idx) => (
                <button
                  key={idx}
                  onClick={() => handleAction(action.action, notification)}
                  className={`flex-1 py-3 rounded-xl font-medium transition-colors ${
                    idx === 0 
                      ? 'bg-red-500 text-white hover:bg-red-600' 
                      : 'bg-white border-2 border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  {action.label}
                </button>
              ))}
              <button
                onClick={() => markAsRead(notification.id)}
                className="px-4 py-3 rounded-xl border-2 border-gray-200 hover:bg-gray-50"
              >
                忽略
              </button>
            </div>
          </div>
        </div>
      )).slice(0, 1)}
    </>
  );
};

export default RealtimeNotifications;

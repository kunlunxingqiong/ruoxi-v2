"""
🌸 若曦V2 - 聊天界面组件
React/Next.js TypeScript组件
"""

import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, Image as ImageIcon, Smile } from 'lucide-react';

// 消息类型
interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  sources?: Array<{
    type: string;
    title: string;
  }>;
}

// 组件Props
interface ChatInterfaceProps {
  userId: string;
  apiBaseUrl: string;
  wsBaseUrl: string;
  initialMode?: 'casual' | 'health' | 'emotional' | 'professional';
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  userId,
  apiBaseUrl,
  wsBaseUrl,
  initialMode = 'casual'
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentMode, setCurrentMode] = useState(initialMode);
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 模式显示名称
  const modeNames: Record<string, string> = {
    casual: '闲聊',
    health: '健康咨询',
    emotional: '情绪陪伴',
    professional: '专业医疗'
  };

  // 模式图标颜色
  const modeColors: Record<string, string> = {
    casual: 'bg-blue-500',
    health: 'bg-green-500',
    emotional: 'bg-pink-500',
    professional: 'bg-purple-500'
  };

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 初始化WebSocket
  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket(`${wsBaseUrl}/ws/chat?client_id=${userId}`);
      
      ws.onopen = () => {
        console.log('🌸 WebSocket已连接');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'chat_message') {
          setMessages(prev => [...prev, {
            id: data.message.message_id,
            content: data.message.content,
            role: 'assistant',
            timestamp: data.message.timestamp,
            sources: data.message.sources
          }]);
          setIsLoading(false);
        } else if (data.type === 'connected') {
          // 连接成功消息
          console.log(data.message);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket断开');
        setIsConnected(false);
        // 3秒后重连
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
      };

      wsRef.current = ws;
    };

    connectWebSocket();

    return () => {
      wsRef.current?.close();
    };
  }, [wsBaseUrl, userId]);

  // 发送消息
  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const messageContent = inputMessage.trim();
    setInputMessage('');
    
    // 添加用户消息
    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      content: messageContent,
      role: 'user',
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // 发送HTTP请求
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        },
        body: JSON.stringify({
          message: messageContent,
          mode: currentMode,
          stream: false
        })
      });

      if (!response.ok) {
        throw new Error('发送失败');
      }

      // 响应会自动通过WebSocket推送
    } catch (error) {
      console.error('发送消息失败:', error);
      setIsLoading(false);
      // 显示错误
      setMessages(prev => [...prev, {
        id: `error_${Date.now()}`,
        content: '🌸 曦曦走神了，请再试一次...',
        role: 'assistant',
        timestamp: new Date().toISOString()
      }]);
    }
  };

  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // 格式化时间
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 发送欢迎语
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        id: 'welcome',
        content: '🌸 你好呀，我是若曦。有什么可以帮你的吗？',
        role: 'assistant',
        timestamp: new Date().toISOString()
      }]);
    }
  }, []);

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-blue-50 to-white rounded-2xl shadow-lg overflow-hidden">
      {/* 头部 */}
      <div className="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-200 to-purple-300 flex items-center justify-center">
              <span className="text-xl">🌸</span>
            </div>
            {isConnected && (
              <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white" />
            )}
          </div>
          <div>
            <h2 className="font-semibold text-gray-800">若曦</h2>
            <p className="text-xs text-gray-500">AI医生朋友</p>
          </div>
        </div>

        {/* 模式选择 */}
        <select
          value={currentMode}
          onChange={(e) => setCurrentMode(e.target.value as any)}
          className={`
            px-4 py-2 rounded-full text-sm text-white 
            cursor-pointer transition-all hover:opacity-90
            ${modeColors[currentMode]}
          `}
        >
          <option value="casual">💬 闲聊</option>
          <option value="health">🩺 健康咨询</option>
          <option value="emotional">🌸 情绪陪伴</option>
          <option value="professional">🏥 专业医疗</option>
        </select>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pink-200 to-purple-300 flex items-center justify-center mr-2 flex-shrink-0">
                <span className="text-sm">🌸</span>
              </div>
            )}

            <div
              className={`
                max-w-[70%] px-4 py-3 rounded-2xl
                ${message.role === 'user' 
                  ? 'bg-blue-500 text-white rounded-br-lg' 
                  : 'bg-white text-gray-800 shadow-sm rounded-bl-lg border border-gray-100'
                }
              `}
            >
              <p className="text-sm leading-relaxed whitespace-pre-wrap">
                {message.content}
              </p>
              
              {/* 引用来源 */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-200/50">
                  <p className="text-xs text-gray-500">参考来源:</p>
                  {message.sources.map((source, idx) => (
                    <span key={idx} className="text-xs text-blue-500 block">
                      • {source.title}
                    </span>
                  ))}
                </div>
              )}

              <span className="text-xs opacity-60 mt-1 block">
                {formatTime(message.timestamp)}
              </span>
            </div>

            {message.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center ml-2 flex-shrink-0">
                <span className="text-white text-sm">👤</span>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pink-200 to-purple-300 flex items-center justify-center mr-2">
              <span className="text-sm">🌸</span>
            </div>
            <div className="bg-white px-4 py-3 rounded-2xl shadow-sm border border-gray-100">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区 */}
      <div className="px-6 py-4 bg-white border-t border-gray-100">
        <div className="flex items-center gap-3">
          <button
            className="p-2 rounded-full hover:bg-gray-100 transition-colors text-gray-500"
            title="表情"
          >
            <Smile size={20} />
          </button>
          
          <button
            className="p-2 rounded-full hover:bg-gray-100 transition-colors text-gray-500"
            title="图片"
          >
            <ImageIcon size={20} />
          </button>

          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="和若曦聊聊..."
              className="w-full px-4 py-3 bg-gray-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-pink-300 transition-all"
            />
          </div>

          <button
            className="p-2 rounded-full hover:bg-gray-100 transition-colors text-gray-500"
            title="语音"
          >
            <Mic size={20} />
          </button>

          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className={`
              p-3 rounded-full transition-all
              ${inputMessage.trim() && !isLoading
                ? 'bg-gradient-to-r from-pink-400 to-purple-500 text-white hover:shadow-lg' 
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }
            `}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Sparkles, Heart, Activity } from 'lucide-react'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  emotion?: string
}

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: '🌸 你好呀~ 曦曦在这里陪着你。有什么想聊的吗？',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsTyping(true)

    // 模拟AI响应 (实际应调用API)
    setTimeout(() => {
      const responses = [
        '🌸 曦曦听到了~ 继续说，我在听。',
        '抱抱你... 这种感觉确实不好受。',
        '听起来你今天很累... 要不要早点休息？',
        '曦曦觉得你可以试试深呼吸，吸气——呼气——',
        '不管发生什么，曦曦都会在这里陪着你。💜',
      ]

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responses[Math.floor(Math.random() * responses.length)],
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, aiMessage])
      setIsTyping(false)
    }, 1500)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
            <Sparkles className="w-8 h-8 text-ruoxi-500" />
            和若曦聊天
          </h1>
          <p className="text-gray-500 mt-1">
            曦曦会记住你们的对话，给你温暖的陪伴 💜
          </p>
        </div>
      </div>

      {/* Chat Container */}
      <div className="flex-1 bg-white/60 backdrop-blur-sm rounded-3xl border border-ruoxi-100 flex flex-col overflow-hidden">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <AnimatePresence>
            {messages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className={`flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[70%] px-5 py-3 rounded-2xl ${
                    message.role === 'user'
                      ? 'bg-ruoxi-500 text-white rounded-br-md'
                      : 'bg-white border border-ruoxi-100 text-gray-700 rounded-bl-md shadow-sm'
                  }`}
                >
                  <p className="leading-relaxed">{message.content}</p>
                  <span
                    className={`text-xs mt-2 block ${
                      message.role === 'user' 
                        ? 'text-ruoxi-100' 
                        : 'text-gray-400'
                    }`}
                  >
                    {format(message.timestamp, 'HH:mm')}
                  </span>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Typing Indicator */}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="bg-white border border-ruoxi-100 rounded-2xl rounded-bl-md px-5 py-4 shadow-sm">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-ruoxi-300 to-lavender-300 flex items-center justify-center">
                    <Heart className="w-4 h-4 text-white animate-pulse" />
                  </div>
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-ruoxi-300 rounded-full animate-typing-dot" />
                    <span className="w-2 h-2 bg-ruoxi-300 rounded-full animate-typing-dot" />
                    <span className="w-2 h-2 bg-ruoxi-300 rounded-full animate-typing-dot" />
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-ruoxi-100 p-4 bg-white/80">
          <div className="flex items-end gap-3">
            <button className="p-3 rounded-xl bg-ruoxi-50 text-ruoxi-500 hover:bg-ruoxi-100 transition-colors">
              <Activity className="w-5 h-5" />
            </button>
            
            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="和曦曦说点什么... 🌸"
                rows={1}
                className="w-full px-4 py-3 pr-12 bg-ruoxi-50 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-ruoxi-300 transition-all min-h-[48px] max-h-[120px]"
                style={{ height: 'auto', overflow: 'hidden' }}
              />
            </div>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSend}
              disabled={!input.trim()}
              className="p-3 rounded-xl bg-gradient-to-r from-ruoxi-500 to-lavender-500 text-white shadow-lg shadow-ruoxi-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <Send className="w-5 h-5" />
            </motion.button>
          </div>
          
          <p className="text-xs text-gray-400 mt-2 ml-16">
            Enter发送 · Shift+Enter换行
          </p>
        </div>
      </div>
    </div>
  )
}

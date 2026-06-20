import { useState } from 'react'
import { motion } from 'framer-motion'
import { Smile, Sparkles, Send } from 'lucide-react'

const emotions = [
  { emoji: '😊', label: '开心', color: 'bg-yellow-100 text-yellow-600' },
  { emoji: '😐', label: '平静', color: 'bg-blue-100 text-blue-600' },
  { emoji: '😔', label: '低落', color: 'bg-gray-100 text-gray-600' },
  { emoji: '😰', label: '焦虑', color: 'bg-orange-100 text-orange-600' },
  { emoji: '😴', label: '疲惫', color: 'bg-purple-100 text-purple-600' },
]

export function EmotionPage() {
  const [selectedEmotion, setSelectedEmotion] = useState<string | null>(null)
  const [note, setNote] = useState('')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
            <Smile className="w-8 h-8 text-ruoxi-500" />
            情绪记录
          </h1>
          <p className="text-gray-500 mt-1">
            你的心事，曦曦都懂 💜
          </p>
        </div>
      </div>

      {/* Mood Check-in */}
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-ruoxi-100">
        <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-ruoxi-500" />
          今天心情如何？
        </h2>

        <div className="flex justify-center gap-4 mb-6">
          {emotions.map((emotion) => (
            <motion.button
              key={emotion.label}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setSelectedEmotion(emotion.label)}
              className={`flex flex-col items-center gap-2 p-4 rounded-2xl transition-all ${
                selectedEmotion === emotion.label
                  ? 'bg-ruoxi-100 ring-2 ring-ruoxi-400'
                  : 'hover:bg-gray-50'
              }`}
            >
              <span className="text-4xl">{emotion.emoji}</span>
              <span className="text-sm font-medium text-gray-600">{emotion.label}</span>
            </motion.button>
          ))}
        </div>

        <div className="space-y-4">
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="想记下点什么吗... (可选)"
            rows={3}
            className="w-full px-4 py-3 rounded-xl bg-ruoxi-50 border-0 focus:ring-2 focus:ring-ruoxi-300 resize-none"
          />

          <button
            disabled={!selectedEmotion}
            className="w-full py-3 bg-gradient-to-r from-ruoxi-500 to-lavender-500 text-white rounded-xl font-medium disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Send className="w-4 h-4" />
            记录心情
          </button>
        </div>
      </div>

      {/* Emotion Trend (placeholder) */}
      <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-ruoxi-100">
        <h3 className="text-lg font-bold text-gray-800 mb-4">情绪趋势</h3>
        <div className="h-48 flex items-end justify-around">
          {[40, 65, 30, 85, 55, 70, 45].map((value, index) => (
            <div key={index} className="flex flex-col items-center gap-2">
              <motion.div
                initial={{ height: 0 }}
                animate={{ height: `${value * 1.5}px` }}
                transition={{ delay: index * 0.1 }}
                className="w-8 bg-gradient-to-t from-ruoxi-400 to-ruoxi-300 rounded-t-lg"
              />
              <span className="text-xs text-gray-400">{['一', '二', '三', '四', '五', '六', '日'][index]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

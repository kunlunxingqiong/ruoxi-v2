import { motion } from 'framer-motion'
import { Heart, TrendingUp, Activity, Calendar } from 'lucide-react'

export function HealthPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
            <Heart className="w-8 h-8 text-ruoxi-500" />
            健康管理
          </h1>
          <p className="text-gray-500 mt-1">
            记录和分析你的健康数据 💜
          </p>
        </div>
      </div>

      {/* Health Stats */}
      <div className="grid md:grid-cols-4 gap-4">
        {[
          { label: '血压记录', value: '15', unit: '次', icon: Activity, color: 'bg-red-50 text-red-500' },
          { label: '血糖记录', value: '8', unit: '次', icon: TrendingUp, color: 'bg-blue-50 text-blue-500' },
          { label: '健康评分', value: '85', unit: '分', icon: Heart, color: 'bg-green-50 text-green-500' },
          { label: '连续记录', value: '12', unit: '天', icon: Calendar, color: 'bg-purple-50 text-purple-500' },
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white/80 backdrop-blur-sm p-6 rounded-2xl border border-ruoxi-100"
          >
            <div className={`w-12 h-12 rounded-xl ${stat.color} flex items-center justify-center mb-3`}>
              <stat.icon className="w-6 h-6" />
            </div>
            <div className="text-3xl font-bold text-gray-800">{stat.value}</div>
            <div className="text-sm text-gray-500">{stat.unit}</div>
            <div className="text-sm font-medium text-gray-600 mt-1">{stat.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Quick Add */}
      <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-ruoxi-100">
        <h2 className="text-lg font-bold text-gray-800 mb-4">快速记录</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {['血压', '血糖', '体重', '睡眠'].map((type) => (
            <button
              key={type}
              className="p-4 rounded-xl bg-ruoxi-50 text-ruoxi-700 hover:bg-ruoxi-100 transition-colors font-medium"
            >
              + {type}
            </button>
          ))}
        </div>
      </div>

      {/* AI Analysis */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-ruoxi-500 to-lavender-500 rounded-2xl p-6 text-white"
      >
        <h3 className="text-xl font-bold mb-2">若曦健康分析</h3>
        <p className="text-ruoxi-100 mb-4">
          基于你最近15天的数据，若曦为你生成了一份健康报告...
        </p>
        <button className="px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors">
          查看完整报告
        </button>
      </motion.div>
    </div>
  )
}

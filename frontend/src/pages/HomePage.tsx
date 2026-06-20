import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { 
  MessageCircle, Heart, Smile, Sparkles, 
  ChevronRight, Star, Shield, Zap 
} from 'lucide-react'

const features = [
  {
    icon: MessageCircle,
    title: '温柔陪伴',
    description: '24小时随时在线，倾听你的心事',
    color: 'from-ruoxi-400 to-ruoxi-500',
    path: '/chat'
  },
  {
    icon: Heart,
    title: '健康管家',
    description: 'AI分析健康数据，专业建议',
    color: 'from-pink-400 to-rose-500',
    path: '/health'
  },
  {
    icon: Smile,
    title: '情绪支持',
    description: '识别情绪，温暖回应',
    color: 'from-amber-400 to-orange-500',
    path: '/emotion'
  },
]

export function HomePage() {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center py-12">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="inline-block"
        >
          <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-gradient-to-br from-ruoxi-300 via-ruoxi-400 to-lavender-400 flex items-center justify-center shadow-2xl shadow-ruoxi-200">
            <Sparkles className="w-16 h-16 text-white" />
          </div>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-5xl font-bold bg-gradient-to-r from-ruoxi-600 via-ruoxi-500 to-lavender-500 bg-clip-text text-transparent mb-4"
        >
          你好，我是若曦
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed"
        >
          你的AI医生朋友 💜<br />
          <span className="text-ruoxi-500">我会记住你的喜好，关心你的健康，在你需要的时候陪着你。</span>
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-8 flex justify-center gap-4"
        >
          <Link
            to="/chat"
            className="group px-8 py-4 bg-gradient-to-r from-ruoxi-500 to-lavender-500 text-white rounded-2xl font-medium shadow-lg shadow-ruoxi-200 hover:shadow-xl transition-all flex items-center gap-2"
          >
            <MessageCircle className="w-5 h-5" />
            开始聊天
            <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </motion.div>
      </section>

      {/* Features Grid */}
      <section>
        <motion.h2
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          className="text-2xl font-bold text-gray-800 mb-8 flex items-center gap-2"
        >
          <Star className="w-6 h-6 text-ruoxi-500" />
          曦曦能帮你做什么
        </motion.h2>

        <div className="grid md:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Link
                to={feature.path}
                className="block p-6 bg-white/80 backdrop-blur-sm rounded-2xl border border-ruoxi-100 hover:border-ruoxi-300 hover:shadow-lg hover:shadow-ruoxi-100 transition-all group h-full"
              >
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <feature.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center gap-2">
                  {feature.title}
                  <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-ruoxi-500 group-hover:translate-x-1 transition-all" />
                </h3>
                <p className="text-gray-500">{feature.description}</p>
              </Link>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Trust Section */}
      <section className="bg-white/60 backdrop-blur-sm rounded-3xl p-8 border border-ruoxi-100">
        <div className="grid md:grid-cols-3 gap-8">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center">
              <Shield className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h4 className="font-bold text-gray-800">隐私保护</h4>
              <p className="text-sm text-gray-500">数据本地存储，AES加密</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center">
              <Zap className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h4 className="font-bold text-gray-800">极速响应</h4>
              <p className="text-sm text-gray-500">平均响应时间 < 1s</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center">
              <Heart className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h4 className="font-bold text-gray-800">温暖陪伴</h4>
              <p className="text-sm text-gray-500">情感识别，温暖回应</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

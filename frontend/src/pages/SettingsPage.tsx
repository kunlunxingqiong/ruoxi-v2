import { motion } from 'framer-motion'
import { Settings, User, Bell, Shield, Moon } from 'lucide-react'

const settingGroups = [
  {
    title: '账户',
    icon: User,
    items: [
      { label: '个人信息', value: '编辑' },
      { label: '修改密码', value: '' },
    ]
  },
  {
    title: '通知',
    icon: Bell,
    items: [
      { label: '消息通知', value: '开启' },
      { label: '健康提醒', value: '开启' },
      { label: '每日打卡', value: '21:00' },
    ]
  },
  {
    title: '隐私',
    icon: Shield,
    items: [
      { label: '数据加密', value: 'AES-256' },
      { label: '本地存储', value: '开启' },
    ]
  },
  {
    title: '外观',
    icon: Moon,
    items: [
      { label: '深色模式', value: '自动' },
      { label: '字体大小', value: '中等' },
    ]
  },
]

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
            <Settings className="w-8 h-8 text-ruoxi-500" />
            设置
          </h1>
          <p className="text-gray-500 mt-1">管理你的账户和偏好</p>
        </div>
      </div>

      <div className="max-w-2xl space-y-4">
        {settingGroups.map((group, groupIndex) => (
          <motion.div
            key={group.title}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: groupIndex * 0.1 }}
            className="bg-white/80 backdrop-blur-sm rounded-2xl border border-ruoxi-100 overflow-hidden"
          >
            <div className="px-6 py-4 bg-ruoxi-50 border-b border-ruoxi-100 flex items-center gap-3">
              <group.icon className="w-5 h-5 text-ruoxi-500" />
              <h3 className="font-bold text-gray-800">{group.title}</h3>
            </div>

            <div className="divide-y divide-ruoxi-100">
              {group.items.map((item) => (
                <div
                  key={item.label}
                  className="px-6 py-4 flex items-center justify-between hover:bg-ruoxi-50/50 transition-colors cursor-pointer"
                >
                  <span className="text-gray-700">{item.label}</span>
                  <span className="text-gray-400 text-sm">{item.value}</span>
                </div>
              ))}
            </div>
          </motion.div>
        ))}
      </div>

      {/* About */}
      <div className="text-center text-sm text-gray-400 pt-8">
        <p>若曦V2.0.0</p>
        <p className="mt-1">用 ❤️+🌸+🤖 构建</p>
      </div>
    </div>
  )
}

import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Home, MessageCircle, Heart, Smile, Settings, Sparkles } from 'lucide-react'

const navItems = [
  { path: '/', icon: Home, label: '首页', exact: true },
  { path: '/chat', icon: MessageCircle, label: '聊天' },
  { path: '/health', icon: Heart, label: '健康' },
  { path: '/emotion', icon: Smile, label: '情绪' },
  { path: '/settings', icon: Settings, label: '设置' },
]

export function Navigation() {
  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-ruoxi-100"
    >
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <NavLink to="/" className="flex items-center gap-2">
            <motion.div
              whileHover={{ rotate: 10 }}
              className="w-10 h-10 rounded-full bg-gradient-to-br from-ruoxi-400 to-lavender-500 flex items-center justify-center"
            >
              <Sparkles className="w-5 h-5 text-white" />
            </motion.div>
            <span className="text-xl font-bold bg-gradient-to-r from-ruoxi-600 to-lavender-600 bg-clip-text text-transparent">
              若曦
            </span>
          </NavLink>

          {/* Nav Links */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.exact}
                className={({ isActive }) => `
                  relative flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium
                  transition-all duration-200
                  ${isActive
                    ? 'text-ruoxi-700 bg-ruoxi-100'
                    : 'text-gray-600 hover:text-ruoxi-600 hover:bg-ruoxi-50'
                  }
                `}
              >
                {({ isActive }) => (
                  <>
                    <item.icon className="w-4 h-4" />
                    <span>{item.label}</span>
                    {isActive && (
                      <motion.div
                        layoutId="nav-pill"
                        className="absolute inset-0 bg-ruoxi-100 rounded-full -z-10"
                        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                      />
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </div>

          {/* User Avatar (placeholder) */}
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-200 to-purple-200 flex items-center justify-center">
            <span className="text-sm font-medium text-ruoxi-700">你</span>
          </div>
        </div>
      </div>
    </motion.nav>
  )
}

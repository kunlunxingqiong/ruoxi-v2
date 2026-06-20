import { Routes, Route } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'

import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { ChatPage } from './pages/ChatPage'
import { HealthPage } from './pages/HealthPage'
import { EmotionPage } from './pages/EmotionPage'
import { SettingsPage } from './pages/SettingsPage'

function App() {
  return (
    <Layout>
      <AnimatePresence mode="wait">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/health" element={<HealthPage />} />
          <Route path="/emotion" element={<EmotionPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </AnimatePresence>
    </Layout>
  )
}

export default App

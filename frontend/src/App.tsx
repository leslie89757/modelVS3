
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import AuthenticatedLayout from './components/AuthenticatedLayout'
import ErrorBoundary from './components/ErrorBoundary'
import Login from './pages/Login'
import Register from './pages/Register'
import ClientAgentExperience from './pages/ClientAgentExperience'
import Dashboard from './pages/Dashboard'
import Models from './pages/Models'
import Agents from './pages/Agents'
import AgentDesigner from './pages/AgentDesigner'
import AgentMarketplace from './pages/AgentMarketplace'
import Tools from './pages/Tools'
import ToolsTest from './pages/ToolsTest'
import ToolsDebug from './pages/ToolsDebug'
import Runs from './pages/Runs'
import Chat from './pages/Chat'
import AgentExecute from './pages/AgentExecute'
import Settings from './pages/Settings'
import MultiModelTestWorkspace from './pages/MultiModelTestWorkspace'
import TestPage from './pages/TestPage'

// 路由保护组件
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

// 公开路由组件（已登录用户重定向到主页）
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      {/* 公开路由 */}
      <Route path="/login" element={
        <PublicRoute>
          <Login />
        </PublicRoute>
      } />
      <Route path="/register" element={
        <PublicRoute>
          <Register />
        </PublicRoute>
      } />
      
      {/* 客户端体验页面 - 公开访问 */}
      <Route path="/experience/:agentId" element={<ClientAgentExperience />} />

      {/* 受保护的路由 */}
      <Route path="/*" element={
        <ProtectedRoute>
          <AuthenticatedLayout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/models" element={<Models />} />
              <Route path="/agents" element={<Agents />} />
              <Route path="/agent-designer" element={<AgentDesigner />} />
              <Route path="/marketplace" element={<AgentMarketplace />} />
              <Route path="/tools" element={<Tools />} />
              <Route path="/tools-test" element={<ToolsTest />} />
              <Route path="/tools-debug" element={<ToolsDebug />} />
              <Route path="/runs" element={<Runs />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/agent-execute/:agentId" element={<AgentExecute />} />
              <Route path="/settings" element={<Settings />} />
              {/* 新增：测试页面路由 */}
              <Route path="/test-page" element={<TestPage />} />
              {/* 新增：操练场路由 */}
              <Route path="/multi-model-workspace" element={<MultiModelTestWorkspace />} />
            </Routes>
          </AuthenticatedLayout>
        </ProtectedRoute>
      } />
    </Routes>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <AppRoutes />
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App 
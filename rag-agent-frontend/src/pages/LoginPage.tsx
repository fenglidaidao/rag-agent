// src/pages/LoginPage.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff } from 'lucide-react'
import { authApi } from '../api/auth'
import { useAuthStore } from '../store/authStore'

export default function LoginPage() {
  const navigate = useNavigate()
  const { setToken } = useAuthStore()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)  // ✅ 新增
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async () => {
    if (!username || !password) { setError('请填写用户名和密码'); return }
    setLoading(true); setError('')
    try {
      if (mode === 'register') {
        await authApi.register(username, password)
        setMode('login')
        setError('')
        return
      }
      const token = await authApi.login(username, password)
      setToken(token, username)
      navigate('/')
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.response?.data?.message || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  return (
      <div className="h-full flex items-center justify-center bg-bg-base">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-accent/5 rounded-full blur-3xl" />
        </div>

        <div className="relative w-full max-w-sm px-4 animate-fade-in">
          <div className="text-center mb-8">
            <div className="w-12 h-12 rounded-2xl bg-accent flex items-center justify-center mx-auto mb-4">
              <span className="text-bg-base text-xl font-bold">R</span>
            </div>
            <h1 className="text-2xl font-semibold text-text-primary">RAG Agent</h1>
            <p className="text-text-muted text-sm mt-1">智能知识库助手</p>
          </div>

          <div className="card space-y-4">
            <div className="flex bg-bg-base rounded-lg p-1">
              {(['login', 'register'] as const).map((m) => (
                  <button
                      key={m}
                      onClick={() => { setMode(m); setError('') }}
                      className={`flex-1 py-1.5 rounded-md text-sm transition-all duration-150 ${
                          mode === m ? 'bg-bg-elevated text-text-primary' : 'text-text-muted hover:text-text-secondary'
                      }`}
                  >
                    {m === 'login' ? '登录' : '注册'}
                  </button>
              ))}
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-text-muted mb-1.5 block">用户名</label>
                <input
                    className="input-base"
                    placeholder="请输入用户名"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && submit()}
                />
              </div>
              <div>
                <label className="text-xs text-text-muted mb-1.5 block">密码</label>
                {/* ✅ 密码输入框 + 小眼睛 */}
                <div className="relative">
                  <input
                      type={showPassword ? 'text' : 'password'}
                      className="input-base pr-10"
                      placeholder="请输入密码"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && submit()}
                  />
                  <button
                      type="button"
                      onClick={() => setShowPassword(v => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                      tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>
            </div>

            {error && (
                <p className="text-danger text-xs bg-danger/10 border border-danger/20 rounded-lg px-3 py-2">
                  {error}
                </p>
            )}

            <button onClick={submit} disabled={loading} className="btn-primary w-full">
              {loading ? '处理中...' : mode === 'login' ? '登录' : '注册'}
            </button>
          </div>
        </div>
      </div>
  )
}
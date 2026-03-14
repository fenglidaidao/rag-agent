// src/components/Sidebar.tsx
import { useEffect, useState, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Plus, MessageSquare, BookOpen, Wrench, LogOut, Trash2, Pencil, Check, X } from 'lucide-react'
import clsx from 'clsx'
import { chatApi } from '../api/chat'
import { useChatStore } from '../store/chatStore'
import { useAuthStore } from '../store/authStore'

export default function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { conversations, currentThreadId, setConversations, setCurrentThread, setMessages } = useChatStore()
  const { username, logout } = useAuthStore()

  // 正在编辑的 thread_id 和临时标题
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')
  const editInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { loadConversations() }, [])

  // 编辑框出现时自动聚焦全选
  useEffect(() => {
    if (editingId && editInputRef.current) {
      editInputRef.current.focus()
      editInputRef.current.select()
    }
  }, [editingId])

  const loadConversations = async () => {
    try {
      const res = await chatApi.listConversations()
      const convs = res.data.conversations
      setConversations(convs)

      // 如果 localStorage 有上次的 thread_id 且该会话仍存在，自动恢复消息
      if (currentThreadId && convs.some(c => c.thread_id === currentThreadId)) {
        try {
          const msgRes = await chatApi.getMessages(currentThreadId)
          setMessages(msgRes.data.messages)
        } catch {}
      } else if (currentThreadId) {
        // 会话已被删除，清除残留
        setCurrentThread('')
      }
    } catch {}
  }

  const newConversation = async () => {
    try {
      const res = await chatApi.createConversation()
      const { thread_id } = res.data
      await loadConversations()
      setCurrentThread(thread_id)
      setMessages([])
      navigate('/')
    } catch {}
  }

  const selectConversation = async (threadId: string) => {
    if (editingId) return   // 编辑中不触发切换
    setCurrentThread(threadId)
    try {
      const res = await chatApi.getMessages(threadId)
      setMessages(res.data.messages)
    } catch {}
    navigate('/')
  }

  const deleteConversation = async (e: React.MouseEvent, threadId: string) => {
    e.stopPropagation()
    try {
      await chatApi.deleteConversation(threadId)
      await loadConversations()
      if (currentThreadId === threadId) {
        setCurrentThread('')
        setMessages([])
      }
    } catch {}
  }

  // 进入编辑模式
  const startEdit = (e: React.MouseEvent, threadId: string, currentTitle: string) => {
    e.stopPropagation()
    setEditingId(threadId)
    setEditingTitle(currentTitle)
  }

  // 保存标题
  const saveTitle = async (threadId: string) => {
    const title = editingTitle.trim()
    if (!title) { cancelEdit(); return }
    try {
      await chatApi.updateTitle(threadId, title)
      // 本地直接更新，不重新请求
      setConversations(conversations.map(c =>
          c.thread_id === threadId ? { ...c, title } : c
      ))
    } catch {}
    setEditingId(null)
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditingTitle('')
  }

  const handleEditKeyDown = (e: React.KeyboardEvent, threadId: string) => {
    if (e.key === 'Enter') { e.preventDefault(); saveTitle(threadId) }
    if (e.key === 'Escape') cancelEdit()
  }

  const handleLogout = () => { logout(); navigate('/login') }

  const navItems = [
    { path: '/',          icon: MessageSquare, label: '对话'   },
    { path: '/knowledge', icon: BookOpen,      label: '知识库' },
    { path: '/tools',     icon: Wrench,        label: '工具管理'},
  ]

  return (
      <aside className="w-60 bg-bg-surface border-r border-bg-border flex flex-col h-full flex-shrink-0">
        {/* Logo */}
        <div className="px-4 py-5 border-b border-bg-border">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center">
              <span className="text-bg-base text-xs font-bold">R</span>
            </div>
            <span className="font-semibold text-text-primary tracking-wide">RAG Agent</span>
          </div>
        </div>

        {/* 导航 */}
        <nav className="px-2 pt-3 pb-2 border-b border-bg-border">
          {navItems.map(({ path, icon: Icon, label }) => (
              <button key={path} onClick={() => navigate(path)}
                      className={clsx(
                          'w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all duration-150 mb-0.5',
                          location.pathname === path
                              ? 'bg-accent-dim text-accent border border-accent/20'
                              : 'text-text-secondary hover:bg-bg-elevated hover:text-text-primary'
                      )}>
                <Icon size={15} />
                {label}
              </button>
          ))}
        </nav>

        {/* 新建会话 */}
        <div className="px-2 pt-3">
          <button onClick={newConversation}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-accent
                     border border-dashed border-accent/30 hover:border-accent/60
                     hover:bg-accent-dim transition-all duration-150">
            <Plus size={14} />
            新建对话
          </button>
        </div>

        {/* 会话列表 */}
        <div className="flex-1 overflow-y-auto px-2 pt-2 pb-2">
          {conversations.map((conv) => (
              <div
                  key={conv.thread_id}
                  onClick={() => selectConversation(conv.thread_id)}
                  onDoubleClick={(e) => startEdit(e, conv.thread_id, conv.title)}
                  className={clsx(
                      'group flex items-center gap-1.5 px-2 py-2 rounded-lg cursor-pointer mb-0.5 transition-all duration-150',
                      currentThreadId === conv.thread_id
                          ? 'bg-bg-elevated text-text-primary border border-bg-border'
                          : 'text-text-secondary hover:bg-bg-elevated hover:text-text-primary'
                  )}
              >
                {editingId === conv.thread_id ? (
                    /* ✅ 编辑模式 */
                    <div className="flex items-center gap-1 flex-1 min-w-0" onClick={e => e.stopPropagation()}>
                      <input
                          ref={editInputRef}
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onKeyDown={(e) => handleEditKeyDown(e, conv.thread_id)}
                          onBlur={() => saveTitle(conv.thread_id)}
                          className="flex-1 min-w-0 bg-bg-base border border-accent/40 rounded-md px-2 py-0.5
                             text-sm text-text-primary outline-none focus:border-accent transition-colors"
                          maxLength={30}
                      />
                      <button
                          onMouseDown={(e) => { e.preventDefault(); saveTitle(conv.thread_id) }}
                          className="text-success hover:text-success flex-shrink-0"
                      >
                        <Check size={13} />
                      </button>
                      <button
                          onMouseDown={(e) => { e.preventDefault(); cancelEdit() }}
                          className="text-text-muted hover:text-danger flex-shrink-0"
                      >
                        <X size={13} />
                      </button>
                    </div>
                ) : (
                    /* ✅ 普通模式 */
                    <>
                      <span className="truncate flex-1 text-sm">{conv.title}</span>

                      {/* 操作按钮 — hover 时显示 */}
                      <div className="opacity-0 group-hover:opacity-100 flex items-center gap-0.5 flex-shrink-0 transition-opacity">
                        <button
                            onClick={(e) => startEdit(e, conv.thread_id, conv.title)}
                            title="重命名"
                            className="p-1 rounded text-text-muted hover:text-accent hover:bg-accent-dim transition-colors"
                        >
                          <Pencil size={12} />
                        </button>
                        <button
                            onClick={(e) => deleteConversation(e, conv.thread_id)}
                            title="删除"
                            className="p-1 rounded text-text-muted hover:text-danger hover:bg-danger/10 transition-colors"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </>
                )}
              </div>
          ))}

          {conversations.length === 0 && (
              <p className="text-text-muted text-xs px-3 py-4 text-center">暂无会话记录</p>
          )}
        </div>

        {/* 底部用户信息 */}
        <div className="px-3 py-3 border-t border-bg-border flex items-center justify-between">
          <span className="text-text-secondary text-sm truncate">{username}</span>
          <button onClick={handleLogout} className="text-text-muted hover:text-danger transition-colors">
            <LogOut size={15} />
          </button>
        </div>
      </aside>
  )
}
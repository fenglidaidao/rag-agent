// src/pages/ChatPage.tsx
import { useEffect, useRef, useState } from 'react'
import { Send, Paperclip, X, FileText, Image, File, Quote } from 'lucide-react'
import MessageBubble from '../components/MessageBubble'
import StreamingBubble from '../components/StreamingBubble'
import { useChatStore } from '../store/chatStore'
import { useStream } from '../hooks/useStream'
import { chatApi } from '../api/chat'

function FileIcon({ name }: { name: string }) {
  const ext = name.split('.').pop()?.toLowerCase() || ''
  if (['png', 'jpg', 'jpeg', 'webp'].includes(ext)) return <Image size={14} />
  if (['txt', 'md', 'pdf', 'docx'].includes(ext)) return <FileText size={14} />
  return <File size={14} />
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

interface UploadedFile {
  file: File
  status: 'uploading' | 'success' | 'error'
  message: string
  previewUrl?: string
}

// 引用内容截断显示
function truncate(text: string, max = 80) {
  return text.length > max ? text.slice(0, max) + '...' : text
}

export default function ChatPage() {
  const { messages, streaming, streamingContent, currentThreadId,
    setCurrentThread, setMessages, setConversations } = useChatStore()
  const { send } = useStream()
  const [input, setInput] = useState('')
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null)
  const [quoteContent, setQuoteContent] = useState('')   // ✅ 引用内容
  const bottomRef = useRef<HTMLDivElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const initThread = async () => {
    try {
      const res = await chatApi.createConversation()
      const { thread_id } = res.data
      setCurrentThread(thread_id)
      const convRes = await chatApi.listConversations()
      setConversations(convRes.data.conversations)
      return thread_id
    } catch { return null }
  }

  const handleSend = async () => {
    if (!input.trim() || streaming) return
    let threadId = currentThreadId
    if (!threadId) threadId = await initThread()
    if (!threadId) return
    const msg = input.trim()
    const quote = quoteContent
    setInput('')
    setQuoteContent('')   // ✅ 发送后清空引用
    await send(msg, threadId, quote)
  }

  // ✅ 引用回调
  const handleQuote = (content: string) => {
    setQuoteContent(content)
    textareaRef.current?.focus()
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    e.target.value = ''
    const isImage = ['png', 'jpg', 'jpeg', 'webp'].includes(file.name.split('.').pop()?.toLowerCase() || '')
    const previewUrl = isImage ? URL.createObjectURL(file) : undefined
    setUploadedFile({ file, status: 'uploading', message: '上传中...', previewUrl })
    try {
      await chatApi.uploadContext(file)
      setUploadedFile({ file, status: 'success', message: '已作为对话上下文', previewUrl })
    } catch {
      setUploadedFile({ file, status: 'error', message: '上传失败，请重试', previewUrl })
    }
  }

  const removeFile = () => {
    if (uploadedFile?.previewUrl) URL.revokeObjectURL(uploadedFile.previewUrl)
    setUploadedFile(null)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const isEmpty = messages.length === 0 && !streaming

  return (
      <div className="flex flex-col h-full">
        {/* 消息区域 */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
          {isEmpty && (
              <div className="h-full flex flex-col items-center justify-center animate-fade-in">
                <div className="w-16 h-16 rounded-2xl bg-accent-dim border border-accent/20 flex items-center justify-center mb-4">
                  <span className="text-accent text-2xl font-bold">R</span>
                </div>
                <h2 className="text-text-primary font-medium text-lg mb-2">RAG Agent 助手</h2>
                <p className="text-text-muted text-sm text-center max-w-xs">
                  支持知识库问答、工具调用和普通对话，可上传文件作为对话上下文
                </p>
                <div className="flex gap-2 mt-6 flex-wrap justify-center">
                  {['知识库有哪些内容？', '上海今天天气', '你好！'].map((q) => (
                      <button key={q} onClick={() => setInput(q)}
                              className="text-xs px-3 py-1.5 rounded-full border border-bg-border text-text-secondary
                             hover:border-accent/40 hover:text-accent hover:bg-accent-dim transition-all">
                        {q}
                      </button>
                  ))}
                </div>
              </div>
          )}

          {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} onQuote={handleQuote} />
          ))}
          {streaming && <StreamingBubble content={streamingContent} />}
          <div ref={bottomRef} />
        </div>

        {/* 输入区域 */}
        <div className="px-6 pb-6 pt-3 border-t border-bg-border">

          {/* 文件预览条 */}
          {uploadedFile && (
              <div className={`flex items-center gap-3 mb-3 px-3 py-2.5 rounded-xl border animate-slide-up
            ${uploadedFile.status === 'uploading' ? 'border-accent/30 bg-accent-dim' : ''}
            ${uploadedFile.status === 'success'   ? 'border-success/30 bg-success/5' : ''}
            ${uploadedFile.status === 'error'     ? 'border-danger/30 bg-danger/5'   : ''}
          `}>
                {uploadedFile.previewUrl ? (
                    <img src={uploadedFile.previewUrl} alt="preview"
                         className="w-10 h-10 rounded-lg object-cover flex-shrink-0 border border-bg-border" />
                ) : (
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 border
                ${uploadedFile.status === 'success'   ? 'border-success/30 text-success bg-success/10' : ''}
                ${uploadedFile.status === 'error'     ? 'border-danger/30 text-danger bg-danger/10' : ''}
                ${uploadedFile.status === 'uploading' ? 'border-accent/30 text-accent bg-accent-dim' : ''}
              `}>
                      <FileIcon name={uploadedFile.file.name} />
                    </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-text-primary truncate">{uploadedFile.file.name}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-text-muted">{formatSize(uploadedFile.file.size)}</span>
                    <span className="text-text-muted">·</span>
                    <span className={`text-xs ${
                        uploadedFile.status === 'uploading' ? 'text-accent' :
                            uploadedFile.status === 'success'   ? 'text-success' : 'text-danger'
                    }`}>
                  {uploadedFile.status === 'uploading' && (
                      <span className="flex items-center gap-1">
                      {[0,1,2].map(i => (
                          <span key={i} className="w-1 h-1 rounded-full bg-accent animate-pulse-dot inline-block"
                                style={{ animationDelay: `${i * 0.2}s` }} />
                      ))}
                        上传中
                    </span>
                  )}
                      {uploadedFile.status === 'success' && '✓ 已作为对话上下文'}
                      {uploadedFile.status === 'error'   && '✗ 上传失败，请重试'}
                </span>
                  </div>
                </div>
                <button onClick={removeFile} className="text-text-muted hover:text-text-primary transition-colors flex-shrink-0">
                  <X size={15} />
                </button>
              </div>
          )}

          {/* ✅ 引用预览条 */}
          {quoteContent && (
              <div className="flex items-start gap-2 mb-3 px-3 py-2.5 rounded-xl border border-accent/20
                          bg-accent-dim animate-slide-up">
                <Quote size={13} className="text-accent flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-accent mb-0.5 font-medium">引用内容</p>
                  <p className="text-xs text-text-secondary leading-relaxed line-clamp-2">
                    {truncate(quoteContent, 120)}
                  </p>
                </div>
                <button onClick={() => setQuoteContent('')}
                        className="text-text-muted hover:text-text-primary transition-colors flex-shrink-0">
                  <X size={13} />
                </button>
              </div>
          )}

          {/* 输入框 */}
          <div className="flex items-end gap-2 bg-bg-elevated border border-bg-border rounded-2xl px-4 py-3
                        focus-within:border-accent/40 transition-colors">
            <input ref={fileRef} type="file" className="hidden" onChange={handleFileUpload}
                   accept=".txt,.md,.csv,.png,.jpg,.jpeg" />

            <button onClick={() => fileRef.current?.click()}
                    className="text-text-muted hover:text-accent transition-colors pb-0.5 flex-shrink-0"
                    title="上传文件（作为对话上下文）">
              <Paperclip size={17} />
            </button>

            <textarea
                ref={textareaRef}
                className="flex-1 bg-transparent text-text-primary placeholder-text-muted outline-none
                       resize-none text-sm leading-relaxed max-h-32"
                placeholder={quoteContent ? '针对引用内容追问...' : '输入消息，Shift+Enter 换行...'}
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
            />

            <button onClick={handleSend} disabled={!input.trim() || streaming}
                    className="w-8 h-8 rounded-xl bg-accent text-bg-base flex items-center justify-center
                       flex-shrink-0 hover:bg-accent-hover transition-all
                       disabled:opacity-30 disabled:cursor-not-allowed">
              <Send size={14} />
            </button>
          </div>

          <p className="text-text-muted text-xs mt-2 text-center">
            Enter 发送 · Shift+Enter 换行 · 悬停消息可复制或引用
          </p>
        </div>
      </div>
  )
}
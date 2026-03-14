// src/api/chat.ts
import client from './client'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  created_at?: string
}

export interface Conversation {
  thread_id: string
  title: string
  created_at: string
  updated_at: string
}

export const chatApi = {
  // 创建会话
  createConversation: () =>
    client.post<{ thread_id: string; title: string }>('/conversations'),

  // 会话列表
  listConversations: () =>
    client.get<{ conversations: Conversation[] }>('/conversations'),

  // 历史消息
  getMessages: (threadId: string) =>
    client.get<{ messages: Message[] }>(`/conversations/${threadId}/messages`),

  // 删除会话
  deleteConversation: (threadId: string) =>
    client.delete(`/conversations/${threadId}`),

  // 普通对话
  chat: (message: string, threadId: string) =>
    client.post<{ response: string; thread_id: string }>('/chat', {
      message,
      thread_id: threadId,
    }),

  // 上传临时文件（对话上下文）
  uploadContext: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return client.post('/uploadfile/', form)
  },

  // 修改聊天记录名
  updateTitle: (threadId: string, title: string) =>
      client.put(`/conversations/${threadId}/title`, { title }),
}

// 流式对话 — 使用原生 fetch 处理 SSE
export async function chatStream(
    message: string,
    threadId: string,
    onChunk: (chunk: string) => void,
    onDone: () => void,
    onError: (err: string) => void,
    quote: string = ""   // ✅ 新增
) {
  const token = localStorage.getItem('token')
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message, thread_id: threadId, quote }),  // ✅ 带上 quote
  })

  if (!res.ok) { onError(`请求失败: ${res.status}`); return }

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const text = decoder.decode(value)
    for (const line of text.split('\n')) {
      if (!line.startsWith('data: ')) continue
      const chunk = line.slice(6)
      if (chunk === '"[DONE]"' || chunk === '[DONE]') { onDone(); return }
      if (chunk.startsWith('"[ERROR]') || chunk.startsWith('[ERROR]')) { onError(chunk); return }
      try {
        onChunk(JSON.parse(chunk))
      } catch {
        onChunk(chunk)
      }
    }
  }
  onDone()
}

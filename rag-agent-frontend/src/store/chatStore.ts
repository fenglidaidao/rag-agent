// src/store/chatStore.ts
import { create } from 'zustand'
import type { Message, Conversation } from '../api/chat'

interface ChatState {
  conversations: Conversation[]
  currentThreadId: string | null
  messages: Message[]
  streaming: boolean
  streamingContent: string

  setConversations: (convs: Conversation[]) => void
  setCurrentThread: (threadId: string) => void
  setMessages: (msgs: Message[]) => void
  addMessage: (msg: Message) => void
  setStreaming: (v: boolean) => void
  appendStreamChunk: (chunk: string) => void
  commitStreamMessage: () => void
  resetStream: () => void
}

const THREAD_KEY = 'currentThreadId'

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentThreadId: localStorage.getItem(THREAD_KEY),
  messages: [],
  streaming: false,
  streamingContent: '',

  setConversations: (conversations) => set({ conversations }),
  setCurrentThread: (threadId) => {
    if (threadId) {
      localStorage.setItem(THREAD_KEY, threadId)
    } else {
      localStorage.removeItem(THREAD_KEY)
    }
    set({ currentThreadId: threadId || null, messages: [] })
  },
  setMessages: (messages) => set({ messages }),

  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, msg] })),

  setStreaming: (streaming) => set({ streaming }),

  appendStreamChunk: (chunk) =>
    set((s) => ({ streamingContent: s.streamingContent + chunk })),

  commitStreamMessage: () => {
    const content = get().streamingContent
    if (!content) return
    set((s) => ({
      messages: [...s.messages, { role: 'assistant', content }],
      streamingContent: '',
      streaming: false,
    }))
  },

  resetStream: () => set({ streamingContent: '', streaming: false }),
}))

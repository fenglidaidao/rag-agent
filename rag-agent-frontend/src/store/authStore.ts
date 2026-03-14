// src/store/authStore.ts
import { create } from 'zustand'

interface AuthState {
  token: string | null
  username: string | null
  setToken: (token: string, username: string) => void
  logout: () => void
  isLoggedIn: () => boolean
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem('token'),
  username: localStorage.getItem('username'),

  setToken: (token, username) => {
    localStorage.setItem('token', token)
    localStorage.setItem('username', username)
    set({ token, username })
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('currentThreadId')  // 加这行
    set({ token: null, username: null })
  },

  isLoggedIn: () => !!get().token,
}))

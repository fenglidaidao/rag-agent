// src/api/auth.ts
import client from './client'

export const authApi = {
  register: (username: string, password: string) =>
    client.post('/auth/register', { username, password }),

  login: async (username: string, password: string): Promise<string> => {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    const res = await client.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    return res.data.access_token
  },
}

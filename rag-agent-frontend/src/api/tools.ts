// src/api/tools.ts
import client from './client'

export interface Tool {
  name: string
  description: string
  enabled: boolean
  builtin: boolean
}

export const toolsApi = {
  list: () =>
    client.get<{ tools: Tool[] }>('/tools'),

  add: (name: string, description: string, code: string) =>
    client.post('/tools', { name, description, code }),

  update: (name: string, data: { description?: string; code?: string; enabled?: boolean }) =>
    client.put(`/tools/${name}`, data),

  delete: (name: string) =>
    client.delete(`/tools/${name}`),
}

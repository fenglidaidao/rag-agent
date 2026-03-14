// src/api/knowledge.ts
import client from './client'

export interface KnowledgeFile {
  filename: string
  uploaded_at: string
}

export const knowledgeApi = {
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return client.post<{ success: boolean; message: string }>('/knowledge/upload', form)
  },

  list: () =>
    client.get<{ files: KnowledgeFile[] }>('/knowledge/list'),

  delete: (filename: string) =>
    client.delete<{ message: string }>(`/knowledge/${encodeURIComponent(filename)}`),
}

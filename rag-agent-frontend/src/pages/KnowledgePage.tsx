// src/pages/KnowledgePage.tsx
import { useEffect, useState } from 'react'
import { Trash2, FileText, RefreshCw, Database } from 'lucide-react'
import FileUploader from '../components/FileUploader'
import { knowledgeApi, type KnowledgeFile } from '../api/knowledge'

export default function KnowledgePage() {
  const [files, setFiles] = useState<KnowledgeFile[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => { load() }, [])

  const load = async () => {
    setLoading(true)
    try {
      const res = await knowledgeApi.list()
      setFiles(res.data.files)
    } catch {}
    setLoading(false)
  }

  const handleUpload = async (file: File) => {
    const res = await knowledgeApi.upload(file)
    await load()
    return { success: res.data.success, message: res.data.message }
  }

  const handleDelete = async (filename: string) => {
    if (!confirm(`确定删除 "${filename}" 并重建向量库？`)) return
    try {
      await knowledgeApi.delete(filename)
      await load()
    } catch {}
  }

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            <Database size={18} className="text-accent" />
            知识库管理
          </h1>
          <p className="text-text-muted text-sm mt-0.5">上传文件后将自动 chunk 并入向量库，供 RAG 检索使用</p>
        </div>
        <button onClick={load} className="btn-ghost flex items-center gap-1.5 text-sm">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          刷新
        </button>
      </div>

      {/* 上传区域 */}
      <div className="card">
        <h2 className="text-sm font-medium text-text-primary mb-3">上传文件</h2>
        <FileUploader
          onUpload={handleUpload}
          accept=".txt,.md,.pdf,.docx,.csv,.png,.jpg,.jpeg"
          label="上传到知识库（txt / md / pdf / docx / csv / 图片）"
        />
      </div>

      {/* 文件列表 */}
      <div className="card">
        <h2 className="text-sm font-medium text-text-primary mb-3">
          已入库文件
          <span className="ml-2 tag border-bg-border text-text-muted">{files.length}</span>
        </h2>

        {files.length === 0 ? (
          <div className="text-center py-10 text-text-muted">
            <FileText size={32} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">知识库为空，请上传文件</p>
          </div>
        ) : (
          <div className="space-y-2">
            {files.map((f) => (
              <div
                key={f.filename}
                className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-bg-base border border-bg-border hover:border-bg-elevated transition-colors group"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <FileText size={15} className="text-accent flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm text-text-primary truncate">{f.filename}</p>
                    <p className="text-xs text-text-muted">{new Date(f.uploaded_at).toLocaleString('zh-CN')}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(f.filename)}
                  className="opacity-0 group-hover:opacity-100 text-text-muted hover:text-danger transition-all ml-3"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

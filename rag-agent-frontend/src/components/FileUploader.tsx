// src/components/FileUploader.tsx
import { useRef, useState } from 'react'
import { Paperclip, X, CheckCircle, AlertCircle, Loader } from 'lucide-react'
import clsx from 'clsx'

interface Props {
  onUpload: (file: File) => Promise<{ success: boolean; message: string }>
  accept?: string
  label?: string
}

type Status = 'idle' | 'uploading' | 'success' | 'error'

export default function FileUploader({ onUpload, accept, label = '上传文件' }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [status, setStatus] = useState<Status>('idle')
  const [message, setMessage] = useState('')
  const [filename, setFilename] = useState('')

  const handleFile = async (file: File) => {
    setFilename(file.name)
    setStatus('uploading')
    setMessage('')
    try {
      const result = await onUpload(file)
      setStatus(result.success ? 'success' : 'error')
      setMessage(result.message)
    } catch (e: any) {
      setStatus('error')
      setMessage(e?.response?.data?.message || '上传失败')
    }
    setTimeout(() => { setStatus('idle'); setFilename('') }, 3000)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = ''
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  return (
    <div>
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
        className={clsx(
          'border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200',
          status === 'idle' && 'border-bg-border hover:border-accent/40 hover:bg-accent-dim',
          status === 'uploading' && 'border-accent/40 bg-accent-dim',
          status === 'success' && 'border-success/40 bg-success/5',
          status === 'error' && 'border-danger/40 bg-danger/5',
        )}
      >
        <input ref={inputRef} type="file" accept={accept} className="hidden" onChange={handleChange} />

        {status === 'idle' && (
          <>
            <Paperclip size={20} className="mx-auto mb-2 text-text-muted" />
            <p className="text-sm text-text-secondary">{label}</p>
            <p className="text-xs text-text-muted mt-1">点击或拖拽文件到此处</p>
          </>
        )}
        {status === 'uploading' && (
          <>
            <Loader size={20} className="mx-auto mb-2 text-accent animate-spin" />
            <p className="text-sm text-accent">正在上传 {filename}...</p>
          </>
        )}
        {status === 'success' && (
          <>
            <CheckCircle size={20} className="mx-auto mb-2 text-success" />
            <p className="text-sm text-success">{message}</p>
          </>
        )}
        {status === 'error' && (
          <>
            <AlertCircle size={20} className="mx-auto mb-2 text-danger" />
            <p className="text-sm text-danger">{message}</p>
          </>
        )}
      </div>
    </div>
  )
}

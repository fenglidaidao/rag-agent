// src/pages/ToolsPage.tsx
import { useEffect, useState } from 'react'
import { Plus, Trash2, Pencil, Power, Wrench, X, Check } from 'lucide-react'
import clsx from 'clsx'
import { toolsApi, type Tool } from '../api/tools'

const TEMPLATE = `def my_tool(param: str) -> str:
    from tools.tool_response import success, logic_error, code_error
    try:
        if not param:
            return logic_error("参数不能为空")
        result = f"处理结果：{param}"
        return success(result)
    except Exception as e:
        return code_error(str(e))`

export default function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editName, setEditName] = useState('')
  const [form, setForm] = useState({ name: '', description: '', code: TEMPLATE })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => { load() }, [])

  const load = async () => {
    try {
      const res = await toolsApi.list()
      setTools(res.data.tools)
    } catch {}
  }

  const openAdd = () => {
    setEditName('')
    setForm({ name: '', description: '', code: TEMPLATE })
    setError('')
    setShowForm(true)
  }

  const openEdit = (tool: Tool) => {
    setEditName(tool.name)
    setForm({ name: tool.name, description: tool.description, code: '' })
    setError('')
    setShowForm(true)
  }

  const save = async () => {
    if (!form.name || !form.description) { setError('名称和描述必填'); return }
    setSaving(true); setError('')
    try {
      if (editName) {
        await toolsApi.update(editName, { description: form.description, code: form.code || undefined })
      } else {
        if (!form.code) { setError('新增工具需要填写代码'); setSaving(false); return }
        await toolsApi.add(form.name, form.description, form.code)
      }
      setShowForm(false)
      await load()
    } catch (e: any) {
      setError(e?.response?.data?.message || '操作失败')
    }
    setSaving(false)
  }

  const toggleEnable = async (tool: Tool) => {
    try {
      await toolsApi.update(tool.name, { enabled: !tool.enabled })
      await load()
    } catch {}
  }

  const deleteTool = async (name: string) => {
    if (!confirm(`确定删除工具 "${name}"？`)) return
    try { await toolsApi.delete(name); await load() } catch {}
  }

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            <Wrench size={18} className="text-accent" />
            工具管理
          </h1>
          <p className="text-text-muted text-sm mt-0.5">管理 Agent 可调用的工具，支持动态新增自定义工具</p>
        </div>
        <button onClick={openAdd} className="btn-primary flex items-center gap-1.5 text-sm">
          <Plus size={14} />
          新增工具
        </button>
      </div>

      {/* 工具列表 */}
      <div className="space-y-3">
        {tools.map((tool) => (
          <div key={tool.name} className={clsx(
            'card flex items-start justify-between gap-4 transition-all',
            !tool.enabled && 'opacity-50'
          )}>
            <div className="flex items-start gap-3 min-w-0 flex-1">
              <div className={clsx(
                'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5',
                tool.enabled ? 'bg-accent-dim text-accent' : 'bg-bg-base text-text-muted'
              )}>
                <Wrench size={14} />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-text-primary font-mono">{tool.name}</span>
                  {tool.builtin && (
                    <span className="tag border-accent/20 text-accent bg-accent-dim">内置</span>
                  )}
                  <span className={clsx('tag', tool.enabled
                    ? 'border-success/20 text-success bg-success/5'
                    : 'border-bg-border text-text-muted'
                  )}>
                    {tool.enabled ? '已启用' : '已禁用'}
                  </span>
                </div>
                <p className="text-sm text-text-secondary mt-1">{tool.description}</p>
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <button
                onClick={() => toggleEnable(tool)}
                title={tool.enabled ? '禁用' : '启用'}
                className={clsx(
                  'p-1.5 rounded-lg transition-colors',
                  tool.enabled
                    ? 'text-success hover:bg-success/10'
                    : 'text-text-muted hover:bg-bg-elevated'
                )}
              >
                <Power size={14} />
              </button>
              {!tool.builtin && (
                <>
                  <button onClick={() => openEdit(tool)} className="p-1.5 rounded-lg text-text-muted hover:text-accent hover:bg-accent-dim transition-colors">
                    <Pencil size={14} />
                  </button>
                  <button onClick={() => deleteTool(tool.name)} className="p-1.5 rounded-lg text-text-muted hover:text-danger hover:bg-danger/10 transition-colors">
                    <Trash2 size={14} />
                  </button>
                </>
              )}
            </div>
          </div>
        ))}

        {tools.length === 0 && (
          <div className="text-center py-16 text-text-muted">
            <Wrench size={32} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">暂无工具</p>
          </div>
        )}
      </div>

      {/* 新增/编辑弹窗 */}
      {showForm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
          <div className="bg-bg-surface border border-bg-border rounded-2xl w-full max-w-lg mx-4 animate-slide-up">
            <div className="flex items-center justify-between px-5 py-4 border-b border-bg-border">
              <h2 className="text-sm font-medium text-text-primary">{editName ? '编辑工具' : '新增工具'}</h2>
              <button onClick={() => setShowForm(false)} className="text-text-muted hover:text-text-primary">
                <X size={16} />
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div>
                <label className="text-xs text-text-muted mb-1.5 block">工具名称 <span className="text-danger">*</span></label>
                <input
                  className="input-base font-mono"
                  placeholder="get_exchange_rate"
                  value={form.name}
                  disabled={!!editName}
                  onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))}
                />
              </div>
              <div>
                <label className="text-xs text-text-muted mb-1.5 block">描述 <span className="text-danger">*</span></label>
                <input
                  className="input-base"
                  placeholder="获取两种货币之间的汇率"
                  value={form.description}
                  onChange={(e) => setForm(f => ({ ...f, description: e.target.value }))}
                />
              </div>
              <div>
                <label className="text-xs text-text-muted mb-1.5 block">
                  Python 代码 {!editName && <span className="text-danger">*</span>}
                  {editName && <span className="text-text-muted ml-1">（留空则不修改）</span>}
                </label>
                <textarea
                  className="input-base font-mono text-xs leading-relaxed"
                  rows={10}
                  value={form.code}
                  onChange={(e) => setForm(f => ({ ...f, code: e.target.value }))}
                />
              </div>

              {error && (
                <p className="text-danger text-xs bg-danger/10 border border-danger/20 rounded-lg px-3 py-2">{error}</p>
              )}

              <div className="flex gap-2 justify-end">
                <button onClick={() => setShowForm(false)} className="btn-ghost text-sm">取消</button>
                <button onClick={save} disabled={saving} className="btn-primary text-sm flex items-center gap-1.5">
                  <Check size={13} />
                  {saving ? '保存中...' : '保存'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// src/components/MessageContent.tsx
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Highlight, themes } from 'prism-react-renderer'
import { useState } from 'react'
import { Copy, Check } from 'lucide-react'

// ========== 代码块组件 ==========
function CodeBlock({ code, language }: { code: string; language: string }) {
    const [copied, setCopied] = useState(false)

    const handleCopy = async () => {
        await navigator.clipboard.writeText(code)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className="my-3 rounded-xl overflow-hidden border border-bg-border">
            {/* 顶栏 */}
            <div className="flex items-center justify-between px-4 py-2 bg-bg-base border-b border-bg-border">
                <span className="text-xs font-mono text-text-muted">{language || 'code'}</span>
                <button
                    onClick={handleCopy}
                    className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-md transition-all ${
                        copied
                            ? 'text-success bg-success/10'
                            : 'text-text-muted hover:text-text-primary hover:bg-bg-elevated'
                    }`}
                >
                    {copied ? <Check size={11} /> : <Copy size={11} />}
                    {copied ? '已复制' : '复制'}
                </button>
            </div>

            {/* 代码高亮 */}
            <Highlight
                theme={themes.oneDark}
                code={code.trimEnd()}
                language={language || 'text'}
            >
                {({ className, style, tokens, getLineProps, getTokenProps }) => (
                    <pre
                        className={className}
                        style={{
                            ...style,
                            margin: 0,
                            padding: '1rem',
                            background: '#13161b',
                            fontSize: '0.75rem',
                            lineHeight: '1.6',
                            overflowX: 'auto',
                            fontFamily: "'JetBrains Mono', monospace",
                        }}
                    >
            {tokens.map((line, i) => (
                <div key={i} {...getLineProps({ line })}>
                    {/* 行号 */}
                    <span style={{ color: '#454d5c', userSelect: 'none', marginRight: '1.2rem', fontSize: '0.7rem' }}>
                  {String(i + 1).padStart(2, ' ')}
                </span>
                    {line.map((token, j) => (
                        <span key={j} {...getTokenProps({ token })} />
                    ))}
                </div>
            ))}
          </pre>
                )}
            </Highlight>
        </div>
    )
}

// ========== 行内代码 ==========
function InlineCode({ children }: { children: string }) {
    return (
        <code className="font-mono text-xs bg-bg-base border border-bg-border rounded px-1.5 py-0.5 text-accent">
            {children}
        </code>
    )
}

// ========== 主组件 ==========
interface Props {
    content: string
    isUser?: boolean
}

export default function MessageContent({ content, isUser }: Props) {
    if (isUser) {
        return (
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
        {content}
      </pre>
        )
    }

    return (
        <div className="text-sm leading-relaxed space-y-0">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    // ✅ 代码块和行内代码统一在这里处理
                    code({ className, children }) {
                        const match = /language-(\w+)/.exec(className || '')
                        const code = String(children).replace(/\n$/, '')
                        const isBlock = code.includes('\n') || !!match

                        if (isBlock) {
                            return <CodeBlock code={code} language={match?.[1] || ''} />
                        }
                        return <InlineCode>{code}</InlineCode>
                    },

                    // 段落
                    p({ children }) {
                        return <p className="mb-3 last:mb-0 text-text-primary leading-relaxed">{children}</p>
                    },

                    // 标题
                    h1({ children }) {
                        return <h1 className="text-lg font-semibold text-text-primary mt-5 mb-3 pb-2 border-b border-bg-border">{children}</h1>
                    },
                    h2({ children }) {
                        return <h2 className="text-base font-semibold text-text-primary mt-4 mb-2">{children}</h2>
                    },
                    h3({ children }) {
                        return <h3 className="text-sm font-semibold text-text-primary mt-3 mb-1.5">{children}</h3>
                    },

                    // 列表
                    ul({ children }) {
                        return <ul className="list-disc pl-5 space-y-1 mb-3 text-text-primary">{children}</ul>
                    },
                    ol({ children }) {
                        return <ol className="list-decimal pl-5 space-y-1 mb-3 text-text-primary">{children}</ol>
                    },
                    li({ children }) {
                        return <li className="leading-relaxed">{children}</li>
                    },

                    // 引用块
                    blockquote({ children }) {
                        return (
                            <blockquote className="border-l-2 border-accent/50 pl-4 my-3 text-text-secondary italic bg-accent-dim rounded-r-lg py-2 pr-3">
                                {children}
                            </blockquote>
                        )
                    },

                    // 表格
                    table({ children }) {
                        return (
                            <div className="overflow-x-auto my-3 rounded-xl border border-bg-border">
                                <table className="w-full text-xs border-collapse">{children}</table>
                            </div>
                        )
                    },
                    thead({ children }) {
                        return <thead className="bg-bg-base">{children}</thead>
                    },
                    th({ children }) {
                        return <th className="px-4 py-2.5 text-left text-text-secondary font-medium border-b border-bg-border">{children}</th>
                    },
                    td({ children }) {
                        return <td className="px-4 py-2.5 text-text-primary border-b border-bg-border last:border-b-0">{children}</td>
                    },
                    tr({ children }) {
                        return <tr className="hover:bg-bg-base/40 transition-colors">{children}</tr>
                    },

                    // 分割线
                    hr() {
                        return <hr className="border-bg-border my-4" />
                    },

                    // 加粗 / 斜体 / 链接
                    strong({ children }) {
                        return <strong className="font-semibold text-text-primary">{children}</strong>
                    },
                    em({ children }) {
                        return <em className="italic text-text-secondary">{children}</em>
                    },
                    a({ href, children }) {
                        return (
                            <a href={href} target="_blank" rel="noopener noreferrer"
                               className="text-accent hover:text-accent-hover underline underline-offset-2 transition-colors">
                                {children}
                            </a>
                        )
                    },
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    )
}
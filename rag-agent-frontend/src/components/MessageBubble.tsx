// src/components/MessageBubble.tsx
import { useState } from 'react'
import { Copy, Quote, Check } from 'lucide-react'
import clsx from 'clsx'
import type { Message } from '../api/chat'
import MessageContent from './MessageContent'

interface Props {
    message: Message
    onQuote?: (content: string) => void
}

export default function MessageBubble({ message, onQuote }: Props) {
    const isUser = message.role === 'user'
    const [copied, setCopied] = useState(false)

    const handleCopy = async () => {
        await navigator.clipboard.writeText(message.content)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className={clsx('group flex gap-3 animate-slide-up', isUser && 'flex-row-reverse')}>
            {/* 头像 */}
            <div className={clsx(
                'w-8 h-8 rounded-lg flex items-center justify-center text-xs font-mono flex-shrink-0 mt-1',
                isUser
                    ? 'bg-accent text-bg-base font-semibold'
                    : 'bg-bg-elevated border border-bg-border text-accent'
            )}>
                {isUser ? 'U' : 'AI'}
            </div>

            <div className={clsx('flex flex-col gap-1', isUser ? 'items-end max-w-[75%]' : 'flex-1 min-w-0')}>
                {/* 消息气泡 */}
                <div className={clsx(
                    'rounded-2xl px-4 py-3 leading-relaxed',
                    isUser
                        ? 'bg-accent text-bg-base rounded-tr-sm text-sm'
                        : 'bg-bg-elevated border border-bg-border text-text-primary rounded-tl-sm w-full'
                )}>
                    {/* ✅ 使用 MessageContent 渲染 */}
                    <MessageContent content={message.content} isUser={isUser} />
                </div>

                {/* 操作按钮 */}
                <div className={clsx(
                    'flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150',
                    isUser && 'flex-row-reverse'
                )}>
                    <button
                        onClick={handleCopy}
                        className={clsx(
                            'flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-all duration-150',
                            copied
                                ? 'text-success bg-success/10 border border-success/20'
                                : 'text-text-muted hover:text-text-primary hover:bg-bg-elevated border border-transparent hover:border-bg-border'
                        )}
                    >
                        {copied ? <Check size={11} /> : <Copy size={11} />}
                        {copied ? '已复制' : '复制'}
                    </button>

                    {!isUser && onQuote && (
                        <button
                            onClick={() => onQuote(message.content)}
                            className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs text-text-muted
                         hover:text-accent hover:bg-accent-dim border border-transparent
                         hover:border-accent/20 transition-all duration-150"
                        >
                            <Quote size={11} />
                            引用
                        </button>
                    )}
                </div>
            </div>
        </div>
    )
}
// src/components/StreamingBubble.tsx
import MessageContent from './MessageContent'

interface Props {
    content: string
}

export default function StreamingBubble({ content }: Props) {
    return (
        <div className="flex gap-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-mono bg-bg-elevated border border-bg-border text-accent flex-shrink-0 mt-1">
                AI
            </div>
            <div className="flex-1 min-w-0 rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed bg-bg-elevated border border-bg-border text-text-primary">
                {content ? (
                    <>
                        <MessageContent content={content} isUser={false} />
                        <span className="inline-block w-0.5 h-4 bg-accent ml-0.5 animate-pulse align-middle" />
                    </>
                ) : (
                    <div className="flex items-center gap-1.5 h-5">
                        {[0, 1, 2].map((i) => (
                            <span
                                key={i}
                                className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse-dot"
                                style={{ animationDelay: `${i * 0.2}s` }}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
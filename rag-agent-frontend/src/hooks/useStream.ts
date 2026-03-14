// src/hooks/useStream.ts
import { useCallback } from 'react'
import { chatStream } from '../api/chat'
import { useChatStore } from '../store/chatStore'

export function useStream() {
  const { addMessage, setStreaming, appendStreamChunk, commitStreamMessage, resetStream } = useChatStore()

  const send = useCallback(async (message: string, threadId: string, quote: string = "") => {
    addMessage({ role: 'user', content: message })
    setStreaming(true)

    await chatStream(
        message,
        threadId,
        (chunk) => appendStreamChunk(chunk),
        () => commitStreamMessage(),
        (err) => {
          resetStream()
          addMessage({ role: 'assistant', content: `错误：${err}` })
        },
        quote   // ✅ 透传
    )
  }, [addMessage, setStreaming, appendStreamChunk, commitStreamMessage, resetStream])

  return { send }
}
import { useEffect, useRef } from 'react'
import { io, Socket } from 'socket.io-client'

// WebSocket Hook - 用于实时进度更新
export function useWebSocket(url: string) {
  const socketRef = useRef<Socket | null>(null)
  
  useEffect(() => {
    // 连接 WebSocket
    socketRef.current = io(url)
    
    socketRef.current.on('connect', () => {
      console.log('WebSocket connected')
    })
    
    socketRef.current.on('disconnect', () => {
      console.log('WebSocket disconnected')
    })
    
    // 清理
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect()
      }
    }
  }, [url])
  
  return socketRef.current
}

// 订阅合同进度更新
export function useContractProgress(
  executionId: string | undefined,
  onProgress: (data: any) => void,
  onComplete: (data: any) => void
) {
  const socket = useWebSocket('http://localhost:8000')
  
  useEffect(() => {
    if (!socket || !executionId) return
    
    // 订阅进度更新
    socket.emit('subscribe', { execution_id: executionId })
    
    // 监听进度事件
    socket.on('progress', onProgress)
    socket.on('completed', onComplete)
    
    // 清理 - 取消订阅并移除监听器 (Bug 3 fix)
    return () => {
      socket.emit('unsubscribe', { execution_id: executionId })
      socket.off('progress', onProgress)
      socket.off('completed', onComplete)
    }
  }, [socket, executionId, onProgress, onComplete])
}


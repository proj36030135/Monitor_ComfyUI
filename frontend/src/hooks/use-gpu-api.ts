"use client"

import { useState, useEffect, useCallback, useRef } from 'react'
import axios from 'axios'

export interface GPUData {
  id: number
  timestamp: string
  device_index: number
  util_percent: number
  mem_used_mb: number
  mem_total_mb: number
  temp_celsius: number
  power_watts: number
}

export interface GPUStats {
  device_index: number
  sample_count: number
  utilization: { avg: number; min: number; max: number }
  memory_used_mb: { avg: number; min: number; max: number }
  temperature_celsius: { avg: number; min: number; max: number }
  power_watts: { avg: number; min: number; max: number }
}

export interface SessionData {
  id: number
  name: string
  description: string
  start_time?: string
  end_time?: string
  is_active: boolean
  created_at: string
  measurement_count: number
  first_measurement?: string
  last_measurement?: string
}

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

interface UseGPUAPIReturn {
  // Connection status
  connectionStatus: ConnectionStatus
  isConnected: boolean
  error: string | null
  
  // Data
  currentData: GPUData[]
  gpuStats: GPUStats[]
  sessions: SessionData[]
  
  // Actions
  connect: (backendUrl?: string) => void
  disconnect: () => void
  refreshData: () => Promise<void>
  
  // Sessions
  createSession: (name: string, description: string) => Promise<SessionData | null>
  startSession: (sessionId: number) => Promise<boolean>
  stopSession: () => Promise<boolean>
  refreshSessions: () => Promise<void>
  
  // Backend URL
  backendUrl: string
  setBackendUrl: (url: string) => void
}

export function useGPUAPI(): UseGPUAPIReturn {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected')
  const [error, setError] = useState<string | null>(null)
  const [currentData, setCurrentData] = useState<GPUData[]>([])
  const [gpuStats, setGpuStats] = useState<GPUStats[]>([])
  const [sessions, setSessions] = useState<SessionData[]>([])
  const [backendUrl, setBackendUrl] = useState('http://localhost:8000')
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const isConnected = connectionStatus === 'connected'

  // Função para fazer requisições HTTP
  const apiRequest = useCallback(async (endpoint: string, options?: any) => {
    try {
      const response = await axios({
        url: `${backendUrl}${endpoint}`,
        timeout: 5000,
        ...options
      })
      return response.data
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error)
      throw error
    }
  }, [backendUrl])

  // Health check do backend
  const checkBackendHealth = useCallback(async (): Promise<boolean> => {
    try {
      await apiRequest('/api/health')
      return true
    } catch (error) {
      return false
    }
  }, [apiRequest])

  // Conectar WebSocket
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return // Já conectado
    }

    const wsUrl = backendUrl.replace(/^http/, 'ws') + '/ws'
    
    try {
      setConnectionStatus('connecting')
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected')
        setConnectionStatus('connected')
        setError(null)
        reconnectAttempts.current = 0
        
        // Enviar ping para manter conexão viva
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }))
          } else {
            clearInterval(pingInterval)
          }
        }, 30000)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'gpu_data' || data.type === 'initial_data') {
            setCurrentData(data.data || [])
          } else if (data.type === 'pong') {
            // Resposta ao ping - conexão está viva
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        setConnectionStatus('disconnected')
        
        // Tentar reconectar se não foi fechado intencionalmente
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000)
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++
            console.log(`Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts})`)
            connectWebSocket()
          }, delay)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionStatus('error')
        setError('Erro de conexão WebSocket')
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setConnectionStatus('error')
      setError('Falha ao criar conexão WebSocket')
    }
  }, [backendUrl])

  // Desconectar
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }
    
    setConnectionStatus('disconnected')
    setCurrentData([])
    setError(null)
  }, [])

  // Conectar
  const connect = useCallback(async (newBackendUrl?: string) => {
    if (newBackendUrl) {
      setBackendUrl(newBackendUrl)
    }
    
    const urlToTest = newBackendUrl || backendUrl
    
    try {
      setConnectionStatus('connecting')
      setError(null)
      
      // Verificar se o backend está funcionando
      const isHealthy = await checkBackendHealth()
      if (!isHealthy) {
        throw new Error('Backend não está respondendo')
      }
      
      // Conectar WebSocket
      connectWebSocket()
      
      // Carregar dados iniciais
      await refreshData()
      await refreshSessions()
      
    } catch (error) {
      setConnectionStatus('error')
      setError(error instanceof Error ? error.message : 'Erro de conexão')
    }
  }, [backendUrl, checkBackendHealth, connectWebSocket])

  // Atualizar dados
  const refreshData = useCallback(async () => {
    try {
      const [currentResponse, statsResponse] = await Promise.all([
        apiRequest('/api/gpu/current'),
        apiRequest('/api/gpu/stats')
      ])
      
      if (currentResponse?.data) {
        setCurrentData(currentResponse.data)
      }
      
      if (statsResponse?.devices) {
        setGpuStats(statsResponse.devices)
      }
    } catch (error) {
      console.error('Failed to refresh data:', error)
    }
  }, [apiRequest])

  // Atualizar sessões
  const refreshSessions = useCallback(async () => {
    try {
      const response = await apiRequest('/api/sessions')
      if (response?.sessions) {
        setSessions(response.sessions)
      }
    } catch (error) {
      console.error('Failed to refresh sessions:', error)
    }
  }, [apiRequest])

  // Criar sessão
  const createSession = useCallback(async (name: string, description: string): Promise<SessionData | null> => {
    try {
      const response = await apiRequest('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        data: { name, description }
      })
      
      await refreshSessions()
      return response
    } catch (error) {
      console.error('Failed to create session:', error)
      return null
    }
  }, [apiRequest, refreshSessions])

  // Iniciar sessão
  const startSession = useCallback(async (sessionId: number): Promise<boolean> => {
    try {
      await apiRequest(`/api/sessions/${sessionId}/start`, { method: 'POST' })
      await refreshSessions()
      return true
    } catch (error) {
      console.error('Failed to start session:', error)
      return false
    }
  }, [apiRequest, refreshSessions])

  // Parar sessão
  const stopSession = useCallback(async (): Promise<boolean> => {
    try {
      await apiRequest('/api/sessions/stop', { method: 'POST' })
      await refreshSessions()
      return true
    } catch (error) {
      console.error('Failed to stop session:', error)
      return false
    }
  }, [apiRequest, refreshSessions])

  // Cleanup ao desmontar
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    connectionStatus,
    isConnected,
    error,
    currentData,
    gpuStats,
    sessions,
    connect,
    disconnect,
    refreshData,
    createSession,
    startSession,
    stopSession,
    refreshSessions,
    backendUrl,
    setBackendUrl
  }
}

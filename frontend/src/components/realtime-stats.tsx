"use client"

import { useState, useEffect } from "react"
import { Activity, TrendingUp } from "lucide-react"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface GPUStats {
  device_index: number
  sample_count: number
  utilization: { avg: number; min: number; max: number }
  memory_used_mb: { avg: number; min: number; max: number }
  temperature_celsius: { avg: number; min: number; max: number }
  power_watts: { avg: number; min: number; max: number }
}

interface RealtimeStatsProps {
  gpuStats: GPUStats[]
}

export function RealtimeStats({ gpuStats }: RealtimeStatsProps) {
  const [currentStats, setCurrentStats] = useState<Record<number, {
    utilization: number
    temperature: number
    memoryUsed: number
    memoryTotal: number
    power: number
  }>>({})

  useEffect(() => {
    // Simula dados em tempo real
    const interval = setInterval(() => {
      const newStats: typeof currentStats = {}
      
      gpuStats.forEach(gpu => {
        newStats[gpu.device_index] = {
          utilization: Math.floor(Math.random() * 40) + 60, // 60-100%
          temperature: Math.floor(Math.random() * 25) + 50, // 50-75°C
          memoryUsed: Math.floor(Math.random() * 3000) + 4000, // 4000-7000 MB
          memoryTotal: 8192, // 8GB
          power: Math.floor(Math.random() * 100) + 150, // 150-250W
        }
      })
      
      setCurrentStats(newStats)
    }, 2000)
    
    return () => clearInterval(interval)
  }, [gpuStats])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Status em Tempo Real
        </CardTitle>
        <CardDescription>
          Últimas métricas de cada GPU
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {gpuStats.map((gpu) => {
          const current = currentStats[gpu.device_index]
          if (!current) return null

          const memoryPercent = Math.round((current.memoryUsed / current.memoryTotal) * 100)
          const tempStatus = current.temperature > 75 ? 'danger' : current.temperature > 65 ? 'warning' : 'normal'
          
          return (
            <div key={gpu.device_index} className="space-y-3 border-b pb-4 last:border-b-0">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-sm">GPU {gpu.device_index}</h4>
                <Badge 
                  variant={current.utilization > 85 ? 'destructive' : current.utilization > 50 ? 'default' : 'secondary'}
                >
                  {current.utilization > 85 ? 'Alta' : current.utilization > 50 ? 'Média' : 'Baixa'} Utilização
                </Badge>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-muted-foreground">Utilização:</span>
                  <div className="font-medium">{current.utilization}%</div>
                  <div className="w-full bg-secondary rounded-full h-1.5">
                    <div 
                      className="bg-blue-600 h-1.5 rounded-full transition-all"
                      style={{ width: `${current.utilization}%` }}
                    />
                  </div>
                </div>
                
                <div>
                  <span className="text-muted-foreground">Temperatura:</span>
                  <div className={`font-medium ${
                    tempStatus === 'danger' ? 'text-red-600' : 
                    tempStatus === 'warning' ? 'text-yellow-600' : 
                    'text-green-600'
                  }`}>
                    {current.temperature}°C
                  </div>
                </div>
                
                <div>
                  <span className="text-muted-foreground">Memória:</span>
                  <div className="font-medium">
                    {Math.round(current.memoryUsed / 1024 * 100) / 100}GB / {Math.round(current.memoryTotal / 1024 * 100) / 100}GB
                  </div>
                  <div className="w-full bg-secondary rounded-full h-1.5">
                    <div 
                      className="bg-green-600 h-1.5 rounded-full transition-all"
                      style={{ width: `${memoryPercent}%` }}
                    />
                  </div>
                </div>
                
                <div>
                  <span className="text-muted-foreground">Potência:</span>
                  <div className="font-medium">{current.power}W</div>
                </div>
              </div>
              
              <div className="flex items-center text-xs text-muted-foreground">
                <TrendingUp className="h-3 w-3 mr-1" />
                Atualizado há poucos segundos
              </div>
            </div>
          )
        })}
        
        {gpuStats.length === 0 && (
          <div className="text-center text-muted-foreground py-8">
            <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>Aguardando conexão com GPUs...</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

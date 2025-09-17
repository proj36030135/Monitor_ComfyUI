"use client"

import { useState, useEffect } from "react"
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

// Mock data para demonstração
const generateMockData = () => {
  const data = []
  const now = new Date()
  
  for (let i = 29; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 2 * 60 * 1000) // Dados a cada 2 minutos
    data.push({
      time: time.toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }),
      gpu0_util: Math.floor(Math.random() * 40) + 60, // 60-100%
      gpu0_temp: Math.floor(Math.random() * 25) + 50, // 50-75°C
      gpu1_util: Math.floor(Math.random() * 50) + 30, // 30-80%
      gpu1_temp: Math.floor(Math.random() * 20) + 45, // 45-65°C
      gpu0_power: Math.floor(Math.random() * 100) + 150, // 150-250W
      gpu1_power: Math.floor(Math.random() * 80) + 100, // 100-180W
    })
  }
  
  return data
}

export function GPUChart() {
  const [data, setData] = useState(generateMockData())
  const [metric, setMetric] = useState<'util' | 'temp' | 'power'>('util')
  
  useEffect(() => {
    // Simula atualização de dados a cada 2 segundos
    const interval = setInterval(() => {
      setData(prevData => {
        const newData = [...prevData.slice(1)]
        const lastTime = new Date()
        
        newData.push({
          time: lastTime.toLocaleTimeString('pt-BR', { 
            hour: '2-digit', 
            minute: '2-digit' 
          }),
          gpu0_util: Math.floor(Math.random() * 40) + 60,
          gpu0_temp: Math.floor(Math.random() * 25) + 50,
          gpu1_util: Math.floor(Math.random() * 50) + 30,
          gpu1_temp: Math.floor(Math.random() * 20) + 45,
          gpu0_power: Math.floor(Math.random() * 100) + 150,
          gpu1_power: Math.floor(Math.random() * 80) + 100,
        })
        
        return newData
      })
    }, 2000)
    
    return () => clearInterval(interval)
  }, [])

  const getMetricConfig = () => {
    switch (metric) {
      case 'util':
        return {
          title: 'Utilização da GPU',
          yAxisDomain: [0, 100],
          unit: '%',
          lines: [
            { key: 'gpu0_util', name: 'GPU 0', color: '#2563eb' },
            { key: 'gpu1_util', name: 'GPU 1', color: '#dc2626' }
          ]
        }
      case 'temp':
        return {
          title: 'Temperatura',
          yAxisDomain: [30, 90],
          unit: '°C',
          lines: [
            { key: 'gpu0_temp', name: 'GPU 0', color: '#ea580c' },
            { key: 'gpu1_temp', name: 'GPU 1', color: '#dc2626' }
          ]
        }
      case 'power':
        return {
          title: 'Consumo de Energia',
          yAxisDomain: [50, 300],
          unit: 'W',
          lines: [
            { key: 'gpu0_power', name: 'GPU 0', color: '#16a34a' },
            { key: 'gpu1_power', name: 'GPU 1', color: '#ca8a04' }
          ]
        }
      default:
        return {
          title: 'Utilização da GPU',
          yAxisDomain: [0, 100],
          unit: '%',
          lines: [
            { key: 'gpu0_util', name: 'GPU 0', color: '#2563eb' },
            { key: 'gpu1_util', name: 'GPU 1', color: '#dc2626' }
          ]
        }
    }
  }

  const config = getMetricConfig()

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>{config.title}</CardTitle>
          <CardDescription>
            Monitoramento em tempo real - últimos 60 minutos
          </CardDescription>
        </div>
        <Select value={metric} onValueChange={(value: 'util' | 'temp' | 'power') => setMetric(value)}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="util">Utilização</SelectItem>
            <SelectItem value="temp">Temperatura</SelectItem>
            <SelectItem value="power">Potência</SelectItem>
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="time" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              domain={config.yAxisDomain}
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}${config.unit}`}
            />
            <Tooltip 
              labelFormatter={(label) => `Horário: ${label}`}
              formatter={(value, name) => [`${value}${config.unit}`, name]}
            />
            <Legend />
            {config.lines.map((line) => (
              <Line
                key={line.key}
                type="monotone"
                dataKey={line.key}
                stroke={line.color}
                strokeWidth={2}
                name={line.name}
                dot={false}
                activeDot={{ r: 4 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

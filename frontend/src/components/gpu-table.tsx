"use client"

import { useState } from "react"
import { MoreHorizontal, ArrowUpDown } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

interface GPUStats {
  device_index: number
  sample_count: number
  utilization: { avg: number; min: number; max: number }
  memory_used_mb: { avg: number; min: number; max: number }
  temperature_celsius: { avg: number; min: number; max: number }
  power_watts: { avg: number; min: number; max: number }
}

interface GPUTableProps {
  gpuStats: GPUStats[]
}

type SortField = 'device_index' | 'utilization' | 'temperature' | 'memory' | 'power'
type SortDirection = 'asc' | 'desc'

export function GPUTable({ gpuStats }: GPUTableProps) {
  const [sortField, setSortField] = useState<SortField>('device_index')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const sortedGPUs = [...gpuStats].sort((a, b) => {
    let aVal: number, bVal: number

    switch (sortField) {
      case 'device_index':
        aVal = a.device_index
        bVal = b.device_index
        break
      case 'utilization':
        aVal = a.utilization.avg
        bVal = b.utilization.avg
        break
      case 'temperature':
        aVal = a.temperature_celsius.avg
        bVal = b.temperature_celsius.avg
        break
      case 'memory':
        aVal = a.memory_used_mb.avg
        bVal = b.memory_used_mb.avg
        break
      case 'power':
        aVal = a.power_watts.avg
        bVal = b.power_watts.avg
        break
      default:
        return 0
    }

    if (sortDirection === 'asc') {
      return aVal - bVal
    } else {
      return bVal - aVal
    }
  })

  const getUtilizationStatus = (utilization: number) => {
    if (utilization >= 80) return { text: 'Alta', variant: 'destructive' as const }
    if (utilization >= 50) return { text: 'Média', variant: 'default' as const }
    if (utilization >= 20) return { text: 'Baixa', variant: 'secondary' as const }
    return { text: 'Inativa', variant: 'outline' as const }
  }

  const getTemperatureStatus = (temperature: number) => {
    if (temperature >= 80) return { text: 'Crítica', variant: 'destructive' as const }
    if (temperature >= 70) return { text: 'Alta', variant: 'default' as const }
    if (temperature >= 60) return { text: 'Normal', variant: 'secondary' as const }
    return { text: 'Fria', variant: 'outline' as const }
  }

  const SortButton = ({ field, children }: { field: SortField; children: React.ReactNode }) => (
    <Button
      variant="ghost"
      onClick={() => handleSort(field)}
      className="h-8 px-2 lg:px-3"
    >
      {children}
      <ArrowUpDown className="ml-2 h-4 w-4" />
    </Button>
  )

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              <SortButton field="device_index">GPU</SortButton>
            </TableHead>
            <TableHead>
              <SortButton field="utilization">Utilização</SortButton>
            </TableHead>
            <TableHead>
              <SortButton field="memory">Memória</SortButton>
            </TableHead>
            <TableHead>
              <SortButton field="temperature">Temperatura</SortButton>
            </TableHead>
            <TableHead>
              <SortButton field="power">Potência</SortButton>
            </TableHead>
            <TableHead>Status</TableHead>
            <TableHead>
              <span className="sr-only">Ações</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedGPUs.map((gpu) => {
            const utilizationStatus = getUtilizationStatus(gpu.utilization.avg)
            const temperatureStatus = getTemperatureStatus(gpu.temperature_celsius.avg)
            const memoryPercent = Math.round((gpu.memory_used_mb.avg / 8192) * 100) // Assumindo 8GB

            return (
              <TableRow key={gpu.device_index}>
                <TableCell className="font-medium">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-sm font-semibold">
                      {gpu.device_index}
                    </div>
                    <span>GPU {gpu.device_index}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex flex-col space-y-1">
                    <span className="font-medium">{Math.round(gpu.utilization.avg)}%</span>
                    <div className="flex space-x-1 text-xs text-muted-foreground">
                      <span>Min: {Math.round(gpu.utilization.min)}%</span>
                      <span>Max: {Math.round(gpu.utilization.max)}%</span>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex flex-col space-y-1">
                    <span className="font-medium">
                      {Math.round(gpu.memory_used_mb.avg / 1024 * 100) / 100}GB
                    </span>
                    <div className="w-full bg-secondary rounded-full h-1.5">
                      <div 
                        className="bg-green-600 h-1.5 rounded-full"
                        style={{ width: `${memoryPercent}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">{memoryPercent}% usado</span>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex flex-col space-y-1">
                    <span className="font-medium">{Math.round(gpu.temperature_celsius.avg)}°C</span>
                    <Badge variant={temperatureStatus.variant} className="w-fit text-xs">
                      {temperatureStatus.text}
                    </Badge>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex flex-col space-y-1">
                    <span className="font-medium">{Math.round(gpu.power_watts.avg)}W</span>
                    <div className="flex space-x-1 text-xs text-muted-foreground">
                      <span>Min: {Math.round(gpu.power_watts.min)}W</span>
                      <span>Max: {Math.round(gpu.power_watts.max)}W</span>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant={utilizationStatus.variant}>
                    {utilizationStatus.text}
                  </Badge>
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <span className="sr-only">Abrir menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Ações</DropdownMenuLabel>
                      <DropdownMenuItem>
                        Ver detalhes
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        Histórico completo
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem>
                        Exportar dados
                      </DropdownMenuItem>
                      <DropdownMenuItem className="text-red-600">
                        Reset estatísticas
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
      
      {sortedGPUs.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="text-muted-foreground text-center">
            <p className="text-lg font-medium mb-2">Nenhuma GPU detectada</p>
            <p className="text-sm">
              Verifique se o backend está conectado e se há GPUs disponíveis no sistema.
            </p>
          </div>
        </div>
      )}
      
      {sortedGPUs.length > 0 && (
        <div className="flex items-center justify-end space-x-2 py-4 px-4 border-t">
          <div className="text-sm text-muted-foreground">
            {sortedGPUs.length} GPU{sortedGPUs.length !== 1 ? 's' : ''} encontrada{sortedGPUs.length !== 1 ? 's' : ''}
          </div>
        </div>
      )}
    </div>
  )
}

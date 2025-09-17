"use client"

import { useState, useEffect } from "react"
import {
  Activity,
  Cpu,
  HardDrive,
  Server,
  Thermometer,
  Zap,
  Settings,
  HelpCircle,
  Search,
  AlertCircle
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

import { Sidebar } from "@/components/sidebar"
import { MetricCard } from "@/components/metric-card"
import { GPUChart } from "@/components/gpu-chart"
import { RealtimeStats } from "@/components/realtime-stats"
import { GPUTable } from "@/components/gpu-table"
import { useGPUAPI } from "@/hooks/use-gpu-api"

export function Dashboard() {
  const {
    connectionStatus,
    isConnected,
    error,
    currentData,
    gpuStats,
    sessions,
    connect,
    disconnect,
    backendUrl,
    setBackendUrl,
    createSession,
    startSession,
    stopSession
  } = useGPUAPI()

  const [showConnectionSettings, setShowConnectionSettings] = useState(false)
  const [tempBackendUrl, setTempBackendUrl] = useState(backendUrl)
  
  const gpuCount = gpuStats.length

  // Auto-conectar na inicialização
  useEffect(() => {
    if (connectionStatus === 'disconnected') {
      connect()
    }
  }, [])

  return (
    <div className="flex min-h-screen w-full bg-muted/40">
      <Sidebar />
      
      <div className="flex flex-col flex-1 sm:gap-4 sm:py-4 sm:pl-14">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background px-4 sm:static sm:h-auto sm:border-0 sm:bg-transparent sm:px-6">
          <div className="relative ml-auto flex-1 md:grow-0">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Buscar GPUs, sessões..."
              className="w-full rounded-lg bg-background pl-8 md:w-[200px] lg:w-[320px]"
            />
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon" className="overflow-hidden rounded-full">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>GM</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>GPU Monitor</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <Settings className="mr-2 h-4 w-4" />
                Configurações
              </DropdownMenuItem>
              <DropdownMenuItem>
                <HelpCircle className="mr-2 h-4 w-4" />
                Ajuda
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

        <main className="flex-1 space-y-4 p-4 pt-6">
          <div className="flex items-center justify-between space-y-2">
            <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
            <div className="flex items-center space-x-2">
              {error && (
                <div className="flex items-center space-x-1 text-red-600 text-sm">
                  <AlertCircle className="h-4 w-4" />
                  <span>{error}</span>
                </div>
              )}
              <Button 
                onClick={isConnected ? disconnect : () => connect()} 
                variant={isConnected ? "destructive" : "default"}
                disabled={connectionStatus === 'connecting'}
              >
                <Activity className={`mr-2 h-4 w-4 ${connectionStatus === 'connecting' ? 'animate-spin' : ''}`} />
                {connectionStatus === 'connecting' && 'Conectando...'}
                {connectionStatus === 'connected' && 'Desconectar'}
                {connectionStatus === 'disconnected' && 'Conectar'}
                {connectionStatus === 'error' && 'Tentar Novamente'}
              </Button>
            </div>
          </div>

          <Tabs defaultValue="overview" className="space-y-4">
            <TabsList>
              <TabsTrigger value="overview">Visão Geral</TabsTrigger>
              <TabsTrigger value="analytics">Análises</TabsTrigger>
              <TabsTrigger value="sessions">Sessões</TabsTrigger>
              <TabsTrigger value="settings">Configurações</TabsTrigger>
            </TabsList>
            
            <TabsContent value="overview" className="space-y-4">
              {/* Metric Cards - Similar ao exemplo ShadCN */}
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <MetricCard
                  title="Utilização Média"
                  value={gpuStats.length > 0 ? `${Math.round(gpuStats.reduce((acc, gpu) => acc + gpu.utilization.avg, 0) / gpuStats.length)}%` : "0%"}
                  description="+12.5%"
                  descriptionLabel="em relação ao mês anterior"
                  icon={<Cpu className="h-4 w-4 text-muted-foreground" />}
                  trend="up"
                />
                <MetricCard
                  title="Temperatura Máxima"
                  value={gpuStats.length > 0 ? `${Math.round(Math.max(...gpuStats.map(gpu => gpu.temperature_celsius.max)))}°C` : "0°C"}
                  description="+2°C"
                  descriptionLabel="desde a última hora"
                  icon={<Thermometer className="h-4 w-4 text-muted-foreground" />}
                  trend="up"
                />
                <MetricCard
                  title="GPUs Ativas"
                  value={gpuCount.toString()}
                  description="100%"
                  descriptionLabel="operacionais"
                  icon={<Server className="h-4 w-4 text-muted-foreground" />}
                  trend="neutral"
                />
                <MetricCard
                  title="Potência Total"
                  value={gpuStats.length > 0 ? `${Math.round(gpuStats.reduce((acc, gpu) => acc + gpu.power_watts.avg, 0))}W` : "0W"}
                  description="+8.2%"
                  descriptionLabel="eficiência melhorada"
                  icon={<Zap className="h-4 w-4 text-muted-foreground" />}
                  trend="up"
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                {/* GPU Chart */}
                <div className="col-span-4">
                  <GPUChart />
                </div>
                
                {/* Real-time Stats */}
                <div className="col-span-3">
                  <RealtimeStats gpuStats={gpuStats} />
                </div>
              </div>

              {/* GPU Table - Similar à tabela do exemplo ShadCN */}
              <Card>
                <CardHeader>
                  <CardTitle>Status das GPUs</CardTitle>
                  <CardDescription>
                    Monitoramento em tempo real de todas as GPUs do sistema
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <GPUTable gpuStats={gpuStats} />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="analytics" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Análise Detalhada</CardTitle>
                  <CardDescription>
                    Estatísticas avançadas e tendências de uso
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-sm text-muted-foreground">
                    Funcionalidades avançadas de análise em desenvolvimento...
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="sessions" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Sessões de Gravação</CardTitle>
                  <CardDescription>
                    Gerencie e visualize sessões de monitoramento gravadas
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-sm text-muted-foreground">
                    Interface de sessões em desenvolvimento...
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="settings" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Configurações</CardTitle>
                  <CardDescription>
                    Configure parâmetros do sistema e preferências
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-sm text-muted-foreground">
                    Painel de configurações em desenvolvimento...
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </div>
  )
}

"use client"

import Link from "next/link"
import {
  Activity,
  BarChart3,
  Home,
  Settings,
  Video,
  Cpu,
  PanelLeft,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

export function Sidebar() {
  return (
    <TooltipProvider>
      <aside className="fixed inset-y-0 left-0 z-20 flex h-full flex-col border-r">
        <div className="border-b p-2">
          <Button variant="outline" size="icon" aria-label="Home">
            <Cpu className="size-5 fill-foreground" />
          </Button>
        </div>
        
        <nav className="grid gap-1 p-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="rounded-lg bg-muted"
                aria-label="Dashboard"
                asChild
              >
                <Link href="#">
                  <Home className="size-5" />
                </Link>
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right" sideOffset={5}>
              Dashboard
            </TooltipContent>
          </Tooltip>
          
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="rounded-lg"
                aria-label="Monitoramento"
                asChild
              >
                <Link href="#">
                  <Activity className="size-5" />
                </Link>
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right" sideOffset={5}>
              Monitoramento
            </TooltipContent>
          </Tooltip>
          
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="rounded-lg"
                aria-label="Análises"
                asChild
              >
                <Link href="#">
                  <BarChart3 className="size-5" />
                </Link>
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right" sideOffset={5}>
              Análises
            </TooltipContent>
          </Tooltip>
          
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="rounded-lg"
                aria-label="Sessões"
                asChild
              >
                <Link href="#">
                  <Video className="size-5" />
                </Link>
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right" sideOffset={5}>
              Sessões
            </TooltipContent>
          </Tooltip>
        </nav>
        
        <nav className="mt-auto grid gap-1 p-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="mt-auto rounded-lg"
                aria-label="Configurações"
                asChild
              >
                <Link href="#">
                  <Settings className="size-5" />
                </Link>
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right" sideOffset={5}>
              Configurações
            </TooltipContent>
          </Tooltip>
        </nav>
      </aside>

      {/* Mobile Sidebar */}
      <div className="flex flex-col sm:gap-4 sm:py-4 sm:pl-14">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background px-4 sm:static sm:h-auto sm:border-0 sm:bg-transparent sm:px-6">
          <Sheet>
            <SheetTrigger asChild>
              <Button size="icon" variant="outline" className="sm:hidden">
                <PanelLeft className="h-5 w-5" />
                <span className="sr-only">Alternar Menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="sm:max-w-xs">
              <nav className="grid gap-6 text-lg font-medium">
                <Link
                  href="#"
                  className="group flex h-10 w-10 shrink-0 items-center justify-center gap-2 rounded-full bg-primary text-lg font-semibold text-primary-foreground md:text-base"
                >
                  <Cpu className="h-5 w-5 transition-all group-hover:scale-110" />
                  <span className="sr-only">GPU Monitor</span>
                </Link>
                <Link
                  href="#"
                  className="flex items-center gap-4 px-2.5 text-muted-foreground hover:text-foreground"
                >
                  <Home className="h-5 w-5" />
                  Dashboard
                </Link>
                <Link
                  href="#"
                  className="flex items-center gap-4 px-2.5 text-muted-foreground hover:text-foreground"
                >
                  <Activity className="h-5 w-5" />
                  Monitoramento
                </Link>
                <Link
                  href="#"
                  className="flex items-center gap-4 px-2.5 text-foreground"
                >
                  <BarChart3 className="h-5 w-5" />
                  Análises
                </Link>
                <Link
                  href="#"
                  className="flex items-center gap-4 px-2.5 text-muted-foreground hover:text-foreground"
                >
                  <Video className="h-5 w-5" />
                  Sessões
                </Link>
                <Link
                  href="#"
                  className="flex items-center gap-4 px-2.5 text-muted-foreground hover:text-foreground"
                >
                  <Settings className="h-5 w-5" />
                  Configurações
                </Link>
              </nav>
            </SheetContent>
          </Sheet>
        </header>
      </div>
    </TooltipProvider>
  )
}

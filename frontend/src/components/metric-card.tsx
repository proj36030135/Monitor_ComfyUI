"use client"

import { ReactNode } from "react"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

interface MetricCardProps {
  title: string
  value: string
  description: string
  descriptionLabel: string
  icon: ReactNode
  trend: "up" | "down" | "neutral"
}

export function MetricCard({
  title,
  value,
  description,
  descriptionLabel,
  icon,
  trend,
}: MetricCardProps) {
  const getTrendIcon = () => {
    switch (trend) {
      case "up":
        return <TrendingUp className="h-4 w-4 text-green-500" />
      case "down":
        return <TrendingDown className="h-4 w-4 text-red-500" />
      case "neutral":
        return <Minus className="h-4 w-4 text-gray-500" />
      default:
        return null
    }
  }

  const getTrendColor = () => {
    switch (trend) {
      case "up":
        return "text-green-600"
      case "down":
        return "text-red-600"
      case "neutral":
        return "text-gray-600"
      default:
        return "text-gray-600"
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          {title}
        </CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <div className="flex items-center space-x-1 text-xs text-muted-foreground">
          {getTrendIcon()}
          <span className={getTrendColor()}>{description}</span>
          <span>{descriptionLabel}</span>
        </div>
      </CardContent>
    </Card>
  )
}

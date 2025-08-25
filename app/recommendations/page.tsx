"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  ArrowLeft,
  Zap,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  TrendingUp,
  Shield,
  Ship,
  Navigation,
  Calendar,
  DollarSign,
  Settings,
} from "lucide-react"
import Link from "next/link"

interface Recommendation {
  id: string
  title: string
  description: string
  priority: "high" | "medium" | "low"
  category: "safety" | "efficiency" | "compliance" | "cost" | "schedule"
  voyageStage: string
  actionRequired: boolean
  estimatedImpact: string
  dueDate?: string
  documents?: string[]
  status: "pending" | "in-progress" | "completed" | "dismissed"
}

interface VoyageStage {
  id: string
  name: string
  description: string
  progress: number
  estimatedCompletion: string
  criticalTasks: string[]
}

export default function RecommendationsPanel() {
  const [selectedVoyageStage, setSelectedVoyageStage] = useState("loading")
  const [filterCategory, setFilterCategory] = useState("all")
  const [filterPriority, setFilterPriority] = useState("all")
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])

  const voyageStages: VoyageStage[] = [
    {
      id: "loading",
      name: "Loading Operations",
      description: "Vessel at loading port, cargo operations in progress",
      progress: 65,
      estimatedCompletion: "2024-01-16 14:00",
      criticalTasks: ["Complete cargo loading", "Finalize documentation", "Weather routing"],
    },
    {
      id: "transit",
      name: "Ocean Transit",
      description: "Vessel en route to discharge port",
      progress: 0,
      estimatedCompletion: "2024-01-22 08:00",
      criticalTasks: ["Monitor weather", "Optimize route", "Prepare discharge docs"],
    },
    {
      id: "discharge",
      name: "Discharge Operations",
      description: "Vessel at discharge port, unloading cargo",
      progress: 0,
      estimatedCompletion: "2024-01-24 16:00",
      criticalTasks: ["Coordinate discharge", "Handle documentation", "Plan next voyage"],
    },
  ]

  const allRecommendations: Recommendation[] = [
    {
      id: "1",
      title: "Weather Route Optimization",
      description:
        "Current weather patterns suggest a 12-hour delay. Consider alternative routing via waypoint 52°N 4°E to avoid storm system.",
      priority: "high",
      category: "efficiency",
      voyageStage: "loading",
      actionRequired: true,
      estimatedImpact: "Save 8 hours, reduce fuel by 15%",
      dueDate: "2024-01-15 18:00",
      documents: ["Weather Routing Plan", "Fuel Consumption Report"],
      status: "pending",
    },
    {
      id: "2",
      title: "Laytime Documentation Review",
      description:
        "Notice of Readiness was tendered 4 hours ago. Ensure all laytime documentation is properly recorded to avoid disputes.",
      priority: "high",
      category: "compliance",
      voyageStage: "loading",
      actionRequired: true,
      estimatedImpact: "Prevent potential $50,000 demurrage claim",
      dueDate: "2024-01-15 16:00",
      documents: ["Notice of Readiness", "Time Sheet", "Statement of Facts"],
      status: "in-progress",
    },
    {
      id: "3",
      title: "Cargo Stowage Optimization",
      description:
        "Based on discharge port sequence, recommend adjusting cargo stowage plan to reduce discharge time by 6 hours.",
      priority: "medium",
      category: "efficiency",
      voyageStage: "loading",
      actionRequired: false,
      estimatedImpact: "Reduce port costs by $12,000",
      documents: ["Stowage Plan", "Cargo Manifest"],
      status: "pending",
    },
    {
      id: "4",
      title: "Port State Control Preparation",
      description:
        "Destination port has increased PSC inspections. Ensure all certificates are current and crew documentation is complete.",
      priority: "medium",
      category: "compliance",
      voyageStage: "transit",
      actionRequired: true,
      estimatedImpact: "Avoid inspection delays",
      dueDate: "2024-01-20 12:00",
      documents: ["Safety Certificates", "Crew Certificates", "Port Clearance"],
      status: "pending",
    },
    {
      id: "5",
      title: "Fuel Optimization Analysis",
      description:
        "Current consumption is 8% above optimal. Recommend speed adjustment to 11.5 knots for better fuel efficiency.",
      priority: "low",
      category: "cost",
      voyageStage: "transit",
      actionRequired: false,
      estimatedImpact: "Save $8,500 in fuel costs",
      documents: ["Fuel Consumption Log", "Performance Report"],
      status: "pending",
    },
    {
      id: "6",
      title: "Discharge Port Preparation",
      description:
        "Pre-arrival documentation should be submitted 72 hours before arrival. Prepare customs and port authority forms.",
      priority: "medium",
      category: "schedule",
      voyageStage: "discharge",
      actionRequired: true,
      estimatedImpact: "Ensure smooth port entry",
      dueDate: "2024-01-21 08:00",
      documents: ["Customs Declaration", "Port Entry Forms", "Cargo Manifest"],
      status: "pending",
    },
  ]

  useEffect(() => {
    // Filter recommendations based on selected voyage stage and filters
    let filtered = allRecommendations.filter((rec) => rec.voyageStage === selectedVoyageStage)

    if (filterCategory !== "all") {
      filtered = filtered.filter((rec) => rec.category === filterCategory)
    }

    if (filterPriority !== "all") {
      filtered = filtered.filter((rec) => rec.priority === filterPriority)
    }

    setRecommendations(filtered)
  }, [selectedVoyageStage, filterCategory, filterPriority])

  const getPriorityColor = (priority: Recommendation["priority"]) => {
    switch (priority) {
      case "high":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
      case "medium":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
      case "low":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
    }
  }

  const getCategoryIcon = (category: Recommendation["category"]) => {
    switch (category) {
      case "safety":
        return <Shield className="w-4 h-4" />
      case "efficiency":
        return <TrendingUp className="w-4 h-4" />
      case "compliance":
        return <FileText className="w-4 h-4" />
      case "cost":
        return <DollarSign className="w-4 h-4" />
      case "schedule":
        return <Calendar className="w-4 h-4" />
    }
  }

  const getCategoryColor = (category: Recommendation["category"]) => {
    switch (category) {
      case "safety":
        return "text-red-600"
      case "efficiency":
        return "text-blue-600"
      case "compliance":
        return "text-purple-600"
      case "cost":
        return "text-green-600"
      case "schedule":
        return "text-orange-600"
    }
  }

  const getStatusIcon = (status: Recommendation["status"]) => {
    switch (status) {
      case "pending":
        return <Clock className="w-4 h-4 text-orange-500" />
      case "in-progress":
        return <Settings className="w-4 h-4 text-blue-500 animate-spin" />
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "dismissed":
        return <AlertTriangle className="w-4 h-4 text-gray-500" />
    }
  }

  const handleRecommendationAction = (id: string, action: "accept" | "dismiss" | "complete") => {
    setRecommendations((prev) =>
      prev.map((rec) => {
        if (rec.id === id) {
          switch (action) {
            case "accept":
              return { ...rec, status: "in-progress" }
            case "dismiss":
              return { ...rec, status: "dismissed" }
            case "complete":
              return { ...rec, status: "completed" }
          }
        }
        return rec
      }),
    )
  }

  const currentStage = voyageStages.find((stage) => stage.id === selectedVoyageStage)
  const priorityStats = {
    high: recommendations.filter((r) => r.priority === "high" && r.status === "pending").length,
    medium: recommendations.filter((r) => r.priority === "medium" && r.status === "pending").length,
    low: recommendations.filter((r) => r.priority === "low" && r.status === "pending").length,
  }

  return (
    <div className="min-h-screen bg-background wave-pattern">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link href="/">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Dashboard
                </Button>
              </Link>
              <Separator orientation="vertical" className="h-6" />
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-primary" />
                <h1 className="text-xl font-bold font-montserrat">Smart Recommendations</h1>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                AI Analysis Active
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Voyage Stage Selector & Stats */}
          <div className="space-y-6">
            {/* Voyage Stage */}
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg font-montserrat flex items-center gap-2">
                  <Ship className="w-5 h-5" />
                  Current Voyage Stage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Select value={selectedVoyageStage} onValueChange={setSelectedVoyageStage}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {voyageStages.map((stage) => (
                      <SelectItem key={stage.id} value={stage.id}>
                        {stage.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {currentStage && (
                  <div className="mt-4 space-y-3">
                    <div>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span>Progress</span>
                        <span>{currentStage.progress}%</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full transition-all"
                          style={{ width: `${currentStage.progress}%` }}
                        ></div>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-2">{currentStage.description}</p>
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="w-4 h-4 text-primary" />
                        <span>ETC: {currentStage.estimatedCompletion}</span>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Priority Stats */}
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg font-montserrat">Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      <span className="text-sm">High Priority</span>
                    </div>
                    <Badge variant="destructive">{priorityStats.high}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                      <span className="text-sm">Medium Priority</span>
                    </div>
                    <Badge variant="default">{priorityStats.medium}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <span className="text-sm">Low Priority</span>
                    </div>
                    <Badge variant="secondary">{priorityStats.low}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Filters */}
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg font-montserrat">Filters</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Category</label>
                  <Select value={filterCategory} onValueChange={setFilterCategory}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Categories</SelectItem>
                      <SelectItem value="safety">Safety</SelectItem>
                      <SelectItem value="efficiency">Efficiency</SelectItem>
                      <SelectItem value="compliance">Compliance</SelectItem>
                      <SelectItem value="cost">Cost</SelectItem>
                      <SelectItem value="schedule">Schedule</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Priority</label>
                  <Select value={filterPriority} onValueChange={setFilterPriority}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Priorities</SelectItem>
                      <SelectItem value="high">High Priority</SelectItem>
                      <SelectItem value="medium">Medium Priority</SelectItem>
                      <SelectItem value="low">Low Priority</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recommendations List */}
          <div className="lg:col-span-3">
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg font-montserrat">
                      AI Recommendations ({recommendations.length})
                    </CardTitle>
                    <CardDescription>Smart suggestions based on current voyage stage and conditions</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-[600px]">
                  <div className="space-y-4 p-6">
                    {recommendations.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <Navigation className="w-8 h-8 mx-auto mb-2" />
                        <p className="text-sm">No recommendations for current filters</p>
                      </div>
                    ) : (
                      recommendations.map((recommendation) => (
                        <Card
                          key={recommendation.id}
                          className={`border-border/50 ${
                            recommendation.priority === "high" ? "border-l-4 border-l-red-500" : ""
                          }`}
                        >
                          <CardContent className="p-4">
                            <div className="space-y-3">
                              {/* Header */}
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <div className={getCategoryColor(recommendation.category)}>
                                      {getCategoryIcon(recommendation.category)}
                                    </div>
                                    <h4 className="font-medium">{recommendation.title}</h4>
                                    {recommendation.actionRequired && (
                                      <Badge variant="outline" className="text-xs">
                                        Action Required
                                      </Badge>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Badge className={`text-xs ${getPriorityColor(recommendation.priority)}`}>
                                      {recommendation.priority.toUpperCase()}
                                    </Badge>
                                    <div className="flex items-center gap-1">
                                      {getStatusIcon(recommendation.status)}
                                      <span className="text-xs text-muted-foreground capitalize">
                                        {recommendation.status.replace("-", " ")}
                                      </span>
                                    </div>
                                  </div>
                                </div>
                              </div>

                              {/* Description */}
                              <p className="text-sm text-muted-foreground leading-relaxed">
                                {recommendation.description}
                              </p>

                              {/* Impact & Due Date */}
                              <div className="flex items-center justify-between text-sm">
                                <div className="flex items-center gap-2">
                                  <TrendingUp className="w-4 h-4 text-green-500" />
                                  <span className="text-green-600">{recommendation.estimatedImpact}</span>
                                </div>
                                {recommendation.dueDate && (
                                  <div className="flex items-center gap-2">
                                    <Clock className="w-4 h-4 text-orange-500" />
                                    <span className="text-orange-600">Due: {recommendation.dueDate}</span>
                                  </div>
                                )}
                              </div>

                              {/* Documents */}
                              {recommendation.documents && recommendation.documents.length > 0 && (
                                <div>
                                  <p className="text-xs font-medium text-muted-foreground mb-2">Related Documents:</p>
                                  <div className="flex flex-wrap gap-2">
                                    {recommendation.documents.map((doc, index) => (
                                      <Badge key={index} variant="outline" className="text-xs">
                                        <FileText className="w-3 h-3 mr-1" />
                                        {doc}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Actions */}
                              {recommendation.status === "pending" && (
                                <div className="flex items-center gap-2 pt-2">
                                  <Button
                                    size="sm"
                                    onClick={() => handleRecommendationAction(recommendation.id, "accept")}
                                  >
                                    Accept
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleRecommendationAction(recommendation.id, "dismiss")}
                                  >
                                    Dismiss
                                  </Button>
                                </div>
                              )}

                              {recommendation.status === "in-progress" && (
                                <div className="flex items-center gap-2 pt-2">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleRecommendationAction(recommendation.id, "complete")}
                                  >
                                    Mark Complete
                                  </Button>
                                </div>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

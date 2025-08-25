"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import {
  ArrowLeft,
  Settings,
  Key,
  Bell,
  Shield,
  Palette,
  CheckCircle,
  AlertCircle,
  Eye,
  EyeOff,
  Save,
  RefreshCw,
  ExternalLink,
} from "lucide-react"
import Link from "next/link"

interface Integration {
  id: string
  name: string
  description: string
  status: "connected" | "disconnected" | "error"
  lastSync: string
  apiKey?: string
  endpoint?: string
  required: boolean
}

interface SystemSettings {
  notifications: {
    weatherAlerts: boolean
    voyageUpdates: boolean
    documentProcessing: boolean
    recommendations: boolean
  }
  display: {
    theme: "light" | "dark" | "auto"
    language: string
    timezone: string
    units: "metric" | "imperial"
  }
  security: {
    sessionTimeout: number
    twoFactorAuth: boolean
    apiRateLimit: number
  }
}

export default function SettingsPage() {
  const [showApiKeys, setShowApiKeys] = useState<{ [key: string]: boolean }>({})
  const [integrations, setIntegrations] = useState<Integration[]>([
    {
      id: "azure-openai",
      name: "Azure OpenAI",
      description: "AI-powered document analysis and chat responses",
      status: "connected",
      lastSync: "2024-01-15 10:30:00",
      apiKey: "sk-proj-***************************",
      endpoint: "https://your-resource.openai.azure.com/",
      required: true,
    },
    {
      id: "weather-api",
      name: "Weather API",
      description: "Real-time weather data and forecasting",
      status: "connected",
      lastSync: "2024-01-15 10:25:00",
      apiKey: "wapi_***************************",
      endpoint: "https://api.weatherapi.com/v1/",
      required: true,
    },
    {
      id: "azure-storage",
      name: "Azure Blob Storage",
      description: "Document storage and file management",
      status: "connected",
      lastSync: "2024-01-15 10:20:00",
      apiKey: "DefaultEndpointsProtocol=https;AccountName=***",
      required: true,
    },
    {
      id: "vessel-tracking",
      name: "Vessel Tracking API",
      description: "Live vessel positions and AIS data",
      status: "error",
      lastSync: "2024-01-15 08:15:00",
      apiKey: "",
      endpoint: "https://api.vesselfinder.com/",
      required: false,
    },
  ])

  const [settings, setSettings] = useState<SystemSettings>({
    notifications: {
      weatherAlerts: true,
      voyageUpdates: true,
      documentProcessing: false,
      recommendations: true,
    },
    display: {
      theme: "auto",
      language: "en",
      timezone: "UTC",
      units: "metric",
    },
    security: {
      sessionTimeout: 30,
      twoFactorAuth: false,
      apiRateLimit: 1000,
    },
  })

  const toggleApiKeyVisibility = (integrationId: string) => {
    setShowApiKeys((prev) => ({
      ...prev,
      [integrationId]: !prev[integrationId],
    }))
  }

  const updateIntegration = (id: string, field: string, value: string) => {
    setIntegrations((prev) =>
      prev.map((integration) => (integration.id === id ? { ...integration, [field]: value } : integration)),
    )
  }

  const testConnection = async (integrationId: string) => {
    // Simulate API test
    setIntegrations((prev) =>
      prev.map((integration) =>
        integration.id === integrationId
          ? { ...integration, status: "connected", lastSync: new Date().toISOString() }
          : integration,
      ),
    )
  }

  const updateSettings = (section: keyof SystemSettings, field: string, value: any) => {
    setSettings((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value,
      },
    }))
  }

  const getStatusIcon = (status: Integration["status"]) => {
    switch (status) {
      case "connected":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "disconnected":
        return <AlertCircle className="w-4 h-4 text-gray-500" />
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-500" />
    }
  }

  const getStatusColor = (status: Integration["status"]) => {
    switch (status) {
      case "connected":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
      case "disconnected":
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200"
      case "error":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
    }
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
                <Settings className="w-5 h-5 text-primary" />
                <h1 className="text-xl font-bold font-montserrat">Settings & Integrations</h1>
              </div>
            </div>
            <Button>
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <Tabs defaultValue="integrations" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="integrations">API Integrations</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="display">Display</TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
          </TabsList>

          {/* API Integrations Tab */}
          <TabsContent value="integrations" className="space-y-6">
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg font-montserrat flex items-center gap-2">
                  <Key className="w-5 h-5" />
                  API Integrations
                </CardTitle>
                <CardDescription>Configure API keys and endpoints for external services</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {integrations.map((integration) => (
                    <Card key={integration.id} className="border-border/50">
                      <CardContent className="p-4">
                        <div className="space-y-4">
                          {/* Header */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="flex items-center gap-2">
                                {getStatusIcon(integration.status)}
                                <h4 className="font-medium">{integration.name}</h4>
                                {integration.required && (
                                  <Badge variant="outline" className="text-xs">
                                    Required
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge className={`text-xs ${getStatusColor(integration.status)}`}>
                                {integration.status.toUpperCase()}
                              </Badge>
                              <Button size="sm" variant="outline" onClick={() => testConnection(integration.id)}>
                                <RefreshCw className="w-3 h-3 mr-1" />
                                Test
                              </Button>
                            </div>
                          </div>

                          <p className="text-sm text-muted-foreground">{integration.description}</p>

                          {/* API Key */}
                          <div className="space-y-2">
                            <Label htmlFor={`${integration.id}-key`}>API Key</Label>
                            <div className="flex gap-2">
                              <div className="relative flex-1">
                                <Input
                                  id={`${integration.id}-key`}
                                  type={showApiKeys[integration.id] ? "text" : "password"}
                                  value={integration.apiKey || ""}
                                  onChange={(e) => updateIntegration(integration.id, "apiKey", e.target.value)}
                                  placeholder="Enter API key..."
                                />
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="sm"
                                  className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                                  onClick={() => toggleApiKeyVisibility(integration.id)}
                                >
                                  {showApiKeys[integration.id] ? (
                                    <EyeOff className="w-3 h-3" />
                                  ) : (
                                    <Eye className="w-3 h-3" />
                                  )}
                                </Button>
                              </div>
                            </div>
                          </div>

                          {/* Endpoint */}
                          {integration.endpoint && (
                            <div className="space-y-2">
                              <Label htmlFor={`${integration.id}-endpoint`}>Endpoint URL</Label>
                              <Input
                                id={`${integration.id}-endpoint`}
                                value={integration.endpoint}
                                onChange={(e) => updateIntegration(integration.id, "endpoint", e.target.value)}
                                placeholder="https://api.example.com/"
                              />
                            </div>
                          )}

                          {/* Last Sync */}
                          <div className="flex items-center justify-between text-sm text-muted-foreground">
                            <span>Last sync: {integration.lastSync}</span>
                            <Button variant="ghost" size="sm" className="h-auto p-0">
                              <ExternalLink className="w-3 h-3 mr-1" />
                              Documentation
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications" className="space-y-6">
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg font-montserrat flex items-center gap-2">
                  <Bell className="w-5 h-5" />
                  Notification Preferences
                </CardTitle>
                <CardDescription>Configure when and how you receive notifications</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Weather Alerts</Label>
                      <p className="text-sm text-muted-foreground">
                        Receive notifications for severe weather conditions
                      </p>
                    </div>
                    <Switch
                      checked={settings.notifications.weatherAlerts}
                      onCheckedChange={(checked) => updateSettings("notifications", "weatherAlerts", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Voyage Updates</Label>
                      <p className="text-sm text-muted-foreground">
                        Get notified about voyage milestones and ETA changes
                      </p>
                    </div>
                    <Switch
                      checked={settings.notifications.voyageUpdates}
                      onCheckedChange={(checked) => updateSettings("notifications", "voyageUpdates", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Document Processing</Label>
                      <p className="text-sm text-muted-foreground">Notifications when document analysis is complete</p>
                    </div>
                    <Switch
                      checked={settings.notifications.documentProcessing}
                      onCheckedChange={(checked) => updateSettings("notifications", "documentProcessing", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>AI Recommendations</Label>
                      <p className="text-sm text-muted-foreground">
                        Receive smart recommendations and optimization suggestions
                      </p>
                    </div>
                    <Switch
                      checked={settings.notifications.recommendations}
                      onCheckedChange={(checked) => updateSettings("notifications", "recommendations", checked)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Display Tab */}
          <TabsContent value="display" className="space-y-6">
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg font-montserrat flex items-center gap-2">
                  <Palette className="w-5 h-5" />
                  Display Settings
                </CardTitle>
                <CardDescription>Customize the appearance and localization</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label>Theme</Label>
                    <select
                      className="w-full p-2 border border-border rounded-md bg-background"
                      value={settings.display.theme}
                      onChange={(e) => updateSettings("display", "theme", e.target.value as "light" | "dark" | "auto")}
                    >
                      <option value="light">Light</option>
                      <option value="dark">Dark</option>
                      <option value="auto">Auto (System)</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label>Language</Label>
                    <select
                      className="w-full p-2 border border-border rounded-md bg-background"
                      value={settings.display.language}
                      onChange={(e) => updateSettings("display", "language", e.target.value)}
                    >
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                      <option value="de">German</option>
                      <option value="zh">Chinese</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label>Timezone</Label>
                    <select
                      className="w-full p-2 border border-border rounded-md bg-background"
                      value={settings.display.timezone}
                      onChange={(e) => updateSettings("display", "timezone", e.target.value)}
                    >
                      <option value="UTC">UTC</option>
                      <option value="America/New_York">Eastern Time</option>
                      <option value="Europe/London">London</option>
                      <option value="Asia/Singapore">Singapore</option>
                      <option value="Australia/Sydney">Sydney</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label>Units</Label>
                    <select
                      className="w-full p-2 border border-border rounded-md bg-background"
                      value={settings.display.units}
                      onChange={(e) => updateSettings("display", "units", e.target.value as "metric" | "imperial")}
                    >
                      <option value="metric">Metric (km, °C, m/s)</option>
                      <option value="imperial">Imperial (mi, °F, mph)</option>
                    </select>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security" className="space-y-6">
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg font-montserrat flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Security Settings
                </CardTitle>
                <CardDescription>Configure security and access control settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Session Timeout (minutes)</Label>
                    <Input
                      type="number"
                      value={settings.security.sessionTimeout}
                      onChange={(e) => updateSettings("security", "sessionTimeout", Number.parseInt(e.target.value))}
                      min="5"
                      max="480"
                    />
                    <p className="text-sm text-muted-foreground">
                      Automatically log out after this period of inactivity
                    </p>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Two-Factor Authentication</Label>
                      <p className="text-sm text-muted-foreground">Add an extra layer of security to your account</p>
                    </div>
                    <Switch
                      checked={settings.security.twoFactorAuth}
                      onCheckedChange={(checked) => updateSettings("security", "twoFactorAuth", checked)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>API Rate Limit (requests/hour)</Label>
                    <Input
                      type="number"
                      value={settings.security.apiRateLimit}
                      onChange={(e) => updateSettings("security", "apiRateLimit", Number.parseInt(e.target.value))}
                      min="100"
                      max="10000"
                    />
                    <p className="text-sm text-muted-foreground">Maximum number of API requests allowed per hour</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

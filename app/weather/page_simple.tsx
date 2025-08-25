"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  ArrowLeft,
  Cloud,
  MapPin,
  Ship,
  Wind,
  Waves,
  Eye,
  ThermometerSun,
  Anchor,
  AlertTriangle,
  Search,
  Loader2,
  Sun,
  CloudRain,
} from "lucide-react"
import Link from "next/link"
import { getWeatherData, type WeatherQuery, type WeatherResponse } from "@/lib/api/client"

interface Port {
  id: string
  name: string
  country: string
  lat: number
  lng: number
}

export default function WeatherPage() {
  const [weatherData, setWeatherData] = useState<WeatherResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [selectedLocation, setSelectedLocation] = useState<string>("")

  const majorPorts: Port[] = [
    { id: "NLRTM", name: "Rotterdam", country: "Netherlands", lat: 51.9225, lng: 4.4792 },
    { id: "DEHAM", name: "Hamburg", country: "Germany", lat: 53.5511, lng: 9.9937 },
    { id: "SGSIN", name: "Singapore", country: "Singapore", lat: 1.3521, lng: 103.8198 },
    { id: "USLAX", name: "Los Angeles", country: "USA", lat: 33.7361, lng: -118.2639 },
  ]

  const [error, setError] = useState<string>('');
  
  const fetchWeather = async (lat: number, lng: number, locationName: string) => {
    setIsLoading(true);
    setSelectedLocation(locationName);
    setWeatherData(null); // Clear previous data
    setError(''); // Clear previous errors
    
    try {
      const query: WeatherQuery = { 
        latitude: lat, 
        longitude: lng,
        include_marine: true,
        include_warnings: true,
        forecast_days: 5
      };
      
      const response = await getWeatherData(query);
      
      if (!response || !response.current_weather) {
        throw new Error('Invalid weather data received');
      }
      
      setWeatherData(response);
    } catch (error) {
      console.error("Weather API error:", error);
      setError(error instanceof Error ? error.message : 'Failed to fetch weather data');
      
      // Use development fallback data for testing
      if (process.env.NODE_ENV === 'development') {
        setWeatherData({
        current_weather: {
          temperature: 15,
          humidity: 75,
          pressure: 1013,
          wind_speed: 22,
          wind_direction: 270,
          visibility: 8000,
          conditions: "Partly Cloudy"
        },
        forecast: [
          { date: "2025-08-16", temperature_high: 18, temperature_low: 12, wind_speed: 25, wind_direction: 280, wave_height: 2.1, conditions: "Cloudy" },
          { date: "2025-08-17", temperature_high: 16, temperature_low: 10, wind_speed: 30, wind_direction: 290, wave_height: 2.8, conditions: "Rainy" },
          { date: "2025-08-18", temperature_high: 20, temperature_low: 14, wind_speed: 18, wind_direction: 250, wave_height: 1.5, conditions: "Sunny" },
        ],
        marine_conditions: {
          wave_height: 2.1,
          wave_direction: 270,
          swell_height: 1.6,
          sea_state: "Moderate",
          current_speed: 1.1,
          current_direction: 85,
          tide: "High at 15:45 UTC"
        },
        warnings: ["Small Craft Advisory", "Strong Wind Warning"]
      })
    } finally {
      setIsLoading(false)
    }
  }

  const getWeatherIcon = (conditions: string) => {
    if (conditions.toLowerCase().includes('sun')) return <Sun className="w-5 h-5 text-yellow-500" />
    if (conditions.toLowerCase().includes('rain')) return <CloudRain className="w-5 h-5 text-blue-500" />
    return <Cloud className="w-5 h-5 text-gray-500" />
  }

  const getCompassDirection = (degrees: number) => {
    const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return directions[Math.round(degrees / 45) % 8]
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-slate-50 to-cyan-50 dark:from-gray-900 dark:via-blue-950 dark:to-slate-900">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Dashboard
                </Button>
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-primary flex items-center gap-2">
                  <Cloud className="w-6 h-6" />
                  Maritime Weather Center
                </h1>
                <p className="text-sm text-muted-foreground">Real-time weather conditions and forecasts</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
                Live Data
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          {/* Sidebar - Port Selection */}
          <div className="lg:col-span-1">
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Search className="w-5 h-5" />
                  Select Port
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {majorPorts.map((port) => (
                  <div
                    key={port.id}
                    className="p-3 rounded-lg border cursor-pointer transition-all hover:border-primary/50 hover:bg-muted/50"
                    onClick={() => fetchWeather(port.lat, port.lng, `${port.name}, ${port.country}`)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{port.name}</h4>
                        <p className="text-sm text-muted-foreground">{port.country}</p>
                      </div>
                      <Anchor className="w-4 h-4 text-muted-foreground" />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            
            {/* Loading State */}
            {isLoading && (
              <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
                <CardContent className="flex items-center justify-center py-12">
                  <div className="flex items-center gap-3">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span>Fetching weather data for {selectedLocation}...</span>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Weather Display */}
            {weatherData && !isLoading && (
              <>
                {/* Current Conditions */}
                <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {getWeatherIcon(weatherData.current_weather.conditions)}
                      Current Conditions - {selectedLocation}
                    </CardTitle>
                    <CardDescription>
                      {weatherData.current_weather.conditions} • Updated: {new Date().toLocaleTimeString()}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                      
                      <div className="flex items-center gap-3">
                        <ThermometerSun className="w-8 h-8 text-orange-500" />
                        <div>
                          <p className="text-3xl font-bold">{weatherData.current_weather.temperature}°C</p>
                          <p className="text-sm text-muted-foreground">Temperature</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <Wind className="w-8 h-8 text-blue-500" />
                        <div>
                          <p className="text-3xl font-bold">{weatherData.current_weather.wind_speed} kts</p>
                          <p className="text-sm text-muted-foreground">
                            Wind {getCompassDirection(weatherData.current_weather.wind_direction)}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <Waves className="w-8 h-8 text-cyan-500" />
                        <div>
                          <p className="text-3xl font-bold">{weatherData.marine_conditions.wave_height}m</p>
                          <p className="text-sm text-muted-foreground">Wave Height</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <Eye className="w-8 h-8 text-gray-500" />
                        <div>
                          <p className="text-3xl font-bold">{(weatherData.current_weather.visibility / 1000).toFixed(1)}km</p>
                          <p className="text-sm text-muted-foreground">Visibility</p>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-6 pt-4 border-t text-sm">
                      <div><span className="font-medium">Humidity:</span> {weatherData.current_weather.humidity}%</div>
                      <div><span className="font-medium">Pressure:</span> {weatherData.current_weather.pressure} hPa</div>
                      <div><span className="font-medium">Sea State:</span> {weatherData.marine_conditions.sea_state}</div>
                      <div><span className="font-medium">Current:</span> {weatherData.marine_conditions.current_speed} kts</div>
                      <div><span className="font-medium">Swell:</span> {weatherData.marine_conditions.swell_height}m</div>
                      <div><span className="font-medium">Tide:</span> {weatherData.marine_conditions.tide}</div>
                    </div>
                  </CardContent>
                </Card>

                {/* Weather Warnings */}
                {weatherData.warnings && weatherData.warnings.length > 0 && (
                  <Alert className="border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-950">
                    <AlertTriangle className="h-4 w-4 text-orange-600" />
                    <AlertDescription>
                      <strong>Weather Warnings:</strong>
                      <ul className="mt-1 space-y-1">
                        {weatherData.warnings.map((warning, index) => (
                          <li key={index} className="text-sm">• {warning}</li>
                        ))}
                      </ul>
                    </AlertDescription>
                  </Alert>
                )}

                {/* 3-Day Forecast */}
                <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Cloud className="w-5 h-5" />
                      3-Day Maritime Forecast
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {weatherData.forecast.slice(0, 3).map((day, index) => (
                        <div key={index} className="p-4 rounded-lg border border-border/50 bg-muted/20">
                          <div className="flex items-center justify-between mb-3">
                            <span className="font-medium">
                              {index === 0 ? "Today" : new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                            </span>
                            {getWeatherIcon(day.conditions)}
                          </div>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span>High/Low:</span>
                              <span>{day.temperature_high}°/{day.temperature_low}°C</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Wind:</span>
                              <span>{day.wind_speed} kts {getCompassDirection(day.wind_direction)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Waves:</span>
                              <span>{day.wave_height}m</span>
                            </div>
                            <div className="text-xs text-muted-foreground mt-2">
                              {day.conditions}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </>
            )}

            {/* No Data State */}
            {!weatherData && !isLoading && (
              <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Cloud className="w-12 h-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">Select a Port</h3>
                  <p className="text-muted-foreground text-center">
                    Choose a major port from the sidebar to view current weather conditions and marine forecasts
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

'use client'

import React, { useState, useEffect } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Search, MapPin, Anchor, Globe, BarChart3, Loader2 } from 'lucide-react'
import { 
  getAllPorts, 
  searchPorts, 
  getNearbyPorts, 
  getPortsByCountry, 
  getPortsByType, 
  getPortByLocode,
  getPortsStatistics,
  type Port, 
  type PortsStatistics 
} from '@/lib/api/client'

export default function PortsPage() {
  const [activeTab, setActiveTab] = useState('search')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Search state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Port[]>([])

  // All ports state
  const [allPorts, setAllPorts] = useState<Port[]>([])
  const [selectedCountry, setSelectedCountry] = useState<string>('')
  const [selectedPortType, setSelectedPortType] = useState<string>('')

  // Nearby ports state
  const [nearbyPorts, setNearbyPorts] = useState<Port[]>([])
  const [latitude, setLatitude] = useState<string>('')
  const [longitude, setLongitude] = useState<string>('')
  const [radius, setRadius] = useState<string>('100')

  // LOCODE search state
  const [locode, setLocode] = useState('')
  const [locodeResult, setLocodeResult] = useState<Port | null>(null)

  // Statistics state
  const [statistics, setStatistics] = useState<PortsStatistics | null>(null)

  // Load initial data
  useEffect(() => {
    handleGetStatistics()
    handleGetAllPorts()
  }, [])

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    
    setLoading(true)
    setError(null)
    try {
      const result = await searchPorts(searchQuery, 50)
      setSearchResults(result.ports)
    } catch (err) {
      setError(`Search failed: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  const handleGetAllPorts = async () => {
    setLoading(true)
    setError(null)
    try {
      const options: any = { limit: 100 }
      if (selectedCountry) options.country = selectedCountry
      if (selectedPortType) options.port_type = selectedPortType
      
      const result = await getAllPorts(options)
      setAllPorts(result.ports)
    } catch (err) {
      setError(`Failed to load ports: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  const handleGetNearbyPorts = async () => {
    if (!latitude || !longitude) return
    
    setLoading(true)
    setError(null)
    try {
      const result = await getNearbyPorts({
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        radius: parseFloat(radius),
        limit: 20
      })
      setNearbyPorts(result.ports)
    } catch (err) {
      setError(`Nearby ports search failed: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  const handleGetCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLatitude(position.coords.latitude.toString())
          setLongitude(position.coords.longitude.toString())
        },
        (error) => {
          setError(`Geolocation failed: ${error.message}`)
        }
      )
    } else {
      setError('Geolocation is not supported by this browser')
    }
  }

  const handleLocodeSearch = async () => {
    if (!locode.trim()) return
    
    setLoading(true)
    setError(null)
    try {
      const result = await getPortByLocode(locode)
      setLocodeResult(result.port)
    } catch (err) {
      setError(`LOCODE search failed: ${err instanceof Error ? err.message : 'Unknown error'}`)
      setLocodeResult(null)
    } finally {
      setLoading(false)
    }
  }

  const handleGetStatistics = async () => {
    try {
      const stats = await getPortsStatistics()
      setStatistics(stats)
    } catch (err) {
      console.error('Failed to load statistics:', err)
    }
  }

  const PortCard = ({ port }: { port: Port }) => (
    <Card className="mb-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Anchor className="h-5 w-5 text-blue-500" />
          {port.name}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div><strong>Country:</strong> {port.country}</div>
          <div><strong>Type:</strong> <Badge variant="outline">{port.type}</Badge></div>
          <div><strong>Coordinates:</strong> {port.latitude.toFixed(4)}, {port.longitude.toFixed(4)}</div>
          {port.locode && <div><strong>LOCODE:</strong> {port.locode}</div>}
          {port.distance_km && <div><strong>Distance:</strong> {port.distance_km} km</div>}
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className="container mx-auto py-6 px-4">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-2 mb-2">
          <Anchor className="h-8 w-8 text-blue-500" />
          Global Ports Database
        </h1>
        <p className="text-muted-foreground">
          Comprehensive database of {statistics?.total_ports || '4000+'} ports worldwide across {statistics?.countries_count || '100+'} countries
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="search">Search Ports</TabsTrigger>
          <TabsTrigger value="browse">Browse All</TabsTrigger>
          <TabsTrigger value="nearby">Nearby Ports</TabsTrigger>
          <TabsTrigger value="locode">By LOCODE</TabsTrigger>
          <TabsTrigger value="stats">Statistics</TabsTrigger>
        </TabsList>

        <TabsContent value="search" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Search Ports
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-4">
                <Input
                  placeholder="Search by port name, city, or country..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
                <Button onClick={handleSearch} disabled={loading}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                  Search
                </Button>
              </div>

              <ScrollArea className="h-96">
                {searchResults.length > 0 ? (
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground mb-4">
                      Found {searchResults.length} ports matching "{searchQuery}"
                    </p>
                    {searchResults.map((port, index) => (
                      <PortCard key={index} port={port} />
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    Enter a search query to find ports
                  </p>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="browse" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Browse All Ports
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-4">
                <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Filter by country" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Countries</SelectItem>
                    {/* Countries selection removed - not available in current API */}
                  </SelectContent>
                </Select>

                <Select value={selectedPortType} onValueChange={setSelectedPortType}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Filter by type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Types</SelectItem>
                    {statistics?.port_types && Object.entries(statistics.port_types).map(([type, count]) => (
                      <SelectItem key={type} value={type}>{type} ({count})</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Button onClick={handleGetAllPorts} disabled={loading}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Load Ports'}
                </Button>
              </div>

              <ScrollArea className="h-96">
                {allPorts.length > 0 ? (
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground mb-4">
                      Showing {allPorts.length} ports
                    </p>
                    {allPorts.map((port, index) => (
                      <PortCard key={index} port={port} />
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    Click "Load Ports" to browse all ports
                  </p>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="nearby" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                Find Nearby Ports
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
                <Input
                  placeholder="Latitude"
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value)}
                  type="number"
                  step="any"
                />
                <Input
                  placeholder="Longitude"
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value)}
                  type="number"
                  step="any"
                />
                <Input
                  placeholder="Radius (km)"
                  value={radius}
                  onChange={(e) => setRadius(e.target.value)}
                  type="number"
                />
                <div className="flex gap-1">
                  <Button onClick={handleGetCurrentLocation} size="sm" variant="outline">
                    My Location
                  </Button>
                  <Button onClick={handleGetNearbyPorts} disabled={loading}>
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Find'}
                  </Button>
                </div>
              </div>

              <ScrollArea className="h-96">
                {nearbyPorts.length > 0 ? (
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground mb-4">
                      Found {nearbyPorts.length} ports within {radius}km
                    </p>
                    {nearbyPorts.map((port, index) => (
                      <PortCard key={index} port={port} />
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    Enter coordinates to find nearby ports
                  </p>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="locode" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Search by UN/LOCODE
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-4">
                <Input
                  placeholder="Enter UN/LOCODE (e.g., SGSIN, NLRTM)"
                  value={locode}
                  onChange={(e) => setLocode(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleLocodeSearch()}
                />
                <Button onClick={handleLocodeSearch} disabled={loading}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Search'}
                </Button>
              </div>

              {locodeResult ? (
                <PortCard port={locodeResult} />
              ) : (
                <p className="text-muted-foreground text-center py-8">
                  Enter a UN/LOCODE to search for a specific port
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stats" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Database Overview
                </CardTitle>
              </CardHeader>
              <CardContent>
                {statistics ? (
                  <div className="space-y-2">
                    <div className="text-2xl font-bold">{statistics.total_ports}</div>
                    <div className="text-sm text-muted-foreground">Total Ports</div>
                    <div className="text-lg font-semibold">{statistics.countries_count}</div>
                    <div className="text-sm text-muted-foreground">Countries</div>
                    <div className="text-lg font-semibold">{Object.keys(statistics.port_types).length}</div>
                    <div className="text-sm text-muted-foreground">Port Types</div>
                  </div>
                ) : (
                  <Loader2 className="h-6 w-6 animate-spin" />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Port Types</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-48">
                  <div className="space-y-1">
                    {statistics?.port_types && Object.entries(statistics.port_types).map(([type, count]) => (
                      <Badge key={type} variant="outline" className="mr-1 mb-1">
                        {type} ({count})
                      </Badge>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Sample Ports section removed - not available in current API */}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

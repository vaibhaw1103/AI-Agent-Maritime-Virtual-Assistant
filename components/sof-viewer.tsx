"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Edit, 
  Save, 
  X, 
  AlertTriangle, 
  CheckCircle, 
  Download, 
  FileText,
  Clock,
  Ship,
  Anchor
} from "lucide-react"

interface SoFEvent {
  event_type: string
  description: string
  start_time: string
  confidence: number
  needs_review: boolean
  extracted_text?: string
  suggested_time?: string
}

interface SoFData {
  vessel_name: string
  imo_number: string
  port: string
  berth: string
  events: SoFEvent[]
  total_events: number
  low_confidence_count: number
  total_laytime_hours?: number
  document_confidence: number
  stops?: any[]
}

interface SoFAnalysis {
  document_type: string
  sof_data: SoFData
  export_formats: string[]
  editable_events: SoFEvent[]
}

interface SoFViewerProps {
  analysis: SoFAnalysis
  filename: string
  onUpdate?: (updatedAnalysis: SoFAnalysis) => void
}

export function SoFViewer({ analysis, filename, onUpdate }: SoFViewerProps) {
  const [editingEvents, setEditingEvents] = useState<{[key: number]: boolean}>({})
  const [editedData, setEditedData] = useState<{[key: number]: Partial<SoFEvent>}>({})
  const [isExporting, setIsExporting] = useState(false)

  const { sof_data, editable_events } = analysis

  const handleEditEvent = (index: number) => {
    setEditingEvents(prev => ({ ...prev, [index]: true }))
    setEditedData(prev => ({ 
      ...prev, 
      [index]: { 
        start_time: sof_data.events[index].start_time,
        description: sof_data.events[index].description
      } 
    }))
  }

  const handleSaveEvent = async (index: number) => {
    const eventUpdate = editedData[index]
    if (!eventUpdate) return

    try {
      // Call API to update event
      const response = await fetch('http://localhost:8000/sof/update-event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_index: index,
          updated_time: eventUpdate.start_time,
          updated_description: eventUpdate.description
        })
      })

      if (response.ok) {
        const result = await response.json()
        
        // Update the event in the local state
        const updatedEvents = [...sof_data.events]
        updatedEvents[index] = {
          ...updatedEvents[index],
          start_time: eventUpdate.start_time || updatedEvents[index].start_time,
          description: eventUpdate.description || updatedEvents[index].description,
          confidence: result.confidence || 0.9, // Updated events get higher confidence
          needs_review: false
        }

        const updatedAnalysis = {
          ...analysis,
          sof_data: {
            ...sof_data,
            events: updatedEvents,
            low_confidence_count: updatedEvents.filter(e => e.needs_review).length
          }
        }

        onUpdate?.(updatedAnalysis)
        setEditingEvents(prev => ({ ...prev, [index]: false }))
      }
    } catch (error) {
      console.error('Failed to update event:', error)
    }
  }

  const handleCancelEdit = (index: number) => {
    setEditingEvents(prev => ({ ...prev, [index]: false }))
    setEditedData(prev => {
      const newData = { ...prev }
      delete newData[index]
      return newData
    })
  }

  const handleExport = async (format: 'json' | 'csv') => {
    setIsExporting(true)
    try {
      const response = await fetch(`http://localhost:8000/sof/export/${format}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sof_data)
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${filename.split('.')[0]}_sof_export.${format}`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.8) {
      return <Badge variant="default" className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />High</Badge>
    } else if (confidence >= 0.6) {
      return <Badge variant="secondary"><Clock className="w-3 h-3 mr-1" />Medium</Badge>
    } else {
      return <Badge variant="destructive"><AlertTriangle className="w-3 h-3 mr-1" />Low</Badge>
    }
  }

  return (
    <div className="space-y-6">
      {/* Document Header */}
      <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Ship className="w-5 h-5 text-blue-500" />
                Statement of Facts - {sof_data.vessel_name || "Unknown Vessel"}
              </CardTitle>
              <CardDescription>
                Document confidence: {(sof_data.document_confidence * 100).toFixed(1)}% 
                | {sof_data.total_events} events extracted
                {sof_data.low_confidence_count > 0 && (
                  <span className="text-amber-500 ml-2">
                    | {sof_data.low_confidence_count} events need review
                  </span>
                )}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExport('json')}
                disabled={isExporting}
              >
                <Download className="w-4 h-4 mr-1" />
                JSON
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExport('csv')}
                disabled={isExporting}
              >
                <FileText className="w-4 h-4 mr-1" />
                CSV
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <Label className="text-xs text-muted-foreground">Vessel</Label>
              <p className="font-medium">{sof_data.vessel_name || "Not specified"}</p>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">IMO Number</Label>
              <p className="font-medium">{sof_data.imo_number || "Not specified"}</p>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Port</Label>
              <p className="font-medium">{sof_data.port || "Not specified"}</p>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Berth</Label>
              <p className="font-medium">{sof_data.berth || "Not specified"}</p>
            </div>
            {sof_data.total_laytime_hours && (
              <div className="col-span-2">
                <Label className="text-xs text-muted-foreground">Total Laytime</Label>
                <p className="font-medium">{sof_data.total_laytime_hours.toFixed(1)} hours</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Events Analysis */}
      <Tabs defaultValue="all-events" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="all-events">
            All Events ({sof_data.events.length})
          </TabsTrigger>
          <TabsTrigger value="needs-review" className="text-amber-600">
            Needs Review ({sof_data.low_confidence_count})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all-events">
          <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-lg">Extracted Events</CardTitle>
              <CardDescription>
                All events extracted from the Statement of Facts document
              </CardDescription>
            </CardHeader>
            <CardContent>
              {sof_data.stops && sof_data.stops.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-md font-semibold mb-2">Port Stops</h4>
                  <div className="space-y-2">
                    {sof_data.stops.map((s: any, idx: number) => (
                      <div key={idx} className="p-2 border rounded">
                        <div className="text-sm text-gray-700">{s.stop_type} — {s.duration_hours ? s.duration_hours.toFixed(2) + ' hrs' : 'n/a'}</div>
                        <div className="text-sm text-gray-500">{s.start_time_str} → {s.end_time_str}</div>
                        <div className="text-xs text-gray-400">Confidence: {(s.confidence||0).toFixed(2)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-4">
                  {sof_data.events.map((event, index) => (
                    <Card key={index} className={`${event.needs_review ? 'border-amber-200 bg-amber-50/50' : 'border-border/30'}`}>
                      <CardContent className="pt-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 space-y-2">
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">{event.event_type}</Badge>
                              {getConfidenceBadge(event.confidence)}
                              {event.needs_review && (
                                <Badge variant="destructive" className="text-xs">
                                  <AlertTriangle className="w-3 h-3 mr-1" />
                                  Review Needed
                                </Badge>
                              )}
                            </div>
                            
                            {editingEvents[index] ? (
                              <div className="space-y-3">
                                <div>
                                  <Label className="text-xs">Event Time</Label>
                                  <Input
                                    value={editedData[index]?.start_time || ''}
                                    onChange={(e) => setEditedData(prev => ({
                                      ...prev,
                                      [index]: { ...prev[index], start_time: e.target.value }
                                    }))}
                                    placeholder="DD/MM/YYYY HH:MM"
                                    className="mt-1"
                                  />
                                </div>
                                <div>
                                  <Label className="text-xs">Description</Label>
                                  <Textarea
                                    value={editedData[index]?.description || ''}
                                    onChange={(e) => setEditedData(prev => ({
                                      ...prev,
                                      [index]: { ...prev[index], description: e.target.value }
                                    }))}
                                    className="mt-1"
                                    rows={2}
                                  />
                                </div>
                                <div className="flex gap-2">
                                  <Button 
                                    size="sm" 
                                    onClick={() => handleSaveEvent(index)}
                                  >
                                    <Save className="w-3 h-3 mr-1" />
                                    Save
                                  </Button>
                                  <Button 
                                    size="sm" 
                                    variant="outline"
                                    onClick={() => handleCancelEdit(index)}
                                  >
                                    <X className="w-3 h-3 mr-1" />
                                    Cancel
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              <div>
                                <div className="flex items-center gap-2 mb-2">
                                  <Clock className="w-4 h-4 text-muted-foreground" />
                                  <span className="font-medium">{event.start_time || "Time not extracted"}</span>
                                </div>
                                <p className="text-sm text-muted-foreground">{event.description}</p>
                                {event.confidence < 0.7 && (
                                  <p className="text-xs text-amber-600 mt-1">
                                    <AlertTriangle className="w-3 h-3 inline mr-1" />
                                    Low confidence extraction - please review and edit if needed
                                  </p>
                                )}
                              </div>
                            )}
                          </div>
                          
                          {!editingEvents[index] && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEditEvent(index)}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="needs-review">
          <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-lg text-amber-600">
                Events Requiring Review
              </CardTitle>
              <CardDescription>
                Events with low confidence that may need manual correction
              </CardDescription>
            </CardHeader>
            <CardContent>
              {sof_data.low_confidence_count === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
                  <p className="text-muted-foreground">All events have high confidence!</p>
                  <p className="text-sm text-muted-foreground">No manual review needed.</p>
                </div>
              ) : (
                <ScrollArea className="h-[600px] pr-4">
                  <div className="space-y-4">
                    {sof_data.events
                      .map((event, originalIndex) => ({ event, originalIndex }))
                      .filter(({ event }) => event.needs_review)
                      .map(({ event, originalIndex }) => (
                        <Card key={originalIndex} className="border-amber-200 bg-amber-50/50">
                          <CardContent className="pt-4">
                            <div className="flex items-start justify-between">
                              <div className="flex-1 space-y-2">
                                <div className="flex items-center gap-2">
                                  <Badge variant="outline">{event.event_type}</Badge>
                                  <Badge variant="destructive">
                                    <AlertTriangle className="w-3 h-3 mr-1" />
                                    Confidence: {(event.confidence * 100).toFixed(0)}%
                                  </Badge>
                                </div>
                                
                                {editingEvents[originalIndex] ? (
                                  <div className="space-y-3">
                                    <div>
                                      <Label className="text-xs">Correct Event Time</Label>
                                      <Input
                                        value={editedData[originalIndex]?.start_time || ''}
                                        onChange={(e) => setEditedData(prev => ({
                                          ...prev,
                                          [originalIndex]: { ...prev[originalIndex], start_time: e.target.value }
                                        }))}
                                        placeholder="DD/MM/YYYY HH:MM"
                                        className="mt-1"
                                      />
                                    </div>
                                    <div>
                                      <Label className="text-xs">Correct Description</Label>
                                      <Textarea
                                        value={editedData[originalIndex]?.description || ''}
                                        onChange={(e) => setEditedData(prev => ({
                                          ...prev,
                                          [originalIndex]: { ...prev[originalIndex], description: e.target.value }
                                        }))}
                                        className="mt-1"
                                        rows={2}
                                      />
                                    </div>
                                    <div className="flex gap-2">
                                      <Button 
                                        size="sm" 
                                        onClick={() => handleSaveEvent(originalIndex)}
                                      >
                                        <Save className="w-3 h-3 mr-1" />
                                        Save Correction
                                      </Button>
                                      <Button 
                                        size="sm" 
                                        variant="outline"
                                        onClick={() => handleCancelEdit(originalIndex)}
                                      >
                                        <X className="w-3 h-3 mr-1" />
                                        Cancel
                                      </Button>
                                    </div>
                                  </div>
                                ) : (
                                  <div>
                                    <div className="bg-gray-50 p-3 rounded mb-2">
                                      <Label className="text-xs text-muted-foreground">Original Extracted Text:</Label>
                                      <p className="text-sm font-mono">{event.extracted_text || event.description}</p>
                                    </div>
                                    <div className="flex items-center gap-2 mb-2">
                                      <Clock className="w-4 h-4 text-muted-foreground" />
                                      <span className="font-medium">{event.start_time || "Time not extracted"}</span>
                                    </div>
                                    <p className="text-sm text-muted-foreground">{event.description}</p>
                                    <p className="text-xs text-amber-600 mt-2">
                                      <AlertTriangle className="w-3 h-3 inline mr-1" />
                                      Please verify and correct if needed
                                    </p>
                                  </div>
                                )}
                              </div>
                              
                              {!editingEvents[originalIndex] && (
                                <Button
                                  variant="default"
                                  size="sm"
                                  onClick={() => handleEditEvent(originalIndex)}
                                  className="bg-amber-500 hover:bg-amber-600"
                                >
                                  <Edit className="w-4 h-4 mr-1" />
                                  Edit
                                </Button>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

      

"use client"

import React from "react"
import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DocumentAnalysis, DocumentSection, DocumentMetadata, UploadedFile } from "@/types/analysis"
import {
  ArrowLeft,
  Upload,
  FileText,
  Download,
  Eye,
  Trash2,
  CheckCircle,
  AlertCircle,
  Ship,
  Anchor,
  Navigation,
  FileCheck,
  FileX,
  Loader2,
  AlertTriangle,
} from "lucide-react"
import Link from "next/link"
import { SoFViewer } from "@/components/sof-viewer"

interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  status: "uploading" | "processing" | "completed" | "error"
  progress: number
  uploadedAt: Date
  extractedText?: string
  keyHighlights?: string[]
  analysis?: DocumentAnalysis | SoFAnalysis
  isSOF?: boolean
  confidence?: number
}

interface DocumentAnalysis {
  document_type: string
  confidence: number
  summary: string
  sections: Array<{
    id: string
    title: string
    content: string
    importance: "high" | "medium" | "low"
    keywords: string[]
  }>
  key_findings: string[]
  entities: Array<{
    type: string
    value: string
    confidence: number
    context?: string
    category?: string
  }>
  metadata: {
    pages: number
    word_count: number
    processed_at: string
    language?: string
  }
  tables?: Array<{
    id: string
    title: string
    headers: string[]
    rows: Array<{ cells: string[] }>
    description?: string
  }>
}

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
}

interface SoFAnalysis {
  document_type: string
  sof_data: SoFData
  export_formats: string[]
  editable_events: SoFEvent[]
}

export default function DocumentUpload() {
  const fileInputRef = React.useRef<HTMLInputElement>(null)
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState<UploadedFile | null>(null)
  const [analysis, setAnalysis] = useState<DocumentAnalysis | null>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    const droppedFiles = Array.from(e.dataTransfer.files)
    handleFileUpload(droppedFiles)
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      handleFileUpload(selectedFiles)
    }
  }

  const handleFileUpload = async (fileList: File[]) => {
    for (const file of fileList) {
      const newFile: UploadedFile = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        type: file.type,
        status: "uploading",
        progress: 0,
        uploadedAt: new Date(),
      }

      setFiles((prev) => [...prev, newFile])

      try {
        // Upload and process the file
        await processFileWithAPI(newFile.id, file)
      } catch (error) {
        console.error("File upload failed:", error)
        setFiles(prev => 
          prev.map(f => 
            f.id === newFile.id 
              ? { ...f, status: "error", progress: 0 }
              : f
          )
        )
      }
    }
  }

  const processFileWithAPI = async (fileId: string, file: File) => {
    try {
      // Update to uploading
      setFiles(prev => 
        prev.map(f => 
          f.id === fileId 
            ? { ...f, status: "uploading", progress: 30 }
            : f
        )
      )

      const formData = new FormData()
      formData.append("file", file)

      // Update to processing
      setFiles(prev => 
        prev.map(f => 
          f.id === fileId 
            ? { ...f, status: "processing", progress: 60 }
            : f
        )
      )

      const response = await fetch("http://localhost:8000/upload-document", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()
      
      // Determine if this is a SOF document
      const isSOF = result.analysis?.document_analysis?.document_type === "Statement of Facts"
      const confidence = result.analysis?.confidence || 0.7

      // Extract text and analysis
      const extractedText = result.analysis?.extracted_text || ""
      const documentAnalysis = result.analysis?.document_analysis || {}

      // Create key highlights based on document type
      let keyHighlights: string[] = []
      
      if (isSOF && documentAnalysis.sof_data) {
        keyHighlights = [
          `${documentAnalysis.sof_data.total_events} events extracted`,
          `Vessel: ${documentAnalysis.sof_data.vessel_name || 'Unknown'}`,
          `Port: ${documentAnalysis.sof_data.port || 'Unknown'}`,
          `Document confidence: ${(documentAnalysis.sof_data.document_confidence * 100).toFixed(1)}%`,
        ]
        
        if (documentAnalysis.sof_data.low_confidence_count > 0) {
          keyHighlights.push(`⚠️ ${documentAnalysis.sof_data.low_confidence_count} events need review`)
        }
        
        if (documentAnalysis.sof_data.total_laytime_hours) {
          keyHighlights.push(`Total laytime: ${documentAnalysis.sof_data.total_laytime_hours.toFixed(1)} hours`)
        }
      } else {
        // General document highlights
        keyHighlights = [
          `Document type: ${documentAnalysis.document_type || 'General Maritime'}`,
          `Confidence: ${(confidence * 100).toFixed(1)}%`,
          `Text length: ${extractedText.length} characters`,
          ...(documentAnalysis.key_findings || []).slice(0, 3)
        ]
      }

      // Update file with results
      setFiles(prev => 
        prev.map(f => 
          f.id === fileId 
            ? { 
                ...f, 
                status: "completed", 
                progress: 100,
                extractedText,
                keyHighlights,
                analysis: documentAnalysis,
                isSOF,
                confidence
              }
            : f
        )
      )

    } catch (error) {
      throw error
    }
  }

  const handleAnalyze = (file: UploadedFile) => {
    setSelectedFile(file);
    
    // If it's a Statement of Facts document
    if (file.isSOF && file.analysis) {
      setSelectedFile(file);
      setAnalysis(file.analysis as any);
      return;
    }
    
    // For general maritime documents
    if (file.analysis && 'document_type' in file.analysis) {
      setAnalysis(file.analysis as DocumentAnalysis);
    } else {
      // In case the analysis is missing or invalid, create a properly structured analysis
      const analysis: DocumentAnalysis = {
        document_type: file.analysis?.document_type || 'General Maritime Document',
        confidence: file.analysis?.confidence || file.confidence || 0.7,
        sections: file.analysis?.sections || [
          {
            id: 'content',
            title: 'Document Content',
            content: file.extractedText || 'No content available',
            confidence: file.confidence || 0.7
          }
        ],
        key_findings: file.analysis?.key_findings || file.keyHighlights || [],
        metadata: {
          ...file.analysis?.metadata || {},
          word_count: file.extractedText?.split(/\s+/).length || 0,
          processed_at: file.analysis?.metadata?.processed_at || file.uploadedAt.toISOString(),
          vessels: file.analysis?.metadata?.vessels || [],
          ports: file.analysis?.metadata?.ports || [],
          dates: file.analysis?.metadata?.dates || [],
          amounts: file.analysis?.metadata?.amounts || [],
          times: file.analysis?.metadata?.times || []
        }
      };
      setAnalysis(analysis);
    }
  }

  const handleDeleteFile = (fileId: string) => {
    setFiles((prev) => prev.filter((file) => file.id !== fileId))
    if (selectedFile?.id === fileId) {
      setSelectedFile(null)
      setAnalysis(null)
    }
  }

  const handleViewFile = (file: UploadedFile) => {
    handleAnalyze(file)
  }

  const handleDownload = (format: "json" | "csv") => {
    if (!selectedFile) return

    const data = {
      fileName: selectedFile.name,
      analysis: analysis,
      extractedText: selectedFile.extractedText,
      keyHighlights: selectedFile.keyHighlights,
      processedAt: new Date().toISOString(),
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${selectedFile.name.split(".")[0]}_analysis.${format}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const getStatusIcon = (status: UploadedFile["status"]) => {
    switch (status) {
      case "uploading":
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
      case "processing":
        return <Ship className="w-4 h-4 ship-loading text-orange-500" />
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-500" />
    }
  }

  const getStatusText = (status: UploadedFile["status"]) => {
    switch (status) {
      case "uploading":
        return "Uploading..."
      case "processing":
        return "Processing with AI..."
      case "completed":
        return "Analysis Complete"
      case "error":
        return "Processing Failed"
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
                <Upload className="w-5 h-5 text-primary" />
                <h1 className="text-xl font-bold font-montserrat">Document Analysis</h1>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                AI Processing Online
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Upload Area & File List */}
          <div className="lg:col-span-1 space-y-6">
            {/* Upload Zone */}
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg font-montserrat">Upload Documents</CardTitle>
                <CardDescription>Drag & drop PDF or Word documents for AI analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    isDragOver ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
                  }`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  style={{ cursor: "pointer" }}
                >
                  <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-sm font-medium mb-2">Drop files here or click to browse</p>
                  <p className="text-xs text-muted-foreground mb-4">Supports PDF, DOC, DOCX up to 10MB</p>
                  <input
                    type="file"
                    multiple
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileSelect}
                    className="hidden"
                    ref={fileInputRef}
                  />
                  <Button variant="outline" className="cursor-pointer bg-transparent" onClick={e => { e.stopPropagation(); fileInputRef.current?.click(); }}>
                    Select Files
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* File List */}
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg font-montserrat flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Uploaded Files ({files.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-[400px]">
                  <div className="space-y-2 p-4">
                    {files.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <FileX className="w-8 h-8 mx-auto mb-2" />
                        <p className="text-sm">No files uploaded yet</p>
                      </div>
                    ) : (
                      files.map((file) => (
                        <div key={file.id} className="border border-border/50 rounded-lg p-3 space-y-2">
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <p className="text-sm font-medium truncate">{file.name}</p>
                                {file.isSOF && (
                                  <Badge variant="default" className="text-xs bg-blue-500">
                                    <Ship className="w-3 h-3 mr-1" />
                                    SOF
                                  </Badge>
                                )}
                                {file.isSOF && file.analysis && 'sof_data' in file.analysis && file.analysis.sof_data.low_confidence_count > 0 && (
                                  <Badge variant="destructive" className="text-xs">
                                    <AlertTriangle className="w-3 h-3 mr-1" />
                                    {file.analysis.sof_data.low_confidence_count} need review
                                  </Badge>
                                )}
                              </div>
                              <p className="text-xs text-muted-foreground">
                                {formatFileSize(file.size)} • {file.uploadedAt.toLocaleTimeString()}
                                {file.confidence && ` • ${(file.confidence * 100).toFixed(0)}% confidence`}
                              </p>
                            </div>
                            <div className="flex items-center gap-1 ml-2">
                              {file.status === "completed" && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 p-0"
                                  onClick={() => handleViewFile(file)}
                                >
                                  <Eye className="w-3 h-3" />
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0 text-red-500 hover:text-red-700"
                                onClick={() => handleDeleteFile(file.id)}
                              >
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {getStatusIcon(file.status)}
                            <span className="text-xs text-muted-foreground flex-1">{getStatusText(file.status)}</span>
                            {file.status !== "completed" && (
                              <span className="text-xs text-muted-foreground">{file.progress}%</span>
                            )}
                          </div>
                          {file.status !== "completed" && <Progress value={file.progress} className="h-1" />}
                        </div>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>

          {/* Analysis Results */}
          <div className="lg:col-span-2">
            {selectedFile ? (
              selectedFile.isSOF && selectedFile.analysis ? (
                <SoFViewer 
                  analysis={selectedFile.analysis as SoFAnalysis} 
                  filename={selectedFile.name}
                  onUpdate={(updatedAnalysis) => {
                    setFiles(prev => 
                      prev.map(f => 
                        f.id === selectedFile.id 
                          ? { ...f, analysis: updatedAnalysis }
                          : f
                      )
                    )
                    setAnalysis(updatedAnalysis as any)
                  }}
                />
              ) : (
                <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg font-montserrat flex items-center gap-2">
                          <FileCheck className="w-5 h-5 text-green-500" />
                          {selectedFile.name}
                        </CardTitle>
                        <CardDescription>
                          {(selectedFile.analysis && 'document_type' in selectedFile.analysis 
                            ? selectedFile.analysis.document_type 
                            : 'General Document')} •{" "}
                          {selectedFile.confidence && Math.round(selectedFile.confidence * 100)}%
                          confidence
                        </CardDescription>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" onClick={() => handleDownload("json")}>
                          <Download className="w-4 h-4 mr-2" />
                          JSON
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleDownload("csv")}>
                          <Download className="w-4 h-4 mr-2" />
                          CSV
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                  <Tabs defaultValue="overview" className="w-full">
                    <TabsList className="grid w-full grid-cols-5">
                      <TabsTrigger value="overview">Overview</TabsTrigger>
                      <TabsTrigger value="sections">Sections</TabsTrigger>
                      <TabsTrigger value="entities">Entities</TabsTrigger>
                      <TabsTrigger value="tables">Tables</TabsTrigger>
                      <TabsTrigger value="text">Full Text</TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview" className="space-y-4">
                      {analysis && (
                        <>
                          <div>
                            <h4 className="font-medium mb-2">Summary</h4>
                            <p className="text-sm text-muted-foreground">{analysis.summary}</p>
                          </div>
                          <div>
                            <h4 className="font-medium mb-2">Key Findings</h4>
                            <div className="space-y-2">
                              {analysis.key_findings.map((finding, index) => (
                                <div key={index} className="flex items-center gap-2">
                                  <Anchor className="w-3 h-3 text-primary" />
                                  <span className="text-sm">{finding}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                          <div>
                            <h4 className="font-medium mb-2">Document Metadata</h4>
                            <div className="grid grid-cols-2 gap-4">
                              <div className="text-sm">
                                <p className="text-muted-foreground">Pages</p>
                                <p className="font-medium">{analysis.metadata.pages}</p>
                              </div>
                              <div className="text-sm">
                                <p className="text-muted-foreground">Word Count</p>
                                <p className="font-medium">{analysis.metadata.word_count}</p>
                              </div>
                              {analysis.metadata.language && (
                                <div className="text-sm">
                                  <p className="text-muted-foreground">Language</p>
                                  <p className="font-medium">{analysis.metadata.language}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        </>
                      )}
                    </TabsContent>

                    <TabsContent value="sections" className="space-y-4">
                      {/* Document Type and Confidence */}
                      {analysis && (
                        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
                          <CardHeader>
                            <CardTitle className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <FileText className="w-5 h-5" />
                                {analysis.document_type}
                              </div>
                              <Badge variant={analysis.confidence > 0.8 ? "success" : "warning"}>
                                {Math.round(analysis.confidence * 100)}% Confidence
                              </Badge>
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-2 gap-4 mb-4">
                              {analysis.metadata?.vessels?.length > 0 && (
                                <div>
                                  <h4 className="font-semibold mb-1">Vessels</h4>
                                  <ul className="list-disc list-inside text-sm">
                                    {analysis.metadata.vessels.map((vessel: string, i: number) => (
                                      <li key={i}>{vessel}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {analysis.metadata?.ports?.length > 0 && (
                                <div>
                                  <h4 className="font-semibold mb-1">Ports</h4>
                                  <ul className="list-disc list-inside text-sm">
                                    {analysis.metadata.ports.map((port: string, i: number) => (
                                      <li key={i}>{port}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {analysis.metadata?.dates?.length > 0 && (
                                <div>
                                  <h4 className="font-semibold mb-1">Key Dates</h4>
                                  <ul className="list-disc list-inside text-sm">
                                    {analysis.metadata.dates.map((date: string, i: number) => (
                                      <li key={i}>{date}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {analysis.metadata?.amounts?.length > 0 && (
                                <div>
                                  <h4 className="font-semibold mb-1">Financial Data</h4>
                                  <ul className="list-disc list-inside text-sm">
                                    {analysis.metadata.amounts.map((amount: string, i: number) => (
                                      <li key={i}>{amount}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {/* Document Sections */}
                      {analysis?.sections?.map((section) => (
                        <Card key={section.id} className="border-border/50 bg-card/80 backdrop-blur-sm">
                          <CardHeader>
                            <CardTitle className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <FileText className="w-5 h-5" />
                                {section.title}
                              </div>
                              <Badge variant={section.confidence > 0.8 ? "success" : "warning"}>
                                {Math.round(section.confidence * 100)}% Confident
                              </Badge>
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <ScrollArea className="h-[200px]">
                              <div className="space-y-4 whitespace-pre-wrap">
                                {section.content}
                              </div>
                            </ScrollArea>
                          </CardContent>
                        </Card>
                      ))}
                    </TabsContent>

                    <TabsContent value="entities" className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {analysis?.entities.map((entity, index) => (
                          <div key={index} className="border border-border/50 rounded-lg p-3">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium text-sm">
                                {entity.category ? `${entity.category} - ${entity.type}` : entity.type}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {Math.round(entity.confidence * 100)}%
                              </span>
                            </div>
                            <p className="text-sm text-primary mb-1">{entity.value}</p>
                            {entity.context && (
                              <p className="text-xs text-muted-foreground">{entity.context}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </TabsContent>

                    <TabsContent value="tables" className="space-y-4">
                      {analysis?.tables && analysis.tables.length > 0 ? (
                        analysis.tables.map((table) => (
                          <div key={table.id} className="border border-border/50 rounded-lg p-3">
                            <h5 className="font-medium text-sm mb-2">{table.title}</h5>
                            <div className="overflow-x-auto">
                              <table className="min-w-full divide-y divide-border">
                                <thead>
                                  <tr>
                                    {table.headers.map((header, idx) => (
                                      <th key={idx} className="py-2 px-3 text-left text-xs font-medium">
                                        {header}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                  {table.rows.map((row, idx) => (
                                    <tr key={idx}>
                                      {row.cells.map((cell, cellIdx) => (
                                        <td key={cellIdx} className="py-2 px-3 text-xs">
                                          {cell}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                            {table.description && (
                              <p className="text-xs text-muted-foreground mt-2">{table.description}</p>
                            )}
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-8 text-sm text-muted-foreground">
                          No tables found in this document
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="text">
                      <ScrollArea className="h-[400px]">
                        <div className="text-sm leading-relaxed whitespace-pre-wrap">
                          {selectedFile.extractedText || "No text extracted yet."}
                        </div>
                      </ScrollArea>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
              )
            ) : (
              <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
                <CardContent className="flex flex-col items-center justify-center py-16">
                  <Navigation className="w-16 h-16 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No Document Selected</h3>
                  <p className="text-sm text-muted-foreground text-center max-w-md">
                    Upload a document and click the view button to see detailed AI analysis results, extracted text, and
                    key insights.
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

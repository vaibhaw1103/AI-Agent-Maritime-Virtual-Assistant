import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import "../maritime-effects.css"
import {
  Mic,
  Send,
  ArrowLeft,
  Compass,
  Ship,
  Anchor,
  Navigation,
  Clock,
  User,
  Bot,
  Volume2,
  VolumeX,
  Loader2,
  Upload,
  X,
  FileImage,
  FileText,
} from "lucide-react"

export default function Layout({ children }) {
  return (
    <div className="wave-bg min-h-screen flex flex-col">
      <header className="glass-card border-b border-[rgba(255,255,255,0.1)] backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button variant="ghost" className="maritime-button glow-effect">
                <Ship className="w-5 h-5 mr-2 animate-float" />
                Maritime Professional Assistant
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <Badge className="maritime-badge status-pulse">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span>Maritime AI Active</span>
              </Badge>
            </div>
          </div>
        </div>
      </header>
      
      <main className="container mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  )
}

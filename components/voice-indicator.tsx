"use client"

import React from 'react'
import { Mic } from 'lucide-react'

interface VoiceIndicatorProps {
  isRecording: boolean
}

export function VoiceIndicator({ isRecording }: VoiceIndicatorProps) {
  return (
    <div className="relative">
      {isRecording && (
        <>
          <div className="absolute -inset-1 bg-red-100 rounded-full animate-pulse"></div>
          <div className="absolute -inset-2 flex items-center justify-center">
            <div className="w-full h-full bg-red-500/20 rounded-full animate-ping"></div>
          </div>
        </>
      )}
      <Mic className={`w-4 h-4 relative z-10 ${isRecording ? 'text-red-500' : 'text-muted-foreground'}`} />
    </div>
  )
}

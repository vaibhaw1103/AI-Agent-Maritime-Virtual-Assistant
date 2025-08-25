import { Loader2, Ship } from "lucide-react"

interface LoadingPageProps {
  title?: string
  subtitle?: string
}

export function LoadingPage({ title = "Maritime Assistant", subtitle = "Loading your maritime tools..." }: LoadingPageProps) {
  return (
    <div className="min-h-screen bg-background wave-pattern flex items-center justify-center">
      <div className="text-center space-y-6">
        <div className="flex items-center justify-center">
          <div className="relative">
            <Ship className="w-16 h-16 text-primary animate-bounce" />
            <Loader2 className="w-8 h-8 text-secondary absolute -bottom-2 -right-2 animate-spin" />
          </div>
        </div>
        
        <div className="space-y-2">
          <h1 className="text-2xl font-bold font-montserrat text-foreground">{title}</h1>
          <p className="text-muted-foreground">{subtitle}</p>
        </div>
        
        <div className="flex items-center justify-center space-x-2">
          <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
          <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
          <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
        </div>
      </div>
    </div>
  )
}

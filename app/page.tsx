"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { login, register, type AuthResponse as ApiAuthResponse } from "@/lib/api/client"
import Link from "next/link"
import {
  MessageSquare,
  Upload,
  Cloud,
  MapPin,
  Settings,
  Compass,
  Ship,
  Waves,
  Navigation,
  FileText,
  Zap,
  Anchor,
  User,
  Lock,
  Mail,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle2,
  Anchor as AnchorIcon,
  Globe,
  TrendingUp,
  Shield,
  Users,
  Clock,
  Award,
  Star,
} from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"

export default function MaritimeDashboard() {
  const [activeModule, setActiveModule] = useState<string | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isAuthLoading, setIsAuthLoading] = useState(true) // Add auth loading state
  const [showPassword, setShowPassword] = useState(false)
  const [alert, setAlert] = useState<{ type: 'success' | 'error', message: string } | null>(null)

  // Login form state
  const [loginData, setLoginData] = useState({
    username: '',
    password: ''
  })

  // Registration form state
  const [registerData, setRegisterData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: ''
  })

  // Additional safety fallback to prevent infinite loading
  useEffect(() => {
    const forceCompletion = setTimeout(() => {
      if (isAuthLoading) {
        console.log('🚨 Force completion of authentication check')
        setIsAuthLoading(false)
        setIsAuthenticated(false)
        setUser(null)
      }
    }, 8000) // 8 second absolute fallback

    return () => clearTimeout(forceCompletion)
  }, [isAuthLoading])

  // Check and restore authentication state on mount
  useEffect(() => {
    const checkAuthState = async () => {
      setIsAuthLoading(true)
      console.log('🔍 Starting authentication check...')
      
      // Add timeout to prevent hanging
      const timeoutId = setTimeout(() => {
        console.log('⏰ Authentication check timeout, forcing completion')
        setIsAuthLoading(false)
        setIsAuthenticated(false)
        setUser(null)
      }, 5000) // Reduced to 5 second timeout
      
      try {
        const token = localStorage.getItem('auth_token')
        const userData = localStorage.getItem('user_data')
        
        console.log('🔑 Token found:', !!token, 'User data found:', !!userData)
        
        if (token && userData) {
          // Validate token by making a call to the auth/me endpoint
          try {
            console.log('🔐 Validating token with backend...')
            const response = await fetch('http://localhost:8000/auth/me', {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              }
            })
            
            console.log('📡 Backend response status:', response.status)
            
            if (response.ok) {
              // Token is valid, restore user session
              const parsedUserData = JSON.parse(userData)
              console.log('✅ Token valid, restoring session for user:', parsedUserData.username)
              setIsAuthenticated(true)
              setUser(parsedUserData)
            } else {
              // Token is invalid, clear auth state
              console.log('❌ Token invalid, clearing auth state')
              localStorage.removeItem('auth_token')
              localStorage.removeItem('user_data')
              setIsAuthenticated(false)
              setUser(null)
            }
          } catch (authError) {
            console.error('🚨 Token validation failed:', authError)
            // If auth endpoint fails, try to parse stored data anyway
            try {
              const parsedUserData = JSON.parse(userData)
              console.log('⚠️ Auth endpoint failed, but using stored data for user:', parsedUserData.username)
              setIsAuthenticated(true)
              setUser(parsedUserData)
            } catch (parseError) {
              console.error('🚨 Failed to parse stored user data:', parseError)
              localStorage.removeItem('auth_token')
              localStorage.removeItem('user_data')
              setIsAuthenticated(false)
              setUser(null)
            }
          }
        } else {
          // No token found, user needs to authenticate
          console.log('🔓 No authentication data found, user needs to login')
          setIsAuthenticated(false)
          setUser(null)
        }
      } catch (error) {
        // Error occurred, clear auth state to be safe
        console.error('🚨 Auth check failed:', error)
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_data')
        setIsAuthenticated(false)
        setUser(null)
      } finally {
        clearTimeout(timeoutId)
        console.log('🏁 Authentication check completed, setting loading to false')
        setIsAuthLoading(false)
      }
    }

    checkAuthState()
  }, [])

  const showAlert = (type: 'success' | 'error', message: string) => {
    setAlert({ type, message })
    // Success messages stay longer, error messages shorter
    const duration = type === 'success' ? 6000 : 4000
    setTimeout(() => setAlert(null), duration)
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const data = await login({
        username: loginData.username,
        password: loginData.password,
      })

      localStorage.setItem('auth_token', data.access_token)
      localStorage.setItem('user_data', JSON.stringify(data.user_info))
      setIsAuthenticated(true)
      setUser(data.user_info)
      showAlert('success', `🚢 Welcome aboard, Captain ${data.user_info?.full_name || loginData.username}! Your maritime assistant is ready!`)
    } catch (error) {
      console.error('Login error:', error)
      const errorMessage = error instanceof Error ? error.message : 'Login failed'
      
      if (errorMessage.includes('401') || errorMessage.includes('Unauthorized')) {
        showAlert('error', '🔐 Invalid username or password. Please check your credentials and try again.')
      } else if (errorMessage.includes('400') || errorMessage.includes('Bad Request')) {
        showAlert('error', '📝 Please enter both username and password.')
      } else if (errorMessage.includes('Network') || errorMessage.includes('Failed to fetch')) {
        showAlert('error', '🌐 Cannot connect to server. Please check if the backend is running on port 8000.')
      } else if (errorMessage.includes('404')) {
        showAlert('error', '❓ User not found. Please register first or check your username.')
      } else {
        showAlert('error', '❌ Login failed. Please try again or contact support if the problem persists.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validation
    if (registerData.password !== registerData.confirmPassword) {
      showAlert('error', 'Passwords do not match')
      return
    }

    if (registerData.password.length < 8) {
      showAlert('error', 'Password must be at least 8 characters long')
      return
    }

    setIsLoading(true)

    try {
      // Step 1: Register the user
      showAlert('success', 'Creating your account...')
      
      await register({
        username: registerData.username,
        email: registerData.email,
        password: registerData.password,
        full_name: registerData.full_name
      })

      showAlert('success', 'Account created successfully! Logging you in...')

      // Step 2: Automatically log in the user after successful registration
      const loginData = await login({
        username: registerData.username,
        password: registerData.password,
      })

      // Step 3: Store the authentication data from login
      localStorage.setItem('auth_token', loginData.access_token)
      localStorage.setItem('user_data', JSON.stringify(loginData.user_info))
      setIsAuthenticated(true)
      setUser(loginData.user_info)
      
      showAlert('success', `🎉 Welcome aboard, Captain ${loginData.user_info?.full_name || registerData.username}! Your maritime assistant is ready! 🚢`)
    } catch (error) {
      console.error('Registration/Login error:', error)
      const errorMessage = error instanceof Error ? error.message : 'Registration failed'
      
      // Handle specific registration errors
      if (errorMessage.includes('400') || errorMessage.includes('Bad Request')) {
        showAlert('error', '❌ Username or email already exists. Please choose different credentials.')
      } else if (errorMessage.includes('422') || errorMessage.includes('validation')) {
        showAlert('error', '❌ Please check your input. Make sure email is valid and all fields are filled correctly.')
      } else if (errorMessage.includes('Network') || errorMessage.includes('Failed to fetch')) {
        showAlert('error', '🌐 Cannot connect to server. Please check if the backend is running on port 8000.')
      } else if (errorMessage.includes('401') || errorMessage.includes('Unauthorized')) {
        // Registration succeeded but login failed - show manual login option
        showAlert('error', '✅ Account created successfully! However, auto-login failed. Please log in manually with your new credentials.')
      } else {
        showAlert('error', '❌ Registration failed. Please try again or contact support if the problem persists.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')
    setIsAuthenticated(false)
    setUser(null)
    showAlert('success', 'Logged out successfully')
  }

  // Show loading screen while checking authentication
  if (isAuthLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-slate-900 to-blue-800 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-cyan-400 border-t-transparent mx-auto mb-4"></div>
          <h2 className="text-2xl font-semibold text-white mb-2">Maritime Assistant</h2>
          <p className="text-cyan-200 mb-4">Checking authentication...</p>
          <p className="text-cyan-300 text-sm mb-6">This may take a few moments</p>
          
          {/* Manual retry button */}
          <button 
            onClick={() => {
              console.log('🔄 Manual retry clicked')
              setIsAuthLoading(false)
              setIsAuthenticated(false)
              setUser(null)
            }}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors"
          >
            Skip Authentication Check
          </button>
        </div>
      </div>
    )
  }

  // If user is authenticated, show the main dashboard
  if (isAuthenticated && user) {
    return <MainDashboard user={user} onLogout={handleLogout} />
  }

  // Show beautiful login/registration landing page
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-slate-900 to-blue-800 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-cyan-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-500 rounded-full mix-blend-multiply filter blur-xl opacity-10 animate-pulse"></div>
        
        {/* Floating Icons */}
        <div className="absolute top-20 left-20 text-white/10 animate-float">
          <Ship className="w-8 h-8" />
        </div>
        <div className="absolute top-40 right-32 text-white/10 animate-float-delay">
          <Anchor className="w-6 h-6" />
        </div>
        <div className="absolute bottom-32 left-1/4 text-white/10 animate-float">
          <Compass className="w-7 h-7" />
        </div>
        <div className="absolute bottom-20 right-20 text-white/10 animate-float-delay">
          <Waves className="w-8 h-8" />
        </div>
      </div>

      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Header */}
        <header className="p-6">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-400 to-cyan-400 rounded-xl flex items-center justify-center shadow-lg">
                  <Ship className="w-7 h-7 text-white" />
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white animate-pulse"></div>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Maritime Assistant</h1>
                <p className="text-blue-200 text-sm">Professional AI-Powered Maritime Platform</p>
              </div>
            </div>
            <ThemeToggle />
          </div>
        </header>

        <main className="flex-1 flex items-center justify-center p-6">
          <div className="max-w-6xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Side - Hero Content */}
            <div className="text-center lg:text-left space-y-8">
              <div className="space-y-4">
                <Badge className="bg-blue-500/20 text-blue-100 border-blue-400/30 px-4 py-2">
                  🚢 Professional Maritime Intelligence
                </Badge>
                <h1 className="text-5xl lg:text-6xl font-bold text-white leading-tight">
                  Navigate the Future with
                  <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                    {" "}AI Power
                  </span>
                </h1>
                <p className="text-xl text-blue-100 leading-relaxed">
                  Transform your maritime operations with intelligent weather insights, 
                  AI-powered consultation, and professional-grade analytics trusted by 
                  shipping professionals worldwide.
                </p>
              </div>

              {/* Feature Highlights */}
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center space-x-3 text-blue-100">
                  <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                    <Globe className="w-5 h-5 text-blue-400" />
                  </div>
                  <div>
                    <p className="font-semibold">Global Coverage</p>
                    <p className="text-sm text-blue-200">365+ Ports Worldwide</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3 text-blue-100">
                  <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                    <Zap className="w-5 h-5 text-yellow-400" />
                  </div>
                  <div>
                    <p className="font-semibold">Lightning Fast</p>
                    <p className="text-sm text-blue-200">0.13s Response Time</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3 text-blue-100">
                  <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                    <Shield className="w-5 h-5 text-green-400" />
                  </div>
                  <div>
                    <p className="font-semibold">Secure Platform</p>
                    <p className="text-sm text-blue-200">Enterprise-Grade</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3 text-blue-100">
                  <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                    <Award className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <p className="font-semibold">AI Powered</p>
                    <p className="text-sm text-blue-200">95% Confidence</p>
                  </div>
                </div>
              </div>

              {/* Stats */}
              <div className="flex items-center space-x-8">
                <div className="text-center">
                  <div className="text-3xl font-bold text-white">100%</div>
                  <div className="text-sm text-blue-200">Integration Success</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-white">365+</div>
                  <div className="text-sm text-blue-200">Global Ports</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-white">24/7</div>
                  <div className="text-sm text-blue-200">Availability</div>
                </div>
              </div>
            </div>

            {/* Right Side - Authentication */}
            <div className="relative">
              {alert && (
                <Alert className={`mb-6 ${alert.type === 'success' ? 'border-green-500 bg-green-900/50 text-green-100' : 'border-red-500 bg-red-900/50 text-red-100'}`}>
                  {alert.type === 'success' ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : (
                    <AlertCircle className="h-4 w-4" />
                  )}
                  <AlertDescription>
                    {alert.message}
                  </AlertDescription>
                </Alert>
              )}

              <Card className="backdrop-blur-lg bg-white/10 border-white/20 shadow-2xl">
                <CardHeader className="text-center pb-2">
                  <div className="w-16 h-16 bg-gradient-to-r from-blue-400 to-cyan-400 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                    <Ship className="w-8 h-8 text-white" />
                  </div>
                  <CardTitle className="text-2xl text-white">Welcome Aboard</CardTitle>
                  <CardDescription className="text-blue-200">
                    Access your maritime intelligence platform
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="login" className="w-full">
                    <TabsList className="grid w-full grid-cols-2 bg-white/10">
                      <TabsTrigger value="login" className="data-[state=active]:bg-blue-500 data-[state=active]:text-white">Login</TabsTrigger>
                      <TabsTrigger value="register" className="data-[state=active]:bg-blue-500 data-[state=active]:text-white">Register</TabsTrigger>
                    </TabsList>

                    <TabsContent value="login" className="space-y-4">
                      <form onSubmit={handleLogin} className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="login-username" className="text-blue-100">Username</Label>
                          <div className="relative">
                            <User className="absolute left-3 top-3 h-4 w-4 text-blue-300" />
                            <Input
                              id="login-username"
                              type="text"
                              placeholder="Enter your username"
                              className="pl-10 bg-white/10 border-white/20 text-white placeholder:text-blue-300 focus:border-blue-400"
                              value={loginData.username}
                              onChange={(e) => setLoginData({...loginData, username: e.target.value})}
                              required
                            />
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="login-password" className="text-blue-100">Password</Label>
                          <div className="relative">
                            <Lock className="absolute left-3 top-3 h-4 w-4 text-blue-300" />
                            <Input
                              id="login-password"
                              type={showPassword ? "text" : "password"}
                              placeholder="Enter your password"
                              className="pl-10 pr-10 bg-white/10 border-white/20 text-white placeholder:text-blue-300 focus:border-blue-400"
                              value={loginData.password}
                              onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                              required
                            />
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent text-blue-300 hover:text-blue-100"
                              onClick={() => setShowPassword(!showPassword)}
                            >
                              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </Button>
                          </div>
                        </div>

                        <Button 
                          type="submit" 
                          className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold py-3 shadow-lg"
                          disabled={isLoading}
                        >
                          {isLoading ? 'Signing in...' : 'Set Sail 🚢'}
                        </Button>
                      </form>
                    </TabsContent>

                    <TabsContent value="register" className="space-y-4">
                      <form onSubmit={handleRegister} className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="register-fullname" className="text-blue-100">Full Name</Label>
                          <div className="relative">
                            <User className="absolute left-3 top-3 h-4 w-4 text-blue-300" />
                            <Input
                              id="register-fullname"
                              type="text"
                              placeholder="Captain John Smith"
                              className="pl-10 bg-white/10 border-white/20 text-white placeholder:text-blue-300 focus:border-blue-400"
                              value={registerData.full_name}
                              onChange={(e) => setRegisterData({...registerData, full_name: e.target.value})}
                              required
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="register-username" className="text-blue-100">Username</Label>
                            <div className="relative">
                              <User className="absolute left-3 top-3 h-4 w-4 text-blue-300" />
                              <Input
                                id="register-username"
                                type="text"
                                placeholder="captain_smith"
                                className="pl-10 bg-white/10 border-white/20 text-white placeholder:text-blue-300 focus:border-blue-400"
                                value={registerData.username}
                                onChange={(e) => setRegisterData({...registerData, username: e.target.value})}
                                required
                              />
                            </div>
                          </div>

                          <div className="space-y-2">
                            <Label htmlFor="register-email" className="text-blue-100">Email</Label>
                            <div className="relative">
                              <Mail className="absolute left-3 top-3 h-4 w-4 text-blue-300" />
                              <Input
                                id="register-email"
                                type="email"
                                placeholder="captain@ship.com"
                                className="pl-10 bg-white/10 border-white/20 text-white placeholder:text-blue-300 focus:border-blue-400"
                                value={registerData.email}
                                onChange={(e) => setRegisterData({...registerData, email: e.target.value})}
                                required
                              />
                            </div>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="register-password" className="text-blue-100">Password</Label>
                          <div className="relative">
                            <Lock className="absolute left-3 top-3 h-4 w-4 text-blue-300" />
                            <Input
                              id="register-password"
                              type={showPassword ? "text" : "password"}
                              placeholder="Enter strong password"
                              className="pl-10 pr-10 bg-white/10 border-white/20 text-white placeholder:text-blue-300 focus:border-blue-400"
                              value={registerData.password}
                              onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
                              required
                            />
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent text-blue-300 hover:text-blue-100"
                              onClick={() => setShowPassword(!showPassword)}
                            >
                              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </Button>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="register-confirm" className="text-blue-100">Confirm Password</Label>
                          <div className="relative">
                            <Lock className="absolute left-3 top-3 h-4 w-4 text-blue-300" />
                            <Input
                              id="register-confirm"
                              type="password"
                              placeholder="Confirm your password"
                              className="pl-10 bg-white/10 border-white/20 text-white placeholder:text-blue-300 focus:border-blue-400"
                              value={registerData.confirmPassword}
                              onChange={(e) => setRegisterData({...registerData, confirmPassword: e.target.value})}
                              required
                            />
                          </div>
                        </div>

                        <Button 
                          type="submit" 
                          className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-semibold py-3 shadow-lg"
                          disabled={isLoading}
                        >
                          {isLoading ? 'Creating Account...' : 'Join the Fleet 🌊'}
                        </Button>
                      </form>
                    </TabsContent>
                  </Tabs>

                  <div className="mt-6 text-center">
                    <p className="text-sm text-blue-200">
                      🔒 Secure • 🚢 Professional • 🌊 Trusted by Maritime Leaders
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="p-6 text-center text-blue-200">
          <div className="max-w-4xl mx-auto">
            <div className="flex justify-center items-center space-x-8 mb-4">
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4" />
                <span className="text-sm">24/7 Available</span>
              </div>
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4" />
                <span className="text-sm">Enterprise Security</span>
              </div>
              <div className="flex items-center space-x-2">
                <Globe className="w-4 h-4" />
                <span className="text-sm">Global Coverage</span>
              </div>
            </div>
            <p className="text-sm">
              © 2025 Maritime Assistant. Navigating the future of maritime intelligence.
            </p>
          </div>
        </footer>
      </div>
    </div>
  )
}

// Main Dashboard Component (loads after successful authentication)
function MainDashboard({ user, onLogout }: { user: any, onLogout: () => void }) {
  const [activeModule, setActiveModule] = useState<string | null>(null)

  const modules = [
    {
      id: "chat",
      title: "AI Chat Assistant",
      description: "Ask questions about laytime, weather, distances, or CP clauses",
      icon: MessageSquare,
      color: "bg-primary",
      features: ["Voice & Text Input", "Maritime Knowledge", "Query History"],
    },
    {
      id: "documents",
      title: "Document Analysis",
      description: "Upload and analyze PDF/Word documents with AI insights",
      icon: Upload,
      color: "bg-secondary",
      features: ["Drag & Drop Upload", "Text Extraction", "Key Highlights"],
    },
    {
      id: "recommendations",
      title: "Smart Recommendations",
      description: "AI-suggested actions based on your current voyage stage",
      icon: Zap,
      color: "bg-chart-1",
      features: ["Voyage Insights", "Action Items", "Document Suggestions"],
    },
    {
      id: "weather",
      title: "Weather & Distance",
      description: "Live weather data, vessel tracking, and route optimization",
      icon: Cloud,
      color: "bg-accent",
      features: ["Live Weather", "Vessel Positions", "Route Planning"],
    },
  ]

  const quickStats = [
    { label: "Active Vessels", value: "247", icon: Ship },
    { label: "Weather Alerts", value: "3", icon: Waves },
    { label: "Documents Processed", value: "1,429", icon: FileText },
    { label: "Queries Resolved", value: "8,756", icon: MessageSquare },
  ]

  return (
    <div className="min-h-screen bg-background wave-pattern">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg maritime-gradient">
                <Compass className="w-6 h-6 text-white wave-animation" />
              </div>
              <div>
                <h1 className="text-2xl font-black font-montserrat text-foreground">Maritime Assistant</h1>
                <p className="text-sm text-muted-foreground">AI-Powered Maritime Intelligence</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="secondary" className="gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                System Online
              </Badge>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={onLogout}
                className="text-red-500 hover:text-red-600"
              >
                Logout
              </Button>
              <ThemeToggle />
              <Link href="/settings">
                <Button variant="outline" size="sm">
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {quickStats.map((stat, index) => (
            <Card key={index} className="border-border/50 bg-card/80 backdrop-blur-sm">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                    <p className="text-2xl font-bold font-montserrat text-foreground">{stat.value}</p>
                  </div>
                  <stat.icon className="w-8 h-8 text-primary/60" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Modules */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {modules.map((module) => (
            <Card
              key={module.id}
              className={`border-border/50 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg cursor-pointer ${
                activeModule === module.id ? "ring-2 ring-primary/50" : ""
              }`}
              onClick={() => setActiveModule(activeModule === module.id ? null : module.id)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${module.color} text-white`}>
                    <module.icon className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <CardTitle className="font-montserrat text-lg">{module.title}</CardTitle>
                    <CardDescription className="text-sm">{module.description}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="flex flex-wrap gap-2 mb-4">
                  {module.features.map((feature, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {feature}
                    </Badge>
                  ))}
                </div>
                {module.id === "chat" ? (
                  <Link href="/chat">
                    <Button className="w-full">Launch Chat Assistant</Button>
                  </Link>
                ) : module.id === "documents" ? (
                  <Link href="/documents">
                    <Button className="w-full">Launch Document Analysis</Button>
                  </Link>
                ) : module.id === "weather" ? (
                  <Link href="/weather">
                    <Button className="w-full">Launch Weather & Distance</Button>
                  </Link>
                ) : module.id === "ports" ? (
                  <Link href="/ports">
                    <Button className="w-full">Launch Ports Database</Button>
                  </Link>
                ) : module.id === "recommendations" ? (
                  <Link href="/recommendations">
                    <Button className="w-full">Launch Smart Recommendations</Button>
                  </Link>
                ) : (
                  <Button className="w-full" variant={activeModule === module.id ? "default" : "outline"}>
                    {activeModule === module.id ? "Launch Module" : "Select Module"}
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Quick Actions */}
        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="font-montserrat flex items-center gap-2">
              <Navigation className="w-5 h-5 text-primary" />
              Quick Actions
            </CardTitle>
            <CardDescription>Common maritime tasks and shortcuts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button variant="outline" className="h-auto p-4 flex flex-col gap-2 bg-transparent">
                <MapPin className="w-6 h-6 text-secondary" />
                <span className="font-medium">Port Information</span>
                <span className="text-xs text-muted-foreground">Get port details & restrictions</span>
              </Button>
              <Button variant="outline" className="h-auto p-4 flex flex-col gap-2 bg-transparent">
                <Waves className="w-6 h-6 text-secondary" />
                <span className="font-medium">Weather Forecast</span>
                <span className="text-xs text-muted-foreground">7-day maritime weather</span>
              </Button>
              <Button variant="outline" className="h-auto p-4 flex flex-col gap-2 bg-transparent">
                <FileText className="w-6 h-6 text-secondary" />
                <span className="font-medium">Document Templates</span>
                <span className="text-xs text-muted-foreground">Standard maritime forms</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>

      {/* Loading Animation */}
      {activeModule && (
        <div className="fixed bottom-4 right-4 bg-primary text-primary-foreground px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <Ship className="w-4 h-4 ship-loading" />
          <span className="text-sm font-medium">Loading {modules.find((m) => m.id === activeModule)?.title}...</span>
        </div>
      )}
    </div>
  )
}

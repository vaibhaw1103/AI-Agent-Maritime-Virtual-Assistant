'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Eye, EyeOff, User, Ship, Lock, Mail, AlertCircle, CheckCircle2 } from 'lucide-react'

interface AuthResponse {
  access_token?: string;
  token_type?: string;
  expires_in?: number;
  user?: {
    user_id: string;
    username: string;
    email: string;
    full_name: string;
    role: string;
    is_active: boolean;
  };
}

export default function AuthPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [alert, setAlert] = useState<{ type: 'success' | 'error', message: string } | null>(null)
  const [authToken, setAuthToken] = useState<string | null>(null)
  const [user, setUser] = useState<any>(null)

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

  const API_BASE = 'http://localhost:8000'

  const showAlert = (type: 'success' | 'error', message: string) => {
    setAlert({ type, message })
    setTimeout(() => setAlert(null), 5000)
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const formData = new URLSearchParams()
      formData.append('username', loginData.username)
      formData.append('password', loginData.password)

      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData
      })

      if (response.ok) {
        const data: AuthResponse = await response.json()
        setAuthToken(data.access_token || '')
        setUser(data.user)
        localStorage.setItem('auth_token', data.access_token || '')
        localStorage.setItem('user_data', JSON.stringify(data.user))
        
        showAlert('success', `Welcome aboard, ${data.user?.full_name || data.user?.username}! 🚢`)
      } else {
        const error = await response.json()
        showAlert('error', error.detail || 'Login failed')
      }
    } catch (error) {
      showAlert('error', 'Network error. Please check if the server is running.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    
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
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: registerData.username,
          email: registerData.email,
          password: registerData.password,
          full_name: registerData.full_name
        })
      })

      if (response.ok) {
        const data: AuthResponse = await response.json()
        setAuthToken(data.access_token || '')
        setUser(data.user)
        localStorage.setItem('auth_token', data.access_token || '')
        localStorage.setItem('user_data', JSON.stringify(data.user))
        
        showAlert('success', `Registration successful! Welcome, ${data.user?.full_name}! 🎉`)
      } else {
        const error = await response.json()
        showAlert('error', error.detail || 'Registration failed')
      }
    } catch (error) {
      showAlert('error', 'Network error. Please check if the server is running.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = () => {
    setAuthToken(null)
    setUser(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')
    showAlert('success', 'Logged out successfully')
  }

  const testChat = async () => {
    if (!authToken) {
      showAlert('error', 'Please login first')
      return
    }

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          query: 'What are the current weather conditions for Singapore port?',
          conversation_id: 'test-' + Date.now()
        })
      })

      if (response.ok) {
        const data = await response.json()
        showAlert('success', `Chat test successful! Response: ${data.response.substring(0, 100)}...`)
      } else {
        const error = await response.json()
        showAlert('error', `Chat test failed: ${error.detail}`)
      }
    } catch (error) {
      showAlert('error', 'Network error during chat test')
    }
  }

  // Check for existing token on component mount
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    const userData = localStorage.getItem('user_data')
    if (token && userData) {
      setAuthToken(token)
      setUser(JSON.parse(userData))
    }
  }, [])

  if (user && authToken) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-cyan-50">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <Ship className="h-12 w-12 mx-auto mb-4 text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-900">Maritime Assistant</h1>
              <p className="text-gray-600 mt-2">Welcome to your maritime dashboard</p>
            </div>

            {alert && (
              <Alert className={`mb-6 ${alert.type === 'success' ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'}`}>
                {alert.type === 'success' ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-red-600" />
                )}
                <AlertDescription className={alert.type === 'success' ? 'text-green-800' : 'text-red-800'}>
                  {alert.message}
                </AlertDescription>
              </Alert>
            )}

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  User Dashboard
                </CardTitle>
                <CardDescription>
                  You are successfully authenticated
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-700">Full Name</Label>
                    <p className="text-lg font-semibold">{user.full_name}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-700">Username</Label>
                    <p className="text-lg font-semibold">{user.username}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-700">Email</Label>
                    <p className="text-lg">{user.email}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-700">Role</Label>
                    <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                      {user.role.toUpperCase()}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-700">User ID</Label>
                    <p className="text-sm text-gray-600 font-mono">{user.user_id}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-700">Status</Label>
                    <Badge variant={user.is_active ? 'default' : 'destructive'}>
                      {user.is_active ? 'ACTIVE' : 'INACTIVE'}
                    </Badge>
                  </div>
                </div>

                <div className="border-t pt-4 space-y-3">
                  <h3 className="text-lg font-semibold">Quick Actions</h3>
                  <div className="flex flex-wrap gap-2">
                    <Button onClick={testChat} variant="default">
                      <Ship className="h-4 w-4 mr-2" />
                      Test AI Chat
                    </Button>
                    <Button onClick={() => window.open('/weather', '_blank')} variant="outline">
                      🌦️ Weather Dashboard
                    </Button>
                    <Button onClick={() => window.open('/chat', '_blank')} variant="outline">
                      💬 Chat Interface
                    </Button>
                    <Button onClick={handleLogout} variant="destructive">
                      <Lock className="h-4 w-4 mr-2" />
                      Logout
                    </Button>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h3 className="text-lg font-semibold mb-2">Authentication Token</h3>
                  <p className="text-xs text-gray-600 mb-2">Use this token for API requests:</p>
                  <div className="bg-gray-100 p-3 rounded-lg">
                    <code className="text-xs break-all">Bearer {authToken}</code>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-cyan-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-md mx-auto">
          <div className="text-center mb-8">
            <Ship className="h-12 w-12 mx-auto mb-4 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">Maritime Assistant</h1>
            <p className="text-gray-600 mt-2">Professional Maritime AI Platform</p>
          </div>

          {alert && (
            <Alert className={`mb-6 ${alert.type === 'success' ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'}`}>
              {alert.type === 'success' ? (
                <CheckCircle2 className="h-4 w-4 text-green-600" />
              ) : (
                <AlertCircle className="h-4 w-4 text-red-600" />
              )}
              <AlertDescription className={alert.type === 'success' ? 'text-green-800' : 'text-red-800'}>
                {alert.message}
              </AlertDescription>
            </Alert>
          )}

          <Tabs defaultValue="login" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">Login</TabsTrigger>
              <TabsTrigger value="register">Register</TabsTrigger>
            </TabsList>

            <TabsContent value="login">
              <Card>
                <CardHeader>
                  <CardTitle>Welcome Back</CardTitle>
                  <CardDescription>
                    Sign in to access your maritime dashboard
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleLogin} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="login-username">Username</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="login-username"
                          type="text"
                          placeholder="Enter your username"
                          className="pl-10"
                          value={loginData.username}
                          onChange={(e) => setLoginData({...loginData, username: e.target.value})}
                          required
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="login-password">Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="login-password"
                          type={showPassword ? "text" : "password"}
                          placeholder="Enter your password"
                          className="pl-10 pr-10"
                          value={loginData.password}
                          onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                          required
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                          onClick={() => setShowPassword(!showPassword)}
                        >
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>

                    <Button type="submit" className="w-full" disabled={isLoading}>
                      {isLoading ? 'Signing in...' : 'Sign In'}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="register">
              <Card>
                <CardHeader>
                  <CardTitle>Create Account</CardTitle>
                  <CardDescription>
                    Join the maritime professionals community
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleRegister} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="register-fullname">Full Name</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="register-fullname"
                          type="text"
                          placeholder="Captain John Smith"
                          className="pl-10"
                          value={registerData.full_name}
                          onChange={(e) => setRegisterData({...registerData, full_name: e.target.value})}
                          required
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-username">Username</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="register-username"
                          type="text"
                          placeholder="captain_smith"
                          className="pl-10"
                          value={registerData.username}
                          onChange={(e) => setRegisterData({...registerData, username: e.target.value})}
                          required
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-email">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="register-email"
                          type="email"
                          placeholder="captain@shipping.com"
                          className="pl-10"
                          value={registerData.email}
                          onChange={(e) => setRegisterData({...registerData, email: e.target.value})}
                          required
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-password">Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="register-password"
                          type={showPassword ? "text" : "password"}
                          placeholder="Enter strong password"
                          className="pl-10 pr-10"
                          value={registerData.password}
                          onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
                          required
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                          onClick={() => setShowPassword(!showPassword)}
                        >
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-confirm">Confirm Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="register-confirm"
                          type="password"
                          placeholder="Confirm your password"
                          className="pl-10"
                          value={registerData.confirmPassword}
                          onChange={(e) => setRegisterData({...registerData, confirmPassword: e.target.value})}
                          required
                        />
                      </div>
                    </div>

                    <Button type="submit" className="w-full" disabled={isLoading}>
                      {isLoading ? 'Creating Account...' : 'Create Account'}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          <div className="mt-8 text-center text-sm text-gray-600">
            <p>🚢 Secure Maritime Platform</p>
            <p className="mt-1">Professional-grade authentication & security</p>
          </div>
        </div>
      </div>
    </div>
  )
}

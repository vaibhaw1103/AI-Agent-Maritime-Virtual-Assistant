"use client"

import { useState, useRef, useEffect } from "react"
import "../maritime.css"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { useDocumentStore } from "@/lib/stores/document-store"
import { searchDocumentContent, formatTableToMarkdown, formatSectionToMarkdown, generateDocumentOverview } from "@/lib/document-utils"
import { ProcessedDocument, DocumentSection, DocumentTable, UserDocument } from "@/types/documents"
import { extractTables, identifyImportantSections, formatDocumentResponse } from "@/lib/document-processor"
import { getMaritimePrompt, getMaritimeContext, enhanceMaritimeQuery } from "@/lib/maritime/prompts"
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
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight
} from "lucide-react"
import Link from "next/link"
import { sendChatMessage, type ChatMessage, type ChatResponse } from "@/lib/api/client"
import { formatTimestamp, createTimestamp } from "@/lib/utils"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

// Client-safe timestamp component to prevent hydration mismatches
function ClientTimestamp({ date }: { date: Date }) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return <span className="text-xs opacity-70">--:--:-- --</span>
  }

  return <span className="text-xs opacity-70">{formatTimestamp(date)}</span>
}

interface Message {
  id: string
  content: string
  sender: "user" | "assistant"
  timestamp: Date
  type: "text" | "voice"
  confidence?: number
  sources?: string[]
}

interface QueryHistory {
  id: string
  query: string
  timestamp: Date
  category: "weather" | "laytime" | "distance" | "clauses" | "general"
}

// Enhanced weather detection function
function isWeatherQuery(query: string): { isWeather: boolean; portName?: string; queryType?: string } {
  const normalizedQuery = query.toLowerCase().trim();

  // Expanded weather-related keywords
  const weatherKeywords = [
    'weather', 'temperature', 'wind', 'conditions', 'forecast',
    'storm', 'rain', 'visibility', 'humidity', 'pressure', 'wave',
    'sea state', 'swell', 'tide', 'current', 'climate', 'cyclone',
    'typhoon', 'hurricane', 'gale', 'fog', 'ice', 'beaufort'
  ];

  // Maritime location keywords
  const locationKeywords = [
    'port', 'harbor', 'harbour', 'terminal', 'anchorage', 'berth',
    'jetty', 'wharf', 'pier', 'dock', 'strait', 'channel', 'bay',
    'gulf', 'sea', 'ocean', 'coast'
  ];

  // Check if query contains weather keywords
  const hasWeatherKeyword = weatherKeywords.some(keyword => normalizedQuery.includes(keyword));

  if (!hasWeatherKeyword) {
    return { isWeather: false };
  }

  // Smart port name extraction using multiple strategies
  let portName = '';
  let queryType = 'general';

  // Strategy 1: Extract port names from common patterns
  const portPatterns = [
    // Direct port mentions
    /(?:port\s+of\s+|port\s+)([a-zA-Z\s\-]+?)(?:\s+(?:weather|temperature|conditions|forecast|wind|storm)|[,.]|$)/i,
    /(?:weather|temperature|conditions|forecast|wind)\s+(?:in|at|for)\s+([a-zA-Z\s\-]+?)(?:\s+port|\s+harbor|\s+terminal|[,.]|$)/i,

    // Location-based patterns
    /(?:in|at|near|around)\s+([a-zA-Z\s\-]+?)(?:\s+port|\s+harbor|\s+terminal|[,.]|$)/i,

    // General location extraction
    /(?:weather|conditions|forecast|temperature)\s+(?:in|at|for|near)\s+([a-zA-Z\s\-]+?)(?:[,.]|$)/i,

    // Question patterns
    /(?:what|how|tell|show|check|get).*?(?:weather|temperature|conditions).*?(?:in|at|for)\s+([a-zA-Z\s\-]+?)(?:[,?.]|$)/i,
  ];

  for (const pattern of portPatterns) {
    const match = normalizedQuery.match(pattern);
    if (match && match[1]) {
      portName = match[1].trim();
      // Clean up common words that might be captured
      portName = portName.replace(/\b(the|and|or|with|for)\b/gi, '').trim();
      if (portName && portName.length > 2) {
        break;
      }
    }
  }

  // Strategy 2: Look for known major ports (you can expand this list)
  const majorPorts = [
    'singapore', 'rotterdam', 'shanghai', 'ningbo', 'guangzhou', 'busan',
    'hong kong', 'tianjin', 'los angeles', 'long beach', 'new york',
    'hamburg', 'antwerp', 'valencia', 'piraeus', 'algeciras', 'barcelona',
    'genoa', 'santos', 'dubai', 'jebel ali', 'mumbai', 'chennai',
    'yokohama', 'kobe', 'nagoya', 'tokyo', 'osaka', 'qingdao', 'dalian',
    'xiamen', 'kaohsiung', 'tanjung pelepas', 'port klang', 'colombo',
    'felixstowe', 'bremen', 'le havre', 'houston', 'savannah', 'norfolk',
    'seattle', 'tacoma', 'oakland', 'miami', 'new orleans', 'charleston'
  ];

  if (!portName) {
    for (const port of majorPorts) {
      if (normalizedQuery.includes(port)) {
        portName = port;
        break;
      }
    }
  }

  // Determine query type based on keywords
  if (normalizedQuery.includes('forecast')) queryType = 'forecast';
  else if (normalizedQuery.includes('current') || normalizedQuery.includes('now')) queryType = 'current';
  else if (normalizedQuery.includes('wind')) queryType = 'wind';
  else if (normalizedQuery.includes('wave') || normalizedQuery.includes('sea state')) queryType = 'sea_state';
  else if (normalizedQuery.includes('visibility')) queryType = 'visibility';

  return {
    isWeather: true,
    portName: portName || undefined,
    queryType
  };
}

// Enhanced maritime context function
function enhanceMaritimeResponse(response: string, query: string): string {
  const queryLower = query.toLowerCase();

  // Add maritime-specific context based on query type
  const maritimeEnhancements: { [key: string]: string } = {
    laytime: '\n\n**Maritime Context:** Remember that laytime calculations are crucial for avoiding demurrage charges. Always check your charter party for specific terms like "SHEX" (Sundays and Holidays Excluded) or "SHINC" (Sundays and Holidays Included).',
    demurrage: '\n\n**Industry Note:** Current demurrage rates vary significantly by vessel type. Capesize vessels typically charge $15,000-25,000/day, while smaller vessels may charge $5,000-10,000/day. Always verify rates in your specific charter party.',
    'charter party': '\n\n**Professional Tip:** Key clauses to review include: laytime terms, loading/discharge rates, demurrage/despatch rates, and force majeure provisions. Consider using standard forms like GENCON, NYPE, or BALTIME as starting points.',
    'bill of lading': '\n\n**Important:** The Bill of Lading serves three critical functions: receipt of cargo, evidence of contract of carriage, and document of title. Ensure all details match the charter party to avoid disputes.',
    'port state control': '\n\n**PSC Alert:** Focus areas include MARPOL compliance, ISM certification, MLC compliance, and navigation safety. Maintain updated certificates and ensure crew familiarization with procedures.',
    bunker: '\n\n**Bunker Management:** With IMO 2020 regulations, ensure compliance with 0.5% sulfur cap. Consider factors: consumption rates, bunker prices at different ports, and deviation costs for bunkering.',
    'imo 2020': '\n\n**Regulatory Update:** Vessels must use VLSFO (0.5% sulfur) or install scrubbers for HSFO use. Non-compliance can result in detention, fines, and commercial disputes.',
    freight: '\n\n**Market Intelligence:** Freight rates are influenced by vessel supply/demand, seasonal patterns, geopolitical events, and commodity prices. Monitor Baltic Dry Index for dry bulk trends.',
    'voyage calculation': '\n\n**Calculation Framework:** Consider: distance, speed, consumption, port costs, canal fees, bunker costs, and market freight rates. Add 5-10% margin for weather and operational delays.',
    etd: '\n\n**Operational Note:** ETD (Estimated Time of Departure) affects entire voyage planning. Factor in: cargo operations, documentation, pilot availability, and tidal windows.',
    eta: '\n\n**Planning Consideration:** ETA (Estimated Time of Arrival) calculations should include weather margins, speed optimization for fuel efficiency, and port congestion factors.',
    'vessel inspection': '\n\n**Inspection Readiness:** Key areas: hull condition, cargo holds cleanliness, safety equipment, certificates validity, crew competency, and environmental compliance records.',
    sof: '\n\n**SOF Documentation:** Statement of Facts is crucial for laytime calculations. Ensure accurate recording of all events, times, and any delays with proper remarks and protest letters if needed.',
    nor: '\n\n**NOR Requirements:** Notice of Readiness must be tendered at agreed location (WIBON/WIPON/ATDNSHINC). Vessel must be physically ready and legally cleared. Invalid NOR can affect laytime commencement.',
    'cargo operation': '\n\n**Efficiency Tips:** Monitor loading/discharge rates against C/P terms. Document any delays, equipment breakdowns, or weather interruptions for potential claims.',
    draft: '\n\n**Draft Survey:** Critical for bulk cargo quantity determination. Ensure proper readings at six points, correct for trim/list/density. Accuracy typically ±0.5% is acceptable.',
    'marine insurance': '\n\n**Coverage Essentials:** H&M (Hull & Machinery), P&I (Protection & Indemnity), FD&D (Freight, Demurrage & Defence), and War Risk insurance. Review deductibles and exclusions carefully.',
    ballast: '\n\n**BWM Convention:** Ballast Water Management requires D-2 standard compliance. Options include ballast water exchange or treatment systems. Maintain accurate ballast water records.',
    'port congestion': '\n\n**Mitigation Strategies:** Monitor port waiting times, consider alternative ports, negotiate congestion clauses in C/P, and maintain good communication with agents for berth prospects.'
  };

  // Find relevant enhancement
  for (const [keyword, enhancement] of Object.entries(maritimeEnhancements)) {
    if (queryLower.includes(keyword)) {
      return response + enhancement;
    }
  }

  // Add general maritime professional note if no specific enhancement found
  if (queryLower.includes('vessel') || queryLower.includes('ship') || queryLower.includes('cargo')) {
    return response + '\n\n**Maritime Professional Note:** Always verify information against your specific contracts, local regulations, and current market conditions. When in doubt, consult with your P&I Club or maritime lawyer.';
  }

  return response;
}


export default function ChatInterface() {
  // Initialize document store
  useEffect(() => {
    if (!useDocumentStore.getState().currentSession) {
      useDocumentStore.getState().initializeSession();
    }
  }, []);

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content: `🚢 **Welcome Aboard!**\n\nI'm your Maritime Virtual Assistant, equipped with expertise in:\n• Laytime & Demurrage Calculations\n• Weather & Route Planning\n• Charter Party Analysis\n• Port Operations\n• Maritime Documentation\n\nI can help you analyze maritime documents and answer specific questions about their content. Simply upload a document and ask away!\n\nHow may I assist you with your maritime operations today?`,
      sender: "assistant",
      timestamp: new Date('2025-08-16T09:00:00Z'),
      type: "text",
    },
  ])
  const [inputValue, setInputValue] = useState("")
  const [isRecording, setIsRecording] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [conversationId, setConversationId] = useState<string>("")
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadedImagePreview, setUploadedImagePreview] = useState<string | null>(null)
  const [documentAnalysis, setDocumentAnalysis] = useState<any>(null)
  const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([
    {
      id: "1",
      query: "What is the laytime calculation for bulk cargo?",
      timestamp: new Date('2025-08-16T08:00:00Z'),
      category: "laytime",
    },
    {
      id: "2",
      query: "Current weather conditions in Port of Rotterdam",
      timestamp: new Date('2025-08-16T07:00:00Z'),
      category: "weather",
    },
    {
      id: "3",
      query: "Distance between Singapore and Hamburg",
      timestamp: new Date('2025-08-16T06:00:00Z'),
      category: "distance",
    },
  ])
  const [isQueryHistoryOpen, setIsQueryHistoryOpen] = useState(true)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    // FIX: Removed setTimeout and smooth scrolling for more reliability.
    // This directly scrolls the view to the latest message after the DOM updates.
    messagesEndRef.current?.scrollIntoView();
  }, [messages]);

  const categorizeQuery = (query: string): QueryHistory["category"] => {
    const queryLower = query.toLowerCase()
    if (queryLower.includes("weather") || queryLower.includes("storm") || queryLower.includes("wind")) {
      return "weather"
    } else if (queryLower.includes("laytime") || queryLower.includes("demurrage") || queryLower.includes("time")) {
      return "laytime"
    } else if (queryLower.includes("distance") || queryLower.includes("route") || queryLower.includes("miles")) {
      return "distance"
    } else if (queryLower.includes("clause") || queryLower.includes("charter") || queryLower.includes("cp")) {
      return "clauses"
    }
    return "general"
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      console.log('File selected:', file.name, file.type)

      if (file.type.startsWith('image/') || file.type === 'application/pdf') {
        setIsLoading(true)
        try {
          // Initialize document session if not exists
          if (!useDocumentStore.getState().currentSession) {
            useDocumentStore.getState().initializeSession()
          }

          // Process the document
          const processedDoc = await processDocument(file)
          
          // Create user document
          const userDoc: UserDocument = {
            id: `doc_${Date.now()}`,
            fileName: file.name,
            content: await convertFileToBase64(file),
            processed: processedDoc
          }

          // Add to store
          useDocumentStore.getState().addDocument(userDoc)
          
          setUploadedFile(file)
          
          // Set preview
          if (file.type.startsWith('image/')) {
            const reader = new FileReader()
            reader.onload = (e) => {
              setUploadedImagePreview(e.target?.result as string)
            }
            reader.readAsDataURL(file)
          } else {
            setUploadedImagePreview('pdf-placeholder')
          }

          // Add system message about successful upload
          const systemMessage: Message = {
            id: Date.now().toString(),
            content: `📄 Document "${file.name}" has been processed successfully.\n\n${
              processedDoc.summary
            }\n\n${
              processedDoc.tables.length > 0 
                ? `Found ${processedDoc.tables.length} tables/schedules in the document.`
                : ''
            }`,
            sender: "assistant",
            timestamp: createTimestamp(),
            type: "text"
          }
          setMessages(prev => [...prev, systemMessage])

        } catch (error) {
          console.error('Document processing error:', error)
          const errorMessage: Message = {
            id: Date.now().toString(),
            content: "I apologize, but I couldn't process the document. Please try again or contact support if the issue persists.",
            sender: "assistant",
            timestamp: createTimestamp(),
            type: "text"
          }
          setMessages(prev => [...prev, errorMessage])
        } finally {
          setIsLoading(false)
        }
      } else {
        console.error('Invalid file type. Please select an image or PDF.')
        const errorMessage: Message = {
          id: Date.now().toString(),
          content: "Please upload only images or PDF files.",
          sender: "assistant",
          timestamp: createTimestamp(),
          type: "text"
        }
        setMessages(prev => [...prev, errorMessage])
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      }
    }
  }

  const triggerFileUpload = () => {
    fileInputRef.current?.click()
  }

  const removeUploadedFile = () => {
    setUploadedFile(null)
    setUploadedImagePreview(null)
    setDocumentAnalysis(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const processDocument = async (file: File): Promise<ProcessedDocument> => {
    let store = useDocumentStore.getState();
    if (!store.currentSession) {
      store.initializeSession();
    }
    
    const base64 = await convertFileToBase64(file);
    const sessionId = store.currentSession!.id;
    
    try {
      // Send to backend for processing using multipart/form-data so server receives a File object
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);

      // Optional: include a flag to help debug whether backend receives form-data
      formData.append('debug', 'true');

      const response = await fetch('/api/process-document', {
        method: 'POST',
        body: formData
      });

      let result;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        result = await response.json();
        if (!response.ok) {
          throw new Error(result.error || 'Document processing failed');
        }
      } else {
        throw new Error('Invalid response format from server');
      }
      
      // Validate the response has the required fields
      if (!result.title || !result.summary || !Array.isArray(result.sections) || !Array.isArray(result.tables)) {
        console.error('Invalid document processing result structure', result);
        throw new Error('Invalid document processing result structure');
      }

      // Debug: show a short excerpt of the processed result in the console
      console.log('Processed document result excerpt:', {
        title: result.title,
        summaryExcerpt: String(result.summary).substring(0, 200),
        sectionsCount: Array.isArray(result.sections) ? result.sections.length : 0
      });

      // Add the processed document to the store
      store.addDocument({
        id: `doc_${Date.now()}`,
        fileName: file.name,
        content: base64,
        processed: result
      });
    } catch (error) {
      console.error('Document processing error:', error);
      throw error;
    }
  }

  const convertFileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => {
        const result = reader.result as string
        const base64 = result.split(',')[1]
        resolve(base64)
      }
      reader.onerror = reject
      reader.readAsDataURL(file)
    })
  }

  const handleSendMessage = async (query: string) => {
    const trimmedQuery = query.trim();
    if ((!trimmedQuery && !uploadedFile) || isLoading) return;

    setInputValue(""); // Clear input immediately

    // Add query to history
    if (trimmedQuery) {
      const newQuery: QueryHistory = {
        id: Date.now().toString(),
        query: trimmedQuery,
        timestamp: createTimestamp(),
        category: categorizeQuery(trimmedQuery),
      };
      setQueryHistory((prev) => [newQuery, ...prev.slice(0, 9)]);
    }

    // Add user message to the chat
    const userMessage: Message = {
        id: Date.now().toString(),
        content: uploadedFile ? `📄 **Uploaded Document**: ${uploadedFile.name}\n\n${trimmedQuery || "Please analyze this maritime document."}` : trimmedQuery,
        sender: "user",
        timestamp: createTimestamp(),
        type: "text",
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Enhanced weather query detection
    const weatherCheck = isWeatherQuery(trimmedQuery);

    if (weatherCheck.isWeather && !uploadedFile) {
        try {
            if (!weatherCheck.portName) {
                // If no port name detected, ask for clarification
                const clarificationMessage: Message = {
                    id: (Date.now() + 1).toString(),
                    content: `I understand you're asking about weather, but I need to know which port or maritime location you're interested in.\n\nPlease specify the location, for example:\n- "Weather at Port of Singapore"\n- "Current conditions in Rotterdam"\n- "Wind forecast for Hong Kong harbor"`,
                    sender: "assistant",
                    timestamp: createTimestamp(),
                    type: "text",
                    confidence: 1,
                    sources: ["Query Clarification"]
                };
                setMessages(prev => [...prev, clarificationMessage]);
                return;
            }

            // Get real-time weather data
            const { getPortWeather, formatWeatherResponse } = await import('@/lib/services/weather');
            const weatherData = await getPortWeather(weatherCheck.portName);
            let formattedResponse = formatWeatherResponse(weatherData);

            // Add maritime-specific weather insights
            const windSpeed = weatherData.wind?.speed || 0;
            const visibility = weatherData.visibility || 10000;
            
            formattedResponse += `\n\n**Maritime Operational Impact:**\n`;
            
            if (windSpeed > 15) {
                formattedResponse += `⚠️ **Strong Winds**: ${windSpeed} m/s may affect cargo operations, especially for container handling.\n`;
            } else if (windSpeed > 10) {
                formattedResponse += `📍 **Moderate Winds**: ${windSpeed} m/s - Monitor for gusts.\n`;
            } else {
                formattedResponse += `✅ **Calm Winds**: ${windSpeed} m/s - Ideal for most operations.\n`;
            }
            
            if (visibility < 1000) {
                formattedResponse += `⚠️ **Poor Visibility**: ${visibility}m - May affect navigation. Follow port fog procedures.\n`;
            }

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                content: formattedResponse,
                sender: "assistant",
                timestamp: createTimestamp(),
                type: "text",
                confidence: 1,
                sources: ["OpenWeather API", "Maritime Analysis"]
            };
            setMessages(prev => [...prev, assistantMessage]);

        } catch (error) {
            console.error('Weather fetch error:', error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                content: `I'm sorry, but I couldn't fetch weather data for "${weatherCheck.portName}". Please check the spelling or try a major nearby port.`,
                sender: "assistant",
                timestamp: createTimestamp(),
                type: "text",
                sources: ["Error Response"]
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
        return;
    }
    
    // Handle document-aware queries and general maritime questions
    try {
        let response: ChatResponse;

        // Check if we have documents in the current session
        const currentSession = useDocumentStore.getState().currentSession;
        const hasRelevantDocuments = currentSession?.documents.length > 0;
          const relevantDocs = currentSession.documents.map(doc => {
            const relevantSections = doc.processed.sections.filter(section => 
              section.content.toLowerCase().includes(trimmedQuery.toLowerCase()) ||
              section.keywords.some(kw => trimmedQuery.toLowerCase().includes(kw))
            );
            return { doc, relevantSections };
          }).filter(item => item.relevantSections.length > 0);

          if (relevantDocs.length > 0) {
            // Process document-specific query
            const formattedResponses = relevantDocs.map(({ doc, relevantSections }) => {
              const response = formatDocumentResponse(relevantSections, trimmedQuery);
              
              // Add tables if they exist and are relevant
              const relevantTables = doc.processed.tables.filter(table => 
                table.description?.toLowerCase().includes(trimmedQuery.toLowerCase()) ||
                table.rows.some(row => 
                  row.cells.some(cell => 
                    cell.toLowerCase().includes(trimmedQuery.toLowerCase())
                  )
                )
              );

              if (relevantTables.length > 0) {
                response += "\n\n### Related Schedules/Tables\n\n";
                relevantTables.forEach(table => {
                  response += `#### ${table.title}\n\n`;
                  response += "| " + table.headers.join(" | ") + " |\n";
                  response += "|" + table.headers.map(() => "---").join("|") + "|\n";
                  table.rows.forEach(row => {
                    response += "| " + row.cells.join(" | ") + " |\n";
                  });
                  if (table.description) {
                    response += `\n*${table.description}*\n\n`;
                  }
                });
              }

              return response;
            }).join("\n\n---\n\n");

            response = {
              response: formattedResponses,
              confidence: 0.95,
              conversation_id: conversationId || undefined,
              sources: relevantDocs.map(({ doc }) => doc.fileName)
            };
        } else {
            // Enhance the query with maritime-specific context
            const maritimeEnhancedQuery = enhanceMaritimeQuery(trimmedQuery);
            const chatMessage: ChatMessage = {
                ...maritimeEnhancedQuery,
                conversation_id: conversationId || undefined,
            };
            response = await sendChatMessage(chatMessage);
        }

        if (response.conversation_id && !conversationId) {
            setConversationId(response.conversation_id);
        }

        // Enhance the response with maritime context
        const maritimeContext = getMaritimeContext(trimmedQuery);
        const enhancedResponse = response.response + maritimeContext;
        
        const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            content: enhancedResponse,
            sender: "assistant",
            timestamp: createTimestamp(),
            type: "text",
            confidence: response.confidence,
            sources: [...(response.sources || []), "Maritime Industry Guidelines", "IMO Regulations"],
        };
        setMessages((prev) => [...prev, assistantMessage]);

        if (uploadedFile) {
            removeUploadedFile();
        }

    } catch (error) {
        console.error("Chat API error:", error);
        const errorMessage: Message = {
            id: (Date.now() + 1).toString(),
            content: `I apologize, but I'm having trouble connecting to the maritime intelligence system. Please check the backend connection and try again.`,
            sender: "assistant",
            timestamp: createTimestamp(),
            type: "text",
            confidence: 0.5,
            sources: ["Fallback Response"],
        };
        setMessages((prev) => [...prev, errorMessage]);
    } finally {
        setIsLoading(false);
    }
  }


  const recognitionRef = useRef<SpeechRecognition | null>(null);

  const handleVoiceToggle = () => {
    if (!isRecording) {
      // @ts-ignore
      if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
        // @ts-ignore
        const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognitionAPI();
        recognitionRef.current = recognition;

        recognition.lang = 'en-US';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
          setIsRecording(true);
          setInputValue('');
        };

        recognition.onresult = (event: SpeechRecognitionEvent) => {
          const transcript = event.results[0][0].transcript;
          setInputValue(transcript);
          // Automatically send message after speech is recognized
          if (transcript.trim()) {
            handleSendMessage(transcript); 
          }
        };

        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
          console.error('Speech recognition error:', event.error);
          setIsRecording(false);
          recognitionRef.current = null;
        };

        recognition.onend = () => {
          setIsRecording(false);
          recognitionRef.current = null;
        };

        recognition.start();
      } else {
        console.error('Speech recognition is not supported in this browser.');
      }
    } else {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
      setIsRecording(false);
    }
  }

  const handleSpeakResponse = (message: string) => {
    if (!isSpeaking) {
      if ('speechSynthesis' in window) {
        // Clean up markdown for better speech synthesis
        const cleanMessage = message.replace(/(\.|_|"|`|#)/g, '');
        const utterance = new SpeechSynthesisUtterance(cleanMessage);
        utterance.lang = 'en-US';
        utterance.rate = 1;
        utterance.pitch = 1;

        utterance.onend = () => {
          setIsSpeaking(false);
        };

        utterance.onerror = (event) => {
          console.error('Speech synthesis error:', event);
          setIsSpeaking(false);
        };

        setIsSpeaking(true);
        window.speechSynthesis.speak(utterance);
      } else {
        console.error('Text-to-speech is not supported in this browser.');
      }
    } else {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      setIsSpeaking(false);
    }
  }

  const getCategoryIcon = (category: QueryHistory["category"]) => {
    switch (category) {
      case "weather":
        return <Navigation className="w-4 h-4 text-sky-600" />
      case "laytime":
        return <Clock className="w-4 h-4 text-blue-600" />
      case "distance":
        return <Compass className="w-4 h-4 text-cyan-600" />
      case "clauses":
        return <Anchor className="w-4 h-4 text-indigo-600" />
      default:
        return <Ship className="w-4 h-4 text-sky-600" />
    }
  }

  const getCategoryColor = (category: QueryHistory["category"]) => {
    switch (category) {
      case "weather":
        return "from-sky-100 to-sky-200 text-sky-800"
      case "laytime":
        return "from-blue-100 to-blue-200 text-blue-800"
      case "distance":
        return "from-cyan-100 to-cyan-200 text-cyan-800"
      case "clauses":
        return "from-indigo-100 to-indigo-200 text-indigo-800"
      default:
        return "from-sky-100 to-blue-100 text-sky-800"
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-100 via-sky-50 to-white flex flex-col font-sans overflow-hidden">
      {/* Header - Ocean-themed Glassmorphism */}
      <header className="sticky top-0 z-20 border-b border-sky-200 bg-sky-100/90 backdrop-blur-lg shadow-lg">
        <div className="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost" size="sm" className="rounded-full px-4 py-2 text-sky-700 hover:bg-sky-200/50 transition-all duration-300 shadow-sm">
                <ArrowLeft className="w-4 h-4 mr-2" /> Dashboard
              </Button>
            </Link>
            <Separator orientation="vertical" className="h-8 mx-2 bg-sky-200" />
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="absolute -inset-1 bg-gradient-to-r from-sky-400 to-blue-500 rounded-full opacity-75 blur"></div>
                <Ship className="w-8 h-8 text-white relative animate-float" />
              </div>
              <h1 className="text-2xl font-black tracking-tight bg-gradient-to-r from-sky-700 to-blue-900 text-transparent bg-clip-text">
                Maritime Professional Assistant
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="secondary" className="flex items-center gap-2 bg-sky-200/80 text-sky-800 px-4 py-1.5 rounded-full shadow-md border border-sky-300/50">
              <div className="w-2 h-2 bg-sky-500 rounded-full animate-pulse"></div>
              Maritime AI Active
            </Badge>
            <Badge variant="secondary" className="flex items-center gap-2 bg-blue-200/80 text-blue-800 px-4 py-1.5 rounded-full shadow-md border border-blue-300/50">
              <Anchor className="w-4 h-4" /> Professional Mode
            </Badge>
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-[1400px] mx-auto px-4 py-8 flex gap-8 relative">
        {/* Ocean-themed Query History Sidebar */}
        {isQueryHistoryOpen && (
          <aside className="w-full max-w-[380px] flex-shrink-0">
            <Card className="h-full flex flex-col shadow-xl rounded-3xl border-none bg-gradient-to-b from-sky-100/90 to-white/80 backdrop-blur-lg border border-sky-200/50">
              <CardHeader className="pb-4 flex items-center justify-between rounded-t-3xl bg-gradient-to-r from-sky-600 to-blue-700 text-white">
                <CardTitle className="text-lg font-bold flex items-center gap-3">
                  <div className="p-2 bg-sky-500/20 rounded-lg">
                    <Compass className="w-5 h-5 text-sky-100 animate-float" />
                  </div>
                  Maritime Query Log
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="ml-auto rounded-full bg-blue-100 hover:bg-blue-200 text-blue-600 shadow"
                  onClick={() => setIsQueryHistoryOpen(false)}
                  aria-label="Collapse query history"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
              </CardHeader>
              <CardContent className="p-0 flex-1 rounded-b-3xl">
                <ScrollArea className="h-full">
                  <div className="space-y-3 p-4">
                    {queryHistory.map((query) => (
                      <div
                        key={query.id}
                        className="p-3 rounded-xl border border-blue-100 bg-white/70 hover:bg-blue-50 cursor-pointer transition-all shadow-sm"
                        onClick={() => setInputValue(query.query)}
                      >
                        <div className="flex items-start gap-2 mb-2">
                          <Badge variant="outline" className="text-xs bg-blue-200 text-blue-900 px-2 py-0.5 rounded-full">
                            {getCategoryIcon(query.category)}
                            <span className="ml-1 capitalize">{query.category}</span>
                          </Badge>
                        </div>
                        <p className="text-sm text-blue-900 line-clamp-2 font-medium">{query.query}</p>
                        <div className="text-xs text-blue-500 mt-1">
                          <ClientTimestamp date={query.timestamp} />
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </aside>
        )}
        {/* Chat Interface - Modern Card & Responsive */}
        <section className="flex-1 relative h-full min-w-0">
          {!isQueryHistoryOpen && (
            <button
              className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-blue-100 hover:bg-blue-200 border border-blue-300 rounded-r-full shadow-lg p-2 transition-all duration-200 flex items-center"
              style={{ minWidth: '32px' }}
              onClick={() => setIsQueryHistoryOpen(true)}
              aria-label="Expand query history"
            >
              <ChevronRight className="w-5 h-5 text-blue-600" />
            </button>
          )}
          <Card className="border-none bg-gradient-to-b from-sky-50 to-white backdrop-blur-lg flex flex-col h-full min-h-0 shadow-xl rounded-3xl border border-sky-200/50">
            <CardHeader className="flex items-center justify-between rounded-t-3xl bg-gradient-to-r from-sky-100/90 to-blue-100/90 border-b border-sky-200">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-r from-sky-200 to-blue-200 rounded-lg shadow-inner">
                  <Ship className="w-6 h-6 text-sky-700 animate-float" />
                </div>
                <span className="font-bold text-xl bg-gradient-to-r from-sky-800 to-blue-900 text-transparent bg-clip-text">
                  Maritime Professional Assistant
                </span>
              </div>
            </CardHeader>
            <CardContent className="flex-1 p-0 flex flex-col min-h-0 rounded-b-3xl">
              {/* Messages Area - Modern Bubbles & Animations */}
              <ScrollArea className="flex-1 p-6 max-h-[calc(100vh-300px)] overflow-y-auto rounded-b-3xl">
                <div className="space-y-6">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex gap-3 ${message.sender === "user" ? "justify-end" : "justify-start"}`}
                    >
                      {message.sender === "assistant" && (
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-200 flex items-center justify-center shadow">
                          <Ship className="w-4 h-4 text-blue-700" />
                        </div>
                      )}
                      <div
                        className={`max-w-[70%] rounded-xl px-5 py-4 shadow-lg transition-all duration-300 ${ 
                          message.sender === "user"
                            ? "bg-blue-700 text-white ml-auto message-user border border-blue-200"
                            : "bg-white text-blue-900 message-assistant border border-blue-100 whitespace-pre-wrap"
                        }`}
                        style={{ whiteSpace: 'pre-wrap' }}
                      >
                        <div className="prose prose-sm max-w-none dark:prose-invert">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                              strong: ({ node, ...props }) => <strong className="font-semibold" {...props} />,
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                        {message.sender === "assistant" && message.confidence && (
                          <div className="mt-3 pt-2 border-t border-blue-100">
                            <div className="flex items-center justify-between gap-2 mb-1">
                              <div className="flex items-center gap-2">
                                <span className="text-xs opacity-70">Confidence:</span>
                                <div className="w-16 h-1 bg-blue-200 rounded-full overflow-hidden">
                                  <div
                                    className="h-full bg-blue-500 transition-all duration-300"
                                    style={{ width: `${message.confidence * 100}%` }}
                                  />
                                </div>
                                <span className="text-xs opacity-70">{Math.round(message.confidence * 100)}%</span>
                              </div>
                            </div>
                            {message.sources && message.sources.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-1">
                                {message.sources.map((source, index) => (
                                  <Badge key={index} variant="secondary" className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                                    {source}
                                  </Badge>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                        <div className="flex items-center justify-between mt-2 gap-2">
                          <ClientTimestamp date={message.timestamp} />
                          {message.sender === "assistant" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0 opacity-70 hover:opacity-100"
                              onClick={() => handleSpeakResponse(message.content)}
                              aria-label="Read message aloud"
                            >
                              {isSpeaking ? <VolumeX className="w-3 h-3" /> : <Volume2 className="w-3 h-3" />}
                            </Button>
                          )}
                        </div>
                      </div>
                      {message.sender === "user" && (
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-700 flex items-center justify-center shadow">
                          <User className="w-4 h-4 text-white" />
                        </div>
                      )}
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex gap-3 justify-start animate-pulse">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-300 flex items-center justify-center shadow">
                        <Bot className="w-4 h-4 text-blue-900" />
                      </div>
                      <div className="bg-blue-50 text-blue-900 rounded-xl px-5 py-4 shadow-lg">
                        <div className="flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span className="text-sm">Analyzing your maritime query...</span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>

              {/* Input Area - Modern, Responsive, Accessible */}
              <div className="border-t border-sky-200 p-6 bg-gradient-to-b from-sky-50/80 to-white/90 backdrop-blur rounded-b-3xl">
                {uploadedImagePreview && (
                  <div className="mb-4 p-4 rounded-2xl bg-gradient-to-r from-sky-50 to-white border border-sky-200/80 flex items-start gap-4 shadow-lg">
                    <div className="relative">
                      {uploadedImagePreview === 'pdf-placeholder' ? (
                        <div className="w-24 h-24 bg-gradient-to-br from-sky-100 to-white border border-sky-200 rounded-xl flex items-center justify-center shadow-inner">
                          <FileText className="w-10 h-10 text-sky-500" />
                        </div>
                      ) : (
                        <img
                          src={uploadedImagePreview}
                          alt="Uploaded document"
                          className="w-24 h-24 object-cover rounded-xl border border-sky-200 shadow-md"
                        />
                      )}
                      <Button
                        variant="destructive"
                        size="sm"
                        className="absolute -top-2 -right-2 h-7 w-7 p-0 rounded-full shadow-lg bg-red-500 hover:bg-red-600 transition-colors"
                        onClick={removeUploadedFile}
                        aria-label="Remove uploaded file"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        {uploadedFile?.type === 'application/pdf' ? (
                          <FileText className="w-5 h-5 text-sky-600" />
                        ) : (
                          <FileImage className="w-5 h-5 text-sky-600" />
                        )}
                        <span className="text-sm font-semibold text-sky-900 truncate">{uploadedFile?.name}</span>
                      </div>
                      <p className="text-xs text-sky-600 mt-1 flex items-center gap-2">
                        <span className="inline-block p-1 bg-sky-100 rounded-md">📄</span>
                        Ready for maritime document analysis
                      </p>
                    </div>
                  </div>
                )}
                <div className="flex gap-3 p-4 border-t border-sky-200">
                  <div className="flex-1 relative">
                    <Input
                      ref={inputRef}
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      placeholder={uploadedFile ? "Ask about your maritime document..." : "Ask about weather, routes, cargo operations..."}
                      className="pr-28 w-full h-12 rounded-2xl border-sky-200 bg-sky-50/50 focus:ring-2 focus:ring-sky-400 focus:border-sky-400 transition-all shadow-inner placeholder:text-sky-600/60"
                      onKeyPress={(e) => e.key === "Enter" && handleSendMessage(inputValue)}
                      aria-label="Type your message"
                    />
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-9 w-9 p-0 rounded-xl bg-sky-100 hover:bg-sky-200 transition-colors shadow-sm"
                        type="button"
                        onClick={triggerFileUpload}
                        title="Upload maritime document"
                        aria-label="Upload maritime document"
                      >
                        <Upload className="w-4 h-4 text-sky-700" />
                      </Button>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*,.pdf"
                        onChange={handleFileUpload}
                        className="hidden"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-9 w-9 p-0 rounded-xl bg-sky-100 hover:bg-sky-200 transition-colors shadow-sm"
                        onClick={handleVoiceToggle}
                        title="Voice input"
                        aria-label="Voice input"
                      >
                        {isRecording ?
                          <Mic className="w-4 h-4 text-red-500" /> :
                          <Mic className="w-4 h-4 text-sky-700" />
                        }
                      </Button>
                    </div>
                  </div>
                  <Button
                    onClick={() => handleSendMessage(inputValue)}
                    disabled={(!inputValue.trim() && !uploadedFile) || isLoading}
                    className="h-12 px-6 rounded-2xl bg-gradient-to-r from-sky-600 to-blue-600 text-white hover:from-sky-700 hover:to-blue-700 transition-all shadow-lg disabled:opacity-50"
                    aria-label="Send message"
                  >
                    {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                  </Button>
                </div>
                <div className="flex items-center justify-between mt-2 text-xs text-blue-500">
                  <span>Press Enter to send</span>
                  {isRecording && (
                    <div className="flex items-center gap-1 text-red-500">
                      <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                      Recording...
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  )
}

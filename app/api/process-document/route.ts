import { NextResponse } from 'next/server';

// Constants for OpenRouter API and Groq
const OPENROUTER_API_URL = 'https://openrouter.ai/api/v1';
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;
const GROQ_API_URL = 'https://api.groq.com/openai/v1';
const GROQ_API_KEY = process.env.GROQ_API_KEY;

// OpenRouter types
interface OpenRouterMessage {
  role: 'system' | 'user' | 'assistant';
  content: string | {
    type: 'text' | 'image_url';
    text?: string;
    image_url?: { url: string };
  }[];
}

interface OpenRouterRequest {
  model: string;
  messages: OpenRouterMessage[];
  temperature?: number;
  max_tokens?: number;
  response_format?: { type: string };
}

interface OpenRouterResponse {
  choices: {
    message: {
      content: string;
    };
  }[];
}

// Function to call OpenRouter API
async function callOpenRouter(request: OpenRouterRequest): Promise<string> {
  console.log('Making OpenRouter API request:', {
    url: `${OPENROUTER_API_URL}/chat/completions`,
    model: request.model,
    messageCount: request.messages.length
  });

  if (!OPENROUTER_API_KEY) {
    console.error('OpenRouter API key is not set');
    throw new Error('OpenRouter API key is not configured');
  }

  try {
    const response = await fetch(`${OPENROUTER_API_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'Content-Type': 'application/json',
        'OpenRouter-Endpoint': request.model || 'anthropic/claude-3-opus',
      },
      body: JSON.stringify(request),
    });

    console.log('OpenRouter API response status:', response.status);
    
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status} ${response.statusText}`;
      try {
        const errorResponse = await response.json();
        console.error('OpenRouter API detailed error:', errorResponse);
        if (errorResponse.error?.message) {
          errorMessage += `: ${errorResponse.error.message}`;
        }
      } catch (e) {
        const errorText = await response.text();
        console.error('OpenRouter API raw error:', errorText);
        errorMessage += `: ${errorText}`;
      }
      throw new Error(`OpenRouter API error: ${errorMessage}`);
    }

    const data: OpenRouterResponse = await response.json();
    console.log('OpenRouter API response received:', {
      hasChoices: !!data.choices,
      choicesLength: data.choices?.length,
      hasContent: !!data.choices?.[0]?.message?.content,
      contentPreview: data.choices?.[0]?.message?.content?.substring(0, 100)
    });

    if (!data.choices?.[0]?.message?.content) {
      console.error('OpenRouter API returned invalid response structure:', data);
      throw new Error('Invalid response structure from OpenRouter API');
    }

    return data.choices[0].message.content;
  } catch (error) {
    console.error('Error in OpenRouter API call:', error);
    throw error;
  }
}

// Call Groq (OpenAI-compatible) chat completions endpoint
async function callGroq(request: OpenRouterRequest): Promise<string> {
  console.log('Making Groq API request:', {
    url: `${GROQ_API_URL}/chat/completions`,
    model: request.model,
    messageCount: request.messages.length
  });

  if (!GROQ_API_KEY) {
    console.error('Groq API key is not set');
    throw new Error('Groq API key is not configured');
  }

  try {
    const response = await fetch(`${GROQ_API_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${GROQ_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    console.log('Groq API response status:', response.status);
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status} ${response.statusText}`;
      try {
        const errorResponse = await response.json();
        console.error('Groq API detailed error:', errorResponse);
        if (errorResponse.error?.message) {
          errorMessage += `: ${errorResponse.error.message}`;
        }
      } catch (e) {
        const errorText = await response.text();
        console.error('Groq API raw error:', errorText);
        errorMessage += `: ${errorText}`;
      }
      throw new Error(`Groq API error: ${errorMessage}`);
    }

    const data: OpenRouterResponse = await response.json();
    if (!data.choices?.[0]?.message?.content) {
      console.error('Groq API returned invalid response structure:', data);
      throw new Error('Invalid response structure from Groq API');
    }

    return data.choices[0].message.content;
  } catch (error) {
    console.error('Error in Groq API call:', error);
    throw error;
  }
}

// Define placeholder types if you don't have them imported.
interface DocumentSection {
  id: string;
  title: string;
  content: string;
  importance: 'high' | 'medium' | 'low';
  keywords: string[];
}

interface DocumentTable {
  id: string;
  title: string;
  headers: string[];
  rows: { cells: string[] }[];
  description?: string;
}

interface ProcessedDocument {
  title: string;
  summary: string;
  sections: DocumentSection[];
  tables: DocumentTable[];
  metadata: {
    uploadedAt: Date;
    fileName: string;
    fileType: string;
    wordCount: number;
    sessionId: string;
  };
}


// Remove duplicate function as we already have a better version above

// Define the expected request body structure.
interface DocumentRequest {
  file_data: string;
  file_name: string;
  file_type: string;
  session_id: string;
}

/**
 * Extracts text from a PDF buffer.
 * @param buffer - The PDF file content as a Buffer.
 * @returns A promise that resolves to the extracted text.
 */
async function extractTextFromPDF(buffer: Buffer): Promise<string> {
  try {
    // Dynamically require 'pdf-parse' as it's a CommonJS module.
    const pdf = require('pdf-parse');
    const data = await pdf(buffer);
    const text = data.text;
    if (!text?.trim()) {
      throw new Error('No text content could be extracted from the PDF.');
    }
    return text;
  } catch (error) {
    console.error('PDF parsing error:', error);
    // Re-throw a more user-friendly error.
    throw new Error('Failed to parse the PDF document.');
  }
}

/**
 * Extracts text from an image using the OpenAI Vision API.
 * @param base64Image - The base64-encoded image string with a data URI prefix.
 * @returns A promise that resolves to the extracted text.
 */
async function extractTextFromImage(base64Image: string): Promise<string> {
  try {
  const request: OpenRouterRequest = {
      model: "anthropic/claude-3-opus",  // Claude 3 has excellent vision capabilities
      messages: [
        {
          role: "user",
          content: [
            {
              type: "text",
              text: "Extract text from this maritime document with careful attention to: " +
                "1. Document structure and hierarchy\\n" +
                "2. Dates and times (maintain exact format as shown)\\n" +
                "3. Company names and contact details\\n" +
                "4. Vessel and port information\\n" +
                "5. Numerical values and measurements\\n" +
                "6. Tables and structured data\\n\\n" +
                "Format the text with:\\n" +
                "- Clear section breaks between different types of information\\n" +
                "- Proper spacing and line breaks\\n" +
                "- Preserved original formatting for dates, times, and numbers\\n" +
                "- Hierarchical structure (main headings, subheadings, details)\\n" +
                "- Lists and enumerations when present\\n" +
                "- Company names in full caps as shown\\n" +
                "- Preserved contact details format\\n\\n" +
                "Pay special attention to:\\n" +
                "- Document headers and titles\\n" +
                "- Timestamps and schedules\\n" +
                "- Company details and addresses\\n" +
                "- Port names and locations\\n" +
                "- Vessel information\\n" +
                "- Operation times and dates"
            },
            {
              type: "image_url",
              image_url: { url: base64Image },
            },
          ],
        },
      ],
      max_tokens: 4096,
    };

  const text = GROQ_API_KEY ? await callGroq(request) : await callOpenRouter(request);
    if (!text) {
      throw new Error('The Vision API did not return any text from the image.');
    }
    return text;
  } catch (error) {
    console.error('OpenRouter Vision API error:', error);
    throw new Error('Failed to extract text from the image.');
  }
}

/**
 * Processes extracted text to identify sections and tables using GPT-4.
 * @param textContent - The text content of the document.
 * @returns A promise that resolves to an object containing structured sections and tables.
 */
async function processDocumentContent(textContent: string): Promise<{ sections: DocumentSection[]; tables: DocumentTable[] }> {
  try {
  const request: OpenRouterRequest = {
      model: "anthropic/claude-3-opus",
      response_format: { type: "json_object" },
      temperature: 0.2,
      messages: [
        {
          role: "user",
          content: `Extract and structure the key information from this maritime document into a well-organized format. Return a JSON object with 'sections' and 'tables' arrays.

For the sections array, extract and organize the following information into separate sections:
1. Vessel Information:
   - Vessel name
   - Owner details
   - Registration numbers

2. Port Details:
   - Ports of Loading (POL) and Discharge (POD)
   - Agent information at each port
   - Port facility details

3. Timeline and Schedule:
   - Extract ALL dates and times chronologically
   - Arrival times
   - Loading/unloading times
   - Departure times
   - Include time zones when specified

4. Cargo Information:
   - Type of cargo
   - Loading details
   - Discharge details
   - Bill of lading information

5. Contractual Information:
   - Charter party details
   - End user information
   - Payment acknowledgments
   - Notice of readiness details

For the tables array, create:
1. A timeline table with columns:
   - Event
   - Date
   - Time
   - Location
   - Details

2. A parties table with columns:
   - Role (Owner, Agent, Charterer, etc.)
   - Company Name
   - Contact Details
   - Location

Each section should have:
- id: unique identifier (section_[category]_[timestamp])
- title: Clear descriptive title
- content: Well-formatted content with proper line breaks
- importance: high/medium/low based on operational relevance
- keywords: Key maritime terms found

Each table should have:
- id: unique identifier (table_[type]_[timestamp])
- title: Clear purpose
- headers: Column headers
- rows: Structured data
- description: Context about the table's contents

Here's the document to analyze:
${textContent.substring(0, 12000)}`
        }
      ]
    };

    const content = GROQ_API_KEY ? await callGroq(request) : await callOpenRouter(request);
    if (!content) {
      throw new Error('API response for content processing was empty.');
    }

    // Parse and validate the response
    let parsed: any;
    try {
      parsed = JSON.parse(content);
    } catch (e) {
      console.error('Failed to parse API response:', e);
      throw new Error('Invalid document structure received from AI');
    }

    // Validate sections format
    if (!Array.isArray(parsed.sections)) {
      throw new Error('Invalid document structure: sections must be an array');
    }

    // Process sections with validation
    const sections: DocumentSection[] = parsed.sections.map((section: any, index: number) => {
      if (!section.content?.trim()) {
        throw new Error(`Section ${index + 1} is missing content`);
      }

      const timestamp = Date.now();
      const sectionId = section.id || `section_${index}_${timestamp}`;
      const safeTitle = section.title?.trim() || 'Untitled Section';
      
      // Validate importance
      const validImportance = ['high', 'medium', 'low'].includes(section.importance?.toLowerCase())
        ? section.importance.toLowerCase()
        : 'medium';

      // Validate and clean keywords
      const keywords = Array.isArray(section.keywords)
        ? section.keywords.filter((kw: any) => typeof kw === 'string' && kw.trim())
        : [];

      return {
        id: sectionId,
        title: safeTitle,
        content: section.content.trim(),
        importance: validImportance as 'high' | 'medium' | 'low',
        keywords: keywords.slice(0, 10) // Limit to 10 keywords
      };
    });

    // Process tables with validation
    const tables: DocumentTable[] = (Array.isArray(parsed.tables) ? parsed.tables : [])
      .map((table: any, index: number) => {
        const timestamp = Date.now();
        const tableId = table.id || `table_${index}_${timestamp}`;
        
        // Validate headers
        const headers = Array.isArray(table.headers)
          ? table.headers.map((h: any) => String(h).trim()).filter(Boolean)
          : [];

        if (headers.length === 0) {
          console.warn(`Table ${index + 1} has no headers, might be malformed`);
        }

        // Validate and process rows
        const rows = Array.isArray(table.rows)
          ? table.rows.map((row: any) => ({
              cells: Array.isArray(row.cells) 
                ? row.cells.map((cell: any) => String(cell).trim())
                : Array.isArray(row)
                  ? row.map((cell: any) => String(cell).trim())
                  : []
            }))
          : [];

        return {
          id: tableId,
          title: table.title?.trim() || `Table ${index + 1}`,
          headers,
          rows,
          description: table.description?.trim()
        };
      })
      .filter((table: DocumentTable) => table.headers.length > 0 || table.rows.length > 0); // Remove empty tables

    return { sections, tables };

  } catch (error) {
    console.error('Error processing document content:', error);
    // Throw the error instead of returning empty arrays
    throw error;
  }
}

/**
 * Generates a concise summary of the document text using GPT-4.
 * @param textContent - The text content of the document.
 * @returns A promise that resolves to the generated summary string.
 */
async function generateDocumentSummary(textContent: string): Promise<string> {
  try {
  const request: OpenRouterRequest = {
      model: "anthropic/claude-3-opus",
      messages: [
        {
          role: "user",
          content: `Create a clear, structured summary of this maritime document, highlighting the most critical points and important details: ${textContent.substring(0, 8000)}`
        }
      ],
      temperature: 0.2
    };

  return GROQ_API_KEY ? await callGroq(request) : await callOpenRouter(request);
  } catch (error) {
    console.error('Error generating document summary:', error);
    return 'Error: Summary generation failed.';
  }
}

/**
 * The main API endpoint for processing uploaded documents.
 * @param req - The incoming Next.js API request object.
 */
export async function POST(req: Request) {
  console.log('Document processing request received');
  
  // Prefer GROQ if available, otherwise use configured OpenRouter key
  if (!process.env.GROQ_API_KEY && !process.env.OPENROUTER_API_KEY) {
    console.error('No AI provider API key found in environment variables (GROQ_API_KEY or OPENROUTER_API_KEY)');
    return NextResponse.json(
      { error: 'Server configuration error: No AI provider API key is set.' },
      { status: 500 }
    );
  }

  try {
    console.log('Parsing request body');
    // Parse and validate request body
    const formData = await req.formData();
    // Debug: list formData keys
    try {
      const keys: string[] = [];
      // formData.keys() returns an iterator
      for (const key of formData.keys()) keys.push(key as string);
      console.log('FormData keys received:', keys);
      const debugFlag = formData.get('debug');
      if (debugFlag) console.log('FormData debug flag:', debugFlag);
    } catch (e) {
      console.warn('Could not enumerate formData keys for debugging', e);
    }
    const file = formData.get('file') as File;
    const sessionId = formData.get('session_id') as string;

    // Log request details
    console.log('Request details:', {
      hasFile: !!file,
      fileName: file?.name,
      fileType: file?.type,
      fileSize: file?.size,
      hasSessionId: !!sessionId
    });

    if (!file) {
      console.error('No file provided in request');
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    if (!sessionId) {
      console.error('No session ID provided in request');
      return NextResponse.json({ error: 'No session ID provided' }, { status: 400 });
    }

    // Convert file to buffer and get content type
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    const fileType = file.type;
    const fileName = file.name;

    let textContent: string;

    // Step 1: Extract text based on file type
    if (fileType === 'application/pdf') {
      textContent = await extractTextFromPDF(buffer);
    } else if (fileType.startsWith('image/')) {
      // For images, convert to base64 with data URI
      const base64 = buffer.toString('base64');
      const base64Image = `data:${fileType};base64,${base64}`;
      textContent = await extractTextFromImage(base64Image);
    } else {
      return NextResponse.json(
        { error: `Unsupported file type: ${fileType}` },
        { status: 400 }
      );
    }

    // Step 2: Process the extracted text in parallel
    const [processedContent, summary] = await Promise.all([
      processDocumentContent(textContent),
      generateDocumentSummary(textContent)
    ]);

    // Step 3: Assemble the final response object
    const processedDocument: ProcessedDocument = {
      title: fileName,
      summary,
      sections: processedContent.sections,
      tables: processedContent.tables,
      metadata: {
        uploadedAt: new Date(),
        fileName: fileName,
        fileType: fileType,
        wordCount: textContent.split(/\s+/).filter(Boolean).length,
        sessionId: sessionId
      }
    };

    return NextResponse.json(processedDocument);

  } catch (error: any) {
    console.error('An error occurred during document processing:', error);
    // Return a specific error message if available, otherwise a generic one.
    const errorMessage = error.message || 'An unexpected error occurred on the server.';
    const statusCode = error.message.includes('parse') || error.message.includes('Unsupported') ? 400 : 500;
    
    return NextResponse.json(
      { error: errorMessage },
      { status: statusCode }
    );
  }
}

export interface DocumentAnalysis {
  document_type: string;
  confidence: number;
  sections: DocumentSection[];
  key_findings: string[];
  metadata: DocumentMetadata;
  summary?: string;
  entities?: DocumentEntity[];
}

export interface DocumentSection {
  id: string;
  title: string;
  content: string;
  confidence?: number;
  importance?: 'high' | 'medium' | 'low';
  keywords?: string[];
}

export interface DocumentEntity {
  type: string;
  value: string;
  confidence: number;
}

export interface DocumentMetadata {
  processed_at: string;
  word_count: number;
  vessels?: string[];
  ports?: string[];
  dates?: string[];
  amounts?: string[];
  times?: string[];
  pages?: number;
  language?: string;
  [key: string]: any;
}

export interface UploadedFile {
  id: string;
  name: string;
  uploadedAt: Date;
  status: "uploading" | "processing" | "completed" | "error";
  progress: number;
  extractedText?: string;
  keyHighlights?: string[];
  analysis?: DocumentAnalysis;
  confidence?: number;
  error?: string;
}

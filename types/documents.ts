export interface TableRow {
  cells: string[];
}

export interface DocumentSession {
  id: string;
  uploadedAt: Date;
  documents: UserDocument[];
}

export interface UserDocument {
  id: string;
  fileName: string;
  content: string;
  processed: ProcessedDocument;
}

export interface ProcessedDocument {
  title: string;
  summary: string;
  sections: DocumentSection[];
  tables: DocumentTable[];
  metadata: DocumentMetadata;
}

export interface DocumentSection {
  id: string;
  title: string;
  content: string;
  importance: 'high' | 'medium' | 'low';
  keywords: string[];
}

export interface DocumentTable {
  id: string;
  title: string;
  headers: string[];
  rows: TableRow[];
  description?: string;
}

export interface DocumentMetadata {
  uploadedAt: Date;
  fileName: string;
  fileType: string;
  pageCount?: number;
  wordCount?: number;
  sessionId: string;
}

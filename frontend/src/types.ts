export type MessageRole = 'user' | 'assistant';

export interface Source {
  id: string;
  title: string;
  type: 'pdf' | 'doc' | 'web' | 'policy';
  snippet: string;
  relevance: number; // 0-100
  url?: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  fileAttachment?: string;
  sources?: Source[];
  confidence?: 'high' | 'medium' | 'low';
  model?: string;
}

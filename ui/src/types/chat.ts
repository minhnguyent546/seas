export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
}

export interface User {
  id: string;
  name: string;
  image?: string;
}

export interface ChatFeature {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
}

export interface ChatSession {
  id: string;
  name: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

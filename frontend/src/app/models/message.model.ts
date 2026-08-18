export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant';
  content: string;
  message_type?: 'text' | 'image' | 'file';
  created_at?: string;
  document?: Record<string, unknown>;
}

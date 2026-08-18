export interface Conversation {
  id: number;
  title: string;
  status?: 'active' | 'inactive';
  created_at?: string;
  updated_at?: string;
}

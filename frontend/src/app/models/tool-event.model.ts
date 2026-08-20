export interface ToolEvent {
  _id?: string;
  type: 'tool_call' | 'tool_result' | 'done';
  tool_name?: string;
  conversation_id: string;
  status?: 'running' | 'success' | 'error';
  timestamp?: string;
}

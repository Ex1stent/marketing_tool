import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { Conversation } from '../models/conversation.model';
import { Message } from '../models/message.model';
import { ToolEvent } from '../models/tool-event.model';

@Injectable({ providedIn: 'root' })
export class ChatService {
  private readonly baseUrl = '/api';

  private readonly http = inject(HttpClient);

  readonly conversations = signal<Conversation[]>([]);

  readonly currentConversation = signal<Conversation | null>(null);

  readonly messages = signal<Message[]>([]);

  readonly isTyping = signal(false);

  readonly toolEvents = signal<ToolEvent[]>([]);

  readonly activeConversationId = computed<number | null>(
    () => this.currentConversation()?.id ?? null,
  );

  loadConversations(): Observable<Conversation[]> {
    return this.http.get<Conversation[]>(`${this.baseUrl}/chats`);
  }

  searchConversations(query: string): Observable<Conversation[]> {
    return this.http.get<Conversation[]>(`${this.baseUrl}/chats/search?q=${encodeURIComponent(query)}`);
  }

  loadConversation(convId: number): Observable<Conversation & { messages: Message[] }> {
    return this.http.get<Conversation & { messages: Message[] }>(
      `${this.baseUrl}/chats/${convId}`,
    );
  }

  createConversation(title = 'New Chat'): Observable<Conversation> {
    return this.http.post<Conversation>(`${this.baseUrl}/chats/create`, { title });
  }

  sendMessage(convId: number, content: string, file?: File): Observable<{ conv_id: number; role: string; content: string }> {
    const form = new FormData();
    form.append('message', content);
    if (file) form.append('file', file);
    return this.http.post<{ conv_id: number; role: string; content: string }>(
      `${this.baseUrl}/chats/${convId}/messages`,
      form,
    );
  }

  sendMessageNew(content: string, file?: File): Observable<{ conv_id: number; role: string; content: string }> {
    const form = new FormData();
    form.append('message', content);
    if (file) form.append('file', file);
    return this.http.post<{ conv_id: number; role: string; content: string }>(
      `${this.baseUrl}/chats/new/messages`,
      form,
    );
  }

  deleteConversation(convId: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/chats/${convId}`);
  }

  updateConversation(convId: number, title: string): Observable<Conversation> {
    return this.http.patch<Conversation>(`${this.baseUrl}/chats/${convId}`, { title });
  }

  subscribeToToolEvents(chatId: number): EventSource {
    const eventSource = new EventSource(`${this.baseUrl}/chats/${chatId}/tool-events`);
    
    eventSource.addEventListener('tool_call', (e: MessageEvent) => {
      const event: ToolEvent = JSON.parse(e.data);
      this.toolEvents.update(events => [...events, { ...event, _id: crypto.randomUUID() }]);
    });
    
    eventSource.addEventListener('tool_result', (e: MessageEvent) => {
      const result: ToolEvent = JSON.parse(e.data);
      this.toolEvents.update(events =>
        events.map(ev =>
          ev.tool_name === result.tool_name && ev.status === 'running'
            ? { ...ev, status: result.status, timestamp: result.timestamp }
            : ev
        )
      );
    });
    
    return eventSource;
  }
}

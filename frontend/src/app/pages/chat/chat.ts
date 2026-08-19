import { Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { ChatArea } from '../../components/chat/chat-area/chat-area';
import { ChatInput } from '../../components/chat/chat-input/chat-input';
import { MessageList } from '../../components/chat/message-list/message-list';
import { Sidebar } from '../../components/chat/sidebar/sidebar';
import { Conversation } from '../../models/conversation.model';
import { Message } from '../../models/message.model';
import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [Sidebar, ChatArea, ChatInput, MessageList],
  templateUrl: './chat.html',
  styleUrl: './chat.css',
})
export class Chat {
  private readonly chatService = inject(ChatService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  protected readonly loading = signal(true);

  protected readonly creating = signal(false);

  protected readonly conversations = this.chatService.conversations;

  protected readonly activeConversationId = this.chatService.activeConversationId;

  protected readonly title = computed(
    () => this.chatService.currentConversation()?.title ?? '',
  );

  protected readonly messages = this.chatService.messages;

  protected readonly isTyping = this.chatService.isTyping;

  protected readonly hasConversation = computed(() =>
    this.chatService.currentConversation() !== null,
  );

  constructor() {
    void this.refreshConversations();

    this.route.paramMap.pipe(takeUntilDestroyed()).subscribe((params) => {
      const id = params.get('id');
      if (id) {
        this.chatService.isTyping.set(false);
        void this.loadDetail(Number(id));
      } else {
        this.chatService.currentConversation.set(null);
        this.chatService.messages.set([]);
      }
    });
  }

  private async refreshConversations(): Promise<void> {
    this.loading.set(true);
    try {
      const list = await firstValueFrom(this.chatService.loadConversations());
      this.conversations.set(list);
    } catch (error) {
      console.error('Failed to load conversations', error);
    } finally {
      this.loading.set(false);
    }
  }

  protected openConversation(conversation: Conversation): void {
    void this.router.navigate(['/chats', conversation.id]);
  }

  private async loadDetail(convId: number): Promise<void> {
    try {
      const detail = await firstValueFrom(this.chatService.loadConversation(convId));
      this.chatService.currentConversation.set(detail);
      if (!this.chatService.isTyping()) {
        this.chatService.messages.set(detail.messages ?? []);
      }
    } catch (error) {
      console.error('Failed to load conversation detail', error);
    }
  }

  //Sending from the landing page creates a new conversation.
  protected async onSendLanding(payload: { text: string; file?: File }): Promise<void> {
    const optimistic: Message = {
      id: Date.now(),
      conversation_id: 0,
      role: 'user',
      content: payload.text,
    };
    this.chatService.messages.set([optimistic]);
    this.creating.set(true);
    this.chatService.isTyping.set(true);
    try {
      const reply = await firstValueFrom(this.chatService.sendMessageNew(payload.text, payload.file));
      const created: Conversation = {
        id: reply.conv_id,
        title: payload.text.length > 100 ? payload.text.slice(0, 100) + '...' : payload.text,
      };
      this.conversations.update((list) => [created, ...list]);
      this.chatService.messages.update((list) => [
        ...list,
        {
          id: Date.now() + 1,
          conversation_id: reply.conv_id,
          role: 'assistant',
          content: reply.content,
        },
      ]);
      await this.router.navigate(['/chats', created.id]);
    } catch (error) {
      console.error('Failed to create chat', error);
    } finally {
      this.chatService.isTyping.set(false);
      this.creating.set(false);
    }
  }

  protected async onSend(payload: { text: string; file?: File }): Promise<void> {
    const conv = this.chatService.currentConversation();
    if (!conv) {
      return;
    }

    const optimistic: Message = {
      id: Date.now(),
      conversation_id: conv.id,
      role: 'user',
      content: payload.text,
    };
    this.chatService.messages.update((list) => [...list, optimistic]);

    this.chatService.isTyping.set(true);
    try {
      const reply = await firstValueFrom(
        this.chatService.sendMessage(conv.id, payload.text, payload.file),
      );
      this.chatService.messages.update((list) => [
        ...list,
        {
          id: Date.now() + 1,
          conversation_id: conv.id,
          role: 'assistant',
          content: reply.content,
        },
      ]);
      try {
        const detail = await firstValueFrom(this.chatService.loadConversation(conv.id));
        this.chatService.currentConversation.set(detail);
        this.chatService.messages.set(detail.messages ?? []);
      } catch (error) {
        console.error('Failed to refresh conversation', error);
      }
    } catch (error) {
      console.error('Failed to send message', error);
    } finally {
      this.chatService.isTyping.set(false);
    }
  }

  protected async onDelete(): Promise<void> {
    if (!confirm('Delete this conversation?')) {
      return;
    }
    const conv = this.chatService.currentConversation();
    if (!conv) {
      return;
    }
    try {
      await firstValueFrom(this.chatService.deleteConversation(conv.id));
      this.conversations.update((list) =>
        list.filter((item) => item.id !== conv.id),
      );
    } catch (error) {
      console.error('Failed to delete conversation', error);
    }
    await this.router.navigate(['/']);
  }

  protected async onGoHome() {
    await this.router.navigate(['/']);
  }

}

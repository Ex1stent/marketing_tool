import { Component, input, output } from '@angular/core';

import { Message } from '../../../models/message.model';
import { ChatHeader } from '../chat-header/chat-header';
import { ChatInput } from '../chat-input/chat-input';
import { MessageList } from '../message-list/message-list';

@Component({
  selector: 'app-chat-area',
  standalone: true,
  imports: [ChatHeader, MessageList, ChatInput],
  templateUrl: './chat-area.html',
  styleUrl: './chat-area.css',
})
export class ChatArea {
  readonly title = input.required<string>();

  readonly convId = input<number | null>(null);

  readonly messages = input.required<Message[]>();

  readonly isTyping = input<boolean>(false);

  readonly send = output<{ text: string; file?: File }>();

  readonly delete = output<void>();

  protected onSend(payload: { text: string; file?: File }): void {
    this.send.emit(payload);
  }

  protected onDelete(): void {
    this.delete.emit();
  }
}

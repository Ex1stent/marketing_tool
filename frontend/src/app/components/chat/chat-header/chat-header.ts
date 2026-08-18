import { Component, input, output, signal, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { ChatService } from '../../../services/chat.service';

@Component({
  selector: 'app-chat-header',
  standalone: true,
  templateUrl: './chat-header.html',
  styleUrl: './chat-header.css',
})
export class ChatHeader {
  private readonly chatService = inject(ChatService);

  readonly title = input.required<string>();

  readonly convId = input<number | null>(null);

  readonly delete = output<void>();

  protected readonly editing = signal(false);

  protected readonly editValue = signal('');

  protected onEditStart(): void {
    this.editValue.set(this.title());
    this.editing.set(true);
  }

  protected async onEditSave(): Promise<void> {
    if (!this.editing()) {
      return;
    }
    const newTitle = this.editValue().trim();
    const id = this.convId();
    if (!newTitle || !id) {
      this.editing.set(false);
      return;
    }
    try {
      const updated = await firstValueFrom(this.chatService.updateConversation(id, newTitle));
      this.chatService.conversations.update((list) =>
        list.map((c) => (c.id === id ? { ...c, title: updated.title } : c)),
      );
      this.chatService.currentConversation.update((conv) =>
        conv ? { ...conv, title: updated.title } : conv,
      );
    } catch (e) {
      console.error('Failed to update title', e);
    }
    this.editing.set(false);
  }

  protected onEditCancel(): void {
    this.editing.set(false);
  }

  protected onEditKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter') void this.onEditSave();
    else if (event.key === 'Escape') this.onEditCancel();
  }

  protected onDelete(): void {
    this.delete.emit();
  }
}

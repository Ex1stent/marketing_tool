import { Component, input, output } from '@angular/core';

import { Conversation } from '../../../models/conversation.model';

@Component({
  selector: 'app-conversation-item',
  standalone: true,
  templateUrl: './conversation-item.html',
  styleUrl: './conversation-item.css',
})
export class ConversationItem {
  readonly conversation = input.required<Conversation>();

  readonly isActive = input<boolean>(false);

  readonly select = output<Conversation>();

  protected onSelect(): void {
    this.select.emit(this.conversation());
  }

  protected relativeTime(): string {
    const raw = this.conversation().updated_at;
    if (!raw) return '';

    const diffMs = Date.now() - new Date(raw).getTime();
    const mins = Math.floor(diffMs / 60_000);

    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h`;
    const days = Math.floor(hours / 24);
    return days < 7 ? `${days}d` : new Date(raw).toLocaleDateString();
  }
}

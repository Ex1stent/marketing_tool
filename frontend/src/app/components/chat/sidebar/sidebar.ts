import { Component, input, output } from '@angular/core';

import { Conversation } from '../../../models/conversation.model';
import { ConversationList } from '../conversation-list/conversation-list';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [ConversationList],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css',
})
export class Sidebar {
  readonly conversations = input.required<Conversation[]>();

  readonly activeConversationId = input<number | null>(null);

  readonly createNew = output<void>();

  readonly select = output<Conversation>();

  readonly goHome = output<void>();

  protected onCreateNew(): void {
    this.createNew.emit();
  }

  protected onSelect(conversation: Conversation): void {
    this.select.emit(conversation);
  }

  protected onGoHome(): void {
    this.goHome.emit();
  }
}

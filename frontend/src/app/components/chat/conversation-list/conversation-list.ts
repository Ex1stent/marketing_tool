import { Component, computed, inject, input, output, signal } from '@angular/core';
import { Router } from '@angular/router';
import { debounceTime, of, Subject, switchMap } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { Conversation } from '../../../models/conversation.model';
import { ChatService } from '../../../services/chat.service';
import { ConversationItem } from '../conversation-item/conversation-item';

@Component({
  selector: 'app-conversation-list',
  standalone: true,
  imports: [ConversationItem],
  templateUrl: './conversation-list.html',
  styleUrl: './conversation-list.css',
})
export class ConversationList {
  private readonly chatService = inject(ChatService);
  private readonly router = inject(Router);

  readonly conversations = input.required<Conversation[]>();

  readonly activeConversationId = input<number | null>(null);

  readonly createNew = output<void>();

  readonly select = output<Conversation>();

  readonly goHome = output<void>();

  protected readonly searchQuery = signal('');

  protected readonly searchResults = signal<Conversation[] | null>(null);

  protected readonly displayed = computed(() =>
    this.searchResults() ?? this.conversations(),
  );

  private readonly search = new Subject<string>();

  constructor() {
    this.search
      .pipe(
        debounceTime(300),
        switchMap((q) => {
          const trimmed = q.trim();
          return trimmed ? this.chatService.searchConversations(trimmed) : of(null);
        }),
        takeUntilDestroyed(),
      )
      .subscribe((results) => this.searchResults.set(results));
  }

  protected onSearch(event: Event): void {
    const q = (event.target as HTMLInputElement).value;
    this.searchQuery.set(q);
    this.search.next(q);
  }

  protected onGoHome(): void {
    this.goHome.emit();
  }

  protected onCreateNew(): void {
    this.createNew.emit();
  }

  protected onSelect(conversation: Conversation): void {
    this.select.emit(conversation);
  }

  protected onGoToScheduler(): void {
    void this.router.navigate(['/scheduler']);
  }
}

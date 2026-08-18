import { Component, computed, inject, input } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';

import { Message } from '../../../models/message.model';

@Component({
  selector: 'app-message-bubble',
  standalone: true,
  templateUrl: './message-bubble.html',
  styleUrl: './message-bubble.css',
})
export class MessageBubble {
  readonly message = input.required<Message>();

  private readonly sanitizer = inject(DomSanitizer);

  protected readonly isUser = computed(() => this.message().role === 'user');

  protected readonly parsedContent = computed<SafeHtml>(() => {
    if (this.isUser()) {
      return this.message().content;
    }
    return this.sanitizer.bypassSecurityTrustHtml(marked.parse(this.message().content) as string);
  });
}

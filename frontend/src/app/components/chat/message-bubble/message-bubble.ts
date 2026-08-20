import { Component, computed, inject, input } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';

import { Message } from '../../../models/message.model';
import { ToolEvent } from '../../../models/tool-event.model';

@Component({
  selector: 'app-message-bubble',
  standalone: true,
  templateUrl: './message-bubble.html',
  styleUrl: './message-bubble.css',
})
export class MessageBubble {
  readonly message = input.required<Message>();
  readonly pendingToolEvent = input<ToolEvent | null>(null);
  readonly isLoading = input(false);

  private readonly sanitizer = inject(DomSanitizer);

  protected readonly isUser = computed(() => this.message().role === 'user');

  protected readonly document = computed<Record<string, unknown> | undefined>(
    () => this.message().document,
  );

  protected readonly parsedContent = computed<string | SafeHtml>(() => {
    const message = this.message();

    if (this.isUser()) {
      let content = message.content;

      const fileName = message.document?.['file_name'];

      if (typeof fileName === 'string' && fileName) {
        content = content.replace(fileName, '').trim();
      }

      return content;
    }

    const html = (marked.parse(message.content) as string).replace(
      /<a href="/g,
      '<a target="_blank" rel="noopener noreferrer" href="',
    );

    return this.sanitizer.bypassSecurityTrustHtml(html);
  });

  protected readonly toolName = computed(() => this.pendingToolEvent()?.tool_name ?? '');

  protected readonly showLoading = computed(
    () => this.isLoading() || this.pendingToolEvent()?.status === 'running',
  );
}

import { Component, input, output } from '@angular/core';
import { DatePipe } from '@angular/common';

import { ScheduledPost } from '../../../models/scheduler.model';

@Component({
  selector: 'app-scheduled-posts',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './scheduled-posts.html',
  styleUrl: './scheduled-posts.css',
})
export class ScheduledPosts {
  readonly posts = input.required<ScheduledPost[]>();
  readonly cancel = output<number>();

  protected onCancel(postId: number): void {
    this.cancel.emit(postId);
  }

  protected statusClass(status: string): string {
    return status;
  }

  protected simplifyError(msg?: string | null): string {
    if (!msg) return 'Failed';
    if (msg.includes('131009') || /malformed/i.test(msg)) return 'Invalid phone number';
    if (/event loop is closed/i.test(msg)) return 'Worker error: event loop closed';
    if (/caption/i.test(msg) && /2200/i.test(msg)) return 'Caption too long';
    if (/url|media|not reachable/i.test(msg)) return 'Media URL invalid or unreachable';
    return msg.length > 80 ? msg.slice(0, 80) + '…' : msg;
  }
}

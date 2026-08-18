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
}

import { Component, input, output } from '@angular/core';
import { DatePipe } from '@angular/common';

import { ScheduledPostBatch } from '../../../models/scheduler.model';

@Component({
  selector: 'app-scheduler-sidebar',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './scheduler-sidebar.html',
  styleUrl: './scheduler-sidebar.css',
})
export class SchedulerSidebar {
  readonly batches = input.required<ScheduledPostBatch[]>();
  readonly activeBatchId = input<number | null>(null);
  readonly canScheduleStates = input<Map<number, boolean>>(new Map());
  readonly selectBatch = output<ScheduledPostBatch>();
  readonly scheduleBatch = output<number>();
  readonly deleteBatch = output<number>();
  readonly resetToLanding = output<void>();
  readonly goHome = output<void>();
  readonly newSchedule = output<void>();

  protected onSelect(batch: ScheduledPostBatch): void {
    this.selectBatch.emit(batch);
  }

  protected onSchedule(batchId: number, event: Event): void {
    event.stopPropagation();
    this.scheduleBatch.emit(batchId);
  }

  protected onDelete(batchId: number, event: Event): void {
    event.stopPropagation();
    this.deleteBatch.emit(batchId);
  }

  protected onGoHome(): void {
    this.goHome.emit();
  }

  protected onResetToLanding(): void {
    this.resetToLanding.emit();
  }

  protected onNewSchedule(): void {
    this.newSchedule.emit();
  }
}

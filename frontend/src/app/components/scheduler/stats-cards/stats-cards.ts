import { Component, input } from '@angular/core';

import { SchedulerStats } from '../../../models/scheduler.model';

@Component({
  selector: 'app-stats-cards',
  standalone: true,
  templateUrl: './stats-cards.html',
  styleUrl: './stats-cards.css',
})
export class StatsCards {
  readonly stats = input<SchedulerStats | null>(null);
}

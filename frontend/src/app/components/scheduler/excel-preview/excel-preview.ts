import { Component, input } from '@angular/core';
import { DatePipe } from '@angular/common';

import { ScheduledPost } from '../../../models/scheduler.model';

@Component({
  selector: 'app-excel-preview',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './excel-preview.html',
  styleUrl: './excel-preview.css',
})
export class ExcelPreview {
  readonly posts = input<ScheduledPost[]>([]);
}

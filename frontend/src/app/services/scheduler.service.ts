import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  BatchScheduleResponse,
  ScheduledPost,
  ScheduledPostBatch,
  SchedulerStats,
  UploadResponse,
} from '../models/scheduler.model';

@Injectable({ providedIn: 'root' })
export class SchedulerService {
  private readonly baseUrl = '/api/scheduler';
  private readonly http = inject(HttpClient);

  readonly stats = signal<SchedulerStats | null>(null);
  readonly batches = signal<ScheduledPostBatch[]>([]);
  readonly posts = signal<ScheduledPost[]>([]);
  readonly selectedBatchId = signal<number | null>(null);

  loadStats(): Observable<SchedulerStats> {
    return this.http.get<SchedulerStats>(`${this.baseUrl}/stats`);
  }

  loadBatches(): Observable<ScheduledPostBatch[]> {
    return this.http.get<ScheduledPostBatch[]>(`${this.baseUrl}/batches`);
  }

  loadPosts(status?: string, batchId?: number): Observable<ScheduledPost[]> {
    const params: string[] = [];
    if (status) params.push(`status=${status}`);
    if (batchId) params.push(`batch_id=${batchId}`);
    const qs = params.length ? '?' + params.join('&') : '';
    return this.http.get<ScheduledPost[]>(`${this.baseUrl}/posts${qs}`);
  }

  uploadExcel(file: File, title?: string): Observable<UploadResponse> {
    const form = new FormData();
    form.append('file', file);
    if (title) {
      form.append('title', title);
    }
    return this.http.post<UploadResponse>(`${this.baseUrl}/uploadexcel`, form);
  }

  scheduleBatch(batchId: number): Observable<BatchScheduleResponse> {
    return this.http.post<BatchScheduleResponse>(`${this.baseUrl}/batches/${batchId}/schedule`, {});
  }

  cancelPost(postId: number): Observable<{ success: boolean; message: string }> {
    return this.http.post<{ success: boolean; message: string }>(`${this.baseUrl}/posts/${postId}/cancel`, {});
  }

  deleteBatch(batchId: number): Observable<{ success: boolean; message: string }> {
    return this.http.delete<{ success: boolean; message: string }>(`${this.baseUrl}/batches/${batchId}`);
  }
}

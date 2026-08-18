import { Component, computed, inject, OnInit, signal, ViewChild } from '@angular/core';

import { ActivatedRoute, Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { ExcelUpload } from '../../components/scheduler/excel-upload/excel-upload';
import { ScheduledPosts } from '../../components/scheduler/scheduled-posts/scheduled-posts';
import { SchedulerSidebar } from '../../components/scheduler/scheduler-sidebar/scheduler-sidebar';
import { StatsCards } from '../../components/scheduler/stats-cards/stats-cards';
import { ExcelPreview } from '../../components/scheduler/excel-preview/excel-preview';
import { PostFilters } from '../../components/scheduler/post-filters/post-filters';
import { ScheduledPost, SchedulerStats } from '../../models/scheduler.model';
import { SchedulerService } from '../../services/scheduler.service';

@Component({
  selector: 'app-scheduler',
  standalone: true,
  imports: [
    SchedulerSidebar,
    ExcelUpload,
    ScheduledPosts,
    StatsCards,
    ExcelPreview,
    PostFilters,
  ],
  templateUrl: './scheduler.html',
  styleUrl: './scheduler.css',
})
export class Scheduler implements OnInit {
  private readonly schedulerService = inject(SchedulerService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  @ViewChild('excelUploadRef') private readonly excelUpload!: ExcelUpload;

  protected readonly loading = signal(true);
  protected readonly previewPosts = signal<ScheduledPost[]>([]);

  protected readonly stats = this.schedulerService.stats;
  protected readonly batches = this.schedulerService.batches;
  protected readonly posts = this.schedulerService.posts;
  protected readonly selectedBatchId = this.schedulerService.selectedBatchId;

  protected readonly sortBy = signal<'asc' | 'desc'>('desc');
  protected readonly filterPlatform = signal('');
  protected readonly platformOptions = ['Facebook', 'Instagram', 'Whatsapp'];
  protected readonly filterType = signal('');
  protected readonly typeOptions = ['Image', 'Reel', 'Story', 'Carousel','Text', 'Video', 'Post'];

  protected readonly canSchedule = computed(() => {
    const batchId = this.selectedBatchId();
    if (!batchId) return false;
    const batch = this.batches().find((b) => b.id === batchId);
    return (batch?.statuses?.['pending'] ?? 0) > 0;
  });

  protected readonly batchStats = computed<SchedulerStats | null>(() => {
    const batchId = this.selectedBatchId();
    if (!batchId) return null;
    const batch = this.batches().find(b => b.id === batchId);
    if (!batch) return null;
    const s = batch.statuses ?? {};
    return {
      total: batch.count,
      scheduled: s['scheduled'] ?? 0,
      posted: s['posted'] ?? 0,
      failed: s['failed'] ?? 0,
      pending: s['pending'] ?? 0,
    };
  });

  protected readonly filteredPosts = computed(() => {
    let list = this.posts();
    const platform = this.filterPlatform();
    if (platform) list = list.filter(p => p.platform?.includes(platform.toLowerCase()));
    const type = this.filterType();
    if (type) list = list.filter(p => p.post_type.includes(type.toLowerCase()));
    const dir = this.sortBy();
    return [...list].sort((a, b) => {
      const ta = a.scheduled_time ? new Date(a.scheduled_time).getTime() : 0;
      const tb = b.scheduled_time ? new Date(b.scheduled_time).getTime() : 0;
      return dir === 'desc' ? tb - ta : ta - tb;
    });
  });

  async ngOnInit(): Promise<void> {
    const id = this.route.snapshot.paramMap.get('id');
    this.selectedBatchId.set(id ? Number(id) : null);
    this.previewPosts.set([]);
    await this.refresh();
  }

  private async refresh(): Promise<void> {
    this.loading.set(true);
    try {
      const batchId = this.selectedBatchId();
      const [stats, batches, posts] = await Promise.all([
        firstValueFrom(this.schedulerService.loadStats()),
        firstValueFrom(this.schedulerService.loadBatches()),
        firstValueFrom(this.schedulerService.loadPosts(undefined, batchId ?? undefined)),
      ]);
      this.schedulerService.stats.set(stats);
      this.schedulerService.batches.set(batches);
      this.schedulerService.posts.set(posts);
      this.previewPosts.set(batchId ? posts :[]);
    } catch (e) {
      console.error('Failed to load scheduler data', e);
    } finally {
      this.loading.set(false);
    }
  }

  protected async onSelectBatch(batch: { id: number }): Promise<void> {
    this.selectedBatchId.set(batch.id);
    void this.router.navigate(['/scheduler', batch.id]);
    try {
      const [posts, batches] = await Promise.all([
        firstValueFrom(this.schedulerService.loadPosts(undefined, batch.id)),
        firstValueFrom(this.schedulerService.loadBatches()),
      ]);
      this.previewPosts.set(posts);
      this.schedulerService.posts.set(posts);
      this.schedulerService.batches.set(batches);
    } catch (e) {
      console.error('Failed to load batch posts', e);
    }
  }

  protected async onScheduleBatch(batchId: number): Promise<void> {
    try {
      await firstValueFrom(this.schedulerService.scheduleBatch(batchId));
      this.previewPosts.set([]);
      await this.refresh();
    } catch (e) {
      console.error('Failed to schedule batch', e);
    }
  }

  protected async onUploadExcel(file: File): Promise<void> {
    try {
      const res = await firstValueFrom(this.schedulerService.uploadExcel(file));
      this.previewPosts.set(res.preview);
      this.selectedBatchId.set(res.batch.id);
      void this.router.navigate(['/scheduler', res.batch.id]);
      const posts = await firstValueFrom(this.schedulerService.loadPosts(undefined, res.batch.id));
      this.schedulerService.posts.set(posts);
      const batches = await firstValueFrom(this.schedulerService.loadBatches());
      this.schedulerService.batches.set(batches);
    } catch (e) {
      const detail = (e as { error?: { detail?: string } })?.error?.detail;
      alert(detail ?? 'Failed to upload Excel');
    } finally {
      this.excelUpload.setUploading(false);
    }
  }



  protected async onCancelPost(postId: number): Promise<void> {
    try {
      await firstValueFrom(this.schedulerService.cancelPost(postId));
      await this.refresh();
    } catch (e) {
      console.error('Failed to cancel post', e);
    }
  }

  protected async onDeleteBatch(batchId: number): Promise<void> {
    if (!confirm('Delete this batch and all its posts?')) return;
    try {
      await firstValueFrom(this.schedulerService.deleteBatch(batchId));
      if (this.selectedBatchId() === batchId) {
        this.selectedBatchId.set(null);
        this.previewPosts.set([]);
        void this.router.navigate(['/scheduler']);
      }
      await this.refresh();
    } catch (e) {
      console.error('Failed to delete batch', e);
    }
  }

  protected onGoHome(): void {
    void this.router.navigate(['/']);
  }

  protected onResetToLanding(): void {
    this.selectedBatchId.set(null);
    this.previewPosts.set([]);
    void this.router.navigate(['/scheduler']);
  }
}

export const POST_STATUSES = ['pending', 'scheduled', 'posted', 'failed', 'cancelled'] as const;

export type PostStatus = (typeof POST_STATUSES)[number];

export interface ScheduledPost {
  id: number;
  batch_id: number;
  post_type: string;
  platform?: string;
  media_url?: string;
  message?: string;
  topic?: string;
  recipient_id?: string;
  scheduled_time?: string;
  status: PostStatus;
  error_message?: string | null;
  created_at?: string;
}

export interface ScheduledPostBatch {
  id: number;
  title: string;
  created_at?: Date;
  count: number;
  statuses: Record<string, number>;
}

export interface SchedulerStats {
  total: number;
  scheduled: number | null;
  posted: number | null;
  failed: number | null;
  pending: number | null;
}

export interface UploadResponse {
  batch: ScheduledPostBatch;
  count: number;
  preview: ScheduledPost[];
}

export interface BatchScheduleResponse {
  batch_id: number;
  pending: number;
  status: string;
}

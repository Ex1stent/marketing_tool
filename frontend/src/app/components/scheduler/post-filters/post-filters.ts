import { Component, input, output } from '@angular/core';

@Component({
  selector: 'app-post-filters',
  standalone: true,
  templateUrl: './post-filters.html',
  styleUrl: './post-filters.css',
})
export class PostFilters {
  readonly sortBy = input<'asc' | 'desc'>('desc');
  readonly filterPlatform = input('');
  readonly filterType = input('');
  readonly platformOptions = input<string[]>([]);
  readonly typeOptions = input<string[]>([]);

  readonly sortByChange = output<'asc' | 'desc'>();
  readonly filterPlatformChange = output<string>();
  readonly filterTypeChange = output<string>();
}

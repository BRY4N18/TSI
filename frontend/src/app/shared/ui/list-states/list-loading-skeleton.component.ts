import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

/** Skeleton de filas — mismo patrón visual que lista-accidentes. */
@Component({
  selector: 'app-list-loading-skeleton',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="grid gap-2" data-testid="loading-skeleton" aria-busy="true">
      @for (i of rows; track i) {
        <div class="h-12 animate-pulse rounded-md bg-bg-surface"></div>
      }
    </div>
  `,
})
export class ListLoadingSkeletonComponent {
  @Input() count = 4;

  get rows(): number[] {
    return Array.from({ length: Math.max(1, this.count) }, (_, i) => i + 1);
  }
}

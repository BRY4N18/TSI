import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

import { TablerIconComponent, TablerIconName } from '../icon/tabler-icon.component';

/** Estado vacío de listado — ícono Tabler + texto (+ proyección opcional para CTA). */
@Component({
  selector: 'app-list-empty-state',
  standalone: true,
  imports: [TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="grid place-items-center gap-3 rounded-md border border-border-default bg-bg-surface p-10 text-center"
      data-testid="empty-state"
    >
      <span class="tsi-node h-14 w-12 bg-accent-primary/10 text-accent-primary" aria-hidden="true">
        <app-tabler-icon [name]="icon" [size]="24" />
      </span>
      <p class="m-0 text-sm text-text-secondary">{{ message }}</p>
      <ng-content />
    </div>
  `,
})
export class ListEmptyStateComponent {
  @Input({ required: true }) message!: string;
  @Input() icon: TablerIconName = 'list';
}

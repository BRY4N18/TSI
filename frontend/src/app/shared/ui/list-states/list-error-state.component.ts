import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';

import { TablerIconComponent } from '../icon/tabler-icon.component';

/** Estado de error de listado — centrado, ícono + Reintentar (design-system / lista-accidentes). */
@Component({
  selector: 'app-list-error-state',
  standalone: true,
  imports: [TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="grid place-items-center gap-3 rounded-lg border border-alert-critical bg-alert-critical-bg p-10 text-center"
      data-testid="error-state"
      role="alert"
    >
      <app-tabler-icon name="alert-triangle" [size]="32" />
      <p class="m-0 text-sm text-alert-critical">{{ message }}</p>
      <button
        type="button"
        data-testid="btn-reintentar-lista"
        class="inline-flex items-center gap-2 rounded-md border border-alert-critical px-4 py-2 text-sm font-medium text-alert-critical hover:bg-alert-critical-bg"
        (click)="retry.emit()"
      >
        <app-tabler-icon name="refresh" [size]="16" />
        {{ retryLabel }}
      </button>
    </div>
  `,
})
export class ListErrorStateComponent {
  @Input({ required: true }) message!: string;
  @Input() retryLabel = 'Reintentar';
  @Output() readonly retry = new EventEmitter<void>();
}

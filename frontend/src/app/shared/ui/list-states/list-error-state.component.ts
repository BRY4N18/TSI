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
      class="grid place-items-center gap-3 rounded-md border border-alert-critical bg-alert-critical-bg p-10 text-center"
      data-testid="error-state"
      role="alert"
    >
      <span class="tsi-node h-14 w-12 bg-alert-critical text-alert-critical-bg" aria-hidden="true">
        <app-tabler-icon name="alert-triangle" [size]="24" />
      </span>
      <p class="m-0 text-sm text-alert-critical">{{ message }}</p>
      <button
        type="button"
        data-testid="btn-reintentar-lista"
        class="tsi-btn border border-alert-critical bg-transparent text-alert-critical hover:bg-alert-critical-bg"
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

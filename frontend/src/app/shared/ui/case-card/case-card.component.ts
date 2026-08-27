import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { TablerIconComponent, TablerIconName } from '../icon/tabler-icon.component';

export type CaseCardTone = 'success' | 'warning' | 'urgent' | 'critical' | 'info';

const TONE_VAR: Record<CaseCardTone, string> = {
  success: 'var(--alert-success)',
  warning: 'var(--alert-warning)',
  urgent: 'var(--alert-urgent)',
  critical: 'var(--alert-critical)',
  info: 'var(--alert-info)',
};

/**
 * Fila de caso como placa de señalización (design-system.md §3.1/v9) — reemplaza
 * la fila de tabla genérica que antes duplicaba desktop (`<table>`) y mobile
 * (cards apiladas) con dos plantillas casi idénticas. Una sola plantilla,
 * responsive por sí misma: en ancho angosto las columnas colapsan a dos filas
 * en vez de truncar el contenido.
 *
 * Doble esquina cortada (`tsi-panel--placa`) en vez de la única esquina del
 * `Panel` estándar: una fila en una lista larga se lee como señalización de
 * carretera, no como una card de SaaS suelta — la diferencia importa porque
 * aquí hay decenas apiladas, no una sola superficie de contenido.
 */
@Component({
  selector: 'app-case-card',
  standalone: true,
  imports: [TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="tsi-panel tsi-panel--placa mb-2.5 overflow-hidden"
      [attr.data-testid]="selected() ? 'row-selected' : null"
    >
      <div
        class="grid min-h-[62px] grid-cols-[56px_1fr_auto] items-stretch gap-x-0 sm:grid-cols-[64px_180px_minmax(0,1fr)_auto]"
      >
        <div
          class="flex items-center justify-center"
          style="background: color-mix(in srgb, var(--route-navy) 6%, transparent); border-right: 2px dashed color-mix(in srgb, var(--route-navy) 30%, transparent)"
        >
          <span
            class="tsi-node flex h-[35px] w-[30px] items-center justify-center"
            [style.background]="toneVar()"
          >
            <app-tabler-icon [name]="severidadIcon()" [size]="14" class="text-bg-surface" />
          </span>
        </div>

        <div class="flex min-w-0 flex-col justify-center gap-0.5 py-2 pl-3">
          <span class="truncate font-mono text-xs font-semibold text-text-primary">{{ id() }}</span>
          <span class="text-[0.6875rem] text-text-secondary">{{ fecha() }}</span>
          <span class="truncate text-xs text-text-secondary sm:hidden">{{ lugar() }}</span>
        </div>

        <div class="hidden min-w-0 items-center pl-3 pr-4 sm:flex">
          <p class="m-0 min-w-0 truncate text-[0.8125rem] text-text-secondary">{{ lugar() }}</p>
        </div>

        <div class="flex items-center gap-3 py-2 pr-3">
          <span class="hidden shrink-0 whitespace-nowrap text-xs font-semibold sm:inline" [style.color]="toneVar()">
            {{ severidadLabel() }}
          </span>
          <span
            class="tsi-badge shrink-0"
            [class.tsi-badge-info]="estadoTone() === 'info'"
            [class.tsi-badge-success]="estadoTone() === 'success'"
            [class.tsi-badge-warning]="estadoTone() === 'warning'"
            [class.tsi-badge-urgent]="estadoTone() === 'urgent'"
            [class.tsi-badge-critical]="estadoTone() === 'critical'"
          >
            {{ estadoLabel() }}
          </span>
          <ng-content />
        </div>
      </div>
    </div>
  `,
})
export class CaseCardComponent {
  readonly id = input.required<string>();
  readonly fecha = input.required<string>();
  readonly lugar = input<string>('—');
  readonly severidadLabel = input.required<string>();
  readonly severidadIcon = input.required<TablerIconName>();
  readonly severidadTone = input.required<CaseCardTone>();
  readonly estadoLabel = input.required<string>();
  readonly estadoTone = input.required<CaseCardTone>();
  readonly selected = input(false);

  protected toneVar(): string {
    return TONE_VAR[this.severidadTone()];
  }
}

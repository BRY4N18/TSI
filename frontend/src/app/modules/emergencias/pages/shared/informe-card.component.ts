import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';

/**
 * Tarjeta base de informe táctico (FR-UI-001): loading/error/vacío/datos
 * independiente por tarjeta — un fallo no bloquea el resto del workpanel.
 */
@Component({
  selector: 'app-informe-card',
  standalone: true,
  imports: [DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="rounded-lg border border-border-default bg-bg-surface p-4">
      <div class="mb-3 flex items-start justify-between gap-2">
        <h3 class="m-0 text-sm font-semibold text-text-primary">{{ title() }}</h3>
        @if (batch()) {
          <span
            class="shrink-0 rounded-full bg-accent-primary/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-accent-primary"
            [title]="ultimaCorrida() ? 'Última actualización: ' + ultimaCorrida() : 'Dato batch (Airflow)'"
          >
            Batch{{ ultimaCorrida() ? ' · ' + (ultimaCorrida() | date: 'short') : '' }}
          </span>
        }
      </div>
      @if (loading()) {
        <div class="animate-pulse space-y-2">
          <div class="h-4 w-3/4 rounded bg-white/10"></div>
          <div class="h-4 w-1/2 rounded bg-white/10"></div>
        </div>
      } @else if (error()) {
        <div class="flex flex-col gap-2">
          <p class="m-0 text-sm text-alert-critical">{{ error() }}</p>
          <button
            type="button"
            class="w-fit rounded-md border border-accent-primary px-3 py-1 text-xs font-semibold text-accent-primary"
            (click)="retry.emit()"
          >
            Reintentar
          </button>
        </div>
      } @else if (noMaterializado()) {
        <p class="m-0 text-sm text-text-secondary">Aún no calculado para este período.</p>
      } @else if (empty()) {
        <p class="m-0 text-sm text-text-secondary">Sin datos en este período.</p>
      } @else {
        <ng-content />
      }
    </div>
  `,
})
export class InformeCardComponent {
  readonly title = input.required<string>();
  readonly loading = input(false);
  readonly error = input<string | null>(null);
  readonly empty = input(false);
  /** FR-UI-002/FR-UI-004: distingue tarjetas de informes compuestos (batch, Airflow) de las simples (tiempo real). */
  readonly batch = input(false);
  readonly ultimaCorrida = input<string | null>(null);
  readonly noMaterializado = input(false);
  readonly retry = output<void>();
}

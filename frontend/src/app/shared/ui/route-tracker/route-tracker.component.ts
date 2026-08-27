import { ChangeDetectionStrategy, Component, input } from '@angular/core';

export type RouteTrackerTone = 'success' | 'warning' | 'urgent' | 'critical' | 'info';

export interface RouteTrackerStep {
  title: string;
  status: string;
  tone: RouteTrackerTone;
  detail?: string;
}

const TONE_VAR: Record<RouteTrackerTone, string> = {
  success: 'var(--alert-success)',
  warning: 'var(--alert-warning)',
  urgent: 'var(--alert-urgent)',
  critical: 'var(--alert-critical)',
  info: 'var(--alert-info)',
};

/**
 * Historial de intentos de asignación (design-system.md §3.1/v9) — traduce un
 * historial que antes era una lista `<ol>` plana a una vía vertical con un nodo
 * hexagonal por intento, cada uno coloreado con el tono del resultado
 * (asignado/confirmado/rechazado). Un timeline de puntos no tiene lenguaje
 * propio; esta vía sí, y es la misma vía que ya usa el sidebar y la nav activa.
 */
@Component({
  selector: 'app-route-tracker',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ol class="m-0 grid list-none gap-0 p-0">
      @for (paso of pasos(); track $index) {
        <li class="relative flex gap-3 pb-5 last:pb-0">
          @if (!$last) {
            <span
              class="absolute left-[9px] top-[26px] w-[2px]"
              style="bottom: -2px; background: var(--border-default)"
              aria-hidden="true"
            ></span>
          }
          <span
            class="tsi-node relative z-[1] mt-0.5 h-[22px] w-[19px] shrink-0"
            [style.background]="TONE_VAR[paso.tone]"
            aria-hidden="true"
          ></span>
          <div class="grid min-w-0 gap-0.5 pt-0.5">
            <span class="truncate text-sm font-medium text-text-primary">{{ paso.title }}</span>
            <span class="text-xs font-semibold" [style.color]="TONE_VAR[paso.tone]">{{ paso.status }}</span>
            @if (paso.detail) {
              <span class="text-xs text-text-secondary">{{ paso.detail }}</span>
            }
          </div>
        </li>
      }
    </ol>
  `,
})
export class RouteTrackerComponent {
  readonly pasos = input.required<RouteTrackerStep[]>();
  protected readonly TONE_VAR = TONE_VAR;
}

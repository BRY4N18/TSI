import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

export interface SerieItem {
  periodo: string;
  valor: number;
}

/**
 * Serie temporal compacta: valor más reciente destacado + mini-barras del resto.
 * Reemplaza el patrón anterior de listar cada período como fila — con 30 días
 * eso se desbordaba de la tarjeta (Gestalt: una serie se lee como forma, no
 * como lista de texto).
 */
@Component({
  selector: 'app-timeseries-chart',
  standalone: true,
  imports: [DecimalPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="flex flex-col gap-2">
      <div class="flex items-baseline justify-between gap-2">
        <span class="text-2xl font-semibold text-text-primary">
          {{ ultimo()?.valor ?? 0 | number: formato() }}{{ sufijo() }}
        </span>
        <span class="text-xs text-text-secondary">{{ ultimo()?.periodo }}</span>
      </div>

      <svg viewBox="0 0 300 56" class="h-14 w-full" preserveAspectRatio="none">
        @for (b of barras(); track b.periodo) {
          <rect
            [attr.x]="b.x"
            [attr.y]="b.y"
            [attr.width]="b.w"
            [attr.height]="b.h"
            rx="1.5"
            class="fill-accent-primary"
            [style.opacity]="b.esUltimo ? 1 : 0.35"
          >
            <title>{{ b.periodo }}: {{ b.valor | number: formato() }}{{ sufijo() }}</title>
          </rect>
        }
      </svg>

      <div class="flex justify-between text-[11px] text-text-secondary">
        <span>{{ primero()?.periodo }}</span>
        <span>{{ items().length }} períodos</span>
      </div>
    </div>
  `,
})
export class TimeseriesChartComponent {
  readonly items = input.required<SerieItem[]>();
  readonly sufijo = input('');
  readonly formato = input('1.0-0');

  readonly primero = computed(() => this.items()[0]);
  readonly ultimo = computed(() => this.items()[this.items().length - 1]);

  readonly barras = computed(() => {
    const data = this.items();
    if (!data.length) return [];
    const max = Math.max(...data.map((d) => d.valor), 0.0001);
    const n = data.length;
    const gap = 2;
    const w = Math.max((300 - gap * (n - 1)) / n, 1);
    return data.map((d, i) => {
      const h = Math.max((d.valor / max) * 48, 2);
      return {
        periodo: d.periodo,
        valor: d.valor,
        x: i * (w + gap),
        y: 54 - h,
        w,
        h,
        esUltimo: i === n - 1,
      };
    });
  });
}

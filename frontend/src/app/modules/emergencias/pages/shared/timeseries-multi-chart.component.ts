import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

export interface SerieMultiItem {
  periodo: string;
  valores: number[];
}

export interface SerieMultiConfig {
  label: string;
  swatchClass: string; // clase de fondo para la leyenda, ej. 'bg-accent-primary'
  fillClass: string; // clase de fill para las barras SVG, ej. 'fill-accent-primary'
}

/**
 * Igual que app-timeseries-chart pero para 2-3 métricas por período (ej.
 * descarte vs. fusión): barras agrupadas por color + leyenda, en vez de listar
 * cada período con sus dos porcentajes como texto.
 */
@Component({
  selector: 'app-timeseries-multi-chart',
  standalone: true,
  imports: [DecimalPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="flex flex-col gap-2">
      <div class="flex flex-wrap items-baseline gap-x-4 gap-y-1">
        @for (s of series(); track s.label; let i = $index) {
          <span class="inline-flex items-center gap-1.5 text-sm">
            <span class="h-2.5 w-2.5 rounded-sm" [class]="s.swatchClass"></span>
            <span class="text-text-secondary">{{ s.label }}:</span>
            <span class="font-semibold text-text-primary">{{ ultimoValor(i) | number: formato() }}{{ sufijo() }}</span>
          </span>
        }
      </div>

      <svg viewBox="0 0 300 56" class="h-14 w-full" preserveAspectRatio="none">
        @for (g of grupos(); track g.periodo) {
          @for (b of g.barras; track b.i) {
            <rect
              [attr.x]="b.x"
              [attr.y]="b.y"
              [attr.width]="b.w"
              [attr.height]="b.h"
              rx="1"
              [class]="series()[b.i].fillClass"
              [style.opacity]="g.esUltimo ? 1 : 0.35"
            >
              <title>{{ g.periodo }} · {{ series()[b.i].label }}: {{ b.valor | number: formato() }}{{ sufijo() }}</title>
            </rect>
          }
        }
      </svg>

      <div class="flex justify-between text-[11px] text-text-secondary">
        <span>{{ items()[0]?.periodo }}</span>
        <span>{{ items().length }} períodos</span>
      </div>
    </div>
  `,
})
export class TimeseriesMultiChartComponent {
  readonly items = input.required<SerieMultiItem[]>();
  readonly series = input.required<SerieMultiConfig[]>();
  readonly sufijo = input('');
  readonly formato = input('1.0-0');

  ultimoValor(i: number): number {
    const data = this.items();
    return data.length ? data[data.length - 1].valores[i] : 0;
  }

  readonly grupos = computed(() => {
    const data = this.items();
    const nSeries = this.series().length;
    if (!data.length || !nSeries) return [];
    const max = Math.max(...data.flatMap((d) => d.valores), 0.0001);
    const n = data.length;
    const gap = 2;
    const groupW = Math.max((300 - gap * (n - 1)) / n, 1);
    const barW = Math.max((groupW - 1 * (nSeries - 1)) / nSeries, 0.5);
    return data.map((d, gi) => ({
      periodo: d.periodo,
      esUltimo: gi === n - 1,
      barras: d.valores.map((v, i) => {
        const h = Math.max((v / max) * 48, 1);
        return { i, valor: v, x: gi * (groupW + gap) + i * (barW + 1), y: 54 - h, w: barW, h };
      }),
    }));
  });
}

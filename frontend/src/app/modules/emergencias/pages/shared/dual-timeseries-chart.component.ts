import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

export interface DualSerieItem {
  periodo: string;
  a: number;
  b: number;
}

/**
 * Serie temporal de dos métricas por período (ej. descarte vs. fusión), en barras
 * agrupadas — mismo criterio que TimeseriesChartComponent: evitar volcar cada
 * período como fila de texto cuando hay muchos (Gestalt: se lee como forma).
 */
@Component({
  selector: 'app-dual-timeseries-chart',
  standalone: true,
  imports: [DecimalPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="flex flex-col gap-2">
      <div class="flex items-center gap-4 text-xs text-text-secondary">
        <span class="inline-flex items-center gap-1.5">
          <span class="h-2.5 w-2.5 rounded-sm bg-alert-warning"></span>
          {{ labelA() }}
        </span>
        <span class="inline-flex items-center gap-1.5">
          <span class="h-2.5 w-2.5 rounded-sm bg-accent-primary"></span>
          {{ labelB() }}
        </span>
        <span class="ml-auto text-text-secondary">{{ ultimo()?.periodo }}</span>
      </div>

      <div class="flex items-baseline gap-4">
        <span class="text-lg font-semibold text-alert-warning"
          >{{ ultimo()?.a ?? 0 | number: formato() }}{{ sufijo() }}</span
        >
        <span class="text-lg font-semibold text-accent-primary"
          >{{ ultimo()?.b ?? 0 | number: formato() }}{{ sufijo() }}</span
        >
      </div>

      <svg viewBox="0 0 300 56" class="h-14 w-full" preserveAspectRatio="none">
        @for (b of barras(); track b.periodo + b.serie) {
          <rect
            [attr.x]="b.x"
            [attr.y]="b.y"
            [attr.width]="b.w"
            [attr.height]="b.h"
            rx="1"
            [class.fill-alert-warning]="b.serie === 'a'"
            [class.fill-accent-primary]="b.serie === 'b'"
            [style.opacity]="b.esUltimo ? 1 : 0.4"
          >
            <title>{{ b.periodo }} — {{ b.serie === 'a' ? labelA() : labelB() }}: {{ b.valor | number: formato() }}{{ sufijo() }}</title>
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
export class DualTimeseriesChartComponent {
  readonly items = input.required<DualSerieItem[]>();
  readonly labelA = input('Serie A');
  readonly labelB = input('Serie B');
  readonly sufijo = input('');
  readonly formato = input('1.0-0');

  readonly primero = computed(() => this.items()[0]);
  readonly ultimo = computed(() => this.items()[this.items().length - 1]);

  readonly barras = computed(() => {
    const data = this.items();
    if (!data.length) return [];
    const max = Math.max(...data.map((d) => Math.max(d.a, d.b)), 0.0001);
    const n = data.length;
    const gap = 2;
    const groupW = Math.max((300 - gap * (n - 1)) / n, 2);
    const barW = Math.max((groupW - 1) / 2, 0.5);
    const out: { periodo: string; serie: 'a' | 'b'; valor: number; x: number; y: number; w: number; h: number; esUltimo: boolean }[] = [];
    data.forEach((d, i) => {
      const gx = i * (groupW + gap);
      const ha = Math.max((d.a / max) * 48, d.a > 0 ? 1.5 : 0);
      const hb = Math.max((d.b / max) * 48, d.b > 0 ? 1.5 : 0);
      const esUltimo = i === n - 1;
      out.push({ periodo: d.periodo, serie: 'a', valor: d.a, x: gx, y: 54 - ha, w: barW, h: ha, esUltimo });
      out.push({ periodo: d.periodo, serie: 'b', valor: d.b, x: gx + barW + 1, y: 54 - hb, w: barW, h: hb, esUltimo });
    });
    return out;
  });
}

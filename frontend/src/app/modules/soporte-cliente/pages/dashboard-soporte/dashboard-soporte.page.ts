import { DecimalPipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';

import { BarChartComponent, BarDatum } from '../../../../shared/ui/charts/bar-chart.component';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { TicketApiService } from '../../services/ticket-api.service';
import { DashboardSoporteData } from '../../services/models/soporte.types';

type DistEntry = { key: string; label: string; count: number; pct: number };

@Component({
  selector: 'app-dashboard-soporte',
  standalone: true,
  imports: [DecimalPipe, TablerIconComponent, BarChartComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './dashboard-soporte.page.html',
})
export class DashboardSoportePage {
  private readonly api = inject(TicketApiService);

  readonly metricas = signal<DashboardSoporteData | null>(null);
  readonly cargando = signal(false);
  readonly error = signal('');

  readonly porEstado = computed(() => this.toDist(this.metricas()?.por_estado, (k) => this.labelEstado(k)));
  readonly porPrioridad = computed(() =>
    this.toDist(this.metricas()?.por_prioridad, (k) => this.labelPrioridad(k)),
  );
  readonly porTipo = computed(() =>
    this.toDist(this.metricas()?.por_tipo_incidencia, (k) => k || 'Sin tipo'),
  );
  readonly porCliente = computed(() => this.toDist(this.metricas()?.por_cliente));

  // ── Distribuciones como gráficos (design-system.md §5.1) ──────────────
  //
  // Las cuatro son repartos de un total entre categorías, así que las
  // cuatro son barras. Lo que cambia es la ESCALA DE COLOR, y ahí está la
  // única decisión real:
  //
  // - estado, tipo y cliente son categorías **nominales**: ordenarlas de
  //   otra forma no cambiaría lo que significan. Van todas del mismo color
  //   y ordenadas por magnitud, que es lo que ayuda a compararlas.
  // - prioridad es **ordinal**: Baja < Media < Alta < Crítico. Ahí el orden
  //   sí significa, así que se ordena por rango (no por conteo, como las
  //   otras) y se pinta con la rampa de un tono, para que la gravedad
  //   creciente se vea en el color y no haya que leer las etiquetas.

  readonly barrasEstado = computed<BarDatum[]>(() =>
    this.porEstado().map((r) => ({ etiqueta: r.label, valor: r.count })),
  );

  readonly barrasPrioridad = computed<BarDatum[]>(() =>
    [...this.porPrioridad()]
      .sort((a, b) => this.rangoPrioridad(a.key) - this.rangoPrioridad(b.key))
      .map((r) => ({ etiqueta: r.label, valor: r.count })),
  );

  readonly barrasTipo = computed<BarDatum[]>(() =>
    this.porTipo().map((r) => ({ etiqueta: r.label, valor: r.count })),
  );

  readonly barrasCliente = computed<BarDatum[]>(() =>
    this.porCliente().map((r) => ({ etiqueta: `Cliente #${r.key}`, valor: r.count })),
  );

  /** Rango de gravedad; lo desconocido cae al final, no en medio. */
  private rangoPrioridad(prioridad: string): number {
    switch (prioridad.toLowerCase()) {
      case 'baja':
        return 0;
      case 'media':
        return 1;
      case 'alta':
        return 2;
      case 'critico':
      case 'crítico':
        return 3;
      default:
        return 99;
    }
  }

  constructor() {
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.error.set('');
    this.api.dashboard().subscribe({
      next: (res) => {
        this.metricas.set(res.data);
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
        this.error.set('No se pudo cargar el dashboard de soporte.');
      },
    });
  }

  formatDuration(ms: number | null): string {
    if (ms == null || Number.isNaN(ms)) {
      return '—';
    }
    const totalMin = Math.round(ms / 60_000);
    if (totalMin < 60) {
      return `${totalMin} min`;
    }
    const h = Math.floor(totalMin / 60);
    const m = totalMin % 60;
    return m ? `${h} h ${m} min` : `${h} h`;
  }

  labelEstado(estado: string): string {
    return estado.replaceAll('_', ' ');
  }

  labelPrioridad(prioridad: string): string {
    if (!prioridad) {
      return 'Sin prioridad';
    }
    return prioridad.charAt(0).toUpperCase() + prioridad.slice(1);
  }



  private toDist(
    map: Record<string, number> | undefined,
    labelFn: (key: string) => string = (k) => k,
  ): DistEntry[] {
    if (!map) {
      return [];
    }
    const entries = Object.entries(map);
    const total = entries.reduce((acc, [, n]) => acc + n, 0) || 1;
    return entries
      .map(([key, count]) => ({
        key,
        label: labelFn(key),
        count,
        pct: Math.round((count / total) * 100),
      }))
      .sort((a, b) => b.count - a.count);
  }
}

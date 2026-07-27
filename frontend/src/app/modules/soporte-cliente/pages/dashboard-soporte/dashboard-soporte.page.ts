import { DecimalPipe, NgClass } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { TicketApiService } from '../../services/ticket-api.service';
import { DashboardSoporteData } from '../../services/models/soporte.types';

type DistEntry = { key: string; label: string; count: number; pct: number };

@Component({
  selector: 'app-dashboard-soporte',
  standalone: true,
  imports: [DecimalPipe, NgClass, TablerIconComponent],
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

  estadoBadge(estado: string): string {
    switch (estado) {
      case 'Resuelto':
      case 'Cerrado':
        return 'tsi-badge-success';
      case 'Escalado':
      case 'Pendiente_de_clasificacion':
        return 'tsi-badge-urgent';
      case 'En_progreso':
      case 'Reabierto':
        return 'tsi-badge-info';
      case 'Abierto':
        return 'tsi-badge-warning';
      default:
        return 'tsi-badge-neutral';
    }
  }

  prioridadBadge(prioridad: string): string {
    const p = prioridad.toLowerCase();
    if (p === 'crítico' || p === 'critico') {
      return 'tsi-badge-critical';
    }
    if (p === 'alta') {
      return 'tsi-badge-urgent';
    }
    if (p === 'media') {
      return 'tsi-badge-warning';
    }
    return 'tsi-badge-neutral';
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

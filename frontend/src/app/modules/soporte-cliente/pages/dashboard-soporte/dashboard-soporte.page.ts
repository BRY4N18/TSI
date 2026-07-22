import { Component, inject, signal } from '@angular/core';

import { TicketApiService } from '../../services/ticket-api.service';
import { DashboardSoporteData } from '../../services/models/soporte.types';

@Component({
  selector: 'app-dashboard-soporte',
  standalone: true,
  imports: [],
  template: `
    @if (metricas(); as m) {
      <section>
        <h1>Dashboard de soporte</h1>
        <p>Total de tickets: {{ m.total_tickets }}</p>
        <p>SLA en riesgo: {{ m.sla_en_riesgo }} · SLA vencidos: {{ m.sla_vencidos }}</p>
        <p>Tasa de reapertura: {{ (m.tasa_reapertura * 100).toFixed(1) }}%</p>

        <h2>Por estado</h2>
        <ul>
          @for (item of estadoEntries(m); track item[0]) {
            <li>{{ item[0] }}: {{ item[1] }}</li>
          }
        </ul>

        <h2>Por prioridad</h2>
        <ul>
          @for (item of prioridadEntries(m); track item[0]) {
            <li>{{ item[0] }}: {{ item[1] }}</li>
          }
        </ul>
      </section>
    }
  `,
})
export class DashboardSoportePage {
  private readonly api = inject(TicketApiService);

  readonly metricas = signal<DashboardSoporteData | null>(null);

  constructor() {
    this.api.dashboard().subscribe({ next: (res) => this.metricas.set(res.data) });
  }

  estadoEntries(m: DashboardSoporteData): [string, number][] {
    return Object.entries(m.por_estado);
  }

  prioridadEntries(m: DashboardSoporteData): [string, number][] {
    return Object.entries(m.por_prioridad);
  }
}

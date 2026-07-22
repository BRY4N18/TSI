import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { TicketApiService } from '../../services/ticket-api.service';
import { Ticket } from '../../services/models/soporte.types';

@Component({
  selector: 'app-cola-agente',
  standalone: true,
  imports: [RouterLink],
  template: `
    <section>
      <h1>Cola de soporte</h1>
      @if (tickets().length) {
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Asunto</th>
              <th>Estado</th>
              <th>Prioridad</th>
              <th>SLA</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            @for (t of tickets(); track t.id_reclamo) {
              <tr>
                <td>{{ t.id_reclamo }}</td>
                <td>{{ t.asunto }}</td>
                <td>{{ t.estado }}</td>
                <td>{{ t.prioridad ?? '—' }}</td>
                <td>{{ t.sla_status ?? '—' }}</td>
                <td>
                  <a [routerLink]="['/soporte-cliente', 'tickets', t.id_reclamo]">Ver</a>
                  @if (t.estado === 'Abierto' || t.estado === 'Reabierto') {
                    <button type="button" (click)="tomar(t)">Tomar</button>
                  }
                </td>
              </tr>
            }
          </tbody>
        </table>
      } @else {
        <p>No hay tickets pendientes.</p>
      }
      @if (mensaje()) {
        <p data-testid="mensaje">{{ mensaje() }}</p>
      }
    </section>
  `,
})
export class ColaAgentePage {
  private readonly api = inject(TicketApiService);

  readonly tickets = signal<Ticket[]>([]);
  readonly mensaje = signal('');

  constructor() {
    this.cargar();
  }

  private cargar(): void {
    this.api.listar().subscribe({ next: (res) => this.tickets.set(res.data.items) });
  }

  tomar(ticket: Ticket): void {
    this.api.tomar(ticket.id_reclamo).subscribe({
      next: () => {
        this.mensaje.set(`Ticket #${ticket.id_reclamo} tomado`);
        this.cargar();
      },
      error: () => this.mensaje.set('Error al tomar el ticket'),
    });
  }
}

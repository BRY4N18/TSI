import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { TicketApiService } from '../../services/ticket-api.service';
import { Ticket } from '../../services/models/soporte.types';

@Component({
  selector: 'app-mis-tickets',
  standalone: true,
  imports: [FormsModule, RouterLink],
  template: `
    <section>
      <h1>Mis tickets de soporte</h1>

      <details>
        <summary>Registrar nuevo ticket</summary>
        <form (ngSubmit)="registrar()">
          <label>Asunto <input name="asunto" [(ngModel)]="asunto" required /></label>
          <label>Descripción <textarea name="descripcion" [(ngModel)]="descripcion" required></textarea></label>
          <label>
            Tipo
            <select name="tipo" [(ngModel)]="tipo">
              <option value="tecnico">Técnico</option>
              <option value="acceso">Acceso</option>
              <option value="operativo">Operativo</option>
            </select>
          </label>
          <button type="submit">Enviar</button>
        </form>
        @if (mensaje()) {
          <p data-testid="mensaje">{{ mensaje() }}</p>
        }
      </details>

      @if (tickets().length) {
        <ul>
          @for (t of tickets(); track t.id_reclamo) {
            <li>
              <a [routerLink]="['/soporte-cliente', 'tickets', t.id_reclamo]">
                #{{ t.id_reclamo }} — {{ t.asunto }} ({{ t.estado }}, SLA: {{ t.sla_status ?? 'sin asignar' }})
              </a>
            </li>
          }
        </ul>
      } @else {
        <p>No tienes tickets registrados.</p>
      }
    </section>
  `,
})
export class MisTicketsPage {
  private readonly api = inject(TicketApiService);

  readonly tickets = signal<Ticket[]>([]);
  readonly mensaje = signal('');
  asunto = '';
  descripcion = '';
  tipo = 'tecnico';

  constructor() {
    this.cargar();
  }

  private cargar(): void {
    this.api.listar().subscribe({ next: (res) => this.tickets.set(res.data.items) });
  }

  registrar(): void {
    if (!this.asunto || !this.descripcion) {
      return;
    }
    this.api
      .registrar({ idcliente: 1, asunto: this.asunto, descripcion: this.descripcion, tipo: this.tipo })
      .subscribe({
        next: (res) => {
          this.mensaje.set(`Ticket #${res.data.id_reclamo} registrado (${res.data.estado})`);
          this.asunto = '';
          this.descripcion = '';
          this.cargar();
        },
        error: () => this.mensaje.set('Error al registrar el ticket'),
      });
  }
}

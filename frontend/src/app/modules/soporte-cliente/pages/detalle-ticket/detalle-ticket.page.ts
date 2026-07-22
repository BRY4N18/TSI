import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { TicketApiService } from '../../services/ticket-api.service';
import { HistorialTicketItem, Ticket } from '../../services/models/soporte.types';

@Component({
  selector: 'app-detalle-ticket',
  standalone: true,
  imports: [FormsModule],
  template: `
    @if (ticket(); as t) {
      <section>
        <h1>Ticket #{{ t.id_reclamo }} — {{ t.asunto }}</h1>
        <p>Estado: {{ t.estado }} · Prioridad: {{ t.prioridad ?? '—' }} · SLA: {{ t.sla_status ?? '—' }}</p>
        <p>{{ t.descripcion }}</p>

        <h2>Historial</h2>
        <ul>
          @for (h of historial(); track h.id_historial) {
            <li>
              [{{ h.tipo_accion }}] {{ h.mensaje }}
              @if (h.es_nota_interna) {
                <em>(nota interna)</em>
              }
            </li>
          }
        </ul>

        @if (esAgente()) {
          <form (ngSubmit)="comentar()">
            <label>
              Comentario
              <textarea name="mensaje" [(ngModel)]="mensaje"></textarea>
            </label>
            <label>
              <input type="checkbox" name="notaInterna" [(ngModel)]="notaInterna" />
              Nota interna
            </label>
            <button type="submit">Comentar</button>
          </form>
          <button type="button" (click)="resolver()">Marcar como resuelto</button>
        }

        @if (esCliente() && t.estado === 'Resuelto') {
          <button type="button" (click)="confirmarCierre()">Confirmar cierre</button>
        }
        @if (esCliente() && t.estado === 'Cerrado') {
          <button type="button" (click)="reabrir()">Reabrir ticket</button>
        }

        @if (mensajeAccion()) {
          <p data-testid="mensaje">{{ mensajeAccion() }}</p>
        }
      </section>
    }
  `,
})
export class DetalleTicketPage {
  private readonly api = inject(TicketApiService);
  private readonly authApi = inject(AuthApiService);
  private readonly route = inject(ActivatedRoute);

  readonly ticket = signal<Ticket | null>(null);
  readonly historial = signal<HistorialTicketItem[]>([]);
  readonly mensajeAccion = signal('');
  mensaje = '';
  notaInterna = false;

  constructor() {
    this.cargar();
  }

  private get idReclamo(): number {
    return Number(this.route.snapshot.paramMap.get('idReclamo'));
  }

  private cargar(): void {
    this.api.obtenerDetalle(this.idReclamo).subscribe({
      next: (res) => {
        this.ticket.set(res.data.ticket);
        this.historial.set(res.data.historial);
      },
    });
  }

  esAgente(): boolean {
    return (
      this.authApi.hasRole('Soporte') ||
      this.authApi.hasRole('DesarrolladorAPIs') ||
      this.authApi.hasRole('DirectorTecnologico') ||
      this.authApi.hasRole('Administrador')
    );
  }

  esCliente(): boolean {
    return this.authApi.hasRole('Cliente');
  }

  comentar(): void {
    if (!this.mensaje) {
      return;
    }
    this.api.comentar(this.idReclamo, this.mensaje, this.notaInterna).subscribe({
      next: () => {
        this.mensaje = '';
        this.notaInterna = false;
        this.cargar();
      },
    });
  }

  resolver(): void {
    this.api.resolver(this.idReclamo).subscribe({ next: () => this.cargar() });
  }

  confirmarCierre(): void {
    this.api.confirmarCierre(this.idReclamo).subscribe({ next: () => this.cargar() });
  }

  reabrir(): void {
    this.api.reabrir(this.idReclamo).subscribe({ next: () => this.cargar() });
  }
}

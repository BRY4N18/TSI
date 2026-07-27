import { NgClass } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { TicketApiService } from '../../services/ticket-api.service';
import { HistorialTicketItem, Ticket } from '../../services/models/soporte.types';

@Component({
  selector: 'app-detalle-ticket',
  standalone: true,
  imports: [FormsModule, NgClass, RouterLink, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './detalle-ticket.page.html',
})
export class DetalleTicketPage {
  private readonly api = inject(TicketApiService);
  private readonly authApi = inject(AuthApiService);
  private readonly route = inject(ActivatedRoute);

  readonly ticket = signal<Ticket | null>(null);
  readonly historial = signal<HistorialTicketItem[]>([]);
  readonly mensajeAccion = signal('');
  readonly cargando = signal(false);
  mensaje = '';
  notaInterna = false;

  constructor() {
    this.cargar();
  }

  private get idReclamo(): number {
    return Number(this.route.snapshot.paramMap.get('idReclamo'));
  }

  cargar(): void {
    this.cargando.set(true);
    this.api.obtenerDetalle(this.idReclamo).subscribe({
      next: (res) => {
        this.ticket.set(res.data.ticket);
        this.historial.set(res.data.historial);
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
        this.mensajeAccion.set('No se pudo cargar el ticket.');
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

  labelEstado(estado: string): string {
    return estado.replaceAll('_', ' ');
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
      error: () => this.mensajeAccion.set('Error al comentar'),
    });
  }

  resolver(): void {
    this.api.resolver(this.idReclamo).subscribe({
      next: () => this.cargar(),
      error: () => this.mensajeAccion.set('Error al resolver'),
    });
  }

  confirmarCierre(): void {
    this.api.confirmarCierre(this.idReclamo).subscribe({
      next: () => this.cargar(),
      error: () => this.mensajeAccion.set('Error al confirmar cierre'),
    });
  }

  reabrir(): void {
    this.api.reabrir(this.idReclamo).subscribe({
      next: () => this.cargar(),
      error: () => this.mensajeAccion.set('Error al reabrir'),
    });
  }
}

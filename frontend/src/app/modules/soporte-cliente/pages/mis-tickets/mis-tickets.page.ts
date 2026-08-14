import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { FacturaApiService } from '../../../suscripciones/services/factura-api.service';
import { Factura } from '../../../suscripciones/services/models/suscripciones.types';
import { TicketApiService } from '../../services/ticket-api.service';
import { CatalogoItem, Ticket } from '../../services/models/soporte.types';

@Component({
  selector: 'app-mis-tickets',
  standalone: true,
  imports: [
    FormsModule,
    RouterLink,
    TablerIconComponent,
    ListLoadingSkeletonComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './mis-tickets.page.html',
})
export class MisTicketsPage {
  private readonly api = inject(TicketApiService);
  private readonly facturas = inject(FacturaApiService);
  private readonly route = inject(ActivatedRoute);

  readonly tickets = signal<Ticket[]>([]);
  readonly servicios = signal<CatalogoItem[]>([]);
  /** Solo las que aun tienen cobro pendiente: no hay nada que disputar en una
   * factura ya pagada, y una ya en disputa la rechaza el backend (RN-TIC-008). */
  readonly facturasDisputables = signal<Factura[]>([]);
  readonly mensaje = signal('');
  readonly cargando = signal(false);
  asunto = '';
  descripcion = '';
  tipo = 'tecnico';
  idservicio: number | null = null;
  /** RF-O83.2 — abre la disputa y **detiene el cobro automatico** de esa factura
   * mientras se resuelve. Sin este campo el cliente no tenia por donde ejercer
   * una capacidad que el backend ya ofrecia (hallazgo F19). */
  idfactura: string | null = null;

  constructor() {
    this.cargar();
    this.api.listarServicios().subscribe({
      next: (res) => this.servicios.set(res.data ?? []),
      error: () => this.servicios.set([]),
    });
    this.facturas.listar({ limit: 20 }).subscribe({
      next: (res) =>
        this.facturasDisputables.set(
          (res.data ?? []).filter(
            (f) => f.estado_pago === 'Pendiente' || f.estado_pago === 'Fallida',
          ),
        ),
      // Que no se puedan listar las facturas no puede impedir abrir un ticket
      // normal: el resto del formulario sigue siendo util.
      error: () => this.facturasDisputables.set([]),
    });
    // Llega preseleccionada desde «Disputar este cargo» del historial de facturas.
    const desdeFactura = this.route.snapshot.queryParamMap.get('idfactura');
    if (desdeFactura) {
      this.idfactura = desdeFactura;
      this.tipo = 'operativo';
    }
  }

  labelEstado(estado: string): string {
    return estado.replaceAll('_', ' ');
  }

  cargar(): void {
    this.cargando.set(true);
    this.api.listar().subscribe({
      next: (res) => {
        this.tickets.set(res.data.items);
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
        this.mensaje.set('No se pudieron cargar tus tickets.');
      },
    });
  }

  registrar(): void {
    if (!this.asunto || !this.descripcion) {
      return;
    }
    this.api
      .registrar({
        idcliente: 1,
        asunto: this.asunto,
        descripcion: this.descripcion,
        tipo: this.tipo,
        ...(this.idservicio != null ? { idservicio: this.idservicio } : {}),
        ...(this.idfactura ? { idfactura: this.idfactura } : {}),
      })
      .subscribe({
        next: (res) => {
          this.mensaje.set(`Ticket #${res.data.id_reclamo} registrado (${res.data.estado})`);
          this.asunto = '';
          this.descripcion = '';
          this.idservicio = null;
          this.idfactura = null;
          this.cargar();
        },
        // El 422 de "esa factura ya tiene una disputa abierta" es informacion
        // util, no ruido: mostrarlo tal cual evita que reintente a ciegas.
        error: (err) =>
          this.mensaje.set(err?.error?.detail ?? 'Error al registrar el ticket'),
      });
  }
}

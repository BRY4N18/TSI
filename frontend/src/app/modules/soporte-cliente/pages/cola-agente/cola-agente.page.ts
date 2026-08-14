import { NgClass } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { esAccionDelSistema, etiquetaAccion } from '../../historial-ui';
import { TicketApiService } from '../../services/ticket-api.service';
import {
  EstadoTicket,
  HistorialTicketItem,
  Ticket,
} from '../../services/models/soporte.types';

const PRIORIDADES = ['', 'baja', 'media', 'alta', 'cr\u00edtico'] as const;
const ESTADOS: { value: string; label: string }[] = [
  { value: '', label: 'Todos los estados' },
  { value: 'Abierto', label: 'Abierto' },
  { value: 'Pendiente_de_clasificacion', label: 'Pendiente de clasificaci\u00f3n' },
  { value: 'En_progreso', label: 'En progreso' },
  { value: 'Escalado', label: 'Escalado' },
  { value: 'Resuelto', label: 'Resuelto' },
  { value: 'Cerrado', label: 'Cerrado' },
  { value: 'Reabierto', label: 'Reabierto' },
];

type BadgeTone = 'neutral' | 'info' | 'success' | 'warning' | 'urgent' | 'critical';

@Component({
  selector: 'app-cola-agente',
  standalone: true,
  imports: [FormsModule, NgClass, TablerIconComponent, ListEmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './cola-agente.page.html',
})
export class ColaAgentePage {
  private readonly api = inject(TicketApiService);

  readonly prioridades = PRIORIDADES;
  readonly estados = ESTADOS;

  readonly tickets = signal<Ticket[]>([]);
  readonly seleccionadoId = signal<number | null>(null);
  readonly ticketDetalle = signal<Ticket | null>(null);
  readonly historial = signal<HistorialTicketItem[]>([]);
  readonly filtroPrioridad = signal('');
  readonly filtroEstado = signal('');
  readonly cargando = signal(false);
  readonly detalleCargando = signal(false);
  readonly accionEnCurso = signal(false);
  readonly mensajeAccion = signal('');
  readonly error = signal('');

  textoRespuesta = '';
  notaInterna = false;

  constructor() {
    this.cargarLista();
  }

  onFiltroPrioridad(value: string): void {
    this.filtroPrioridad.set(value);
    this.cargarLista();
  }

  onFiltroEstado(value: string): void {
    this.filtroEstado.set(value);
    this.cargarLista();
  }

  cargarLista(): void {
    this.cargando.set(true);
    this.error.set('');
    const params: { prioridad?: string; idestadosoporte?: string } = {};
    if (this.filtroPrioridad()) {
      params.prioridad = this.filtroPrioridad();
    }
    if (this.filtroEstado()) {
      params.idestadosoporte = this.filtroEstado();
    }
    this.api.listar(params).subscribe({
      next: (res) => {
        const items = res.data.items;
        this.tickets.set(items);
        this.cargando.set(false);
        const current = this.seleccionadoId();
        if (current && items.some((t) => t.id_reclamo === current)) {
          this.cargarDetalle(current);
        } else if (items.length) {
          this.seleccionar(this.primerTicketAccionable(items));
        } else {
          this.seleccionadoId.set(null);
          this.ticketDetalle.set(null);
          this.historial.set([]);
        }
      },
      error: () => {
        this.cargando.set(false);
        this.error.set('No se pudo cargar la cola de soporte.');
      },
    });
  }

  seleccionar(ticket: Ticket): void {
    this.seleccionadoId.set(ticket.id_reclamo);
    this.cargarDetalle(ticket.id_reclamo);
  }

  private cargarDetalle(id: number): void {
    this.detalleCargando.set(true);
    this.api.obtenerDetalle(id).subscribe({
      next: (res) => {
        this.ticketDetalle.set(res.data.ticket);
        this.historial.set(res.data.historial);
        this.detalleCargando.set(false);
      },
      error: () => {
        this.detalleCargando.set(false);
        this.error.set('No se pudo cargar el detalle del ticket.');
      },
    });
  }

  puedeTomar(t: Ticket): boolean {
    return t.estado === 'Abierto' || t.estado === 'Reabierto';
  }

  puedeResolver(t: Ticket): boolean {
    return t.estado === 'En_progreso' || t.estado === 'Escalado';
  }

  puedeResponder(t: Ticket): boolean {
    return t.estado !== 'Cerrado';
  }

  private primerTicketAccionable(items: Ticket[]): Ticket {
    const preferidos = new Set([
      'Abierto',
      'Reabierto',
      'En_progreso',
      'Escalado',
      'Pendiente_de_clasificacion',
      'Resuelto',
    ]);
    return items.find((t) => preferidos.has(t.estado)) ?? items[0];
  }

  etiquetaAsignacion(t: Ticket): string {
    return t.id_agente_asignado ? `Agente #${t.id_agente_asignado}` : 'Sin asignar';
  }

  tomar(): void {
    const id = this.seleccionadoId();
    if (id == null) {
      return;
    }
    this.accionEnCurso.set(true);
    this.api.tomar(id).subscribe({
      next: () => {
        this.mensajeAccion.set(`Ticket #${id} tomado`);
        this.accionEnCurso.set(false);
        this.cargarLista();
      },
      error: () => {
        this.accionEnCurso.set(false);
        this.mensajeAccion.set('Error al tomar el ticket');
      },
    });
  }

  resolver(): void {
    const id = this.seleccionadoId();
    if (id == null) {
      return;
    }
    this.accionEnCurso.set(true);
    this.api.resolver(id).subscribe({
      next: () => {
        this.mensajeAccion.set(`Ticket #${id} marcado como resuelto`);
        this.accionEnCurso.set(false);
        this.cargarLista();
      },
      error: () => {
        this.accionEnCurso.set(false);
        this.mensajeAccion.set('Error al resolver el ticket');
      },
    });
  }

  enviarRespuesta(): void {
    const id = this.seleccionadoId();
    const texto = this.textoRespuesta.trim();
    if (id == null || !texto) {
      return;
    }
    this.accionEnCurso.set(true);
    this.api.comentar(id, texto, this.notaInterna).subscribe({
      next: () => {
        this.textoRespuesta = '';
        this.notaInterna = false;
        this.accionEnCurso.set(false);
        this.cargarDetalle(id);
      },
      error: () => {
        this.accionEnCurso.set(false);
        this.mensajeAccion.set('Error al enviar la respuesta');
      },
    });
  }

  labelPrioridad(p: string): string {
    if (!p) {
      return '';
    }
    return p.charAt(0).toUpperCase() + p.slice(1);
  }

  labelEstado(estado: EstadoTicket | string): string {
    return String(estado).replaceAll('_', ' ');
  }

  prioridadTone(prioridad: string): BadgeTone {
    const p = prioridad.toLowerCase();
    if (p === 'cr\u00edtico' || p === 'critico') {
      return 'critical';
    }
    if (p === 'alta') {
      return 'urgent';
    }
    if (p === 'media') {
      return 'warning';
    }
    return 'neutral';
  }

  estadoTone(estado: EstadoTicket | string): BadgeTone {
    switch (estado) {
      case 'Resuelto':
      case 'Cerrado':
        return 'success';
      case 'Escalado':
      case 'Pendiente_de_clasificacion':
        return 'urgent';
      case 'En_progreso':
      case 'Reabierto':
        return 'info';
      case 'Abierto':
        return 'warning';
      default:
        return 'neutral';
    }
  }

  badgeClass(tone: BadgeTone): string {
    switch (tone) {
      case 'info':
        return 'tsi-badge-info';
      case 'success':
        return 'tsi-badge-success';
      case 'warning':
        return 'tsi-badge-warning';
      case 'urgent':
        return 'tsi-badge-urgent';
      case 'critical':
        return 'tsi-badge-critical';
      default:
        return 'tsi-badge-neutral';
    }
  }
  /** Frase legible en vez del identificador interno de la acción. */
  etiqueta(tipoAccion: string): string {
    return etiquetaAccion(tipoAccion);
  }

  /** R-03: una acción automática debe distinguirse de una humana al leerla. */
  esDelSistema(h: HistorialTicketItem): boolean {
    return esAccionDelSistema(h);
  }

}

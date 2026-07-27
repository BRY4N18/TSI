import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { TicketApiService } from '../../services/ticket-api.service';
import { Ticket } from '../../services/models/soporte.types';

@Component({
  selector: 'app-mis-tickets',
  standalone: true,
  imports: [FormsModule, RouterLink, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './mis-tickets.page.html',
})
export class MisTicketsPage {
  private readonly api = inject(TicketApiService);

  readonly tickets = signal<Ticket[]>([]);
  readonly mensaje = signal('');
  readonly cargando = signal(false);
  asunto = '';
  descripcion = '';
  tipo = 'tecnico';

  constructor() {
    this.cargar();
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

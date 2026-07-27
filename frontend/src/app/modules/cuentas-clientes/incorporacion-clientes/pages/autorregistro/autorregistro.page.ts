import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { NotificationService } from '../../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { IncorporacionClienteApiService } from '../../services/incorporacion-cliente-api.service';
import {
  AutorregistroProveedorRequest,
  TipoCliente,
} from '../../models/incorporacion-cliente.contract';

@Component({
  selector: 'app-autorregistro-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TablerIconComponent],
  templateUrl: './autorregistro.page.html',
})
export class AutorregistroPage {
  private readonly api = inject(IncorporacionClienteApiService);
  private readonly notifications = inject(NotificationService);

  readonly tipos: TipoCliente[] = ['Proveedor', 'Aseguradora', 'Municipio', 'Smart City'];
  form: AutorregistroProveedorRequest = {
    razon_social: '',
    nombre: '',
    tipo: 'Proveedor',
    nit_identificacion: '',
    admin_local: { nombres: '', apellidos: '', gmail: '' },
  };
  enviando = false;
  enviado = false;
  idSolicitud: number | null = null;
  estadoSolicitud = '';

  enviar(): void {
    this.enviando = true;
    this.api.autorregistrar(this.form).subscribe({
      next: (res) => {
        this.enviando = false;
        this.enviado = true;
        this.idSolicitud = res.data.idcliente;
        this.estadoSolicitud = res.data.estado;
        this.notifications.toast(
          `Solicitud #${res.data.idcliente} enviada. Queda en revisión.`,
          'success',
        );
      },
      error: (err) => {
        this.enviando = false;
        this.notifications.toast(
          err?.error?.detail || 'No se pudo enviar la solicitud',
          'critical',
        );
      },
    });
  }

  nuevaSolicitud(): void {
    this.enviado = false;
    this.idSolicitud = null;
    this.estadoSolicitud = '';
    this.form = {
      razon_social: '',
      nombre: '',
      tipo: 'Proveedor',
      nit_identificacion: '',
      admin_local: { nombres: '', apellidos: '', gmail: '' },
    };
  }
}

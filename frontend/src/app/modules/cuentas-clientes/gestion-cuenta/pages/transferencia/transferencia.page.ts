import { ChangeDetectorRef, Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { CuentaClienteApiService } from '../../services/cuenta-cliente-api.service';
import { UsuarioElegible } from '../../models/cuenta-cliente.contract';

@Component({
  selector: 'app-transferencia-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './transferencia.page.html',
})
export class TransferenciaPage implements OnInit {
  private readonly api = inject(CuentaClienteApiService);
  private readonly route = inject(ActivatedRoute);
  // El shell de la aplicación es OnPush: sin marcar la vista, nada de lo que
  // llega por HTTP se repinta. Ver §9 del design-system.
  private readonly cdr = inject(ChangeDetectorRef);

  usuarios: UsuarioElegible[] = [];
  selectedId: number | null = null;
  mensaje = '';
  error = '';
  /** La cuenta se nombra por su razón social, no por su identificador (§8 del design-system). */
  razonSocial = '';
  readonly idcliente = Number(this.route.snapshot.paramMap.get('idcliente')) || 1;

  ngOnInit(): void {
    this.api.getPerfil(this.idcliente).subscribe({
      next: (res) => {
        this.razonSocial = res.data.razon_social ?? '';
        this.cdr.markForCheck();
      },
      error: () => undefined,
    });
    this.api.listUsuariosElegibles(this.idcliente).subscribe({
      next: (res) => {
        this.cdr.markForCheck();
        this.usuarios = res.data.usuarios;
        this.selectedId = this.usuarios[0]?.idusuario ?? null;
      },
      error: () => {
        this.cdr.markForCheck();
        this.error = 'No se pudieron cargar los usuarios elegibles.';
      },
    });
  }

  transferir(): void {
    if (!this.selectedId) return;
    this.api.transferirPropiedad(this.idcliente, this.selectedId).subscribe({
      next: () => {
        this.cdr.markForCheck();
        this.mensaje = 'Transferencia confirmada.';
        this.error = '';
      },
      error: () => {
        this.cdr.markForCheck();
        this.error = 'No se pudo transferir la propiedad.';
      },
    });
  }
}

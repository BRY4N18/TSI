import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { CuentaClienteApiService } from '../../services/cuenta-cliente-api.service';

@Component({
  selector: 'app-baja-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './baja.page.html',
})
export class BajaPage {
  private readonly api = inject(CuentaClienteApiService);
  private readonly route = inject(ActivatedRoute);

  motivo = '';
  mensaje = '';
  error = '';
  readonly idcliente = Number(this.route.snapshot.paramMap.get('idcliente')) || 1;

  confirmar(): void {
    this.api.darBaja(this.idcliente, this.motivo || undefined).subscribe({
      next: () => {
        this.mensaje = `Cuenta #${this.idcliente} dada de baja.`;
        this.error = '';
      },
      error: () => {
        this.error = 'No se pudo dar de baja la cuenta.';
      },
    });
  }
}

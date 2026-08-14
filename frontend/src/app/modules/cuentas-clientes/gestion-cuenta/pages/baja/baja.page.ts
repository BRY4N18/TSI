import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
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
export class BajaPage implements OnInit {
  private readonly api = inject(CuentaClienteApiService);
  private readonly route = inject(ActivatedRoute);
  // El shell de la aplicación es OnPush: sin marcar la vista, nada de lo que
  // llega por HTTP se repinta. Ver §9 del design-system.
  private readonly cdr = inject(ChangeDetectorRef);

  motivo = '';
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
  }

  confirmar(): void {
    this.api.darBaja(this.idcliente, this.motivo || undefined).subscribe({
      next: () => {
        this.cdr.markForCheck();
        this.mensaje = `${this.razonSocial || 'La cuenta'} quedó dada de baja. Su historial se conserva.`;
        this.error = '';
      },
      error: () => {
        this.cdr.markForCheck();
        this.error = 'No se pudo dar de baja la cuenta.';
      },
    });
  }
}

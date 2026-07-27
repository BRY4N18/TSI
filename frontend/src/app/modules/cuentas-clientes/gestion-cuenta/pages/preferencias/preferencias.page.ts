import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { CuentaClienteApiService } from '../../services/cuenta-cliente-api.service';
import { PreferenciasData } from '../../models/cuenta-cliente.contract';

@Component({
  selector: 'app-preferencias-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './preferencias.page.html',
})
export class PreferenciasPage implements OnInit {
  private readonly api = inject(CuentaClienteApiService);
  private readonly route = inject(ActivatedRoute);

  preferencias: PreferenciasData | null = null;
  mensaje = '';
  error = '';
  readonly idcliente = Number(this.route.snapshot.paramMap.get('idcliente')) || 1;

  ngOnInit(): void {
    this.api.getPreferencias(this.idcliente).subscribe({
      next: (res) => {
        this.preferencias = res.data;
      },
      error: () => {
        this.error = 'No se pudieron cargar las preferencias.';
      },
    });
  }

  guardar(): void {
    if (!this.preferencias) return;
    this.api
      .patchPreferencias(this.idcliente, {
        telefono_sms: this.preferencias.telefono_sms ?? undefined,
        canales_notificacion: this.preferencias.canales_notificacion,
      })
      .subscribe({
        next: () => {
          this.mensaje = 'Preferencias guardadas.';
          this.error = '';
        },
        error: () => {
          this.error = 'No se pudieron guardar las preferencias.';
        },
      });
  }
}

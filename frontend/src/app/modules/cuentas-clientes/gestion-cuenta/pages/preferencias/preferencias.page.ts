import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { CuentaClienteApiService } from '../../services/cuenta-cliente-api.service';
import { PreferenciasData } from '../../models/cuenta-cliente.contract';

@Component({
  selector: 'app-preferencias-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h1>Preferencias operativas</h1>
    @if (preferencias) {
      <form (ngSubmit)="guardar()">
        <label>Teléfono SMS <input [(ngModel)]="preferencias.telefono_sms" name="telefono_sms" /></label>
        <label>Canales <input [(ngModel)]="preferencias.canales_notificacion" name="canales" /></label>
        <button type="submit">Guardar</button>
      </form>
    }
  `,
})
export class PreferenciasPage {
  private readonly api = inject(CuentaClienteApiService);
  preferencias: PreferenciasData | null = null;
  readonly idcliente = 1;

  ngOnInit(): void {
    this.api.getPreferencias(this.idcliente).subscribe((res) => {
      this.preferencias = res.data;
    });
  }

  guardar(): void {
    if (!this.preferencias) return;
    this.api.patchPreferencias(this.idcliente, {
      telefono_sms: this.preferencias.telefono_sms ?? undefined,
      canales_notificacion: this.preferencias.canales_notificacion,
    }).subscribe();
  }
}

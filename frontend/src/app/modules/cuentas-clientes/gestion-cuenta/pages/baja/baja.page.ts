import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { CuentaClienteApiService } from '../../services/cuenta-cliente-api.service';

@Component({
  selector: 'app-baja-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h1>Dar de baja cuenta</h1>
    <label>Motivo (opcional) <textarea [(ngModel)]="motivo" name="motivo"></textarea></label>
    <button type="button" (click)="confirmar()">Confirmar baja</button>
  `,
})
export class BajaPage {
  private readonly api = inject(CuentaClienteApiService);
  motivo = '';
  readonly idcliente = 1;

  confirmar(): void {
    this.api.darBaja(this.idcliente, this.motivo || undefined).subscribe();
  }
}

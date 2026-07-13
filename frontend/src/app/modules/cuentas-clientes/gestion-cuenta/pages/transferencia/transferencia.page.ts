import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { CuentaClienteApiService } from '../../services/cuenta-cliente-api.service';
import { UsuarioElegible } from '../../models/cuenta-cliente.contract';

@Component({
  selector: 'app-transferencia-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h1>Transferir administración</h1>
    <select [(ngModel)]="selectedId" name="responsable">
      @for (u of usuarios; track u.idusuario) {
        <option [value]="u.idusuario">{{ u.nombres }} {{ u.apellidos }}</option>
      }
    </select>
    <button type="button" (click)="transferir()">Confirmar transferencia</button>
  `,
})
export class TransferenciaPage {
  private readonly api = inject(CuentaClienteApiService);
  usuarios: UsuarioElegible[] = [];
  selectedId: number | null = null;
  readonly idcliente = 1;

  ngOnInit(): void {
    this.api.listUsuariosElegibles(this.idcliente).subscribe((res) => {
      this.usuarios = res.data.usuarios;
      this.selectedId = this.usuarios[0]?.idusuario ?? null;
    });
  }

  transferir(): void {
    if (!this.selectedId) return;
    this.api.transferirPropiedad(this.idcliente, this.selectedId).subscribe();
  }
}

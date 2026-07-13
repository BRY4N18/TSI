import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { inject } from '@angular/core';

import { CuentaClienteApiService } from '../../services/cuenta-cliente-api.service';
import { PerfilData } from '../../models/cuenta-cliente.contract';

@Component({
  selector: 'app-perfil-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h1>Perfil corporativo</h1>
    @if (perfil) {
      <form (ngSubmit)="guardar()">
        <label>Razón social <input [(ngModel)]="perfil.razon_social" name="razon_social" /></label>
        <label>Nombre <input [(ngModel)]="perfil.nombre" name="nombre" /></label>
        <p>Tipo: {{ perfil.tipo }} (solo lectura)</p>
        <p>NIT: {{ perfil.nit_identificacion }} (solo lectura)</p>
        <button type="submit">Guardar</button>
      </form>
    }
  `,
})
export class PerfilPage {
  private readonly api = inject(CuentaClienteApiService);
  perfil: PerfilData | null = null;
  readonly idcliente = 1;

  ngOnInit(): void {
    this.api.getPerfil(this.idcliente).subscribe((res) => {
      this.perfil = res.data;
    });
  }

  guardar(): void {
    if (!this.perfil) return;
    this.api
      .patchPerfil(this.idcliente, {
        razon_social: this.perfil.razon_social,
        nombre: this.perfil.nombre,
      })
      .subscribe();
  }
}

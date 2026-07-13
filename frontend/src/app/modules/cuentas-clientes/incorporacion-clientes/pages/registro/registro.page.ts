import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { IncorporacionClienteApiService } from '../../services/incorporacion-cliente-api.service';
import { RegistroCuentaRequest, TipoCliente } from '../../models/incorporacion-cliente.contract';

@Component({
  selector: 'app-registro-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h1>Registro de cuenta cliente</h1>
    <form (ngSubmit)="registrar()">
      <label>Razón social <input [(ngModel)]="form.razon_social" name="razon_social" required /></label>
      <label>Nombre <input [(ngModel)]="form.nombre" name="nombre" /></label>
      <label>
        Tipo
        <select [(ngModel)]="form.tipo" name="tipo">
          @for (t of tipos; track t) {
            <option [value]="t">{{ t }}</option>
          }
        </select>
      </label>
      <label>NIT <input [(ngModel)]="form.nit_identificacion" name="nit" required /></label>
      <label>Fecha inicio contrato <input type="date" [(ngModel)]="fechaContrato" name="fecha" required /></label>
      <fieldset>
        <legend>Administrador local</legend>
        <label>Nombres <input [(ngModel)]="form.admin_local.nombres" name="nombres" required /></label>
        <label>Apellidos <input [(ngModel)]="form.admin_local.apellidos" name="apellidos" required /></label>
        <label>Email <input type="email" [(ngModel)]="form.admin_local.gmail" name="gmail" required /></label>
      </fieldset>
      <button type="submit" [disabled]="enviando">Registrar cuenta</button>
    </form>
    @if (mensaje) {
      <p class="ok">{{ mensaje }}</p>
    }
    @if (error) {
      <p class="err">{{ error }}</p>
    }
  `,
  styles: [
    `
      form {
        display: grid;
        gap: 0.75rem;
        max-width: 28rem;
      }
      fieldset {
        display: grid;
        gap: 0.5rem;
        border: 1px solid var(--border-default);
        border-radius: var(--radius-md);
        padding: 1rem;
      }
      .ok {
        color: #3b6d11;
      }
      .err {
        color: #b42318;
      }
    `,
  ],
})
export class RegistroPage {
  private readonly api = inject(IncorporacionClienteApiService);
  private readonly router = inject(Router);

  readonly tipos: TipoCliente[] = ['Aseguradora', 'Municipio', 'Smart City'];
  fechaContrato = '';
  enviando = false;
  mensaje = '';
  error = '';

  form: RegistroCuentaRequest = {
    razon_social: '',
    nombre: '',
    tipo: 'Aseguradora',
    nit_identificacion: '',
    fecha_inicio_contrato: 0,
    admin_local: { nombres: '', apellidos: '', gmail: '' },
  };

  registrar(): void {
    this.enviando = true;
    this.error = '';
    this.mensaje = '';
    const payload: RegistroCuentaRequest = {
      ...this.form,
      fecha_inicio_contrato: new Date(this.fechaContrato).getTime(),
    };

    this.api.registrarCuenta(payload).subscribe({
      next: (res) => {
        this.mensaje = `Cuenta #${res.data.idcliente} creada. Admin: ${res.data.admin_local_gmail}`;
        this.enviando = false;
        this.router.navigate([
          '/cuentas-clientes/incorporacion-clientes',
          res.data.idcliente,
          'configuracion',
        ]);
      },
      error: (err) => {
        this.error = err?.error?.detail ?? 'No se pudo registrar la cuenta';
        this.enviando = false;
      },
    });
  }
}

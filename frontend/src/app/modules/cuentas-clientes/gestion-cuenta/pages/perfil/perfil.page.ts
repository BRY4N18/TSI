import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { CuentaClienteFacadeService } from '../../services/cuenta-cliente-facade.service';
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
        @if (perfil.logo_url) {
          <p>
            Logo actual:
            <a [href]="perfil.logo_url" target="_blank" rel="noopener">ver</a>
          </p>
        }
        <label>
          Actualizar logo
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            (change)="onLogoSeleccionado($event)"
            name="logo"
          />
        </label>
        @if (mensaje) {
          <p class="ok">{{ mensaje }}</p>
        }
        @if (error) {
          <p class="err">{{ error }}</p>
        }
        <button type="submit">Guardar</button>
      </form>
    }
  `,
  styles: [
    `
      form {
        display: grid;
        gap: 0.75rem;
        max-width: 28rem;
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
export class PerfilPage implements OnInit {
  private readonly api = inject(CuentaClienteApiService);
  private readonly facade = inject(CuentaClienteFacadeService);
  private readonly route = inject(ActivatedRoute);

  perfil: PerfilData | null = null;
  logoFile: File | null = null;
  mensaje = '';
  error = '';
  readonly idcliente = Number(this.route.snapshot.paramMap.get('idcliente')) || 1;

  ngOnInit(): void {
    this.api.getPerfil(this.idcliente).subscribe((res) => {
      this.perfil = res.data;
    });
  }

  onLogoSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.logoFile = input.files?.[0] ?? null;
  }

  guardar(): void {
    if (!this.perfil) return;
    this.mensaje = '';
    this.error = '';

    if (this.logoFile) {
      this.facade.uploadLogoAndUpdatePerfil(this.idcliente, this.logoFile).subscribe({
        next: (data) => {
          if (this.perfil && data.perfil) {
            this.perfil.logo_url = data.perfil.logo_url;
          }
          this.logoFile = null;
          this._guardarTextos();
        },
        error: (err) => {
          this.error = err?.error?.detail ?? 'No se pudo subir el logo';
        },
      });
      return;
    }

    this._guardarTextos();
  }

  private _guardarTextos(): void {
    if (!this.perfil) return;
    this.api
      .patchPerfil(this.idcliente, {
        razon_social: this.perfil.razon_social,
        nombre: this.perfil.nombre,
      })
      .subscribe({
        next: () => {
          this.mensaje = 'Perfil actualizado';
        },
        error: (err) => {
          this.error = err?.error?.detail ?? 'No se pudo guardar el perfil';
        },
      });
  }
}

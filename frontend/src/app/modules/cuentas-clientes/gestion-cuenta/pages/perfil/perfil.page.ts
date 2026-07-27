import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { CuentaClienteFacadeService } from '../../services/cuenta-cliente-facade.service';
import { CuentaClienteApiService } from '../../services/cuenta-cliente-api.service';
import { PerfilData } from '../../models/cuenta-cliente.contract';

@Component({
  selector: 'app-perfil-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './perfil.page.html',
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
    this.api.getPerfil(this.idcliente).subscribe({
      next: (res) => {
        this.perfil = res.data;
      },
      error: (err) => {
        this.error = err?.error?.detail ?? 'No se pudo cargar el perfil';
      },
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

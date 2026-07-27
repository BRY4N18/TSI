import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ConversionApiService } from '../../services/conversion-api.service';

@Component({
  selector: 'app-entrada-directa',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="page">
      <h1>Entrada directa de cliente</h1>
      @if (success()) {
        <p class="ok">Cliente creado (idprospecto=null).</p>
      } @else {
        <form [formGroup]="form" (ngSubmit)="enviar()">
          <input formControlName="nombre" placeholder="Nombre" />
          <input formControlName="razon_social" placeholder="Razón social" />
          <select formControlName="tipo">
            <option value="Municipio">Municipio</option>
            <option value="Aseguradora">Aseguradora</option>
            <option value="Proveedor">Proveedor</option>
            <option value="Smart City">Smart City</option>
          </select>
          <input formControlName="nit_identificacion" placeholder="NIT" />
          <button type="submit" [disabled]="loading() || form.invalid">Crear</button>
        </form>
        @if (error()) {
          <p class="err">{{ error() }}</p>
          <button type="button" (click)="enviar()">Reintentar</button>
        }
      }
    </section>
  `,
  styles: `
    .page {
      max-width: 24rem;
      margin: 1.5rem auto;
      display: grid;
      gap: 0.5rem;
    }
    form {
      display: grid;
      gap: 0.5rem;
    }
    .err {
      color: #b00020;
    }
    .ok {
      color: #0a7a32;
    }
  `,
})
export class EntradaDirectaPage {
  private readonly api = inject(ConversionApiService);
  private readonly fb = inject(FormBuilder);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal(false);

  readonly form = this.fb.nonNullable.group({
    nombre: ['', Validators.required],
    razon_social: ['', Validators.required],
    tipo: ['Municipio' as const, Validators.required],
    nit_identificacion: ['', Validators.required],
  });

  enviar(): void {
    if (this.form.invalid) return;
    this.loading.set(true);
    this.error.set(null);
    this.api.entradaDirecta(this.form.getRawValue()).subscribe({
      next: () => {
        this.loading.set(false);
        this.success.set(true);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err?.error?.detail ?? 'No se pudo crear el cliente');
      },
    });
  }
}

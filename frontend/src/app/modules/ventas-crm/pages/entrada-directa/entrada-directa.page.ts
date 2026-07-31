import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  inject,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ConversionApiService } from '../../services/conversion-api.service';
import { TipoCliente } from '../../models/prospectos.types';

@Component({
  selector: 'app-entrada-directa',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="mx-auto max-w-6xl p-8">
      <a
        routerLink="/ventas-crm/prospectos"
        class="mb-6 inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary no-underline hover:text-text-primary"
      >
        <app-tabler-icon name="arrow-left" [size]="16" />
        Volver a la lista
      </a>

      <div class="mb-6">
        <p class="m-0 text-sm font-medium text-text-secondary">Administración</p>
        <h1 class="m-0 mt-1 text-2xl font-bold text-text-primary">Entrada directa</h1>
        <p class="m-0 mt-1 text-sm text-text-secondary">
          Crear cliente sin prospecto previo (solo Administrador)
        </p>
      </div>

      @if (success()) {
        <section
          class="grid place-items-center gap-3 rounded-lg border border-alert-success bg-alert-success-bg p-10 text-center"
          data-testid="entrada-directa-ok"
        >
          <app-tabler-icon name="circle-check" [size]="32" />
          <p class="m-0 text-sm text-alert-success">Cliente creado correctamente.</p>
          <button
            type="button"
            class="inline-flex min-h-11 items-center gap-2 rounded-md bg-accent-primary px-4 text-sm font-semibold text-white hover:bg-accent-hover"
            (click)="reset()"
          >
            Crear otro
          </button>
        </section>
      } @else {
        <form
          class="grid max-w-xl gap-4 rounded-lg border border-border-default bg-bg-surface p-6"
          [formGroup]="form"
          (ngSubmit)="enviar()"
        >
          <h2 class="m-0 text-base font-semibold text-text-primary">Datos del cliente</h2>

          <label class="grid gap-1.5 text-sm font-medium text-text-secondary">
            Nombre
            <input
              formControlName="nombre"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            />
          </label>
          <label class="grid gap-1.5 text-sm font-medium text-text-secondary">
            Razón social
            <input
              formControlName="razon_social"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            />
          </label>
          <label class="grid gap-1.5 text-sm font-medium text-text-secondary">
            Tipo
            <select
              formControlName="tipo"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            >
              <option value="Municipio">Municipio</option>
              <option value="Aseguradora">Aseguradora</option>
              <option value="Proveedor">Proveedor</option>
              <option value="Smart City">Smart City</option>
            </select>
          </label>
          <label class="grid gap-1.5 text-sm font-medium text-text-secondary">
            NIT
            <input
              formControlName="nit_identificacion"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            />
          </label>

          @if (error()) {
            <div
              class="flex items-center gap-2 rounded-md border border-alert-critical bg-alert-critical-bg px-4 py-3 text-sm text-alert-critical"
              role="alert"
            >
              <app-tabler-icon name="alert-triangle" [size]="18" />
              <span>{{ error() }}</span>
            </div>
          }

          <button
            type="submit"
            data-testid="btn-crear-cliente-directo"
            class="inline-flex min-h-11 w-fit items-center gap-2 rounded-md bg-accent-primary px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-hover disabled:opacity-60"
            [disabled]="loading() || form.invalid"
          >
            @if (loading()) {
              <span
                class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
                aria-hidden="true"
              ></span>
              Creando…
            } @else {
              Crear cliente
            }
          </button>
        </form>
      }
    </div>
  `,
})
export class EntradaDirectaPage {
  private readonly api = inject(ConversionApiService);
  private readonly fb = inject(FormBuilder);
  private readonly notifications = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal(false);

  readonly form = this.fb.nonNullable.group({
    nombre: ['', Validators.required],
    razon_social: ['', Validators.required],
    tipo: ['Municipio' as TipoCliente, Validators.required],
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
        this.notifications.toast('Cliente creado.', 'success');
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err?.error?.detail ?? 'No se pudo crear el cliente');
        this.cdr.markForCheck();
      },
    });
  }

  reset(): void {
    this.success.set(false);
    this.form.reset({
      nombre: '',
      razon_social: '',
      tipo: 'Municipio',
      nit_identificacion: '',
    });
  }
}

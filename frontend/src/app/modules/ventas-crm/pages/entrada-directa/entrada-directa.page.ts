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
    <div class="mx-auto max-w-4xl px-4 py-8 text-text-primary">
      <a
        routerLink="/ventas-crm/prospectos"
        class="mb-6 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-secondary no-underline transition-colors hover:text-accent-primary"
      >
        <app-tabler-icon name="arrow-left" [size]="16" />
        Volver a prospectos
      </a>

      <header class="mb-6 border-b border-border-default pb-4">
        <p class="m-0 text-xs font-semibold uppercase tracking-wider text-text-secondary">Administración CRM</p>
        <h1 class="tsi-display m-0 text-2xl font-bold tracking-tight text-text-primary">Entrada directa de cliente</h1>
        <p class="m-0 mt-1 text-sm text-text-secondary">
          Alta directa de cliente y asignación de su primer administrador local sin pasar por el flujo de prospección.
        </p>
      </header>

      @if (success()) {
        <section
          class="grid place-items-center gap-4 rounded-xl border border-alert-success/40 bg-alert-success/10 p-12 text-center shadow-sm"
          data-testid="entrada-directa-ok"
        >
          <div class="flex h-16 w-16 items-center justify-center rounded-full bg-alert-success/20 text-alert-success">
            <app-tabler-icon name="circle-check" [size]="36" />
          </div>
          <div>
            <h2 class="tsi-display m-0 text-xl font-bold text-text-primary">¡Cliente creado exitosamente!</h2>
            <p class="m-0 mt-1 text-sm text-text-secondary">Se han generado las credenciales y el perfil corporativo del cliente.</p>
          </div>
          <div class="mt-2 flex flex-wrap gap-3">
            <button
              type="button"
              class="tsi-btn tsi-btn-primary inline-flex items-center gap-2"
              (click)="reset()"
            >
              <app-tabler-icon name="plus" [size]="16" />
              Crear otro cliente
            </button>
            <a
              routerLink="/ventas-crm/prospectos"
              class="tsi-btn tsi-btn-secondary no-underline"
            >
              Ver lista de prospectos
            </a>
          </div>
        </section>
      } @else {
        <form
          class="grid gap-6"
          [formGroup]="form"
          (ngSubmit)="enviar()"
        >
          <div class="tsi-panel tsi-panel--elevado rounded-xl border border-border-default bg-bg-surface p-6 shadow-sm">
            <div class="mb-4 flex items-center gap-2 border-b border-border-default/60 pb-3">
              <h2 class="tsi-display m-0 text-base font-semibold text-text-primary">1. Datos de la organización</h2>
            </div>

            <div class="grid gap-4 md:grid-cols-2">
              <div class="grid gap-1.5">
                <label for="org-nombre" class="text-xs font-semibold text-text-secondary">
                  Nombre comercial <span class="text-alert-danger">*</span>
                </label>
                <input
                  id="org-nombre"
                  formControlName="nombre"
                  class="tsi-input w-full"
                  placeholder="Ej. Flota Centro"
                />
              </div>

              <div class="grid gap-1.5">
                <label for="org-razon" class="text-xs font-semibold text-text-secondary">
                  Razón social <span class="text-alert-danger">*</span>
                </label>
                <input
                  id="org-razon"
                  formControlName="razon_social"
                  class="tsi-input w-full"
                  placeholder="Ej. Transportes del Norte S.A. de C.V."
                />
              </div>

              <div class="grid gap-1.5">
                <label for="org-tipo" class="text-xs font-semibold text-text-secondary">
                  Tipo de cliente <span class="text-alert-danger">*</span>
                </label>
                <select
                  id="org-tipo"
                  formControlName="tipo"
                  class="tsi-select w-full"
                >
                  <option value="Municipio">Municipio</option>
                  <option value="Aseguradora">Aseguradora</option>
                  <option value="Proveedor">Proveedor</option>
                  <option value="Smart City">Smart City</option>
                </select>
              </div>

              <div class="grid gap-1.5">
                <label for="org-nit" class="text-xs font-semibold text-text-secondary">
                  NIT / Identificación fiscal <span class="text-alert-danger">*</span>
                </label>
                <input
                  id="org-nit"
                  formControlName="nit_identificacion"
                  class="tsi-input w-full font-mono"
                  placeholder="RFC, NIT o RUT"
                />
              </div>
            </div>
          </div>

          <div class="tsi-panel tsi-panel--elevado rounded-xl border border-border-default bg-bg-surface p-6 shadow-sm">
            <div class="mb-4 flex items-center gap-2 border-b border-border-default/60 pb-3">
              <h2 class="tsi-display m-0 text-base font-semibold text-text-primary">
                2. Administrador local principal (primer usuario)
              </h2>
            </div>

            <div class="grid gap-4 md:grid-cols-2">
              <div class="grid gap-1.5">
                <label for="admin-nombres" class="text-xs font-semibold text-text-secondary">
                  Nombres <span class="text-alert-danger">*</span>
                </label>
                <input
                  id="admin-nombres"
                  formControlName="admin_nombres"
                  class="tsi-input w-full"
                  placeholder="Ej. María"
                />
              </div>

              <div class="grid gap-1.5">
                <label for="admin-apellidos" class="text-xs font-semibold text-text-secondary">
                  Apellidos <span class="text-alert-danger">*</span>
                </label>
                <input
                  id="admin-apellidos"
                  formControlName="admin_apellidos"
                  class="tsi-input w-full"
                  placeholder="Ej. Salazar"
                />
              </div>

              <div class="grid gap-1.5 md:col-span-2">
                <label for="admin-email" class="text-xs font-semibold text-text-secondary">
                  Correo electrónico institucional <span class="text-alert-danger">*</span>
                </label>
                <input
                  id="admin-email"
                  type="email"
                  formControlName="admin_gmail"
                  class="tsi-input w-full"
                  placeholder="nombre@empresa.com"
                />
              </div>
            </div>
          </div>

          @if (error()) {
            <div
              class="flex items-center gap-2.5 rounded-lg border border-alert-critical/40 bg-alert-critical-bg p-4 text-sm text-alert-critical"
              role="alert"
            >
              <app-tabler-icon name="alert-triangle" [size]="18" />
              <span>{{ error() }}</span>
            </div>
          }

          <div class="flex items-center justify-end gap-3 pt-2">
            <a
              routerLink="/ventas-crm/prospectos"
              class="tsi-btn tsi-btn-ghost no-underline"
            >
              Cancelar
            </a>
            <button
              type="submit"
              data-testid="btn-crear-cliente-directo"
              class="tsi-btn tsi-btn-primary inline-flex items-center gap-2"
              [disabled]="loading() || form.invalid"
            >
              @if (loading()) {
                <app-tabler-icon name="refresh" [size]="16" class="animate-spin" />
                Creando cliente...
              } @else {
                <app-tabler-icon name="circle-check" [size]="16" />
                Crear cliente
              }
            </button>
          </div>
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
    admin_nombres: ['', Validators.required],
    admin_apellidos: ['', Validators.required],
    admin_gmail: ['', [Validators.required, Validators.email]],
  });

  enviar(): void {
    if (this.form.invalid) return;
    this.loading.set(true);
    this.error.set(null);
    const raw = this.form.getRawValue();
    this.api
      .entradaDirecta({
        nombre: raw.nombre,
        razon_social: raw.razon_social,
        tipo: raw.tipo,
        nit_identificacion: raw.nit_identificacion,
        admin_local: {
          nombres: raw.admin_nombres,
          apellidos: raw.admin_apellidos,
          gmail: raw.admin_gmail.trim().toLowerCase(),
        },
      })
      .subscribe({
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
      admin_nombres: '',
      admin_apellidos: '',
      admin_gmail: '',
    });
  }
}

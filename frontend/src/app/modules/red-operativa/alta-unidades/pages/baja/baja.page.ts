import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';

@Component({
  selector: 'app-red-operativa-baja-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TablerIconComponent],
  template: `
    <div class="mx-auto max-w-2xl space-y-6 p-6">
      <header>
        <h1 class="text-[28px] font-bold text-text-primary">Dar de baja unidad #{{ idunidademergencia }}</h1>
      </header>

      <section class="space-y-4 rounded-lg border border-border-default bg-bg-surface p-6">
        <form (ngSubmit)="darDeBaja()" class="space-y-4">
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Motivo</span>
            <input
              [(ngModel)]="motivo"
              name="motivo"
              required
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
            />
          </label>
          <button
            type="submit"
            class="rounded-md border border-alert-critical px-5 py-2.5 font-medium text-alert-critical transition-colors hover:bg-alert-critical-bg"
          >
            Dar de baja
          </button>
        </form>

        @if (requiereForzar) {
          <div
            role="alert"
            class="space-y-3 rounded-md border-l-4 border-alert-warning bg-alert-warning-bg px-4 py-3 text-sm text-alert-warning"
          >
            <div class="flex items-center gap-2">
              <app-tabler-icon name="alert-triangle" [size]="18" />
              <span>La unidad tiene un despacho activo en curso. Confirma para forzar la baja.</span>
            </div>
            <button
              type="button"
              (click)="darDeBaja(true)"
              class="rounded-md border border-alert-warning px-4 py-2 text-sm font-medium text-alert-warning hover:bg-alert-warning/10"
            >
              Forzar baja
            </button>
          </div>
        }

        @if (mensaje) {
          <div
            class="flex items-center gap-2 rounded-md border-l-4 border-alert-success bg-alert-success-bg px-4 py-3 text-sm text-alert-success"
          >
            <app-tabler-icon name="circle-check" [size]="18" />
            <span>{{ mensaje }}</span>
          </div>
        }
      </section>

      <section class="space-y-4 rounded-lg border border-border-default bg-bg-surface p-6">
        <h2 class="text-lg font-semibold text-text-primary">Reactivar unidad</h2>
        <button
          type="button"
          (click)="reactivar()"
          class="rounded-md border border-accent-primary px-5 py-2.5 font-medium text-accent-primary transition-colors hover:bg-accent-primary/5"
        >
          Reactivar
        </button>
        @if (mensajeReactivacion) {
          <div class="flex items-center gap-2 text-sm text-text-secondary">
            <app-tabler-icon name="info-circle" [size]="16" />
            <span>{{ mensajeReactivacion }}</span>
          </div>
        }
      </section>
    </div>
  `,
})
export class BajaPage {
  private readonly route = inject(ActivatedRoute);
  private readonly facade = inject(UnidadEmergenciaFacadeService);

  readonly idunidademergencia = Number(this.route.snapshot.paramMap.get('idunidademergencia'));
  motivo = '';
  mensaje: string | null = null;
  mensajeReactivacion: string | null = null;
  requiereForzar = false;

  darDeBaja(forzar = false): void {
    this.mensaje = null;
    this.requiereForzar = false;
    this.facade.darDeBaja(this.idunidademergencia, this.motivo, forzar).subscribe((result) => {
      if (result.ok) {
        this.mensaje = 'Unidad dada de baja correctamente.';
      } else if (result.error?.includes('despacho activo')) {
        this.requiereForzar = true;
      } else {
        this.mensaje = result.error ?? 'Error al dar de baja la unidad';
      }
    });
  }

  reactivar(): void {
    this.mensajeReactivacion = null;
    this.facade.reactivar(this.idunidademergencia).subscribe((result) => {
      this.mensajeReactivacion = result.ok
        ? 'Unidad reactivada correctamente.'
        : (result.error ?? 'Error al reactivar la unidad');
    });
  }
}

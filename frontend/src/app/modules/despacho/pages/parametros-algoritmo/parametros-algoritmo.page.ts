import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { DespachoParametrosApiService } from '../../services/despacho-parametros-api.service';
import { ParametrosDespachoData } from '../../services/models/despacho.types';

@Component({
  selector: 'app-parametros-algoritmo',
  standalone: true,
  imports: [CommonModule, FormsModule, TablerIconComponent],
  template: `
    <section class="mx-auto max-w-2xl px-4 py-8 text-text-primary">
      <header class="mb-6 grid gap-1.5">
        <p class="m-0 text-xs font-semibold uppercase tracking-wider text-text-secondary">
          Despacho y asignación
        </p>
        <h1 class="tsi-display m-0 text-2xl font-bold tracking-tight text-text-primary">
          Parámetros del algoritmo
        </h1>
        <p class="m-0 text-sm text-text-secondary">
          Configuración global de tiempos límite y reglas operativas para el motor de asignación automática de unidades.
        </p>
      </header>

      @if (mensaje()) {
        <div
          class="mb-6 flex items-center gap-2.5 rounded-lg border p-4 text-sm"
          [ngClass]="esError() ? 'border-alert-danger/40 bg-alert-danger/10 text-alert-danger' : 'border-alert-success/40 bg-alert-success/10 text-alert-success'"
          role="status"
        >
          <app-tabler-icon [name]="esError() ? 'alert-circle' : 'circle-check'" [size]="18" />
          <span data-testid="mensaje">{{ mensaje() }}</span>
        </div>
      }

      <div class="tsi-panel tsi-panel--elevado rounded-xl border border-border-default bg-bg-surface p-6 shadow-sm">
        <h2 class="tsi-display m-0 text-base font-semibold text-text-primary">
          Tiempo límite de respuesta (Timeout)
        </h2>
        <p class="mt-1 text-xs text-text-secondary">
          Define el tiempo máximo que el algoritmo esperará la confirmación de una unidad antes de reasignar el caso a la siguiente unidad disponible.
        </p>

        <div class="mt-5 grid gap-4">
          <div class="grid gap-2">
            <label for="timeout-input" class="text-xs font-semibold text-text-secondary">
              Timeout de respuesta (segundos) <span class="text-accent-primary">*</span>
            </label>
            <div class="flex items-center gap-3">
              <div class="relative w-48">
                <input
                  id="timeout-input"
                  type="number"
                  [(ngModel)]="timeout"
                  min="30"
                  max="300"
                  step="5"
                  class="tsi-input w-full font-mono text-base pr-12"
                  placeholder="90"
                />
                <span class="pointer-events-none absolute right-3 top-2.5 text-xs font-medium text-text-secondary">
                  seg
                </span>
              </div>
              <span class="text-xs text-text-secondary">
                Rango permitido: 30 s a 300 s (5 min)
              </span>
            </div>
          </div>

          <div class="mt-4 flex items-center justify-start border-t border-border-default/60 pt-4">
            <button
              type="button"
              class="tsi-btn tsi-btn-primary inline-flex items-center gap-2"
              [disabled]="guardando() || timeout < 30 || timeout > 300"
              (click)="guardar()"
            >
              @if (guardando()) {
                <app-tabler-icon name="refresh" [size]="16" class="animate-spin" />
                Guardando...
              } @else {
                <app-tabler-icon name="circle-check" [size]="16" />
                Guardar parámetros
              }
            </button>
          </div>
        </div>
      </div>
    </section>
  `,
})
export class ParametrosAlgoritmoPage {
  private readonly api = inject(DespachoParametrosApiService);

  readonly parametros = signal<ParametrosDespachoData | null>(null);
  readonly mensaje = signal('');
  readonly esError = signal(false);
  readonly guardando = signal(false);
  timeout = 90;

  constructor() {
    this.api.obtener().subscribe({
      next: (res) => {
        this.parametros.set(res.data);
        this.timeout = res.data.timeout_respuesta_seg;
      },
    });
  }

  guardar(): void {
    this.guardando.set(true);
    this.mensaje.set('');
    this.esError.set(false);
    this.api.actualizar({ timeout_respuesta_seg: this.timeout }).subscribe({
      next: () => {
        this.mensaje.set('Parámetros actualizados exitosamente.');
        this.esError.set(false);
        this.guardando.set(false);
      },
      error: () => {
        this.mensaje.set('Error al guardar los parámetros.');
        this.esError.set(true);
        this.guardando.set(false);
      },
    });
  }
}

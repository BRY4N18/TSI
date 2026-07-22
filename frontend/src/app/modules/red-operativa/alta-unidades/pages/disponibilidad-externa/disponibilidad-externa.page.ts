import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';
import { EstadoDisponibilidad } from '../../models/unidad-emergencia.contract';

const ESTADOS_DECLARABLES: EstadoDisponibilidad[] = ['Activa', 'Ocupada', 'Fuera de servicio'];

@Component({
  selector: 'app-red-operativa-disponibilidad-externa-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TablerIconComponent],
  template: `
    <div class="mx-auto max-w-lg space-y-6 p-6">
      <header>
        <h1 class="text-[28px] font-bold text-text-primary">Declarar disponibilidad de unidad externa</h1>
      </header>

      <section class="space-y-4 rounded-lg border border-border-default bg-bg-surface p-6">
        <form (ngSubmit)="declarar()" class="space-y-4">
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Unidad (ID)</span>
            <input
              type="number"
              [(ngModel)]="idunidademergencia"
              name="idunidademergencia"
              required
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
            />
          </label>
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Nuevo estado</span>
            <select
              [(ngModel)]="estadonuevo"
              name="estadonuevo"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none"
            >
              @for (estado of estados; track estado) {
                <option [value]="estado">{{ estado }}</option>
              }
            </select>
          </label>
          <button
            type="submit"
            class="rounded-md bg-accent-primary px-5 py-2.5 font-medium text-white transition-colors hover:bg-accent-hover"
          >
            Declarar
          </button>
        </form>

        @if (mensaje) {
          <div
            class="flex items-center gap-2 rounded-md border-l-4 border-alert-success bg-alert-success-bg px-4 py-3 text-sm text-alert-success"
          >
            <app-tabler-icon name="circle-check" [size]="18" />
            <span>{{ mensaje }}</span>
          </div>
        }
        @if (alerta) {
          <div
            role="alert"
            class="flex items-center gap-2 rounded-md border-l-4 border-alert-critical bg-alert-critical-bg px-4 py-3 text-sm text-alert-critical"
          >
            <app-tabler-icon name="alert-triangle" [size]="18" />
            <span>{{ alerta }}</span>
          </div>
        }
      </section>
    </div>
  `,
})
export class DisponibilidadExternaPage {
  private readonly facade = inject(UnidadEmergenciaFacadeService);

  readonly estados = ESTADOS_DECLARABLES;
  idunidademergencia: number | null = null;
  estadonuevo: EstadoDisponibilidad = 'Activa';
  mensaje: string | null = null;
  alerta: string | null = null;

  declarar(): void {
    if (!this.idunidademergencia) return;
    this.mensaje = null;
    this.alerta = null;
    this.facade
      .declararDisponibilidad(this.idunidademergencia, this.estadonuevo)
      .subscribe((result) => {
        if (result.ok && result.data) {
          this.mensaje = `Disponibilidad actualizada a ${result.data.estadonuevo}.`;
        } else {
          this.alerta = result.error ?? 'Error al declarar disponibilidad';
        }
      });
  }
}

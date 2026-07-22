import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { UnidadEmergenciaApiService } from '../../services/unidad-emergencia-api.service';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';
import { UnidadEmergenciaData } from '../../models/unidad-emergencia.contract';

@Component({
  selector: 'app-red-operativa-edicion-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TablerIconComponent],
  template: `
    <div class="mx-auto max-w-2xl space-y-6 p-6">
      @if (unidad) {
        <header>
          <h1 class="text-[28px] font-bold text-text-primary">Editar unidad #{{ unidad.idunidademergencia }}</h1>
        </header>

        <section class="space-y-4 rounded-lg border border-border-default bg-bg-surface p-6">
          <form (ngSubmit)="guardar()" class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label class="block">
              <span class="mb-1 block text-sm font-medium text-text-secondary">Capacidad</span>
              <input
                [(ngModel)]="unidad.capacidad"
                name="capacidad"
                class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
              />
            </label>
            <label class="block">
              <span class="mb-1 block text-sm font-medium text-text-secondary">Condado (ID)</span>
              <input
                type="number"
                [(ngModel)]="unidad.idcondado"
                name="idcondado"
                class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
              />
            </label>
            <label class="block sm:col-span-2">
              <span class="mb-1 block text-sm font-medium text-text-secondary">Tipo de unidad</span>
              <select
                [(ngModel)]="unidad.tipounidademergencia"
                name="tipounidademergencia"
                class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none"
              >
                <option value="Ambulancia">Ambulancia</option>
                <option value="Grúa">Grúa</option>
                <option value="Patrulla">Patrulla</option>
                <option value="Bomberos">Bomberos</option>
                <option value="Defensa Civil">Defensa Civil</option>
              </select>
            </label>
            <div class="sm:col-span-2">
              <button
                type="submit"
                class="rounded-md bg-accent-primary px-5 py-2.5 font-medium text-white transition-colors hover:bg-accent-hover"
              >
                Guardar
              </button>
            </div>
          </form>

          @if (requiereConfirmacion) {
            <div
              role="alert"
              class="space-y-3 rounded-md border-l-4 border-alert-warning bg-alert-warning-bg px-4 py-3 text-sm text-alert-warning"
            >
              <div class="flex items-center gap-2">
                <app-tabler-icon name="alert-triangle" [size]="18" />
                <span>La unidad tiene un despacho activo. Confirma para forzar la edición del tipo de unidad.</span>
              </div>
              <button
                type="button"
                (click)="guardar(true)"
                class="rounded-md border border-alert-warning px-4 py-2 text-sm font-medium text-alert-warning hover:bg-alert-warning/10"
              >
                Confirmar edición crítica
              </button>
            </div>
          }

          @if (mensaje) {
            <div
              [class]="
                mensajeEsError
                  ? 'flex items-center gap-2 rounded-md border-l-4 border-alert-critical bg-alert-critical-bg px-4 py-3 text-sm text-alert-critical'
                  : 'flex items-center gap-2 rounded-md border-l-4 border-alert-success bg-alert-success-bg px-4 py-3 text-sm text-alert-success'
              "
            >
              <app-tabler-icon [name]="mensajeEsError ? 'alert-triangle' : 'circle-check'" [size]="18" />
              <span>{{ mensaje }}</span>
            </div>
          }
        </section>
      }
    </div>
  `,
})
export class EdicionPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(UnidadEmergenciaApiService);
  private readonly facade = inject(UnidadEmergenciaFacadeService);

  unidad: UnidadEmergenciaData | null = null;
  mensaje: string | null = null;
  mensajeEsError = false;
  requiereConfirmacion = false;

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('idunidademergencia'));
    this.api.obtener(id).subscribe((res) => {
      this.unidad = res.data;
    });
  }

  guardar(confirmarEdicionCritica = false): void {
    if (!this.unidad) return;
    this.mensaje = null;
    this.mensajeEsError = false;
    this.requiereConfirmacion = false;
    this.facade
      .editar(
        this.unidad.idunidademergencia,
        {
          capacidad: this.unidad.capacidad ?? undefined,
          idcondado: this.unidad.idcondado,
          tipounidademergencia: this.unidad.tipounidademergencia,
        },
        confirmarEdicionCritica,
      )
      .subscribe((result) => {
        if (result.ok) {
          this.mensaje = 'Unidad actualizada correctamente.';
        } else if (result.error?.includes('despacho activo')) {
          this.requiereConfirmacion = true;
        } else {
          this.mensaje = result.error ?? 'Error al editar la unidad';
          this.mensajeEsError = true;
        }
      });
  }
}

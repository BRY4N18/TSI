import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { RegionOperativaFacadeService } from '../../services/region-operativa-facade.service';
import {
  EstadoRegion,
  ResultadoValidacion,
  ValidacionHistorialItem,
} from '../../models/region-operativa.contract';

const ESTADO_BADGE_CLASSES: Record<EstadoRegion, string> = {
  En_Validación: 'bg-alert-info-bg text-alert-info',
  Producción: 'bg-alert-success-bg text-alert-success',
  En_Alerta: 'bg-alert-warning-bg text-alert-warning',
  Despublicada: 'bg-alert-critical-bg text-alert-critical',
};

@Component({
  selector: 'app-region-validacion-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TablerIconComponent],
  template: `
    <div class="mx-auto max-w-2xl space-y-8 p-6">
      <header>
        <h1 class="text-[28px] font-bold text-text-primary">Validación de operatividad de región</h1>
        <p class="mt-1 text-sm text-text-secondary">CU-O55 — Ejecutar protocolo de validación.</p>
      </header>

      <section class="space-y-5 rounded-lg border border-border-default bg-bg-surface p-6">
        <form (ngSubmit)="ejecutarValidacion()" class="space-y-5">
          <fieldset class="space-y-3 rounded-md border border-border-default p-4">
            <legend class="px-1 text-sm font-semibold text-text-primary">Región</legend>
            <label class="block">
              <span class="mb-1 block text-sm font-medium text-text-secondary">
                idregionoperativa (dejar vacío si es alta de región nueva)
              </span>
              <input
                [(ngModel)]="idregionoperativa"
                name="idregionoperativa"
                type="number"
                class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
              />
            </label>
            @if (!idregionoperativa) {
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <label class="block">
                  <span class="mb-1 block text-sm font-medium text-text-secondary">idestado</span>
                  <input
                    [(ngModel)]="idestado"
                    name="idestado"
                    type="number"
                    required
                    class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
                  />
                </label>
                <label class="block">
                  <span class="mb-1 block text-sm font-medium text-text-secondary">nombreregion</span>
                  <input
                    [(ngModel)]="nombreregion"
                    name="nombreregion"
                    required
                    class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
                  />
                </label>
              </div>
            }
          </fieldset>

          <fieldset class="space-y-3 rounded-md border border-border-default p-4">
            <legend class="px-1 text-sm font-semibold text-text-primary">Resultado</legend>
            <div class="flex gap-6">
              <label class="flex items-center gap-2 text-sm text-text-primary">
                <input type="radio" name="resultado" value="Aprobada" [(ngModel)]="resultado" class="accent-accent-primary" />
                Aprobada
              </label>
              <label class="flex items-center gap-2 text-sm text-text-primary">
                <input type="radio" name="resultado" value="Rechazada" [(ngModel)]="resultado" class="accent-accent-primary" />
                Rechazada
              </label>
            </div>
            @if (resultado === 'Rechazada') {
              <label class="block">
                <span class="mb-1 block text-sm font-medium text-text-secondary">Motivo</span>
                <input
                  [(ngModel)]="motivo"
                  name="motivo"
                  required
                  class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
                />
              </label>
            }
          </fieldset>

          <button
            type="submit"
            class="rounded-md bg-accent-primary px-5 py-2.5 font-medium text-white transition-colors hover:bg-accent-hover"
          >
            Ejecutar validación
          </button>
        </form>

        @if (mensaje) {
          <div
            role="status"
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
        @if (estadoregionActual) {
          <p class="flex items-center gap-2 text-sm text-text-secondary">
            Estado actual de la región:
            <span [class]="'rounded-md px-2 py-1 text-xs font-medium ' + estadoBadgeClass(estadoregionActual)">
              {{ estadoregionActual }}
            </span>
          </p>
        }
      </section>

      @if (idregionoperativa) {
        <section class="space-y-4 rounded-lg border border-border-default bg-bg-surface p-6">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-text-primary">Historial de validaciones</h2>
            <button
              type="button"
              (click)="cargarHistorial()"
              class="rounded-md border border-accent-primary px-4 py-2 text-sm font-medium text-accent-primary hover:bg-accent-primary/5"
            >
              Cargar historial
            </button>
          </div>

          @if (historial.length) {
            <div class="overflow-x-auto rounded-lg border border-border-default">
              <table class="w-full text-left text-sm">
                <thead class="bg-bg-page">
                  <tr>
                    <th class="px-4 py-3 text-xs font-medium uppercase tracking-wide text-text-primary">ID</th>
                    <th class="px-4 py-3 text-xs font-medium uppercase tracking-wide text-text-primary">Resultado</th>
                    <th class="px-4 py-3 text-xs font-medium uppercase tracking-wide text-text-primary">Motivo</th>
                    <th class="px-4 py-3 text-xs font-medium uppercase tracking-wide text-text-primary">Fecha/hora</th>
                  </tr>
                </thead>
                <tbody>
                  @for (item of historial; track item.idvalidacionregion) {
                    <tr class="border-t border-border-default">
                      <td class="px-4 py-3 text-text-primary">{{ item.idvalidacionregion }}</td>
                      <td class="px-4 py-3">
                        <span
                          [class]="
                            'rounded-md px-2 py-1 text-xs font-medium ' +
                            (item.resultado === 'Aprobada'
                              ? 'bg-alert-success-bg text-alert-success'
                              : 'bg-alert-critical-bg text-alert-critical')
                          "
                        >
                          {{ item.resultado }}
                        </span>
                      </td>
                      <td class="px-4 py-3 text-text-secondary">{{ item.motivo }}</td>
                      <td class="px-4 py-3 text-text-secondary">{{ item.fechahora }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          }

          <div class="border-t border-border-default pt-4">
            <h3 class="mb-2 text-sm font-semibold text-text-primary">Rechazo definitivo</h3>
            <button
              type="button"
              (click)="rechazarDefinitivamente()"
              class="rounded-md border border-alert-critical px-5 py-2.5 font-medium text-alert-critical transition-colors hover:bg-alert-critical-bg"
            >
              Marcar rechazo definitivo
            </button>
            @if (mensajeRechazo) {
              <p role="status" class="mt-2 flex items-center gap-2 text-sm text-text-secondary">
                <app-tabler-icon name="info-circle" [size]="16" />
                {{ mensajeRechazo }}
              </p>
            }
          </div>
        </section>
      }
    </div>
  `,
})
export class ValidacionPage {
  private readonly facade = inject(RegionOperativaFacadeService);

  idregionoperativa: number | null = null;
  idestado: number | null = null;
  nombreregion = '';
  resultado: ResultadoValidacion = 'Aprobada';
  motivo = '';
  mensaje: string | null = null;
  mensajeEsError = false;
  mensajeRechazo: string | null = null;
  estadoregionActual: EstadoRegion | null = null;
  historial: ValidacionHistorialItem[] = [];

  estadoBadgeClass(estado: EstadoRegion): string {
    return ESTADO_BADGE_CLASSES[estado];
  }

  ejecutarValidacion(): void {
    this.mensaje = null;
    this.mensajeEsError = false;
    this.facade
      .ejecutarValidacion({
        idregionoperativa: this.idregionoperativa ?? undefined,
        idestado: this.idestado ?? undefined,
        nombreregion: this.nombreregion || undefined,
        resultado: this.resultado,
        motivo: this.resultado === 'Rechazada' ? this.motivo : undefined,
      })
      .subscribe((result) => {
        if (result.ok && result.data) {
          this.mensaje = 'Validación registrada correctamente.';
          this.estadoregionActual = result.data.estadoregion_actual;
          this.idregionoperativa = result.data.idregionoperativa;
        } else {
          this.mensaje = result.error ?? 'Error al ejecutar la validación';
          this.mensajeEsError = true;
        }
      });
  }

  cargarHistorial(): void {
    if (!this.idregionoperativa) {
      return;
    }
    this.facade.listarHistorialValidacion(this.idregionoperativa).subscribe((result) => {
      this.historial = result.ok ? (result.data ?? []) : [];
    });
  }

  rechazarDefinitivamente(): void {
    if (!this.idregionoperativa) {
      return;
    }
    this.mensajeRechazo = null;
    this.facade.rechazarDefinitivamente(this.idregionoperativa).subscribe((result) => {
      this.mensajeRechazo = result.ok
        ? 'Región marcada como inactiva (rechazo definitivo).'
        : (result.error ?? 'Error al marcar el rechazo definitivo');
    });
  }
}

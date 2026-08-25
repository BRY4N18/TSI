import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { RegionOperativaFacadeService } from '../../services/region-operativa-facade.service';
import { EstadoRegion } from '../../models/region-operativa.contract';

const ESTADO_BADGE_CLASSES: Record<EstadoRegion, string> = {
  En_Validación: 'bg-alert-info-bg text-alert-info',
  Producción: 'bg-alert-success-bg text-alert-success',
  En_Alerta: 'bg-alert-warning-bg text-alert-warning',
  Despublicada: 'bg-alert-critical-bg text-alert-critical',
};

@Component({
  selector: 'app-region-reevaluacion-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TablerIconComponent],
  template: `
    <div class="mx-auto max-w-lg space-y-6 p-6">
      <header>
        <h1 class="tsi-display text-[28px] font-extrabold text-text-primary">
          Re-evaluar/despublicar región #{{ idregionoperativa }}
        </h1>
<div class="tsi-rail-h mt-2 w-24" aria-hidden="true"></div>
        <p class="mt-1 text-sm text-text-secondary">CU-O61 — Región habilitada en producción.</p>
      </header>

      <section class="space-y-5 tsi-panel p-6">
        <form (ngSubmit)="reevaluar()" class="space-y-4">
          <div class="flex gap-6">
            <label class="flex items-center gap-2 text-sm text-text-primary">
              <input
                type="radio"
                name="estadoregion"
                value="En_Alerta"
                [(ngModel)]="estadoregion"
                class="accent-accent-primary"
              />
              Degradar a En_Alerta
            </label>
            <label class="flex items-center gap-2 text-sm text-text-primary">
              <input
                type="radio"
                name="estadoregion"
                value="Despublicada"
                [(ngModel)]="estadoregion"
                class="accent-accent-primary"
              />
              Despublicar
            </label>
          </div>
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Motivo</span>
            <input
              [(ngModel)]="motivo"
              name="motivo"
              required
              class="tsi-input w-full"
          placeholder="Motivo, en una frase"
        />
          </label>
          <button
            type="submit"
            [class]="
              estadoregion === 'Despublicada'
                ? 'rounded-md border border-alert-critical px-5 py-2.5 font-medium text-alert-critical transition-colors hover:bg-alert-critical-bg'
                : 'rounded-md bg-accent-primary px-5 py-2.5 font-medium text-white transition-colors hover:bg-accent-hover'
            "
          >
            Confirmar
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
          <div class="flex items-start gap-2 rounded-md border-l-4 border-alert-info bg-alert-info-bg px-4 py-3 text-sm text-alert-info">
            <app-tabler-icon name="info-circle" [size]="18" class="mt-0.5 shrink-0" />
            <p>
              La despublicación nunca cancela casos activos en curso — solo bloquea casos nuevos.
              Estado actual:
              <span [class]="'rounded-md px-2 py-1 text-xs font-medium ' + estadoBadgeClass(estadoregionActual)">
                {{ estadoregionActual }}
              </span>
            </p>
          </div>
        }
      </section>
    </div>
  `,
})
export class ReevaluacionPage {
  private readonly route = inject(ActivatedRoute);
  private readonly facade = inject(RegionOperativaFacadeService);
  // El shell de la aplicación es OnPush: sin marcar la vista, nada de lo que
  // llega por HTTP se repinta. Ver §9 del design-system.
  private readonly cdr = inject(ChangeDetectorRef);

  readonly idregionoperativa = Number(this.route.snapshot.paramMap.get('idregionoperativa'));
  estadoregion: 'En_Alerta' | 'Despublicada' = 'En_Alerta';
  motivo = '';
  mensaje: string | null = null;
  mensajeEsError = false;
  estadoregionActual: EstadoRegion | null = null;

  estadoBadgeClass(estado: EstadoRegion): string {
    return ESTADO_BADGE_CLASSES[estado];
  }

  reevaluar(): void {
    this.mensaje = null;
    this.mensajeEsError = false;
    this.facade
      .reevaluarRegion(this.idregionoperativa, this.estadoregion, this.motivo)
      .subscribe((result) => {
      this.cdr.markForCheck();
        if (result.ok && result.data) {
          this.mensaje = 'Región re-evaluada correctamente.';
          this.estadoregionActual = result.data.estadoregion;
        } else {
          this.mensaje = result.error ?? 'Error al re-evaluar la región';
          this.mensajeEsError = true;
        }
      });
  }
}

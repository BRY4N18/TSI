import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { AuthApiService } from '../../../../cuentas-clientes/auth/services/auth-api.service';
import { RegionOperativaFacadeService } from '../../services/region-operativa-facade.service';
import { EstadoRegion, RegionOperativaData } from '../../models/region-operativa.contract';

const ESTADO_BADGE: Record<EstadoRegion, string> = {
  En_Validación: 'bg-alert-info-bg text-alert-info',
  Producción: 'bg-alert-success-bg text-alert-success',
  En_Alerta: 'bg-alert-warning-bg text-alert-warning',
  Despublicada: 'bg-alert-critical-bg text-alert-critical',
};

@Component({
  selector: 'app-region-catalogo-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TablerIconComponent],
  template: `
    <div class="mx-auto max-w-4xl space-y-8 p-6">
      <header class="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 class="text-[28px] font-bold text-text-primary">Regiones operativas</h1>
          <p class="mt-1 text-sm text-text-secondary">
            Catálogo y accesos a validación / reevaluación.
          </p>
        </div>
        <div class="flex gap-2">
          <a
            routerLink="/red-operativa/incorporacion-regional/validacion"
            class="rounded-md bg-accent-primary px-4 py-2 text-sm font-medium text-white hover:bg-accent-hover"
          >
            Nueva validación
          </a>
          <button
            type="button"
            (click)="cargar()"
            class="rounded-md border border-accent-primary px-4 py-2 text-sm font-medium text-accent-primary hover:bg-accent-primary/5"
          >
            Actualizar
          </button>
        </div>
      </header>

      @if (error) {
        <p class="text-sm text-alert-critical">{{ error }}</p>
      }
      @if (!error && regiones.length === 0) {
        <p class="text-sm text-text-secondary">No hay regiones registradas.</p>
      }
      @if (regiones.length > 0) {
        <div class="overflow-x-auto rounded-lg border border-border-default">
          <table class="w-full text-left text-sm">
            <thead class="bg-bg-page">
              <tr>
                <th class="px-4 py-3 text-xs font-medium uppercase text-text-primary">ID</th>
                <th class="px-4 py-3 text-xs font-medium uppercase text-text-primary">Nombre</th>
                <th class="px-4 py-3 text-xs font-medium uppercase text-text-primary">Estado</th>
                <th class="px-4 py-3 text-xs font-medium uppercase text-text-primary">Activo</th>
                <th class="px-4 py-3 text-xs font-medium uppercase text-text-primary">Acciones</th>
              </tr>
            </thead>
            <tbody>
              @for (r of regiones; track r.idregionoperativa) {
                <tr class="border-t border-border-default">
                  <td class="px-4 py-3 text-text-primary">{{ r.idregionoperativa }}</td>
                  <td class="px-4 py-3 text-text-primary">{{ r.nombreregion || '—' }}</td>
                  <td class="px-4 py-3">
                    <span class="rounded-md px-2 py-1 text-xs" [class]="badge(r.estadoregion)">
                      {{ r.estadoregion }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-text-secondary">{{ r.activo ? 'Sí' : 'No' }}</td>
                  <td class="space-x-3 px-4 py-3">
                    <a
                      [routerLink]="['/red-operativa/incorporacion-regional/validacion']"
                      [queryParams]="{ id: r.idregionoperativa }"
                      class="text-accent-primary hover:underline"
                      >Validar</a
                    >
                    @if (esDirector && (r.estadoregion === 'Producción' || r.estadoregion === 'En_Alerta')) {
                      <a
                        [routerLink]="[
                          '/red-operativa/incorporacion-regional/reevaluacion',
                          r.idregionoperativa
                        ]"
                        class="text-alert-warning hover:underline"
                        >Reevaluar</a
                      >
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `,
})
export class CatalogoRegionesPage implements OnInit {
  private readonly facade = inject(RegionOperativaFacadeService);
  private readonly authApi = inject(AuthApiService);

  readonly esDirector = this.authApi.hasRole('DirectorTecnologico');

  regiones: RegionOperativaData[] = [];
  error: string | null = null;

  ngOnInit(): void {
    this.cargar();
  }

  badge(estado: EstadoRegion): string {
    return ESTADO_BADGE[estado] ?? 'bg-bg-muted text-text-secondary';
  }

  cargar(): void {
    this.error = null;
    this.facade.listar().subscribe((result) => {
      if (result.ok && result.data) {
        this.regiones = result.data;
      } else {
        this.error = result.error ?? 'No se pudo cargar el catálogo de regiones';
      }
    });
  }
}

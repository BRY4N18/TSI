import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../../shared/ui/list-states/list-loading-skeleton.component';
import {
  LIST_MOBILE_CARD_CLASS,
  LIST_ROW_CLASS,
  LIST_TABLE_CLASS,
  LIST_TABLE_TD_CLASS,
  LIST_TABLE_TD_PRIMARY_CLASS,
  LIST_TABLE_TH_CLASS,
} from '../../../../../shared/ui/list-states/list-table.styles';
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
  imports: [
    CommonModule,
    RouterLink,
    TablerIconComponent,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
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

      @if (loading && regiones.length === 0 && !error) {
        <app-list-loading-skeleton [count]="3" />
      } @else if (error && regiones.length === 0) {
        <app-list-error-state [message]="error" (retry)="cargar()" />
      } @else if (!loading && regiones.length === 0) {
        <app-list-empty-state message="No hay regiones registradas." icon="map-pin" />
      } @else {
        <table [class]="listTableClass">
          <thead>
            <tr class="bg-bg-surface">
              <th [class]="listTableThClass">ID</th>
              <th [class]="listTableThClass">Nombre</th>
              <th [class]="listTableThClass">Estado</th>
              <th [class]="listTableThClass">Activo</th>
              <th [class]="listTableThClass">Acciones</th>
            </tr>
          </thead>
          <tbody>
            @for (r of regiones; track r.idregionoperativa) {
              <tr [class]="listRowClass">
                <td [class]="listTableTdPrimaryClass">{{ r.idregionoperativa }}</td>
                <td [class]="listTableTdClass">{{ r.nombreregion || '—' }}</td>
                <td [class]="listTableTdClass">
                  <span class="rounded-md px-2 py-1 text-xs" [class]="badge(r.estadoregion)">
                    {{ r.estadoregion }}
                  </span>
                </td>
                <td [class]="listTableTdClass">{{ r.activo ? 'Sí' : 'No' }}</td>
                <td [class]="listTableTdClass + ' space-x-3'">
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

        <!-- Mobile: cards apiladas -->
        <div class="grid gap-3 md:hidden">
          @for (r of regiones; track r.idregionoperativa) {
            <div [class]="listMobileCardClass">
              <div class="mb-2 flex items-center justify-between gap-2">
                <span class="text-sm font-semibold text-text-primary">{{ r.nombreregion || '—' }}</span>
                <span class="rounded-md px-2 py-1 text-xs" [class]="badge(r.estadoregion)">
                  {{ r.estadoregion }}
                </span>
              </div>
              <dl class="grid gap-1 text-sm">
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">ID</dt>
                  <dd class="font-medium text-text-primary">{{ r.idregionoperativa }}</dd>
                </div>
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">Activo</dt>
                  <dd class="font-medium text-text-primary">{{ r.activo ? 'Sí' : 'No' }}</dd>
                </div>
              </dl>
              <div class="mt-3 flex flex-wrap gap-3 text-sm">
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
              </div>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class CatalogoRegionesPage implements OnInit {
  private readonly facade = inject(RegionOperativaFacadeService);
  private readonly authApi = inject(AuthApiService);

  readonly esDirector = this.authApi.hasRole('DirectorTecnologico');
  readonly listTableClass = LIST_TABLE_CLASS;
  readonly listTableThClass = LIST_TABLE_TH_CLASS;
  readonly listTableTdClass = LIST_TABLE_TD_CLASS;
  readonly listTableTdPrimaryClass = LIST_TABLE_TD_PRIMARY_CLASS;
  readonly listRowClass = LIST_ROW_CLASS;
  readonly listMobileCardClass = LIST_MOBILE_CARD_CLASS;

  regiones: RegionOperativaData[] = [];
  error: string | null = null;
  loading = false;

  ngOnInit(): void {
    this.cargar();
  }

  badge(estado: EstadoRegion): string {
    return ESTADO_BADGE[estado] ?? 'bg-bg-muted text-text-secondary';
  }

  cargar(): void {
    this.error = null;
    this.loading = true;
    this.facade.listar().subscribe((result) => {
      this.loading = false;
      if (result.ok && result.data) {
        this.regiones = result.data;
      } else {
        this.error = result.error ?? 'No se pudo cargar el catálogo de regiones';
      }
    });
  }
}

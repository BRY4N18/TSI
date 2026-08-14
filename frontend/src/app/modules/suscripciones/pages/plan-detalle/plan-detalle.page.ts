import { CommonModule, CurrencyPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import {
  Plan,
  PlanLimites,
  SeveridadCatalogo,
  SeveridadPlan,
} from '../../services/models/suscripciones.types';
import { PlanApiService } from '../../services/plan-api.service';
import { billingBadge } from '../../billing-ui';

@Component({
  selector: 'app-plan-detalle-page',
  standalone: true,
  imports: [
    CommonModule,
    CurrencyPipe,
    RouterLink,
    TablerIconComponent,
    ListErrorStateComponent,
    ListLoadingSkeletonComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './plan-detalle.page.html',
})
export class PlanDetallePage implements OnInit {
  private readonly api = inject(PlanApiService);
  private readonly route = inject(ActivatedRoute);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly plan = signal<Plan | null>(null);
  readonly idplan = signal<number | null>(null);
  /** Catálogo `Dim_Severidad` para traducir los ids que guarda el plan. */
  readonly severidadesCatalogo = signal<SeveridadCatalogo[]>([]);

  ngOnInit(): void {
    this.api.listarSeveridades().subscribe({
      next: (items) => this.severidadesCatalogo.set(items),
      error: () => this.severidadesCatalogo.set([]),
    });
    const idRaw = this.route.snapshot.paramMap.get('idplan');
    const id = Number(idRaw);
    if (!Number.isFinite(id) || id <= 0) {
      this.loading.set(false);
      this.error.set('Identificador de plan inválido.');
      return;
    }
    this.idplan.set(id);
    this.cargar(id);
  }

  cargar(id?: number): void {
    const planId = id ?? this.idplan();
    if (planId == null) return;
    this.loading.set(true);
    this.error.set(null);
    this.api.buscarPorId(planId).subscribe({
      next: (found) => {
        this.plan.set(found);
        this.loading.set(false);
        if (!found) {
          this.error.set('No se encontró el plan.');
        }
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err?.error?.detail ?? 'Error al cargar el plan.');
      },
    });
  }

  okBadge(): string {
    return billingBadge('ok');
  }

  warnBadge(): string {
    return billingBadge('warn');
  }

  infoBadge(): string {
    return billingBadge('info');
  }

  limitesTexto(limites?: PlanLimites | string): string {
    if (!limites) return 'Sin límites';
    if (typeof limites === 'string') {
      try {
        return this.limitesTexto(JSON.parse(limites) as PlanLimites);
      } catch {
        return limites;
      }
    }
    // Ver nota en `catalogo-planes.page.ts`: las claves ausentes se omiten en
    // vez de renderizarse como `undefined`.
    const partes = [
      limites.unidades_max == null ? null : `${limites.unidades_max} unidades`,
      limites.usuarios_max == null ? null : `${limites.usuarios_max} usuarios`,
      limites.api_calls_mes == null ? null : `${limites.api_calls_mes} API/mes`,
      limites.api_calls_minuto == null ? null : `${limites.api_calls_minuto} API/min`,
    ].filter((p): p is string => p !== null);
    return partes.length ? partes.join(' · ') : 'Sin límites';
  }

  severidadesTexto(severidades?: SeveridadPlan[] | string): string {
    if (!severidades) return 'Sin configurar';
    if (typeof severidades === 'string') {
      try {
        return this.severidadesTexto(JSON.parse(severidades) as SeveridadPlan[]);
      } catch {
        return 'Sin configurar';
      }
    }
    const nombres = new Map(
      this.severidadesCatalogo().map((s) => [s.idseveridad, s.severidad]),
    );
    const etiquetas = severidades
      .map((id) => nombres.get(Number(id)))
      .filter((n): n is string => Boolean(n));
    return etiquetas.length ? etiquetas.join(' · ') : 'Sin configurar';
  }
}

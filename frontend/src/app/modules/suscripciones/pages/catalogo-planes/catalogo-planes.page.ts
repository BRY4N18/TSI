import { CommonModule, CurrencyPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';

import { Plan, PlanLimites } from '../../services/models/suscripciones.types';
import { PlanApiService } from '../../services/plan-api.service';
import { billingBadge } from '../../billing-ui';

@Component({
  selector: 'app-catalogo-planes-suscripciones',
  standalone: true,
  imports: [CommonModule, CurrencyPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './catalogo-planes.page.html',
})
export class CatalogoPlanesPage implements OnInit {
  private readonly api = inject(PlanApiService);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly planes = signal<Plan[]>([]);

  ngOnInit(): void {
    this.cargar();
  }

  infoBadge(): string {
    return billingBadge('info');
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listar(true).subscribe({
      next: (res) => {
        this.planes.set(res.data ?? []);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Error al cargar planes.');
        this.loading.set(false);
      },
    });
  }

  limitesTexto(limites?: PlanLimites | string): string {
    if (!limites) return 'Sin límites publicados';
    if (typeof limites === 'string') {
      try {
        const parsed = JSON.parse(limites) as PlanLimites;
        return this.limitesTexto(parsed);
      } catch {
        return limites;
      }
    }
    return [
      `${limites.unidades_max} unidades`,
      `${limites.usuarios_max} usuarios`,
      `${limites.api_calls_mes} API calls/mes`,
    ].join(' · ');
  }
}

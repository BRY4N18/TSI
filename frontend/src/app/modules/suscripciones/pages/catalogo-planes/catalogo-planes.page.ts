import { CommonModule, CurrencyPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { Plan, PlanLimites } from '../../services/models/suscripciones.types';
import { PlanApiService } from '../../services/plan-api.service';
import { billingBadge } from '../../billing-ui';

@Component({
  selector: 'app-catalogo-planes-suscripciones',
  standalone: true,
  imports: [CommonModule, CurrencyPipe, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './catalogo-planes.page.html',
})
export class CatalogoPlanesPage implements OnInit {
  private readonly api = inject(PlanApiService);
  private readonly auth = inject(AuthApiService);
  private readonly notifications = inject(NotificationService);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly planes = signal<Plan[]>([]);
  readonly esDirector = signal(false);
  readonly planPendienteDesactivar = signal<Plan | null>(null);
  readonly desactivando = signal(false);

  ngOnInit(): void {
    this.esDirector.set(this.auth.hasRole('DirectorEstrategia'));
    this.cargar();
  }

  infoBadge(): string {
    return billingBadge('info');
  }

  okBadge(): string {
    return billingBadge('ok');
  }

  warnBadge(): string {
    return billingBadge('warn');
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    const soloActivos = !this.esDirector();
    this.api.listar(soloActivos).subscribe({
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

  pedirDesactivar(plan: Plan): void {
    if (!this.esDirector() || plan.idplan == null) return;
    this.planPendienteDesactivar.set(plan);
  }

  cancelarDesactivar(): void {
    this.planPendienteDesactivar.set(null);
  }

  confirmarDesactivar(): void {
    const plan = this.planPendienteDesactivar();
    if (!this.esDirector() || !plan || plan.idplan == null) return;
    this.desactivando.set(true);
    this.api.actualizar(plan.idplan, { activo: false }, crypto.randomUUID()).subscribe({
      next: () => {
        this.desactivando.set(false);
        this.planPendienteDesactivar.set(null);
        this.notifications.toast(`Plan «${plan.nombre}» desactivado.`, 'success');
        this.cargar();
      },
      error: (err) => {
        this.desactivando.set(false);
        this.notifications.toast(
          err?.error?.detail ?? 'No se pudo desactivar el plan.',
          'critical',
        );
      },
    });
  }

  reactivar(plan: Plan): void {
    if (!this.esDirector() || plan.idplan == null) return;
    this.api.actualizar(plan.idplan, { activo: true }, crypto.randomUUID()).subscribe({
      next: () => {
        this.notifications.toast(`Plan «${plan.nombre}» reactivado.`, 'success');
        this.cargar();
      },
      error: (err) => {
        this.notifications.toast(
          err?.error?.detail ?? 'No se pudo reactivar el plan.',
          'critical',
        );
      },
    });
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
    return [
      `${limites.unidades_max} unidades`,
      `${limites.usuarios_max} usuarios`,
      `${limites.api_calls_mes} API/mes`,
    ].join(' · ');
  }
}

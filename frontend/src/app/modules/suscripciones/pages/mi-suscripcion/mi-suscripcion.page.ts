import { CommonModule, CurrencyPipe, DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { Plan, SuscripcionDetalle } from '../../services/models/suscripciones.types';
import { PlanApiService } from '../../services/plan-api.service';
import { SuscripcionApiService } from '../../services/suscripcion-api.service';
import { billingBadge, billingEstadoBadge } from '../../billing-ui';

@Component({
  selector: 'app-mi-suscripcion',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, CurrencyPipe, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './mi-suscripcion.page.html',
})
export class MiSuscripcionPage implements OnInit {
  private readonly api = inject(SuscripcionApiService);
  private readonly plansApi = inject(PlanApiService);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly detalle = signal<SuscripcionDetalle | null>(null);
  readonly planes = signal<Plan[]>([]);
  readonly message = signal<string | null>(null);
  readonly busy = signal(false);

  selectedPlanId: number | null = null;
  motivoCancelacion = '';

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.obtenerMiSuscripcion().subscribe({
      next: (res) => {
        this.detalle.set(res.data ?? null);
        this.loading.set(false);
      },
      error: (err) => {
        if (err?.status === 404) {
          this.detalle.set(null);
          this.error.set(null);
          this.plansApi.listar(true).subscribe({
            next: (p) => this.planes.set(p.data ?? []),
          });
        } else {
          this.error.set(err?.error?.detail ?? 'No se pudo cargar la suscripción.');
        }
        this.loading.set(false);
      },
    });
  }

  estadoBadge(estado?: string): string {
    return billingEstadoBadge(estado);
  }

  infoBadge(): string {
    return billingBadge('info');
  }

  contratar(): void {
    if (!this.selectedPlanId) return;
    this.busy.set(true);
    this.message.set(null);
    this.api.alta({ idplan: this.selectedPlanId, renovacionautomatica: true }, crypto.randomUUID()).subscribe({
      next: () => {
        this.message.set('Suscripción activada correctamente.');
        this.busy.set(false);
        this.cargar();
      },
      error: (err) => {
        this.message.set(err?.error?.detail ?? 'No se pudo contratar el plan.');
        this.busy.set(false);
      },
    });
  }

  reintentarCobro(): void {
    this.busy.set(true);
    this.message.set(null);
    this.api.reintentarCobro(crypto.randomUUID()).subscribe({
      next: (res) => {
        this.message.set(
          `Regularización: pago ${res.data?.estado_pago}, suscripción ${res.data?.estado_suscripcion}.`,
        );
        this.busy.set(false);
        this.cargar();
      },
      error: (err) => {
        this.message.set(err?.error?.detail ?? 'No se pudo reintentar el cobro.');
        this.busy.set(false);
      },
    });
  }

  cancelar(): void {
    if (!this.motivoCancelacion.trim()) {
      this.message.set('Indica un motivo de cancelación.');
      return;
    }
    this.busy.set(true);
    this.message.set(null);
    this.api
      .cancelar({ motivocancelacion: this.motivoCancelacion.trim() }, crypto.randomUUID())
      .subscribe({
        next: () => {
          this.message.set('Suscripción cancelada. Conservarás acceso hasta la fecha de fin.');
          this.busy.set(false);
          this.cargar();
        },
        error: (err) => {
          this.message.set(err?.error?.detail ?? 'No se pudo cancelar.');
          this.busy.set(false);
        },
      });
  }
}

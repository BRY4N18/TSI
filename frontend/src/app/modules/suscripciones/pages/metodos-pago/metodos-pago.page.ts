import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import {
  LIST_MOBILE_CARD_CLASS,
  LIST_ROW_CLASS,
  LIST_TABLE_CLASS,
  LIST_TABLE_TD_CLASS,
  LIST_TABLE_TD_PRIMARY_CLASS,
  LIST_TABLE_TH_CLASS,
} from '../../../../shared/ui/list-states/list-table.styles';
import { MetodoPago, TipoMetodoPago } from '../../services/models/suscripciones.types';
import { MetodoPagoApiService } from '../../services/metodo-pago-api.service';
import { billingBadge } from '../../billing-ui';

@Component({
  selector: 'app-metodos-pago',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './metodos-pago.page.html',
})
export class MetodosPagoPage implements OnInit {
  private readonly api = inject(MetodoPagoApiService);

  readonly tableClass = LIST_TABLE_CLASS;
  readonly thClass = LIST_TABLE_TH_CLASS;
  readonly tdClass = LIST_TABLE_TD_CLASS;
  readonly tdPrimaryClass = LIST_TABLE_TD_PRIMARY_CLASS;
  readonly rowClass = LIST_ROW_CLASS;
  readonly mobileCardClass = LIST_MOBILE_CARD_CLASS;

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly items = signal<MetodoPago[]>([]);
  readonly message = signal<string | null>(null);
  readonly busy = signal(false);

  tipo: TipoMetodoPago = 'tarjeta';
  numero = '';
  fechaexpiracion = '';

  /**
   * `fechaexpiracion` viaja como epoch en milisegundos porque la columna de
   * Pinot es LONG. Mostrarlo crudo dejaba un número de 13 dígitos en pantalla,
   * así que se devuelve al formato MM/AAAA con el que el usuario lo escribió.
   */
  expiracion(valor: string | number | null | undefined): string {
    if (valor === null || valor === undefined || valor === '') return '—';
    const ms = Number(valor);
    if (!Number.isFinite(ms) || ms <= 0) return '—';
    const fecha = new Date(ms);
    if (Number.isNaN(fecha.getTime())) return '—';
    const mes = String(fecha.getUTCMonth() + 1).padStart(2, '0');
    return `${mes}/${fecha.getUTCFullYear()}`;
  }

  badgeOk(): string {
    return billingBadge('ok');
  }

  badgeNeutral(): string {
    return billingBadge('neutral');
  }

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listar().subscribe({
      next: (res) => {
        this.items.set(res.data ?? []);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Error al listar métodos de pago.');
        this.loading.set(false);
      },
    });
  }

  registrar(): void {
    this.busy.set(true);
    this.message.set(null);
    this.api
      .registrar(
        {
          tipo: this.tipo,
          datos_pasarela: {
            numero: this.numero,
            fechaexpiracion: this.fechaexpiracion || undefined,
          },
        },
        crypto.randomUUID(),
      )
      .subscribe({
        next: () => {
          this.message.set('Método registrado. El PAN no se almacena; solo token y últimos dígitos.');
          this.numero = '';
          this.fechaexpiracion = '';
          this.busy.set(false);
          this.cargar();
        },
        error: (err) => {
          this.message.set(err?.error?.detail ?? 'No se pudo registrar el método.');
          this.busy.set(false);
        },
      });
  }
}

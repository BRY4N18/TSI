import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
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
import { MetodoPago } from '../../services/models/suscripciones.types';
import { MetodoPagoApiService } from '../../services/metodo-pago-api.service';
import { billingBadge } from '../../billing-ui';

@Component({
  selector: 'app-metodos-pago',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TablerIconComponent,
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

  // Estado del Modal de registro
  readonly modalAbierto = signal(false);

  // Campos del formulario exclusivo de Tarjeta
  numeroTarjeta = '';
  fechaExpiracion = '';
  cvv = '';
  titular = '';

  // Validaciones en tiempo real
  readonly numeroLimpio = computed(() => this.numeroTarjeta.replace(/\D/g, ''));
  readonly numeroValido = computed(() => {
    const digitos = this.numeroLimpio();
    return digitos.length >= 13 && digitos.length <= 19;
  });

  readonly expiracionValida = computed(() => {
    const exp = this.fechaExpiracion.trim();
    const match = exp.match(/^(\d{2})\/(\d{2})$/);
    if (!match) return false;
    const mes = parseInt(match[1], 10);
    return mes >= 1 && mes <= 12;
  });

  readonly cvvValido = computed(() => {
    const c = this.cvv.trim();
    return /^\d{3,4}$/.test(c);
  });

  readonly formularioValido = computed(() => {
    return this.numeroValido() && this.expiracionValida() && this.cvvValido();
  });

  onNumeroInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const digitos = input.value.replace(/\D/g, '').slice(0, 19);
    const grupos = digitos.match(/.{1,4}/g);
    this.numeroTarjeta = grupos ? grupos.join(' ') : digitos;
    input.value = this.numeroTarjeta;
  }

  onExpiracionInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    let val = input.value.replace(/[^\d/]/g, '');
    if (val.length === 2 && !val.includes('/') && (event as InputEvent).inputType !== 'deleteContentBackward') {
      val = val + '/';
    }
    val = val.slice(0, 5);
    this.fechaExpiracion = val;
    input.value = val;
  }

  onCvvInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const val = input.value.replace(/\D/g, '').slice(0, 4);
    this.cvv = val;
    input.value = val;
  }

  abrirModal(): void {
    this.numeroTarjeta = '';
    this.fechaExpiracion = '';
    this.cvv = '';
    this.titular = '';
    this.modalAbierto.set(true);
  }

  cerrarModal(): void {
    if (!this.busy()) {
      this.modalAbierto.set(false);
    }
  }

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
    if (!this.formularioValido()) return;

    this.busy.set(true);
    this.message.set(null);
    this.api
      .registrar(
        {
          tipo: 'tarjeta',
          datos_pasarela: {
            numero: this.numeroLimpio(),
            fechaexpiracion: this.fechaExpiracion || undefined,
            cvv: this.cvv,
            titular: this.titular.trim() || undefined,
          },
        },
        crypto.randomUUID(),
      )
      .subscribe({
        next: () => {
          this.message.set('Tarjeta registrada exitosamente. Los datos sensibles se tokenizan; no se persiste el número completo.');
          this.busy.set(false);
          this.modalAbierto.set(false);
          this.cargar();
        },
        error: (err) => {
          this.message.set(err?.error?.detail ?? 'No se pudo registrar la tarjeta.');
          this.busy.set(false);
        },
      });
  }
}

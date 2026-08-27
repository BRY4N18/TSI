import {
  ChangeDetectionStrategy,
  Component,
  inject,
  input,
  OnInit,
  output,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { AccidenteApiService } from '../../services/accidente-api.service';
import { CatalogoItem } from '../../services/models/accidente.types';
import { UbicacionCatalogoApiService } from '../../services/ubicacion-catalogo-api.service';
import { SEVERIDADES, SeveridadInfo } from '../../severidad.constants';

@Component({
  selector: 'app-escalar-severidad-panel',
  standalone: true,
  imports: [FormsModule, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div>
      @if (error()) {
        <p class="mb-4 rounded-md border border-alert-critical bg-alert-critical-bg px-4 py-3 text-sm text-alert-critical"
           data-testid="escalar-error">{{ error() }}</p>
      }

      @if (!confirmando()) {
        <form (ngSubmit)="pedirConfirmacion()" class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div class="grid gap-1.5">
            <label for="escalarSeveridad" class="text-sm font-medium text-text-secondary">Nueva severidad</label>
            <select
              id="escalarSeveridad"
              class="tsi-select w-full min-w-0"
              [(ngModel)]="idseveridad"
              name="idseveridad"
            >
              @for (s of severidadesDisponibles(); track s.value) {
                <option [ngValue]="s.value">{{ s.label }}</option>
              }
            </select>
            @if (severidadActual()) {
              <p class="m-0 text-xs text-text-secondary">
                Severidad actual del caso: <strong>{{ severidadActualLabel() }}</strong>. Escalar solo sube.
              </p>
            }
          </div>
          <div class="grid gap-1.5">
            <label for="escalarHeridos" class="text-sm font-medium text-text-secondary">Heridos</label>
            <input
              id="escalarHeridos"
              type="number"
              [min]="heridosMinimo()"
              class="tsi-input w-full"
              [(ngModel)]="numheridos"
              name="numheridos"
              placeholder="Ej. 0"
            />
            <p class="m-0 text-xs text-text-secondary">
              Registrados: {{ heridosMinimo() }}. Solo puede aumentar.
            </p>
          </div>
          <div class="grid gap-1.5">
            <label for="escalarFallecidos" class="text-sm font-medium text-text-secondary">Fallecidos</label>
            <input
              id="escalarFallecidos"
              type="number"
              [min]="fallecidosMinimo()"
              class="tsi-input w-full"
              [(ngModel)]="numfallecidos"
              name="numfallecidos"
              placeholder="Ej. 0"
            />
            <p class="m-0 text-xs text-text-secondary">
              Registrados: {{ fallecidosMinimo() }}. Solo puede aumentar.
            </p>
          </div>
          <div class="grid gap-1.5 sm:col-span-2">
            <label for="escalarUnidadAdicional" class="text-sm font-medium text-text-secondary"
              >Unidad adicional (opcional)</label
            >
            <select
              id="escalarUnidadAdicional"
              class="tsi-select w-full min-w-0"
              [(ngModel)]="idunidademergenciaAdicional"
              name="idunidademergencia_adicional"
            >
              <option [ngValue]="null">— Sin unidad adicional —</option>
              @for (u of unidades(); track u.id) {
                <option [ngValue]="u.id">{{ u.nombre }}</option>
              }
            </select>
          </div>
          <div class="grid gap-1.5 sm:col-span-2">
            <label for="escalarNota" class="text-sm font-medium text-text-secondary">Nota (obligatoria)</label>
            <textarea
              id="escalarNota"
              rows="3"
              required
              class="tsi-textarea w-full"
              [(ngModel)]="nota"
              name="nota"
              placeholder="Escribe el detalle"
            ></textarea>
          </div>
          <div class="sm:col-span-2 flex justify-end gap-3 pt-2">
            <button
              type="button"
              class="tsi-btn tsi-btn-secondary"
              (click)="cancelar.emit()"
            >
              Cancelar
            </button>
            <button
              type="submit"
              [disabled]="!nota.trim()"
              class="tsi-btn tsi-btn-primary"
            >
              Escalar severidad
            </button>
          </div>
        </form>
      } @else {
        <div class="grid gap-3 rounded-md border border-alert-warning bg-alert-warning-bg p-4">
          <p class="m-0 flex items-center gap-2 text-sm font-medium text-alert-warning">
            <app-tabler-icon name="alert-triangle" [size]="18" />
            La severidad es un campo crítico. ¿Confirmas cambiarla a "{{ severidadLabel() }}"? Esta acción queda
            registrada en el historial del caso.
          </p>
          <div class="flex justify-end gap-2">
            <button
              type="button"
              [disabled]="enviando()"
              class="tsi-btn tsi-btn-secondary"
              (click)="confirmando.set(false)"
            >
              Cancelar
            </button>
            <button
              type="button"
              [disabled]="enviando()"
              class="tsi-btn bg-alert-warning text-white"
              (click)="confirmar()"
            >
              @if (enviando()) {
                Confirmando…
              } @else {
                Confirmar cambio
              }
            </button>
          </div>
        </div>
      }
    </div>
  `,
})
export class EscalarSeveridadPanel implements OnInit {
  private readonly api = inject(AccidenteApiService);
  private readonly catalogoApi = inject(UbicacionCatalogoApiService);
  private readonly notifications = inject(NotificationService);

  readonly idaccidente = input.required<string>();

  /**
   * Estado VIGENTE del caso, tal como lo devuelve `/mi-seguimiento/actual`.
   */
  readonly severidadActual = input<number | null>(null);
  readonly heridosActuales = input<number>(0);
  readonly fallecidosActuales = input<number>(0);

  readonly severidades = SEVERIDADES;
  readonly unidades = signal<CatalogoItem[]>([]);

  idseveridad: number = 3;
  numheridos = 0;
  numfallecidos = 0;
  idunidademergenciaAdicional: number | null = null;
  nota = '';

  /** Deja que la pantalla contenedora recargue el caso tras un escalado. */
  readonly escalado = output<void>();
  readonly cancelar = output<void>();

  readonly confirmando = signal(false);
  readonly enviando = signal(false);
  readonly error = signal('');

  ngOnInit(): void {
    // Precarga: se parte de lo que el caso ya tiene, no de cero.
    this.numheridos = this.heridosActuales();
    this.numfallecidos = this.fallecidosActuales();
    this.idseveridad = this.siguienteSeveridadPropuesta();

    this.catalogoApi.listarUnidadesEmergencia().subscribe({
      next: (items) => this.unidades.set(items),
      error: () => this.unidades.set([]),
    });
  }

  heridosMinimo(): number {
    return this.heridosActuales();
  }

  fallecidosMinimo(): number {
    return this.fallecidosActuales();
  }

  /**
   * Escalar es subir. Ofrecer severidades por debajo de la vigente invitaba a un
   * envío que el backend iba a rechazar de todas formas.
   */
  severidadesDisponibles(): SeveridadInfo[] {
    const actual = this.severidadActual();
    if (actual == null) {
      return this.severidades;
    }
    return this.severidades.filter((s) => s.value >= actual);
  }

  private siguienteSeveridadPropuesta(): number {
    const actual = this.severidadActual();
    const disponibles = this.severidadesDisponibles();
    if (actual == null) {
      return disponibles[0]?.value ?? 3;
    }
    // Propone el escalón siguiente si existe; si ya está en Fatal, se queda ahí.
    return disponibles.find((s) => s.value > actual)?.value ?? actual;
  }

  severidadLabel(): string {
    return this.severidades.find((s) => s.value === this.idseveridad)?.label ?? String(this.idseveridad);
  }

  severidadActualLabel(): string {
    const actual = this.severidadActual();
    return this.severidades.find((s) => s.value === actual)?.label ?? String(actual ?? '—');
  }

  pedirConfirmacion(): void {
    if (!this.nota.trim()) {
      return;
    }
    this.error.set('');
    this.confirmando.set(true);
  }

  confirmar(): void {
    this.enviando.set(true);
    this.error.set('');
    this.api
      .escalarSeveridad(this.idaccidente(), {
        idseveridad: this.idseveridad,
        numheridos: this.numheridos,
        numfallecidos: this.numfallecidos,
        nota: this.nota,
        ...(this.idunidademergenciaAdicional
          ? { idunidademergencia_adicional: this.idunidademergenciaAdicional }
          : {}),
      })
      .subscribe({
        next: () => {
          this.enviando.set(false);
          this.confirmando.set(false);
          this.notifications.toast('Severidad escalada correctamente', 'success');
          this.escalado.emit();
        },
        error: (err) => {
          this.enviando.set(false);
          this.confirmando.set(false);
          // El 409/422 trae el motivo exacto —severidad incoherente, conteo que
          // baja, estado que no permite escalar—. Tragárselo dejaba a la unidad
          // reintentando a ciegas.
          const detalle =
            err?.error?.error?.detail ?? err?.error?.detail ?? 'No se pudo escalar la severidad.';
          this.error.set(detalle);
          this.notifications.alert(detalle, 'Error al escalar');
        },
      });
  }
}

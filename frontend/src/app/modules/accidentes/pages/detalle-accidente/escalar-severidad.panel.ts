import { ChangeDetectionStrategy, Component, inject, input, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { AccidenteApiService } from '../../services/accidente-api.service';
import { CatalogoItem } from '../../services/models/accidente.types';
import { UbicacionCatalogoApiService } from '../../services/ubicacion-catalogo-api.service';
import { SEVERIDADES } from '../../severidad.constants';

@Component({
  selector: 'app-escalar-severidad-panel',
  standalone: true,
  imports: [FormsModule, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="tsi-panel p-6">
      <h2 class="tsi-display m-0 mb-4 text-base font-semibold text-text-primary">Escalar severidad</h2>

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
              @for (s of severidades; track s.value) {
                <option [ngValue]="s.value">{{ s.label }}</option>
              }
            </select>
          </div>
          <div class="grid gap-1.5">
            <label for="escalarHeridos" class="text-sm font-medium text-text-secondary">Heridos</label>
            <input
              id="escalarHeridos"
              type="number"
              min="0"
              class="tsi-input w-full"
              [(ngModel)]="numheridos"
              name="numheridos"
            />
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
              rows="2"
              required
              class="tsi-textarea w-full"
              [(ngModel)]="nota"
              name="nota"
            ></textarea>
          </div>
          <div class="sm:col-span-2">
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
          <div class="flex gap-2">
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
            <button
              type="button"
              [disabled]="enviando()"
              class="tsi-btn tsi-btn-secondary"
              (click)="confirmando.set(false)"
            >
              Cancelar
            </button>
          </div>
        </div>
      }
    </section>
  `,
})
export class EscalarSeveridadPanel implements OnInit {
  private readonly api = inject(AccidenteApiService);
  private readonly catalogoApi = inject(UbicacionCatalogoApiService);
  private readonly notifications = inject(NotificationService);

  readonly idaccidente = input.required<string>();
  readonly severidades = SEVERIDADES;
  readonly unidades = signal<CatalogoItem[]>([]);

  idseveridad: 1 | 2 | 3 | 4 = 3;
  numheridos = 0;
  idunidademergenciaAdicional: number | null = null;
  nota = '';

  readonly confirmando = signal(false);
  readonly enviando = signal(false);

  ngOnInit(): void {
    this.catalogoApi.listarUnidadesEmergencia().subscribe({
      next: (items) => this.unidades.set(items),
      error: () => this.unidades.set([]),
    });
  }

  severidadLabel(): string {
    return this.severidades.find((s) => s.value === this.idseveridad)?.label ?? String(this.idseveridad);
  }

  pedirConfirmacion(): void {
    if (!this.nota.trim()) {
      return;
    }
    this.confirmando.set(true);
  }

  confirmar(): void {
    this.enviando.set(true);
    this.api
      .escalarSeveridad(this.idaccidente(), {
        idseveridad: this.idseveridad,
        numheridos: this.numheridos,
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
        },
        error: () => {
          this.enviando.set(false);
          this.notifications.alert('No se pudo escalar la severidad.', 'Error al escalar');
        },
      });
  }
}

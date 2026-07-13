import { ChangeDetectionStrategy, Component, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { AccidenteApiService } from '../../services/accidente-api.service';
import { SEVERIDADES } from '../../severidad.constants';

@Component({
  selector: 'app-escalar-severidad-panel',
  standalone: true,
  imports: [FormsModule, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="rounded-lg border border-border-default bg-bg-surface p-6">
      <h2 class="m-0 mb-4 text-base font-semibold text-text-primary">Escalar severidad</h2>

      @if (!confirmando()) {
        <form (ngSubmit)="pedirConfirmacion()" class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div class="grid gap-1.5">
            <label for="escalarSeveridad" class="text-sm font-medium text-text-secondary">Nueva severidad</label>
            <select
              id="escalarSeveridad"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
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
              class="w-full [appearance:textfield] rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
              [(ngModel)]="numheridos"
              name="numheridos"
            />
          </div>
          <div class="grid gap-1.5 sm:col-span-2">
            <label for="escalarNota" class="text-sm font-medium text-text-secondary">Nota (obligatoria)</label>
            <textarea
              id="escalarNota"
              rows="2"
              required
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
              [(ngModel)]="nota"
              name="nota"
            ></textarea>
          </div>
          <div class="sm:col-span-2">
            <button
              type="submit"
              [disabled]="!nota.trim()"
              class="inline-flex items-center gap-2 rounded-md bg-accent-primary px-5 py-2.5 font-semibold text-white disabled:opacity-50 [&:hover:not(:disabled)]:bg-accent-hover"
            >
              Escalar severidad
            </button>
          </div>
        </form>
      } @else {
        <div class="grid gap-3 rounded-lg border border-alert-warning bg-alert-warning-bg p-4">
          <p class="m-0 flex items-center gap-2 text-sm font-medium text-alert-warning">
            <app-tabler-icon name="alert-triangle" [size]="18" />
            La severidad es un campo crítico. ¿Confirmas cambiarla a "{{ severidadLabel() }}"? Esta acción queda
            registrada en el historial del caso.
          </p>
          <div class="flex gap-2">
            <button
              type="button"
              [disabled]="enviando()"
              class="inline-flex items-center gap-2 rounded-md bg-alert-warning px-4 py-2 text-sm font-semibold text-white disabled:opacity-70"
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
              class="inline-flex items-center gap-2 rounded-md border border-border-default px-4 py-2 text-sm font-medium text-text-primary hover:bg-bg-page"
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
export class EscalarSeveridadPanel {
  private readonly api = inject(AccidenteApiService);
  private readonly notifications = inject(NotificationService);

  readonly idaccidente = input.required<string>();
  readonly severidades = SEVERIDADES;

  idseveridad: 1 | 2 | 3 | 4 = 3;
  numheridos = 0;
  nota = '';

  readonly confirmando = signal(false);
  readonly enviando = signal(false);

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

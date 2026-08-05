import { ChangeDetectionStrategy, Component, OnInit, output } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { PeriodoParams } from '../../services/models/informes-tacticos.types';

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

/** FR-UI-002: selector de período compartido por todas las tarjetas de un workpanel. */
@Component({
  selector: 'app-periodo-selector',
  standalone: true,
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="flex flex-wrap items-end gap-3 rounded-lg border border-border-default bg-bg-surface p-3">
      <label class="flex flex-col text-xs text-text-secondary">
        Desde
        <input
          type="date"
          class="mt-1 rounded-md border border-border-default bg-transparent px-2 py-1 text-sm text-text-primary"
          [(ngModel)]="desde"
          (change)="emitir()"
        />
      </label>
      <label class="flex flex-col text-xs text-text-secondary">
        Hasta
        <input
          type="date"
          class="mt-1 rounded-md border border-border-default bg-transparent px-2 py-1 text-sm text-text-primary"
          [(ngModel)]="hasta"
          (change)="emitir()"
        />
      </label>
      <ng-content />
    </div>
  `,
})
export class PeriodoSelectorComponent implements OnInit {
  readonly cambio = output<PeriodoParams>();

  desde = '';
  hasta = '';

  ngOnInit(): void {
    const hoy = new Date();
    const hace30 = new Date(hoy);
    hace30.setDate(hoy.getDate() - 30);
    this.hasta = isoDate(hoy);
    this.desde = isoDate(hace30);
    this.emitir();
  }

  emitir(): void {
    if (!this.desde || !this.hasta) {
      return;
    }
    this.cambio.emit({ desde: this.desde, hasta: this.hasta });
  }
}

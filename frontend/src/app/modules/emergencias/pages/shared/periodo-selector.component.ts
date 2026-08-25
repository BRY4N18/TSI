import { ChangeDetectionStrategy, Component, OnInit, output } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { PeriodoParams } from '../../services/models/informes-tacticos.types';

/**
 * Ventana por defecto, en días. **Tiene que coincidir con la del backend**
 * (`apps/informes_tacticos/periodo.py::DIAS_POR_DEFECTO`): si difieren, la
 * pantalla y la API responden cifras distintas para «los últimos 30 días» y
 * ninguna de las dos parece equivocada.
 */
const DIAS_POR_DEFECTO = 30;

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
    <div class="flex flex-wrap items-end gap-3 rounded-md border border-border-default bg-bg-surface p-3">
      <label class="flex flex-col text-xs text-text-secondary">
        Desde
        <input
          type="date"
          class="tsi-input mt-1"
          [(ngModel)]="desde"
          (change)="emitir()"
        />
      </label>
      <label class="flex flex-col text-xs text-text-secondary">
        Hasta
        <input
          type="date"
          class="tsi-input mt-1"
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
    // ⚠️ `- 29` y no `- 30`: los 30 días **incluyen hoy**, así que el rango es
    // [hoy-29, hoy]. Restar 30 da 31 días contando ambos extremos, y ese día de
    // más no se ve — el informe sale, solo que con datos de una jornada extra.
    //
    // Importa además porque el backend usa [hoy-29, hoy] para su período por
    // defecto: con `- 30` la pantalla y la API respondían cifras distintas para
    // «los últimos 30 días» (492 casos frente a 462), y ninguna de las dos
    // parecía equivocada.
    const hoy = new Date();
    const inicio = new Date(hoy);
    inicio.setDate(hoy.getDate() - (DIAS_POR_DEFECTO - 1));
    this.hasta = isoDate(hoy);
    this.desde = isoDate(inicio);
    this.emitir();
  }

  emitir(): void {
    if (!this.desde || !this.hasta) {
      return;
    }
    this.cambio.emit({ desde: this.desde, hasta: this.hasta });
  }
}

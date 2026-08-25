import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { CargaInforme, num } from '../models/informes-compuestos.types';

export interface BloqueApoyo {
  titulo: string;
  informe: string;
  carga: CargaInforme;
}

@Component({
  selector: 'app-apoyo-plegable',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <details
      class="rounded-md border border-border-default bg-bg-surface"
      data-testid="zona-apoyo"
    >
      <summary
        class="cursor-pointer list-none px-4 py-3 text-sm font-semibold text-text-primary marker:content-none [&::-webkit-details-marker]:hidden"
      >
        <span class="flex items-center justify-between gap-2">
          <span>Detalle</span>
          <span class="text-xs font-medium uppercase tracking-wide text-text-secondary">
            {{ bloques().length }} informes
          </span>
        </span>
      </summary>
      <div class="grid gap-3 border-t border-border-default p-4 sm:grid-cols-2">
        @for (bloque of bloques(); track bloque.informe) {
          <article class="rounded-md border border-border-default bg-bg-page p-3">
            <h3 class="tsi-display m-0 text-xs font-medium uppercase tracking-wide text-text-secondary">
              {{ bloque.titulo }}
            </h3>
            @switch (bloque.carga.estado) {
              @case ('carga') {
                <div class="mt-2 h-8 animate-pulse rounded-md bg-bg-surface"></div>
              }
              @case ('error') {
                <p class="m-0 mt-2 text-sm text-alert-critical">{{ bloque.carga.error }}</p>
              }
              @case ('vacio') {
                <p class="m-0 mt-2 text-sm text-text-secondary">Sin datos en este período.</p>
              }
              @default {
                <p class="m-0 mt-2 text-lg font-semibold text-text-primary">
                  {{ resumen(bloque) }}
                </p>
              }
            }
          </article>
        }
      </div>
    </details>
  `,
})
export class ApoyoPlegableComponent {
  readonly bloques = input.required<BloqueApoyo[]>();

  resumen(bloque: BloqueApoyo): string {
    const filas = bloque.carga.data;
    if (!filas.length) {
      return 'Sin datos en este período.';
    }
    const primera = filas[0];
    const casos = num(primera['casos']);
    const evidencias = num(primera['evidencias']);
    const pendientes = num(primera['pendientes']);
    if (bloque.informe === 'latencia-sincronizacion') {
      // ⚠️ Esto decía «0 sincronizadas · 50 pendientes», que era **lo contrario**
      // de la verdad operativa: las 50 están marcadas como sincronizadas en el
      // origen. Lo que se cuenta es si hay instante con el que medir la
      // latencia, no si la evidencia llegó.
      const con = filas.reduce((acc, f) => acc + (num(f['con_instante_sincronia']) ?? 0), 0);
      const sin = filas.reduce((acc, f) => acc + (num(f['sin_instante_sincronia']) ?? 0), 0);
      const total = con + sin;
      return total === 0
        ? 'sin evidencias en el período'
        : `latencia medible en ${con} de ${total}`;
    }
    if (bloque.informe === 'completitud-enriquecimiento') {
      const pct = num(primera['pct_enriquecidos']);
      return pct === null ? 'sin dato' : `${(pct * 100).toFixed(1)} % enriquecidos`;
    }
    if (bloque.informe === 'volumen-evidencia-por-unidad') {
      return `${filas.length} unidades · ${evidencias ?? '—'} evidencias (primera)`;
    }
    if (bloque.informe === 'escaladas-severidad') {
      const total = filas.reduce((acc, f) => acc + (num(f['con_escalada']) ?? 0), 0);
      return `${total} casos con escalada`;
    }
    if (casos !== null) {
      return `${casos} casos`;
    }
    if (evidencias !== null) {
      return `${evidencias} evidencias`;
    }
    if (pendientes !== null) {
      return `${pendientes} pendientes`;
    }
    return String(primera['periodo'] ?? '') || `${filas.length} filas`;
  }
}

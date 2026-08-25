import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { CargaInforme, num, texto } from '../models/informes-compuestos.types';

export interface BloqueApoyo {
  titulo: string;
  informe: string;
  carga: CargaInforme;
}

@Component({
  selector: 'app-apoyo-plegable-cuentas',
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
        @for (bloque of bloques(); track bloque.informe + bloque.titulo) {
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
                @if (bloque.informe === 'antiguedad-media') {
                  <ul class="m-0 mt-2 flex list-none flex-col gap-1 p-0">
                    @for (fila of bloque.carga.data; track $index) {
                      <li class="text-sm text-text-secondary">
                        {{ texto(fila['tipo_cliente']) }} · {{ texto(fila['plan']) || 'sin plan' }}
                        · {{ num(fila['dias_mediana']) }} días
                      </li>
                    }
                  </ul>
                }
                @if (bloque.informe === 'concurrencia-sesiones') {
                  <p class="m-0 mt-2 text-sm text-text-secondary" data-testid="sesiones-sin-cierre">
                    {{ sesionesSinCierre(bloque) }} sesiones sin cierre, fuera de la mediana
                  </p>
                }
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

  readonly texto = texto;
  readonly num = num;

  resumen(bloque: BloqueApoyo): string {
    const filas = bloque.carga.data;
    if (!filas.length) {
      return 'Sin datos en este período.';
    }
    if (bloque.informe === 'antiguedad-media') {
      return `${filas.length} grupos de antigüedad`;
    }
    if (bloque.informe === 'concurrencia-sesiones') {
      return 'Duración solo sobre sesiones cerradas';
    }
    return `${filas.length} filas`;
  }

  sesionesSinCierre(bloque: BloqueApoyo): number {
    return bloque.carga.data.reduce((acc, fila) => acc + (num(fila['sesiones_sin_cierre']) ?? 0), 0);
  }
}

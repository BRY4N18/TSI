import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { CargaInforme, num, texto } from '../models/informes-compuestos.types';

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
      class="rounded-lg border border-border-default bg-bg-surface"
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
            <h3 class="m-0 text-xs font-medium uppercase tracking-wide text-text-secondary">
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
                @if (notaDe(bloque); as nota) {
                  <p class="m-0 mt-2 text-xs text-text-secondary" data-testid="nota-pesos">
                    {{ nota }}
                  </p>
                }
                @if (bloque.informe === 'carga-por-ejecutivo') {
                  <ul class="m-0 mt-2 flex list-none flex-col gap-1 p-0">
                    @for (fila of bloque.carga.data; track texto(fila['idejecutivo'])) {
                      <li class="text-sm text-text-secondary">
                        Ejecutivo {{ texto(fila['idejecutivo']) }}
                        · {{ num(fila['activos']) ?? 0 }} activos
                        · {{ num(fila['conversiones']) ?? 0 }} conversiones
                      </li>
                    }
                  </ul>
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

  readonly num = num;
  readonly texto = texto;

  notaDe(bloque: BloqueApoyo): string {
    const filtros = bloque.carga.meta.filtros ?? {};
    const notaFiltro = filtros['nota_pesos'];
    if (typeof notaFiltro === 'string' && notaFiltro) {
      return notaFiltro;
    }
    return bloque.carga.meta.nota_pesos || '';
  }

  resumen(bloque: BloqueApoyo): string {
    const filas = bloque.carga.data;
    if (!filas.length) {
      return 'Sin datos en este período.';
    }
    if (bloque.informe === 'carga-por-ejecutivo') {
      const activos = filas.reduce((acc, f) => acc + (num(f['activos']) ?? 0), 0);
      return `${filas.length} ejecutivos · ${activos} activos`;
    }
    if (bloque.informe === 'pipeline-ponderado') {
      const valor = filas.reduce((acc, f) => acc + (num(f['valor_ponderado']) ?? 0), 0);
      return `Pipeline ponderado ${valor}`;
    }
    if (bloque.informe === 'reglas-disparo') {
      return `${filas.length} reglas disparadas`;
    }
    return `${filas.length} filas`;
  }
}

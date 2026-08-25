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
                @if (bloque.carga.meta.medida_exacta_desde) {
                  <p
                    class="m-0 mt-2 text-xs text-text-secondary"
                    data-testid="medida-exacta-desde"
                  >
                    Medida exacta desde {{ bloque.carga.meta.medida_exacta_desde }}. Un vacío no
                    significa que nunca haya pasado.
                  </p>
                }
              }
              @default {
                <p class="m-0 mt-2 text-lg font-semibold text-text-primary">
                  {{ resumen(bloque) }}
                </p>
                @if (notaDe(bloque); as nota) {
                  <p class="m-0 mt-2 text-xs text-text-secondary">{{ nota }}</p>
                }
                @if (bloque.carga.meta.medida_exacta_desde) {
                  <p class="m-0 mt-2 text-xs text-text-secondary" data-testid="medida-exacta-desde">
                    Medida exacta desde {{ bloque.carga.meta.medida_exacta_desde }}
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

  notaDe(bloque: BloqueApoyo): string {
    return (
      bloque.carga.meta.nota_region ||
      bloque.carga.meta.nota_historico ||
      bloque.carga.meta.nota ||
      ''
    );
  }

  resumen(bloque: BloqueApoyo): string {
    const filas = bloque.carga.data;
    if (!filas.length) {
      return 'Sin datos en este período.';
    }
    if (bloque.informe === 'cobertura-flota-por-region') {
      const primera = texto(filas[0]['region']) || 'Sin región asignada';
      const unidades = filas.reduce((acc, f) => acc + (num(f['unidades']) ?? 0), 0);
      return `${primera} · ${unidades} unidades`;
    }
    if (bloque.informe === 'pendientes-primer-acceso') {
      return `${filas.length} unidades pendientes de primer acceso`;
    }
    if (bloque.informe === 'rendimiento-proveedor') {
      return `${filas.length} proveedores`;
    }
    if (bloque.informe === 'rotacion-flota') {
      const bajas = filas.reduce((acc, f) => acc + (num(f['bajas']) ?? 0), 0);
      return `${bajas} bajas en el período`;
    }
    if (bloque.informe === 'bajas-forzadas') {
      const forzadas = filas.reduce(
        (acc, f) => acc + (num(f['forzadas']) ?? 0) + (num(f['forzadas_con_reasignacion']) ?? 0),
        0,
      );
      const enCurso = filas.reduce((acc, f) => acc + (num(f['con_caso_en_curso']) ?? 0), 0);
      return `${forzadas} forzadas · ${enCurso} con caso en curso`;
    }
    if (bloque.informe === 'casos-activos-al-despublicar') {
      const casos = filas.reduce((acc, f) => acc + (num(f['casos_activos']) ?? 0), 0);
      return `${filas.length} regiones · ${casos} casos activos al despublicar`;
    }
    if (bloque.informe === 'tiempo-perdida-a-despublicacion') {
      const primera = filas[0];
      const mediana = num(primera['mediana_dias']);
      const inaccion = num(primera['aun_publicadas_sin_flota']);
      const medianaTxt = mediana === null ? 'ausente' : `${mediana} días de mediana`;
      return `${medianaTxt} · ${inaccion ?? 0} aún publicadas sin flota`;
    }
    return `${filas.length} filas`;
  }
}

import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { CargaInforme, num, texto } from '../models/informes-oe2.types';

export interface BloqueApoyo {
  titulo: string;
  informe: string;
  carga: CargaInforme;
}

@Component({
  selector: 'app-apoyo-plegable-oe2',
  standalone: true,
  imports: [DecimalPipe],
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
                @if (bloque.informe === 'latencia-por-endpoint') {
                  <ul class="m-0 mt-2 flex list-none flex-col gap-2 p-0" data-testid="trio-latencia">
                    @for (fila of bloque.carga.data; track texto(fila['endpoint_path'])) {
                      <li>
                        <p class="m-0 text-sm font-semibold text-text-primary">
                          {{ texto(fila['endpoint_path']) }}
                        </p>
                        <p class="m-0 text-lg font-bold tabular-nums text-text-primary">
                          @if (num(fila['latencia_p95_ms']) === null) {
                            <span data-testid="p95-sin-dato">sin dato</span>
                          } @else {
                            {{ num(fila['latencia_p95_ms']) | number: '1.0-1' }}
                            <span class="text-sm font-medium">ms p95</span>
                          }
                        </p>
                        <p class="m-0 text-sm text-text-secondary">
                          media {{ num(fila['latencia_media_ms']) | number: '1.0-1' }} ms ·
                          {{ num(fila['muestras']) | number }} muestras
                          @if (num(fila['percentil_fiable']) === 0) {
                            <span data-testid="marca-no-fiable"> · no fiable</span>
                          }
                        </p>
                      </li>
                    }
                  </ul>
                } @else if (bloque.informe === 'participacion-ingresos-api' || bloque.informe === 'mrr-por-linea') {
                  <p class="m-0 mt-2 text-sm text-text-secondary" data-testid="zona-parcial">
                    @if (bloque.carga.meta.cobertura === 'parcial') {
                      Parcial
                      @if (bloque.carga.meta.falta?.length) {
                        · falta {{ bloque.carga.meta.falta!.join(', ') }}
                      }
                    } @else {
                      {{ resumen(bloque) }}
                    }
                  </p>
                  <ul class="m-0 mt-2 flex list-none flex-col gap-1 p-0">
                    @for (fila of bloque.carga.data; track $index) {
                      <li class="text-sm text-text-secondary">
                        {{ texto(fila['linea'] ?? fila['periodo']) }} ·
                        {{ num(fila['monto'] ?? fila['llamadas']) }}
                      </li>
                    }
                  </ul>
                } @else {
                  <p class="m-0 mt-2 text-lg font-semibold text-text-primary">
                    {{ resumen(bloque) }}
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
    return `${bloque.carga.data.length} filas`;
  }
}

import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { CargaInforme, num, texto } from '../models/informes-oe5.types';

export interface BloqueApoyo {
  titulo: string;
  informe: string;
  carga: CargaInforme;
}

@Component({
  selector: 'app-apoyo-plegable-oe5',
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
                @if (bloque.informe === 'rendimiento-por-agente') {
                  <ul class="m-0 mt-2 flex list-none flex-col gap-1 p-0">
                    @for (fila of bloque.carga.data; track $index) {
                      <li class="text-sm text-text-secondary">
                        agente {{ texto(fila['idagente']) }} ·
                        {{ num(fila['asignados']) | number }} asignados ·
                        {{ num(fila['resueltos']) | number }} resueltos
                      </li>
                    }
                  </ul>
                } @else if (bloque.informe === 'reincidencia-soporte') {
                  <ul class="m-0 mt-2 flex list-none flex-col gap-1 p-0">
                    @for (fila of bloque.carga.data; track $index) {
                      <li class="text-sm text-text-secondary">
                        cliente {{ texto(fila['idcliente']) }} ·
                        {{ texto(fila['servicio']) }} ·
                        {{ num(fila['tickets']) | number }} tickets
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

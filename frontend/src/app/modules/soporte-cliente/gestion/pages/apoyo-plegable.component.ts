import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

import { CargaInforme, num, texto } from '../models/informes-compuestos.types';
import { mensajeVacio } from '../../../../shared/informes/mensaje-vacio';

export interface BloqueApoyo {
  titulo: string;
  informe: string;
  carga: CargaInforme;
}

@Component({
  selector: 'app-apoyo-plegable-soporte',
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
                <p class="m-0 mt-2 text-sm text-text-secondary">{{ textoVacio() }}</p>
              }
              @default {
                <p class="m-0 mt-2 text-lg font-semibold text-text-primary">
                  {{ resumen(bloque) }}
                </p>
                @if (bloque.informe === 'tickets-por-servicio') {
                  <ul class="m-0 mt-2 flex list-none flex-col gap-1 p-0">
                    @for (fila of bloque.carga.data; track texto(fila['servicio'])) {
                      <li class="text-sm text-text-secondary" data-testid="fila-servicio">
                        {{ texto(fila['servicio']) || 'sin servicio' }}
                        · {{ num(fila['tickets']) ?? 0 }} tickets
                        · {{ num(fila['incumplidos']) ?? 0 }} incumplidos
                      </li>
                    }
                  </ul>
                }
                @for (decl of bloque.carga.declaraciones; track $index) {
                  <p class="m-0 mt-2 text-xs text-text-secondary" data-testid="declaracion-apoyo">
                    {{ decl.mensaje }}
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
  /** Alcance declarado por el envelope; decide el texto del estado vacío. */
  readonly alcance = input<string | null>(null);

  readonly textoVacio = computed(() => mensajeVacio(this.alcance()));

  readonly num = num;
  readonly texto = texto;

  resumen(bloque: BloqueApoyo): string {
    const filas = bloque.carga.data;
    if (!filas.length) {
      return mensajeVacio(this.alcance());
    }
    if (bloque.informe === 'tickets-por-servicio') {
      const tickets = filas.reduce((acc, f) => acc + (num(f['tickets']) ?? 0), 0);
      return `${tickets} tickets · la operación no asigna servicio`;
    }
    return `${filas.length} filas`;
  }
}

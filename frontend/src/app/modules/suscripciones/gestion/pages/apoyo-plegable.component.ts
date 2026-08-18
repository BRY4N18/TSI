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
                @if (bloque.informe === 'clientes-sin-metodo-pago') {
                  <ul class="m-0 mt-2 flex list-none flex-col gap-1 p-0">
                    @for (fila of bloque.carga.data; track $index) {
                      <li class="text-sm text-text-secondary" data-testid="sin-metodo-fila">
                        {{ texto(fila['nombre_comercial']) || 'Cliente' }}
                        @if (num(fila['caduca_en_dias']) !== null) {
                          · caduca en {{ num(fila['caduca_en_dias']) }} días
                        }
                      </li>
                    }
                  </ul>
                }
                @if (notaDe(bloque); as nota) {
                  <p class="m-0 mt-2 text-xs text-text-secondary">{{ nota }}</p>
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

  notaDe(bloque: BloqueApoyo): string {
    const filtros = bloque.carga.meta.filtros ?? {};
    if (bloque.informe === 'efectividad-dunning' && filtros['escalones_dunning']) {
      return `Escalones (días): ${String(filtros['escalones_dunning'])}`;
    }
    return bloque.carga.meta.nota || '';
  }

  resumen(bloque: BloqueApoyo): string {
    const filas = bloque.carga.data;
    if (!filas.length) {
      return 'Sin datos en este período.';
    }
    if (bloque.informe === 'cobro-primer-intento') {
      const primera = filas[0];
      const primer = num(primera['primer_intento']);
      const pagadas = num(primera['pagadas']);
      return `${primer ?? 0} de ${pagadas ?? 0} cobradas al primer intento`;
    }
    if (bloque.informe === 'efectividad-dunning') {
      return `${filas.length} escalones de recuperación`;
    }
    if (bloque.informe === 'clientes-sin-metodo-pago') {
      return `${filas.length} clientes sin método`;
    }
    if (bloque.informe === 'suspension-reactivacion') {
      const primera = filas[0];
      return `${num(primera['suspendidas']) ?? 0} suspendidas · ${num(primera['reactivadas']) ?? 0} reactivadas`;
    }
    return `${filas.length} filas`;
  }
}

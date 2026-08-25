import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { BrandMarkComponent } from './brand-mark.component';

/**
 * Panel de marca de las pantallas públicas (login, registro). Vivía duplicado
 * literal en `login.page.html` y `registro-publico.page.html`, con los hex
 * `#14161f` y `#ffffff` escritos a mano y un patrón de líneas que no decía nada
 * del logo. Ahora es un solo componente y usa las primitivas de §3.1:
 *
 * - Fondo `.tsi-node-surface` (degradado de convergencia) en vez de un hex fijo,
 *   así el panel sigue el tema en vez de ser siempre el gris oscuro de la paleta
 *   anterior.
 * - Patrón de tres vías que convergen en el hexágono del isotipo, cada una con
 *   su divisoria interior — trazo grueso en cian, línea fina encima. Es el rol
 *   que §3.1 le asigna al cian sobre esta superficie: trazo, no relleno.
 *
 * El panel es decorativo (`aria-hidden`): solo aparece en ≥lg, y el contenido
 * accionable de la pantalla vive siempre en la columna del formulario.
 */
@Component({
  selector: 'app-brand-panel',
  standalone: true,
  imports: [BrandMarkComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  // Los estilos van en el HOST, no en un <section> interno: el elemento que
  // entra en la rejilla de la pantalla es `<app-brand-panel>`. Con el envoltorio
  // dentro, el host quedaba sin estilo y el panel no se estiraba al alto de la
  // fila — el contenido se apelotonaba arriba y `justify-between` no tenía
  // espacio que repartir.
  host: {
    class:
      'tsi-node-surface relative hidden overflow-hidden p-12 lg:flex lg:flex-col lg:justify-between',
    'aria-hidden': 'true',
  },
  template: `
    <svg
      class="pointer-events-none absolute inset-0 h-full w-full"
      viewBox="0 0 400 500"
      fill="none"
    >
      <!-- Tres vías convergiendo en el nodo hexagonal. El grupo se dibuja dos
           veces: primero el trazo grueso (la vía), luego la línea fina encima
           (la divisoria interior). Es la misma construcción del isotipo.

           Los tramos de entrada arrancan muy por fuera del viewBox a propósito:
           con preserveAspectRatio por defecto (meet) el viewBox no cubre todo
           el panel, y un extremo que acabe en su borde queda *dentro* del panel,
           dejando ver el remate del trazo colgando en el aire. El SVG recorta a
           su viewport, no al viewBox, así que el sobrante simplemente se sale. -->
        <g opacity="0.16" fill="none" stroke-linejoin="round" stroke-linecap="round">
          <g stroke="#00a8e8" stroke-width="26">
            <path d="M150 -400 L150 40 L200 110 L200 192" />
            <path d="M-500 480 L50 480 L120 400 L150 279" />
            <path d="M900 390 L330 390 L260 320 L250 279" />
            <path d="M200 192 L250 221 L250 279 L200 308 L150 279 L150 221 Z" />
          </g>
          <g stroke="#001a38" stroke-width="2">
            <path d="M150 -400 L150 40 L200 110 L200 192" />
            <path d="M-500 480 L50 480 L120 400 L150 279" />
            <path d="M900 390 L330 390 L260 320 L250 279" />
            <path d="M200 192 L250 221 L250 279 L200 308 L150 279 L150 221 Z" />
          </g>
        </g>
      </svg>

    <div class="relative flex items-center gap-3">
      <app-brand-mark size="lg" [decorative]="true" />
      <span class="text-base font-semibold text-white">Tráfico Seguro Integral</span>
    </div>

    <div class="relative grid max-w-sm gap-4">
      <p class="m-0 text-xs font-medium uppercase tracking-wide text-white/60">
        {{ eyebrow() }}
      </p>
      <p class="m-0 text-[28px] font-bold leading-tight text-white">{{ headline() }}</p>
      <p class="m-0 text-sm leading-relaxed text-white/70">{{ body() }}</p>
    </div>

    <div class="relative flex items-center gap-2 text-xs text-white/70">
      <span class="h-2 w-2 rounded-full bg-alert-success motion-safe:animate-pulse"></span>
      {{ status() }}
    </div>
  `,
})
export class BrandPanelComponent {
  readonly eyebrow = input.required<string>();
  readonly headline = input.required<string>();
  readonly body = input.required<string>();
  readonly status = input.required<string>();
}

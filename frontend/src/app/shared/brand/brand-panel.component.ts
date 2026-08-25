import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { BrandMarkComponent } from './brand-mark.component';
import { NodePatternComponent } from './node-pattern.component';

/**
 * Panel de marca de las pantallas públicas (login, registro). Vivía duplicado
 * literal en `login.page.html` y `registro-publico.page.html`, con los hex
 * `#14161f` y `#ffffff` escritos a mano y un patrón de líneas que no decía nada
 * del logo. Ahora es un solo componente y usa las primitivas de §3.1:
 *
 * - Fondo `.tsi-node-surface` (degradado de convergencia) en vez de un hex fijo,
 *   así el panel sigue el tema en vez de ser siempre el gris oscuro de la paleta
 *   anterior.
 * - Patrón de tres vías del isotipo, vía app-node-pattern.
 *
 * El panel es decorativo (`aria-hidden`): solo aparece en ≥lg, y el contenido
 * accionable de la pantalla vive siempre en la columna del formulario.
 */
@Component({
  selector: 'app-brand-panel',
  standalone: true,
  imports: [BrandMarkComponent, NodePatternComponent],
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
    <app-node-pattern variante="panel" />

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

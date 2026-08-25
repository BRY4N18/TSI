import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

/**
 * El patrón de las tres vías convergiendo en el nodo, del isotipo Nodo Integral.
 *
 * Vivía incrustado en app-brand-panel. Se extrae porque el hub de inicio lo
 * necesita en horizontal: es el mismo motivo, no una segunda decoración.
 *
 * Cada vía se dibuja dos veces —trazo grueso y divisoria fina encima—, que es
 * la construcción del logo. Los tramos de entrada arrancan muy por fuera del
 * viewBox a propósito: con preserveAspectRatio por defecto el viewBox no cubre
 * todo el contenedor, y un extremo que acabe en su borde queda dentro,
 * dejando ver el remate del trazo colgando en el aire.
 */
@Component({
  selector: 'app-node-pattern',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <svg
      class="pointer-events-none absolute inset-0 h-full w-full"
      [attr.viewBox]="viewBox()"
      fill="none"
      aria-hidden="true"
    >
      <g
        [attr.opacity]="opacidad()"
        fill="none"
        stroke-linejoin="round"
        stroke-linecap="round"
      >
        <g stroke="#00a8e8" [attr.stroke-width]="grosor()">
          @for (d of trazos(); track d) {
            <path [attr.d]="d" />
          }
        </g>
        <g stroke="#001a38" [attr.stroke-width]="grosorDivisoria()">
          @for (d of trazos(); track d) {
            <path [attr.d]="d" />
          }
        </g>
      </g>
    </svg>
  `,
})
export class NodePatternComponent {
  /** 'panel' para columnas altas (auth); 'banda' para cabeceras anchas. */
  readonly variante = input<'panel' | 'banda'>('panel');
  readonly opacidad = input(0.16);

  readonly viewBox = computed(() =>
    this.variante() === 'banda' ? '0 0 900 200' : '0 0 400 500',
  );

  readonly grosor = computed(() => (this.variante() === 'banda' ? 26 : 26));
  readonly grosorDivisoria = computed(() => 2);

  readonly trazos = computed(() =>
    this.variante() === 'banda'
      ? [
          'M-400 40 L380 40 L470 77 L660 77',
          'M-400 180 L340 180 L470 123 L660 123',
          'M1400 100 L740 100',
          'M700 54 L740 77 L740 123 L700 146 L660 123 L660 77 Z',
        ]
      : [
          'M150 -400 L150 40 L200 110 L200 192',
          'M-500 480 L50 480 L120 400 L150 279',
          'M900 390 L330 390 L260 320 L250 279',
          'M200 192 L250 221 L250 279 L200 308 L150 279 L150 221 Z',
        ],
  );
}

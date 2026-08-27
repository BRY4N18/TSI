import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, LOCALE_ID, computed, inject, input } from '@angular/core';

import { TablerIconComponent } from '../icon/tabler-icon.component';

/**
 * Medidor de consumo contra un límite (design-system.md §5.1).
 *
 * **Por qué no es una barra normal.** Una barra compara magnitudes entre
 * categorías; un medidor responde otra pregunta: *¿cuánto de lo contratado
 * se está usando, y se pasó?* La diferencia importa porque el 100% no es el
 * máximo del eje — es **el límite**, y superarlo es un hecho operativo, no
 * un valor más alto.
 *
 * Esto arregla un problema real: la utilización de límites se mostraba como
 * texto («19 de 5 unidades») y un plan pasado de cupo se leía igual que uno
 * al 20%. Había que restar mentalmente, fila por fila, para notarlo.
 *
 * **La pista es un paso claro de la misma rampa** que el relleno (azul sobre
 * azul), no un gris neutro: así el estado se lee a lo largo de toda la
 * barra y no solo en el trozo lleno.
 *
 * **El exceso viste color de alerta, y con etiqueta.** Pasarse de cupo
 * significa «mal», no «más»: ahí el token de severidad es el correcto. Y
 * como el color nunca puede ser el único portador, va acompañado de un
 * ícono y de la palabra «excedido».
 */
@Component({
  selector: 'app-meter',
  standalone: true,
  imports: [TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="grid gap-1">
      <div class="flex items-baseline justify-between gap-3 text-sm">
        <span class="min-w-0 truncate text-text-secondary">{{ etiqueta() }}</span>
        <span class="shrink-0 tabular-nums">
          @if (limite() === null) {
            <span class="text-text-secondary">sin límite configurado</span>
          } @else {
            <span class="font-semibold" [class.text-alert-critical]="excedido()" [class.text-text-primary]="!excedido()">
              {{ fmt(usado()) }} de {{ fmt(limite()!) }}
            </span>
            <span class="ml-1 text-text-secondary">{{ unidad() }}</span>
          }
        </span>
      </div>

      @if (limite() !== null) {
        <div class="flex items-center gap-2">
          <div
            class="h-2.5 min-w-0 flex-1 overflow-hidden rounded-sm"
            style="background: var(--chart-seq-1)"
          >
            <div
              class="h-full"
              style="border-radius: 0 4px 4px 0"
              [style.width.%]="anchoRelleno()"
              [style.background]="excedido() ? 'var(--alert-critical)' : 'var(--chart-seq-4)'"
            ></div>
          </div>
          <span
            class="shrink-0 text-xs tabular-nums"
            [class.text-alert-critical]="excedido()"
            [class.text-text-secondary]="!excedido()"
          >
            {{ pct() }}
          </span>
        </div>

        @if (excedido()) {
          <!-- El color no puede ser el único portador del estado: ícono y
               palabra van siempre con él. -->
          <p class="m-0 flex items-center gap-1 text-xs font-medium text-alert-critical">
            <app-tabler-icon name="alert-triangle" [size]="14" />
            Excedido en {{ fmt(usado() - limite()!) }} {{ unidad() }}
          </p>
        }
      }
    </div>
  `,
})
export class MeterComponent {
  readonly etiqueta = input.required<string>();
  readonly usado = input.required<number>();
  /** `null` = el plan no declara límite. No es lo mismo que un límite de 0. */
  readonly limite = input.required<number | null>();
  readonly unidad = input<string>('');

  private readonly locale = inject(LOCALE_ID);
  private readonly decimal = new DecimalPipe(this.locale);

  protected readonly excedido = computed(() => {
    const lim = this.limite();
    return lim !== null && lim > 0 && this.usado() > lim;
  });

  /**
   * El relleno se topa al 100%: la barra representa el límite, no el
   * consumo, así que pasarse no la alarga —eso sugeriría que el límite es
   * mayor de lo que es—. El exceso lo comunican el color, el porcentaje y
   * la línea de «excedido».
   */
  protected readonly anchoRelleno = computed(() => {
    const lim = this.limite();
    if (lim === null || lim <= 0) {
      return 0;
    }
    return Math.min(100, (this.usado() / lim) * 100);
  });

  protected pct(): string {
    const lim = this.limite();
    if (lim === null || lim <= 0) {
      return '—';
    }
    return `${this.decimal.transform((this.usado() / lim) * 100, '1.0-0')} %`;
  }

  protected fmt(valor: number): string {
    return this.decimal.transform(valor, '1.0-0') ?? String(valor);
  }
}

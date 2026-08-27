import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, LOCALE_ID, computed, inject, input } from '@angular/core';

export type BarTono = 'success' | 'warning' | 'urgent' | 'critical' | 'info';

export interface BarDatum {
  etiqueta: string;
  /** `null` = el dato no llegó. No es lo mismo que 0 y no se dibuja como 0. */
  valor: number | null;
  /** Texto extra a la derecha del valor (contexto, no otra medida). */
  nota?: string;
  /**
   * Rótulo ya formateado, cuando la unidad no es un número a secas
   * («3 h 20 min», «$149.00»). Sustituye al formato automático; el valor
   * numérico se sigue usando para la longitud de la barra.
   */
  valorTexto?: string;
  /**
   * Tono semántico, **solo** cuando la categoría significa bien/mal por sí
   * misma («completos» vs «incompletos», «sin evidencia»). Pinta la barra
   * con el token de alerta correspondiente y anula la escala.
   *
   * No es un atajo para colorear categorías cualesquiera: si la categoría
   * es solo «otra más», va sin tono. Un color de severidad usado como
   * identidad deja de poder significar severidad en el resto del sistema.
   */
  tono?: BarTono;
}

const TONO_COLOR: Record<BarTono, string> = {
  success: 'var(--alert-success)',
  warning: 'var(--alert-warning)',
  urgent: 'var(--alert-urgent)',
  critical: 'var(--alert-critical)',
  info: 'var(--alert-info)',
};

/** Escalas de las 5 pasos de `--chart-seq-*`, de claro a oscuro. */
const RAMPA = [
  'var(--chart-seq-1)',
  'var(--chart-seq-2)',
  'var(--chart-seq-3)',
  'var(--chart-seq-4)',
  'var(--chart-seq-5)',
];

/**
 * Barras horizontales para comparar magnitudes (design-system.md §5.1).
 *
 * **Por qué horizontal y no columnas:** las etiquetas de este sistema son
 * nombres largos («Pendiente de clasificacion», «Region Miami-Dade»). En
 * columnas verticales habría que rotarlas o truncarlas; en barras
 * horizontales el nombre se lee de corrido.
 *
 * **La regla de color, que es la parte que se suele hacer mal.** Hay dos
 * escalas y elegir la equivocada desinforma:
 *
 * - `nominal` (por defecto): las categorías no tienen orden propio — planes,
 *   regiones, agentes, estados. **Todas las barras van del mismo color**
 *   (`--chart-cat-1`). Teñir cada barra de un color distinto según su valor
 *   gastaría el canal de identidad en repetir lo que la longitud de la barra
 *   ya dice, y además insinuaría que las categorías son series distintas.
 * - `ordinal`: el orden de las categorías **significa** algo — niveles de
 *   prioridad (Baja→Alta), tramos de antigüedad, etapas. Ahí sí se usa la
 *   rampa de un solo tono, para que el orden se vea en el color.
 *
 * **Sin tooltip, a propósito.** Cada barra lleva su valor rotulado en la
 * punta, así que un tooltip al pasar el ratón repetiría un dato que ya está
 * en pantalla — y dejaría el valor fuera del alcance de quien navega con
 * teclado. El gráfico de líneas sí lo lleva, porque ahí los puntos no se
 * pueden rotular todos.
 */
@Component({
  selector: 'app-bar-chart',
  standalone: true,
  imports: [DecimalPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ul class="m-0 flex list-none flex-col gap-3 p-0">
      @for (d of datos(); track d.etiqueta; let i = $index) {
        <li>
          <div class="mb-1 flex items-baseline justify-between gap-3 text-sm">
            <span class="min-w-0 truncate text-text-secondary">{{ d.etiqueta }}</span>
            <!-- El valor va rotulado en la punta y en tokens de TEXTO, nunca
                 en el color de la serie: un tono claro sería ilegible como
                 texto. La identidad la lleva la barra de al lado. -->
            <span class="shrink-0 font-semibold tabular-nums text-text-primary">
              @if (d.valor === null) {
                <span class="font-normal text-text-secondary">sin dato</span>
              } @else {
                {{ d.valorTexto ?? formatear(d.valor) }}
              }
              @if (d.nota) {
                <span class="ml-1 font-normal text-text-secondary">{{ d.nota }}</span>
              }
            </span>
          </div>
          <!-- Pista de 10px: marca fina, muy por debajo del tope de 24px. -->
          @if (escala() === 'divergente') {
            <!-- Divergente: la línea base está en el CENTRO, no a la
                 izquierda. Lo positivo crece a la derecha y lo negativo a la
                 izquierda, así que el signo se ve antes de leer el número. -->
            <div class="relative h-2.5 w-full rounded-sm bg-bg-page">
              <span
                class="absolute inset-y-0 left-1/2 w-px"
                style="background: var(--chart-grid)"
                aria-hidden="true"
              ></span>
              @if (d.valor !== null && d.valor !== 0) {
                <div
                  class="absolute inset-y-0"
                  [style.left.%]="d.valor > 0 ? 50 : 50 - semiAncho(d.valor)"
                  [style.width.%]="semiAncho(d.valor)"
                  [style.border-radius]="d.valor > 0 ? '0 4px 4px 0' : '4px 0 0 4px'"
                  [style.background]="color(i, d)"
                ></div>
              }
            </div>
          } @else {
            <div class="h-2.5 w-full overflow-hidden rounded-sm bg-bg-page">
              @if (d.valor !== null) {
                <!-- Extremo del dato redondeado 4px, recto en la línea base:
                     así se lee de dónde crece la barra. -->
                <div
                  class="h-full"
                  style="border-radius: 0 4px 4px 0"
                  [style.width.%]="ancho(d.valor)"
                  [style.background]="color(i, d)"
                ></div>
              }
            </div>
          }
        </li>
      }
    </ul>
  `,
})
export class BarChartComponent {
  readonly datos = input.required<BarDatum[]>();
  readonly escala = input<'nominal' | 'ordinal' | 'divergente'>('nominal');
  readonly formato = input<'numero' | 'porcentaje'>('numero');
  /** Decimales del valor rotulado. Importa en importes, donde 0 miente. */
  readonly decimales = input(0);
  /** Tope del eje. Sin él se usa el mayor valor presente (100 en porcentaje). */
  readonly maximo = input<number | null>(null);

  // El locale se INYECTA, no se escribe a mano: `new DecimalPipe('es-EC')`
  // lanza NG0701 porque ese locale no está registrado en la app, y el fallo
  // se come en silencio el valor y el ancho de la barra. Misma pauta que
  // `informes-listado.component.ts`.
  private readonly locale = inject(LOCALE_ID);
  private readonly decimal = new DecimalPipe(this.locale);

  private readonly tope = computed(() => {
    const declarado = this.maximo();
    if (declarado !== null && declarado > 0) {
      return declarado;
    }
    if (this.formato() === 'porcentaje') {
      return 100;
    }
    const valores = this.datos()
      .map((d) => d.valor)
      .filter((v): v is number => v !== null)
      // En divergente el eje se escala por la MAGNITUD mayor, venga del
      // lado que venga: si no, el brazo negativo se mediría contra un tope
      // positivo y un -200 se vería más corto que un +200 igual de grande.
      .map((v) => (this.escala() === 'divergente' ? Math.abs(v) : v));
    const max = Math.max(0, ...valores);
    // Con todo en cero no hay escala posible; se evita dividir por 0 y todas
    // las barras quedan vacías, que es la lectura honesta.
    return max > 0 ? max : 1;
  });

  protected ancho(valor: number): number {
    return Math.max(0, Math.min(100, (valor / this.tope()) * 100));
  }

  /** Mitad del ancho que ocupa un valor en escala divergente (cada brazo es 50%). */
  protected semiAncho(valor: number): number {
    return Math.min(50, (Math.abs(valor) / this.tope()) * 50);
  }

  protected color(indice: number, d: BarDatum): string {
    // El tono semántico manda sobre la escala: si la categoría significa
    // bien/mal, ese es el dato y no puede quedar tapado por el color de
    // identidad.
    if (d.tono) {
      return TONO_COLOR[d.tono];
    }
    if (this.escala() === 'divergente') {
      // Dos polos + el centro neutro que ya dibuja la línea. No se usan
      // tokens de alerta: un downgrade es la otra dirección de un
      // movimiento normal, no una incidencia.
      return (d.valor ?? 0) >= 0 ? 'var(--chart-cat-1)' : 'var(--chart-cat-2)';
    }
    if (this.escala() === 'nominal') {
      return 'var(--chart-cat-1)';
    }
    // Ordinal: se reparten los 5 pasos a lo largo de las categorías, de
    // claro a oscuro, para que el orden se lea en el color.
    const total = this.datos().length;
    if (total <= 1) {
      return RAMPA[RAMPA.length - 1];
    }
    const paso = Math.round((indice / (total - 1)) * (RAMPA.length - 1));
    return RAMPA[paso];
  }

  protected formatear(valor: number): string {
    if (this.formato() === 'porcentaje') {
      return `${this.decimal.transform(valor, '1.0-1')} %`;
    }
    const d = this.decimales();
    return this.decimal.transform(valor, `1.${d}-${d}`) ?? String(valor);
  }
}

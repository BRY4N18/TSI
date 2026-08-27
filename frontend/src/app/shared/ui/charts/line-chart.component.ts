import { DecimalPipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
  computed,
  input,
  signal,
} from '@angular/core';

export interface LineSeries {
  nombre: string;
  /** Un `null` corta la línea: es un hueco declarado, no un cero. */
  valores: (number | null)[];
}

const CAT = ['var(--chart-cat-1)', 'var(--chart-cat-2)', 'var(--chart-cat-3)', 'var(--chart-cat-4)'];

// Márgenes del área de trazado. `DER` reserva sitio al rótulo del extremo.
const SUP = 12;
const DER = 16;
const INF = 26;
const IZQ = 44;

/**
 * Serie temporal (design-system.md §5.1).
 *
 * **Por qué existe:** varias pantallas tenían una evolución por fecha
 * («carga entrante frente a resuelta», «evolución del incumplimiento»)
 * dibujada como una lista de días. Una lista obliga a reconstruir la
 * tendencia leyendo número por número; eso es exactamente el trabajo que
 * una línea hace de un vistazo.
 *
 * **Un solo eje, siempre.** Dos medidas de escalas distintas no se
 * superponen con dos ejes Y: eso deja que la escala invente cruces que no
 * existen. Si dos medidas no comparten escala, van en dos gráficos.
 *
 * Marca: línea de 2px con uniones redondas, punto final de 8px con anillo
 * de 2px del color del fondo para que no se pierda al cruzarse con otra
 * serie, y relleno de área al 10% solo cuando hay una sola serie (con dos
 * se taparían).
 */
@Component({
  selector: 'app-line-chart',
  standalone: true,
  imports: [DecimalPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="relative w-full" #caja>
      @if (series().length > 1) {
        <!-- Leyenda: con dos o más series la identidad nunca puede depender
             solo del color. El texto va en tokens de texto; el color lo
             lleva la muestra de al lado. -->
        <ul class="m-0 mb-2 flex list-none flex-wrap gap-x-4 gap-y-1 p-0 text-xs">
          @for (s of series(); track s.nombre; let i = $index) {
            <li class="flex items-center gap-1.5 text-text-secondary">
              <span
                class="h-0.5 w-4 shrink-0 rounded-full"
                [style.background]="color(i)"
                aria-hidden="true"
              ></span>
              {{ s.nombre }}
            </li>
          }
        </ul>
      }

      <svg
        [attr.width]="ancho()"
        [attr.height]="alto()"
        [attr.viewBox]="'0 0 ' + ancho() + ' ' + alto()"
        role="img"
        [attr.aria-label]="resumenAccesible()"
        (mousemove)="alMover($event)"
        (mouseleave)="activo.set(null)"
      >
        <!-- Rejilla: fina, sólida y recesiva. Nunca punteada. -->
        @for (t of ticks(); track t.valor) {
          <line
            [attr.x1]="IZQ"
            [attr.x2]="ancho() - DER"
            [attr.y1]="t.y"
            [attr.y2]="t.y"
            stroke="var(--chart-grid)"
            stroke-width="1"
          />
          <text
            [attr.x]="IZQ - 8"
            [attr.y]="t.y + 4"
            text-anchor="end"
            font-size="11"
            fill="var(--text-secondary)"
            style="font-variant-numeric: tabular-nums"
          >
            {{ t.etiqueta }}
          </text>
        }

        <!-- Etiquetas del eje X: se ralean para que nunca se solapen. -->
        @for (e of etiquetasX(); track e.i) {
          <text
            [attr.x]="e.x"
            [attr.y]="alto() - 8"
            [attr.text-anchor]="e.ancla"
            font-size="11"
            fill="var(--text-secondary)"
          >
            {{ e.texto }}
          </text>
        }

        @if (activo() !== null) {
          <line
            [attr.x1]="x(activo()!)"
            [attr.x2]="x(activo()!)"
            [attr.y1]="SUP"
            [attr.y2]="alto() - INF"
            stroke="var(--chart-grid)"
            stroke-width="1"
          />
        }

        @for (s of series(); track s.nombre; let i = $index) {
          @if (series().length === 1) {
            <path [attr.d]="areaDe(s)" [attr.fill]="color(i)" opacity="0.1" />
          }
          <path
            [attr.d]="lineaDe(s)"
            fill="none"
            [attr.stroke]="color(i)"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <!-- Punto final: 8px con anillo del color del fondo. -->
          @if (ultimo(s); as u) {
            <circle
              [attr.cx]="u.x"
              [attr.cy]="u.y"
              r="4"
              [attr.fill]="color(i)"
              stroke="var(--bg-surface)"
              stroke-width="2"
            />
          }
          @if (activo() !== null && valorEn(s, activo()!) !== null) {
            <circle
              [attr.cx]="x(activo()!)"
              [attr.cy]="y(valorEn(s, activo()!)!)"
              r="4"
              [attr.fill]="color(i)"
              stroke="var(--bg-surface)"
              stroke-width="2"
            />
          }
        }
      </svg>

      @if (activo() !== null) {
        <div
          class="tsi-panel pointer-events-none absolute z-10 min-w-32 p-2.5 text-xs shadow-lg"
          [style.left.px]="posTooltip()"
          [style.top.px]="0"
        >
          <p class="m-0 mb-1 font-semibold text-text-primary">{{ etiquetas()[activo()!] }}</p>
          @for (s of series(); track s.nombre; let i = $index) {
            <p class="m-0 flex items-center gap-1.5 text-text-secondary">
              <span
                class="h-0.5 w-3 shrink-0 rounded-full"
                [style.background]="color(i)"
                aria-hidden="true"
              ></span>
              {{ s.nombre }}:
              <span class="font-semibold tabular-nums text-text-primary">
                {{ valorEn(s, activo()!) === null ? 'sin dato' : (valorEn(s, activo()!) | number: '1.0-0') }}
              </span>
            </p>
          }
        </div>
      }
    </div>
  `,
})
export class LineChartComponent implements OnDestroy {
  readonly etiquetas = input.required<string[]>();
  readonly series = input.required<LineSeries[]>();
  readonly alto = input(200);

  @ViewChild('caja', { static: true }) private readonly caja!: ElementRef<HTMLDivElement>;

  protected readonly SUP = SUP;
  protected readonly DER = DER;
  protected readonly INF = INF;
  protected readonly IZQ = IZQ;

  protected readonly ancho = signal(640);
  protected readonly activo = signal<number | null>(null);

  private readonly ro = new ResizeObserver((entradas) => {
    const w = entradas[0]?.contentRect.width ?? 0;
    if (w > 0) {
      this.ancho.set(Math.round(w));
    }
  });

  constructor() {
    queueMicrotask(() => this.ro.observe(this.caja.nativeElement));
  }

  ngOnDestroy(): void {
    this.ro.disconnect();
  }

  protected color(i: number): string {
    return CAT[i % CAT.length];
  }

  /**
   * Tope del eje Y.
   *
   * Se redondea hacia arriba a un número limpio y además **a un valor par**.
   * Lo segundo no es estética: los cortes del eje están en 0, ½ y 1 del
   * tope, así que con un tope impar el corte central cae en un valor
   * fraccionario (3 → 1,5) y su etiqueta redondeada dice «2» sobre una
   * línea que está en 1,5. Una rejilla rotulada con un valor que no es el
   * suyo hace leer mal todos los puntos que se comparan contra ella.
   */
  private readonly tope = computed(() => {
    const todos = this.series().flatMap((s) => s.valores.filter((v): v is number => v !== null));
    const max = Math.max(0, ...todos);
    if (max <= 0) {
      return 2;
    }
    const magnitud = Math.pow(10, Math.floor(Math.log10(max)));
    const limpio = Math.ceil(max / magnitud) * magnitud;
    return limpio % 2 === 0 ? limpio : limpio + magnitud;
  });

  /**
   * Ticks del eje Y.
   *
   * Se descartan los que colapsan al mismo entero: con un tope de 1, los
   * tres cortes (0 · 0,5 · 1) se redondean a «0, 1, 1» y el eje muestra dos
   * veces el mismo número en alturas distintas, que se lee como un error de
   * datos. Con rangos pequeños el eje se queda con dos marcas, y está bien.
   */
  protected readonly ticks = computed(() => {
    const tope = this.tope();
    const alto = this.alto();
    const vistos = new Set<string>();
    return [0, 0.5, 1]
      .map((f) => ({
        valor: tope * f,
        etiqueta: String(Math.round(tope * f)),
        y: SUP + (1 - f) * (alto - SUP - INF),
      }))
      .filter((t) => {
        if (vistos.has(t.etiqueta)) {
          return false;
        }
        vistos.add(t.etiqueta);
        return true;
      });
  });

  protected x(i: number): number {
    const n = this.etiquetas().length;
    if (n <= 1) {
      return IZQ;
    }
    return IZQ + (i * (this.ancho() - IZQ - DER)) / (n - 1);
  }

  protected y(v: number): number {
    return SUP + (1 - v / this.tope()) * (this.alto() - SUP - INF);
  }

  protected valorEn(s: LineSeries, i: number): number | null {
    return s.valores[i] ?? null;
  }

  /** Traza la línea cortándola en cada hueco, en vez de puentearlo. */
  protected lineaDe(s: LineSeries): string {
    let d = '';
    let abierto = false;
    s.valores.forEach((v, i) => {
      if (v === null) {
        abierto = false;
        return;
      }
      d += `${abierto ? 'L' : 'M'}${this.x(i)} ${this.y(v)} `;
      abierto = true;
    });
    return d.trim();
  }

  protected areaDe(s: LineSeries): string {
    const base = this.y(0);
    const puntos = s.valores
      .map((v, i) => ({ v, i }))
      .filter((p): p is { v: number; i: number } => p.v !== null);
    if (!puntos.length) {
      return '';
    }
    const cuerpo = puntos.map((p) => `L${this.x(p.i)} ${this.y(p.v)}`).join(' ');
    return `M${this.x(puntos[0].i)} ${base} ${cuerpo} L${this.x(puntos[puntos.length - 1].i)} ${base} Z`;
  }

  protected ultimo(s: LineSeries): { x: number; y: number } | null {
    for (let i = s.valores.length - 1; i >= 0; i--) {
      const v = s.valores[i];
      if (v !== null && v !== undefined) {
        return { x: this.x(i), y: this.y(v) };
      }
    }
    return null;
  }

  /**
   * Cuántas fechas caben se MIDE, no se fija a un número redondo: el mismo
   * gráfico vive en un panel ancho y en media columna, y «6 etiquetas»
   * funciona en el primero y se amontona en la segunda.
   *
   * ⚠️ Tampoco se fija el ANCHO de una etiqueta: «2026-08-27» (10 caracteres)
   * y «2026-08-27 madrugada» (21) no ocupan lo mismo, y calibrar para la
   * corta hacía que la larga se solapara consigo misma en este mismo
   * informe (Acceso, franjas horarias). El ancho se deriva de la etiqueta
   * MÁS LARGA de la serie, a ~6px por carácter (11px monoespaciado
   * aproximado) más el mismo aire que antes.
   *
   * La última se rotula siempre —es la que el ojo busca— **salvo que caiga
   * encima de la anterior**. Una etiqueta pisada es peor que ausente: se
   * leen dos fechas a medias y ninguna entera. El resto de valores los
   * lleva el tooltip.
   */
  protected readonly etiquetasX = computed(() => {
    const et = this.etiquetas();
    if (!et.length) {
      return [];
    }
    const util = Math.max(1, this.ancho() - IZQ - DER);
    const largoMax = Math.max(...et.map((e) => e.length));
    // ×1.3: la primera etiqueta ancla a la izquierda (`start`) y crece solo
    // hacia la derecha, pero la siguiente ancla al centro (`middle`) y crece
    // hacia ambos lados — ese primer hueco necesita más que el espaciado
    // parejo del resto o la segunda etiqueta empieza antes de que la
    // primera termine. El margen parejo es más simple que calcular ese caso
    // aparte, y solo cuesta una etiqueta menos visible en el peor caso.
    const anchoEtiqueta = Math.max(68, largoMax * 6 * 1.3 + 12);
    const caben = Math.max(2, Math.floor(util / anchoEtiqueta));
    const salto = Math.max(1, Math.ceil(et.length / caben));
    // El primer y el último rótulo se anclan al borde en vez de centrarse:
    // centrados sobresalen del viewBox y el SVG los recorta a media fecha.
    const ultimoIdx = et.length - 1;
    const anclaDe = (i: number) => (i === 0 ? 'start' : i === ultimoIdx ? 'end' : 'middle');

    const regulares = et
      .map((texto, i) => ({ texto, i, x: this.x(i), ancla: anclaDe(i) }))
      .filter((e) => e.i % salto === 0);

    const ultimo = et.length - 1;
    const previo = regulares[regulares.length - 1];
    if (previo && previo.i !== ultimo) {
      // Misma medida que `anchoEtiqueta`: si no cabe entre las dos, se
      // sacrifica la marca regular, no la última.
      if (this.x(ultimo) - previo.x < anchoEtiqueta) {
        regulares.pop();
      }
      regulares.push({ texto: et[ultimo], i: ultimo, x: this.x(ultimo), ancla: 'end' });
    }
    return regulares;
  });

  protected alMover(evento: MouseEvent): void {
    const n = this.etiquetas().length;
    if (n === 0) {
      return;
    }
    const caja = (evento.currentTarget as SVGElement).getBoundingClientRect();
    const rel = evento.clientX - caja.left;
    const util = this.ancho() - IZQ - DER;
    const frac = util <= 0 ? 0 : (rel - IZQ) / util;
    this.activo.set(Math.max(0, Math.min(n - 1, Math.round(frac * (n - 1)))));
  }

  /** Mantiene el tooltip dentro de la caja en los dos extremos. */
  protected posTooltip(): number {
    const i = this.activo();
    if (i === null) {
      return 0;
    }
    return Math.max(0, Math.min(this.ancho() - 150, this.x(i) - 60));
  }

  protected resumenAccesible(): string {
    const n = this.etiquetas().length;
    const nombres = this.series().map((s) => s.nombre).join(' y ');
    return `Evolución de ${nombres} en ${n} puntos, de ${this.etiquetas()[0] ?? ''} a ${this.etiquetas()[n - 1] ?? ''}.`;
  }
}

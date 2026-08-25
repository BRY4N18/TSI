import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

const RADIO = 42;
const CIRCUNFERENCIA = 2 * Math.PI * RADIO;

/**
 * Anillo de progreso para una cifra héroe con meta (design-system.md §5).
 *
 * §5 pedía "bloques de KPIs con indicadores circulares de progreso" y §3.1 le
 * asignaba al cian el arco "en proceso", pero no existía ninguno en el código:
 * el documento describía una figura que nadie había construido. Este es el
 * primero, y a propósito **solo** para el caso que lo justifica — una métrica de
 * porcentaje que tiene meta declarada. Un anillo sin meta no añade nada sobre el
 * número, y §5 limita a 3-4 rings visibles: no es un adorno para repartir.
 *
 * Lectura del anillo, que es la de §5 sin reinterpretarla:
 * - **Arco navy (`accent-primary`)**: lo ya conseguido.
 * - **Arco cian (`accent-flow`)**: lo que falta para la meta — "en proceso".
 *   Desaparece cuando el valor ya alcanzó la meta.
 * - **Marca en la pista**: dónde está la meta.
 *
 * El cian aquí no comunica severidad —quedarse corto de un SLA no es "leve"—,
 * comunica recorrido pendiente. La severidad sigue siendo competencia exclusiva
 * de los tokens de alerta.
 *
 * La cifra va por `ng-content` en vez de por input: así la pantalla conserva su
 * propio elemento, su formato y su `data-testid`, y el anillo no se mete en cómo
 * se escribe el número.
 */
@Component({
  selector: 'app-kpi-ring',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="relative inline-grid shrink-0 place-items-center"
      [style.width.px]="tamano()"
      [style.height.px]="tamano()"
    >
      <svg
        class="absolute inset-0 h-full w-full -rotate-90"
        viewBox="0 0 100 100"
        role="img"
        [attr.aria-label]="etiquetaAccesible()"
      >
        <!-- Pista -->
        <circle
          cx="50"
          cy="50"
          [attr.r]="radio"
          fill="none"
          stroke="var(--border-default)"
          [attr.stroke-width]="grosor()"
        />

        <!-- Lo que falta para la meta: se dibuja primero, para que el arco
             conseguido quede por encima si hubiera solapamiento por redondeo. -->
        @if (arcoPendiente(); as p) {
          <circle
            cx="50"
            cy="50"
            [attr.r]="radio"
            fill="none"
            stroke="var(--accent-flow)"
            [attr.stroke-width]="grosor()"
            [attr.stroke-dasharray]="p.dasharray"
            [attr.stroke-dashoffset]="p.dashoffset"
          />
        }

        <!-- Lo conseguido -->
        @if (valorAcotado() > 0) {
          <circle
            cx="50"
            cy="50"
            [attr.r]="radio"
            fill="none"
            stroke="var(--accent-primary)"
            [attr.stroke-width]="grosor()"
            [attr.stroke-dasharray]="dasharrayLogrado()"
          />
        }

        <!-- Marca de la meta sobre la pista -->
        @if (marcaMeta(); as m) {
          <line
            [attr.x1]="m.x1"
            [attr.y1]="m.y1"
            [attr.x2]="m.x2"
            [attr.y2]="m.y2"
            stroke="var(--text-secondary)"
            stroke-width="2"
            stroke-linecap="round"
          />
        }
      </svg>

      <div class="relative grid place-items-center px-4 text-center">
        <ng-content />
      </div>
    </div>
  `,
})
export class KpiRingComponent {
  /** Porcentaje 0-100. `null` = sin dato: solo se pinta la pista. */
  readonly valor = input.required<number | null>();
  /** Meta declarada, si la hay. Sin meta no se pinta ni marca ni arco pendiente. */
  readonly meta = input<number | null>(null);
  /** Qué mide, para el lector de pantalla. */
  readonly etiqueta = input<string>('');
  readonly tamano = input(168);

  protected readonly radio = RADIO;

  protected readonly grosor = computed(() => (this.tamano() < 120 ? 10 : 8));

  protected readonly valorAcotado = computed(() => acotar(this.valor()));

  private readonly metaAcotada = computed(() => {
    const m = this.meta();
    return m === null || m === undefined ? null : acotar(m);
  });

  protected readonly dasharrayLogrado = computed(() => {
    const largo = (CIRCUNFERENCIA * this.valorAcotado()) / 100;
    return `${largo} ${CIRCUNFERENCIA}`;
  });

  /** Tramo entre el valor y la meta. Nulo si no hay meta o si ya se alcanzó. */
  protected readonly arcoPendiente = computed(() => {
    const meta = this.metaAcotada();
    const valor = this.valorAcotado();
    if (meta === null || this.valor() === null || valor >= meta) {
      return null;
    }
    const largo = (CIRCUNFERENCIA * (meta - valor)) / 100;
    return {
      dasharray: `${largo} ${CIRCUNFERENCIA}`,
      // Negativo: desplaza el inicio del trazo hasta donde acaba lo conseguido.
      dashoffset: -((CIRCUNFERENCIA * valor) / 100),
    };
  });

  protected readonly marcaMeta = computed(() => {
    const meta = this.metaAcotada();
    if (meta === null) {
      return null;
    }
    const angulo = (meta / 100) * 2 * Math.PI;
    const grosor = this.grosor();
    const interior = RADIO - grosor / 2 - 1;
    const exterior = RADIO + grosor / 2 + 1;
    return {
      x1: 50 + interior * Math.cos(angulo),
      y1: 50 + interior * Math.sin(angulo),
      x2: 50 + exterior * Math.cos(angulo),
      y2: 50 + exterior * Math.sin(angulo),
    };
  });

  protected readonly etiquetaAccesible = computed(() => {
    const v = this.valor();
    const base = this.etiqueta() || 'Progreso';
    if (v === null) {
      return `${base}: sin dato`;
    }
    const meta = this.meta();
    const metaTxt = meta === null || meta === undefined ? '' : `, meta ${meta} %`;
    return `${base}: ${v.toFixed(1)} %${metaTxt}`;
  });
}

function acotar(valor: number | null): number {
  if (valor === null || Number.isNaN(valor)) {
    return 0;
  }
  return Math.min(100, Math.max(0, valor));
}

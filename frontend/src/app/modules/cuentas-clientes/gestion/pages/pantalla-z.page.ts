import { DecimalPipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';

import { BarChartComponent, BarDatum } from '../../../../shared/ui/charts/bar-chart.component';
import { LineChartComponent, LineSeries } from '../../../../shared/ui/charts/line-chart.component';
import { MeterComponent } from '../../../../shared/ui/charts/meter.component';
import { PeriodoSelectorComponent } from '../../../emergencias/pages/shared/periodo-selector.component';
import { PeriodoParams } from '../../../emergencias/services/models/informes-tacticos.types';
import { definicionDe, informesDe } from '../definiciones/pantallas-gestion.definiciones';
import { cargaDeEnvelope } from '../models/estado-zona';
import {
  CargaInforme,
  DefinicionPantalla,
  EnvelopeInforme,
  PeriodoVista,
  num,
  texto,
} from '../models/informes-compuestos.types';
import { InformesCompuestosApiService } from '../services/informes-compuestos-api.service';
import { ApoyoPlegableComponent, BloqueApoyo } from './apoyo-plegable.component';
import { humanizar } from '../../../../shared/informes/informes-opciones';

const VACIA: CargaInforme = {
  estado: 'carga',
  error: null,
  data: [],
  meta: {},
};

@Component({
  selector: 'app-pantalla-z-cuentas',
  standalone: true,
  imports: [
    DecimalPipe,
    PeriodoSelectorComponent,
    ApoyoPlegableComponent,
    BarChartComponent,
    LineChartComponent,
    MeterComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './pantalla-z.page.html',
})
export class PantallaZPage {
  private readonly api = inject(InformesCompuestosApiService);
  private readonly route = inject(ActivatedRoute);
  private secuencia = 0;

  readonly definicion = signal<DefinicionPantalla | null>(null);
  readonly cargas = signal<Record<string, CargaInforme>>({});
  readonly periodo = signal<PeriodoVista | null>(null);

  readonly idPantalla = computed(() => this.definicion()?.id ?? null);

  readonly cargaHeroe = computed(() => this.cargaDe(this.definicion()?.heroe.informes[0]));
  readonly cargaVisual = computed(() => this.cargaDe(this.definicion()?.visual.informes[0]));
  readonly cargaLectura = computed(() => this.cargaDe(this.definicion()?.lectura?.informes[0]));

  readonly bloquesApoyo = computed<BloqueApoyo[]>(() => {
    const def = this.definicion();
    if (!def?.apoyo) {
      return [];
    }
    return def.apoyo.informes.map((informe) => ({
      titulo: etiquetaApoyo(informe),
      informe,
      carga: this.cargaDe(informe),
    }));
  });

  readonly notaCobertura = computed(
    () => this.cargaVisual().meta.nota_cobertura || this.cargaLectura().meta.nota_cobertura || '',
  );
  readonly notaCatalogo = computed(() => this.cargaVisual().meta.nota_catalogo || '');
  readonly notaSolape = computed(
    () => this.cargaHeroe().meta.nota_solape || this.cargaVisual().meta.nota_solape || '',
  );

  readonly filaOnboarding = computed(() => this.cargaHeroe().data[0]);

  readonly concurrenciaMaxima = computed(() =>
    this.maxDe(this.cargaHeroe().data, 'concurrencia_maxima'),
  );
  readonly sesionesIniciadas = computed(() =>
    this.cargaHeroe().data.reduce(
      (acc, fila) => acc + (num(fila['sesiones_iniciadas']) ?? 0),
      0,
    ),
  );

  readonly num = num;

  // ── Adaptadores a gráficos (design-system.md §5.1) ────────────────────

  /**
   * Ocupación de plan: consumo contra un tope, no una magnitud suelta.
   * Va como MEDIDOR — con barras, una cuenta al 120% del tope se leía igual
   * que una holgada, porque el 100% no era una referencia visible.
   */
  readonly medidoresCiclo = computed(() =>
    this.cargaVisual().data.map((f) => ({
      cuenta: texto(f['cuenta']) || 'Cuenta #' + texto(f['idcliente']),
      usados: num(f['usuarios_conocidos']) ?? 0,
      tope: num(f['tope_plan']),
      cobertura: this.pct(num(f['pct_cobertura_pertenencia'])),
    })),
  );

  /**
   * Embudo de incorporación: las etapas están ORDENADAS (una sucede a la
   * otra), así que la escala es ordinal y la rampa deja ver el orden en el
   * color. No se dibuja como cono: estrechar la figura distorsiona el área
   * y hace parecer mayores las caídas de las etapas anchas.
   */
  /** Orden real del onboarding (`EtapaOnboarding`) — el API no lo garantiza. */
  private static readonly ORDEN_ETAPA_ONBOARDING = ['cambio_password', 'perfil_corporativo', 'preferencias'];

  /**
   * Embudo de incorporación: ordinal, y por eso hace falta ordenar primero
   * por la etapa REAL — sin esto la rampa pinta el color según el orden en
   * que llegó la fila del API, no según a qué altura del embudo está.
   */
  readonly barrasIncorporacion = computed<BarDatum[]>(() =>
    [...this.cargaVisual().data]
      .sort(
        (a, b) =>
          PantallaZPage.ORDEN_ETAPA_ONBOARDING.indexOf(texto(a['etapa'])) -
          PantallaZPage.ORDEN_ETAPA_ONBOARDING.indexOf(texto(b['etapa'])),
      )
      .map((f) => ({
        etiqueta: humanizar(texto(f['etapa'])),
        valor: num(f['clientes_que_llegaron']),
        nota: num(f['clientes_que_llegaron']) === 0 ? '· cero' : undefined,
      })),
  );

  /** Concurrencia por franja: es una evolución en el tiempo, va en línea. */
  readonly etiquetasAcceso = computed(() =>
    this.cargaVisual().data.map((f) => `${texto(f['fecha'])} ${texto(f['franja'])}`),
  );

  readonly seriesAcceso = computed<LineSeries[]>(() => [
    {
      nombre: 'Concurrencia máxima',
      valores: this.cargaVisual().data.map((f) => num(f['concurrencia_maxima'])),
    },
  ]);
  readonly texto = texto;
  readonly humanizar = humanizar;

  constructor() {
    this.route.url.pipe(takeUntilDestroyed()).subscribe((segs) => {
      const id = segs[segs.length - 1]?.path ?? this.route.snapshot.url.at(-1)?.path ?? '';
      this.definicion.set(definicionDe(id));
      const periodo = this.periodo();
      if (periodo) {
        this.cargar(periodo);
      }
    });
  }

  onPeriodoChange(periodo: PeriodoParams): void {
    const vista: PeriodoVista = { desde: periodo.desde, hasta: periodo.hasta };
    this.periodo.set(vista);
    this.cargar(vista);
  }

  reintentar(informe: string): void {
    const periodo = this.periodo();
    if (!periodo) {
      return;
    }
    this.pedir(informe, periodo, this.secuencia);
  }

  pct(valor: number | null): string {
    if (valor === null) {
      return 'sin dato';
    }
    return `${(valor * 100).toFixed(1)} %`;
  }

  maxDe(filas: Record<string, unknown>[], campo: string): number {
    const vals = filas.map((f) => num(f[campo]) ?? 0);
    return Math.max(0, ...vals);
  }


  private cargaDe(informe: string | undefined): CargaInforme {
    if (!informe) {
      return VACIA;
    }
    return this.cargas()[informe] ?? VACIA;
  }

  private cargar(periodo: PeriodoVista): void {
    const def = this.definicion();
    if (!def) {
      return;
    }
    const seq = ++this.secuencia;
    for (const informe of informesDe(def)) {
      this.pedir(informe, periodo, seq);
    }
  }

  private pedir(informe: string, periodo: PeriodoVista, seq: number): void {
    this.patch(informe, { ...VACIA, estado: 'carga' });
    this.api.obtener(informe, periodo).subscribe({
      next: (env) => {
        if (seq !== this.secuencia) {
          return;
        }
        this.patch(informe, desdeEnvelope(env, informe));
      },
      error: (err: { error?: { detail?: string } }) => {
        if (seq !== this.secuencia) {
          return;
        }
        const detalle =
          typeof err?.error?.detail === 'string'
            ? err.error.detail
            : 'No se pudo cargar este informe.';
        this.patch(informe, {
          estado: 'error',
          error: detalle,
          data: [],
          meta: {},
        });
      },
    });
  }

  private patch(informe: string, carga: CargaInforme): void {
    this.cargas.update((actual) => ({ ...actual, [informe]: carga }));
  }
}

function desdeEnvelope(env: EnvelopeInforme, informe: string): CargaInforme {
  return cargaDeEnvelope(env, metricaNula(env, informe));
}

function metricaNula(env: EnvelopeInforme, informe: string): boolean {
  const data = cargaDeEnvelope(env).data;
  if (!data.length) {
    return false;
  }
  if (informe === 'usuarios-vs-tope') {
    return data.every((f) => num(f['pct_ocupacion']) === null && num(f['tope_plan']) === null);
  }
  if (informe === 'tiempo-onboarding') {
    return data.every((f) => num(f['dias_mediana']) === null);
  }
  return false;
}

function etiquetaApoyo(informe: string): string {
  switch (informe) {
    case 'antiguedad-media':
      return 'Antigüedad media';
    case 'concurrencia-sesiones':
      return 'Duración de sesión';
    default:
      return informe;
  }
}

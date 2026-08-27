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
import { PeriodoSelectorComponent } from '../../../emergencias/pages/shared/periodo-selector.component';
import { PeriodoParams } from '../../../emergencias/services/models/informes-tacticos.types';
import { definicionDe, informesDe } from '../definiciones/pantallas-gestion.definiciones';
import { cargaDeEnvelope } from '../models/estado-zona';
import {
  AlcanceVista,
  CargaInforme,
  DefinicionPantalla,
  EnvelopeInforme,
  PeriodoVista,
  num,
  texto,
} from '../models/informes-compuestos.types';
import { InformesCompuestosApiService } from '../services/informes-compuestos-api.service';
import { ApoyoPlegableComponent, BloqueApoyo } from './apoyo-plegable.component';
import { mensajeVacio } from '../../../../shared/informes/mensaje-vacio';

const VACIA: CargaInforme = {
  estado: 'carga',
  error: null,
  data: [],
  meta: {},
};

@Component({
  selector: 'app-pantalla-z-ventas',
  standalone: true,
  imports: [DecimalPipe, PeriodoSelectorComponent, ApoyoPlegableComponent, BarChartComponent],
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
  readonly cargaVisualSecundaria = computed(() =>
    this.cargaDe(this.definicion()?.visual.informes[1]),
  );
  readonly cargaLectura = computed(() => this.cargaDe(this.definicion()?.lectura.informes[0]));

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

  /** D4: el alcance sale del envelope, nunca del rol en cliente. */
  readonly alcance = computed<AlcanceVista | null>(() => {
    for (const carga of Object.values(this.cargas())) {
      const valor = carga.meta.acotado_a;
      if (valor === 'todos' || valor === 'propios') {
        return valor;
      }
    }
    return null;
  });

  /**
   * ⚠️ El vacío de un informe acotado **no es el vacío de un período sin datos**.
   * Ver `shared/informes/mensaje-vacio.ts`: decir «no hay datos en este período»
   * cuando la causa es el alcance manda al lector a ampliar el rango, y puede
   * ampliarlo indefinidamente sin que aparezca una fila.
   */
  readonly textoVacio = computed(() => mensajeVacio(this.alcance()));

  readonly totalTransiciones = computed(() =>
    this.cargaHeroe().data.reduce((acc, f) => acc + (num(f['transiciones']) ?? 0), 0),
  );

  readonly totalProspectosCanal = computed(() =>
    this.cargaHeroe().data.reduce((acc, f) => acc + (num(f['prospectos']) ?? 0), 0),
  );

  readonly intensidadPorEmpresa = computed(() => agregarPorEmpresa(this.cargaVisual().data));

  readonly notaIndicador = computed(() => {
    const meta = this.cargaLectura().meta;
    const deFiltro = meta.filtros?.['nota_indicador'];
    if (typeof deFiltro === 'string' && deFiltro) {
      return deFiltro;
    }
    const deFila = texto(this.cargaLectura().data[0]?.['nota_indicador']);
    return deFila;
  });

  readonly num = num;

  // ── Adaptadores a gráficos (design-system.md §5.1) ────────────────────

  /** Orden real del pipeline (pipeline-board.page.ts) — el API no lo garantiza. */
  private static readonly ORDEN_ETAPA = ['Nuevo', 'Contactado', 'Calificado', 'Propuesta', 'Negociación'];

  /**
   * Embudo comercial: las etapas van en orden, así que escala ordinal — pero
   * la rampa ordinal solo dice la verdad si las filas YA están en ese orden;
   * el API las devuelve en el orden que le resulta cómodo (aquí, alfabético),
   * no en el del pipeline. Sin este `sort` la rampa pintaría "Nuevo" con el
   * tono más oscuro y "Propuesta" con el más claro — el color contando lo
   * contrario del progreso real.
   *
   * Ojo con lo que mide la barra — no son prospectos, es la MEDIANA DE
   * TIEMPO en cada etapa; el conteo de abiertos y medidos va como nota.
   */
  readonly barrasEmbudo = computed<BarDatum[]>(() =>
    [...this.cargaVisual().data]
      .sort(
        (a, b) =>
          PantallaZPage.ORDEN_ETAPA.indexOf(texto(a['etapa'])) -
          PantallaZPage.ORDEN_ETAPA.indexOf(texto(b['etapa'])),
      )
      .map((f) => ({
        etiqueta: texto(f['etapa']),
        valor: num(f['segundos_mediana']),
        valorTexto: this.formatSegundos(num(f['segundos_mediana'])),
        nota: `· ${num(f['abiertos']) ?? 0} abiertos de ${num(f['prospectos_medidos']) ?? 0}`,
      })),
  );

  /** Secciones visitadas: nominales. */
  readonly barrasSecciones = computed<BarDatum[]>(() =>
    this.cargaVisualSecundaria().data.map((f) => ({
      etiqueta: texto(f['seccion']),
      valor: num(f['visitas']),
    })),
  );
  readonly texto = texto;

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

  etiquetaGrupo(grupo: string): string {
    if (grupo === 'con_demo') {
      return 'Con demo';
    }
    if (grupo === 'sin_demo') {
      return 'Sin demo';
    }
    return grupo;
  }


  formatSegundos(valor: number | null): string {
    if (valor === null) {
      return 'sin dato';
    }
    if (valor >= 86400) {
      return `${(valor / 86400).toFixed(1)} días`;
    }
    if (valor >= 3600) {
      return `${(valor / 3600).toFixed(1)} h`;
    }
    return `${Math.round(valor)} s`;
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
  return cargaDeEnvelope(env, metricaNula(Array.isArray(env.data) ? env.data : [], informe));
}

function metricaNula(data: Record<string, unknown>[], informe: string): boolean {
  if (!data.length) {
    return false;
  }
  if (informe === 'conversion-por-canal' || informe === 'efectividad-nutricion') {
    return data.every((f) => num(f['pct_conversion']) === null);
  }
  return false;
}

function agregarPorEmpresa(filas: Record<string, unknown>[]): {
  empresa: string;
  eventos: number;
  secciones_distintas: number;
}[] {
  const mapa = new Map<string, { empresa: string; eventos: number; secciones_distintas: number }>();
  for (const fila of filas) {
    const empresa = texto(fila['empresa']) || 'Sin empresa';
    const actual = mapa.get(empresa) ?? { empresa, eventos: 0, secciones_distintas: 0 };
    actual.eventos += num(fila['eventos']) ?? 0;
    actual.secciones_distintas = Math.max(
      actual.secciones_distintas,
      num(fila['secciones_distintas']) ?? 0,
    );
    mapa.set(empresa, actual);
  }
  return [...mapa.values()];
}

function etiquetaApoyo(informe: string): string {
  switch (informe) {
    case 'carga-por-ejecutivo':
      return 'Carga por ejecutivo';
    case 'pipeline-ponderado':
      return 'Pipeline ponderado';
    case 'reglas-disparo':
      return 'Reglas de disparo';
    default:
      return informe;
  }
}

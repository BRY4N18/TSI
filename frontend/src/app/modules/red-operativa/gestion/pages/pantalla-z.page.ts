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
import {
  TEXTO_CONVENCION_DIAS,
  TEXTO_CONVENCION_UMBRAL,
  TEXTO_GRANO,
  definicionDe,
  informesDe,
} from '../definiciones/pantallas-gestion.definiciones';
import { cargaDeEnvelope } from '../models/estado-zona';
import {
  CargaInforme,
  DefinicionPantalla,
  EnvelopeInforme,
  PeriodoVista,
  esVerdadero,
  num,
  texto,
} from '../models/informes-compuestos.types';
import { InformesCompuestosApiService } from '../services/informes-compuestos-api.service';
import { ApoyoPlegableComponent, BloqueApoyo } from './apoyo-plegable.component';

const VACIA: CargaInforme = {
  estado: 'carga',
  error: null,
  data: [],
  meta: {},
};

@Component({
  selector: 'app-pantalla-z-red',
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

  readonly criticos = computed(() => agregarCriticos(this.cargaHeroe()));
  readonly mercados = computed(() => agregarMercados(this.cargaHeroe().data));
  readonly tasa = computed(() => agregarTasa(this.cargaHeroe().data));
  readonly notaUmbral = computed(
    () =>
      this.cargaHeroe().meta.nota_umbral ||
      this.cargaLectura().meta.nota_umbral ||
      TEXTO_CONVENCION_UMBRAL,
  );
  readonly notaObjetivo = computed(
    () => this.cargaVisual().meta.nota_objetivo || TEXTO_CONVENCION_DIAS,
  );
  readonly notaGrano = computed(
    () => this.definicion()?.lecturaTexto || this.cargaHeroe().meta.nota_grano || TEXTO_GRANO,
  );
  readonly notaRiesgo = computed(
    () => this.cargaLectura().meta.nota_umbral || this.cargaLectura().meta.nota || '',
  );

  readonly num = num;

  // ── Adaptadores a gráficos (design-system.md §5.1) ────────────────────

  /** Estados de flota: nominales, un solo color. */
  readonly barrasFlota = computed<BarDatum[]>(() =>
    this.cargaVisual().data.map((f) => ({
      etiqueta: texto(f['estado']) || 'Desconocido',
      valor: this.cuentaEstado(f),
    })),
  );

  /**
   * Motivos de rechazo: todos son el mismo tipo de hecho (un rechazo), así
   * que no se tiñe cada barra de un tono distinto. El que la pantalla trate
   * de rechazos ya lo dice el título, no hace falta repetirlo en el color.
   */
  readonly barrasValidacion = computed<BarDatum[]>(() =>
    this.cargaVisual().data.map((f) => ({
      etiqueta: texto(f['motivo']),
      valor: num(f['rechazos']),
    })),
  );
  readonly texto = texto;
  readonly esVerdadero = esVerdadero;

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


  cuentaEstado(fila: Record<string, unknown>): number {
    return num(fila['unidades']) ?? num(fila['transiciones']) ?? 0;
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
  if (informe === 'tasa-aprobacion-primer-intento') {
    return data.every((f) => num(f['pct_aprobacion_primer_intento']) === null);
  }
  return false;
}

function agregarCriticos(carga: CargaInforme): {
  total: number;
  sinAlternativas: number;
  umbral: number | null;
  filas: Record<string, unknown>[];
} {
  const filas = carga.data;
  const umbral =
    num(filas[0]?.['umbral_aplicado']) ?? num(carga.meta.filtros?.['umbral_unidades']);
  return {
    total: filas.length,
    sinAlternativas: filas.filter((f) => esVerdadero(f['sin_alternativas'])).length,
    umbral,
    filas,
  };
}

function agregarMercados(filas: Record<string, unknown>[]): {
  produccion: number;
  total: number;
  filas: Record<string, unknown>[];
} {
  const produccion = filas
    .filter((f) => texto(f['estado_ciclo_vida']) === 'Producción')
    .reduce((acc, f) => acc + (num(f['regiones']) ?? 0), 0);
  const total = filas.reduce((acc, f) => acc + (num(f['regiones']) ?? 0), 0);
  return { produccion, total, filas };
}

function agregarTasa(filas: Record<string, unknown>[]): {
  validadas: number;
  aprobadas: number;
  pct: number | null;
} {
  const validadas = filas.reduce((acc, f) => acc + (num(f['regiones_validadas']) ?? 0), 0);
  const aprobadas = filas.reduce((acc, f) => acc + (num(f['aprobadas_al_primero']) ?? 0), 0);
  const pct =
    validadas === 0
      ? filas.length === 1
        ? num(filas[0]['pct_aprobacion_primer_intento'])
        : null
      : filas.length === 1
        ? (num(filas[0]['pct_aprobacion_primer_intento']) ?? aprobadas / validadas)
        : aprobadas / validadas;
  return { validadas, aprobadas, pct };
}

function etiquetaApoyo(informe: string): string {
  switch (informe) {
    case 'cobertura-flota-por-region':
      return 'Cobertura por región';
    case 'pendientes-primer-acceso':
      return 'Pendientes de primer acceso';
    case 'rendimiento-proveedor':
      return 'Rendimiento por proveedor';
    case 'rotacion-flota':
      return 'Rotación de flota';
    case 'bajas-forzadas':
      return 'Bajas forzadas';
    case 'casos-activos-al-despublicar':
      return 'Casos al despublicar';
    case 'tiempo-perdida-a-despublicacion':
      return 'Pérdida de cobertura → despublicación';
    default:
      return informe;
  }
}

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

import { PeriodoSelectorComponent } from '../../pages/shared/periodo-selector.component';
import { PeriodoParams } from '../../services/models/informes-tacticos.types';
import {
  definicionDe,
  informesDe,
  TEXTO_NO_SLA,
} from '../definiciones/pantallas-gestion.definiciones';
import { estadoDeZona } from '../models/estado-zona';
import {
  CargaInforme,
  DefinicionPantalla,
  EnvelopeInforme,
  MetaInforme,
  PeriodoVista,
  num,
  texto,
} from '../models/informes-compuestos.types';
import { esSinCapacidad } from '../models/sin-capacidad';
import { InformesCompuestosApiService } from '../services/informes-compuestos-api.service';
import { ApoyoPlegableComponent, BloqueApoyo } from './apoyo-plegable.component';

const VACIA: CargaInforme = {
  estado: 'carga',
  error: null,
  data: [],
  meta: {},
};

@Component({
  selector: 'app-pantalla-z',
  standalone: true,
  imports: [DecimalPipe, PeriodoSelectorComponent, ApoyoPlegableComponent],
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
  readonly camposComprobados = computed(() => this.definicion()?.camposComprobados ?? []);

  readonly cargaHeroe = computed(() => this.cargaDe(this.definicion()?.heroe.informes[0]));
  readonly cargaVisual = computed(() => this.cargaDe(this.definicion()?.visual.informes[0]));
  readonly cargaLectura = computed(() => this.cargaDe(this.definicion()?.lectura.informes[0]));
  readonly cargaLecturaB = computed(() => this.cargaDe(this.definicion()?.lectura.informes[1]));

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

  readonly completitud = computed(() => agregarCompletitud(this.cargaHeroe().data));
  readonly primerIntento = computed(() => agregarPrimerIntento(this.cargaHeroe().data));
  readonly cartera = computed(() => agregarCartera(this.cargaHeroe().data));
  readonly cobertura = computed(() => agregarCobertura(this.cargaVisual().data));
  readonly notaNoSla = computed(
    () => this.cargaVisual().meta.nota_referencia || TEXTO_NO_SLA,
  );
  readonly ratios = computed(() => this.cargas()['ratio-demanda-capacidad'] ?? VACIA);

  readonly esSinCapacidad = esSinCapacidad;
  readonly num = num;
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

  completitudBaja(): boolean {
    const pct = this.completitud().pct;
    return pct !== null && pct < 1;
  }

  primerIntentoCumple(): boolean {
    const pct = this.primerIntento().pct;
    return pct !== null && pct >= 0.9;
  }

  primerIntentoBajo(): boolean {
    const pct = this.primerIntento().pct;
    return pct !== null && pct < 0.9;
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
  const data = Array.isArray(env.data) ? env.data : [];
  const meta: MetaInforme = env.meta ?? {};
  return {
    estado: estadoDeZona({
      loading: false,
      error: null,
      data,
      metricaAusente: metricaNula(data, informe),
    }),
    error: null,
    data,
    meta,
  };
}

function metricaNula(data: Record<string, unknown>[], informe: string): boolean {
  if (!data.length) {
    return false;
  }
  if (informe === 'completitud-campos-criticos') {
    return data.every((f) => num(f['pct_completitud']) === null);
  }
  if (informe === 'primer-intento') {
    return data.every((f) => num(f['pct_primer_intento']) === null);
  }
  if (informe === 'desviacion-llegada') {
    return data.every((f) => num(f['desviacion_mediana']) === null);
  }
  return false;
}

function agregarCompletitud(filas: Record<string, unknown>[]): {
  casos: number;
  completos: number;
  incompletos: number;
  pct: number | null;
} {
  const casos = filas.reduce((acc, f) => acc + (num(f['casos']) ?? 0), 0);
  const completos = filas.reduce((acc, f) => acc + (num(f['completos']) ?? 0), 0);
  const pct =
    casos === 0
      ? null
      : filas.length === 1
        ? num(filas[0]['pct_completitud'])
        : completos / casos;
  return { casos, completos, incompletos: Math.max(casos - completos, 0), pct };
}

function agregarPrimerIntento(filas: Record<string, unknown>[]): {
  casos: number;
  resueltos: number;
  pct: number | null;
} {
  const casos = filas.reduce((acc, f) => acc + (num(f['casos']) ?? 0), 0);
  const resueltos = filas.reduce(
    (acc, f) => acc + (num(f['resueltos_primer_intento']) ?? 0),
    0,
  );
  const pct =
    casos === 0
      ? null
      : filas.length === 1
        ? num(filas[0]['pct_primer_intento'])
        : resueltos / casos;
  return { casos, resueltos, pct };
}

function agregarCartera(filas: Record<string, unknown>[]): {
  total: number;
  tramos: { tramo: string; casos: number }[];
} {
  const tramos = filas.map((f) => ({
    tramo: texto(f['tramo_dias']) || '0',
    casos: num(f['casos_abiertos']) ?? 0,
  }));
  return { total: tramos.reduce((acc, t) => acc + t.casos, 0), tramos };
}

function agregarCobertura(filas: Record<string, unknown>[]): {
  soloFoto: number;
  soloNota: number;
  fotoYNota: number;
  sinEvidencia: number;
  casos: number;
  pct: number | null;
} {
  const soloFoto = filas.reduce((acc, f) => acc + (num(f['solo_foto']) ?? 0), 0);
  const soloNota = filas.reduce((acc, f) => acc + (num(f['solo_nota']) ?? 0), 0);
  const fotoYNota = filas.reduce((acc, f) => acc + (num(f['foto_y_nota']) ?? 0), 0);
  const sinEvidencia = filas.reduce((acc, f) => acc + (num(f['sin_evidencia']) ?? 0), 0);
  const casos = filas.reduce((acc, f) => acc + (num(f['casos']) ?? 0), 0);
  const conAlguna = soloFoto + soloNota + fotoYNota;
  return {
    soloFoto,
    soloNota,
    fotoYNota,
    sinEvidencia,
    casos,
    pct: casos === 0 ? null : conAlguna / casos,
  };
}

function etiquetaApoyo(informe: string): string {
  switch (informe) {
    case 'latencia-sincronizacion':
      return 'Latencia de sincronización';
    case 'completitud-enriquecimiento':
      return 'Enriquecimiento';
    case 'volumen-evidencia-por-unidad':
      return 'Volumen por unidad';
    case 'escaladas-severidad':
      return 'Escaladas de severidad';
    default:
      return informe;
  }
}

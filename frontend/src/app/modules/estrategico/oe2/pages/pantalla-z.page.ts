import { DecimalPipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { BarChartComponent, BarDatum } from '../../../../shared/ui/charts/bar-chart.component';
import { PeriodoSelectorComponent } from '../../../emergencias/pages/shared/periodo-selector.component';
import { PeriodoParams } from '../../../emergencias/services/models/informes-tacticos.types';
import { definicionDe, informesDe } from '../definiciones/pantallas-oe2.definiciones';
import { cargaDeEnvelope } from '../models/estado-zona';
import {
  CargaInforme,
  Comparacion,
  DefinicionPantalla,
  EnvelopeInforme,
  Granularidad,
  PeriodoVista,
  num,
  texto,
} from '../models/informes-oe2.types';
import { InformesOe2ApiService } from '../services/informes-oe2-api.service';
import { ApoyoPlegableComponent, BloqueApoyo } from './apoyo-plegable.component';

const VACIA: CargaInforme = {
  estado: 'carga',
  error: null,
  data: [],
  meta: {},
};

@Component({
  selector: 'app-pantalla-z-oe2',
  standalone: true,
  imports: [DecimalPipe, FormsModule, PeriodoSelectorComponent, ApoyoPlegableComponent, BarChartComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './pantalla-z.page.html',
})
export class PantallaZPage {
  private readonly api = inject(InformesOe2ApiService);
  private readonly route = inject(ActivatedRoute);
  private secuencia = 0;

  readonly definicion = signal<DefinicionPantalla | null>(null);
  readonly cargas = signal<Record<string, CargaInforme>>({});
  readonly periodo = signal<PeriodoVista | null>(null);
  granularidad: Granularidad = 'mes';
  comparacion: Comparacion = 'ninguna';

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

  readonly noTarificables = computed(() =>
    this.cargaHeroe().data.filter((f) => num(f['no_tarificable']) === 1),
  );

  readonly importeTotal = computed(() =>
    this.cargaHeroe().data.reduce((acc, f) => acc + (num(f['importe_facturable']) ?? 0), 0),
  );

  readonly num = num;

  // ── Adaptadores a gráficos (design-system.md §5.1) ────────────────────

  /** Llamadas por clase HTTP: categorías nominales, un solo color. */
  readonly barrasUso = computed<BarDatum[]>(() =>
    this.cargaVisual().data.map((f) => ({
      etiqueta: texto(f['clase_http']),
      valor: num(f['llamadas']),
      nota: `· ${this.pct(num(f['pct']))}`,
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
    this.emitirVista(periodo.desde, periodo.hasta);
  }

  onFiltrosChange(): void {
    const actual = this.periodo();
    if (!actual) {
      return;
    }
    this.emitirVista(actual.desde, actual.hasta);
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


  private emitirVista(desde: string, hasta: string): void {
    const vista: PeriodoVista = {
      desde,
      hasta,
      granularidad: this.granularidad,
      comparacion: this.comparacion,
    };
    this.periodo.set(vista);
    this.cargar(vista);
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
        this.patch(informe, { estado: 'error', error: detalle, data: [], meta: {} });
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
  if (informe === 'latencia-por-endpoint') {
    return data.every((f) => num(f['latencia_p95_ms']) === null);
  }
  return false;
}

function etiquetaApoyo(informe: string): string {
  switch (informe) {
    case 'latencia-por-endpoint':
      return 'Latencia p95, media y muestras';
    case 'participacion-ingresos-api':
      return 'Participación de ingresos';
    case 'mrr-por-linea':
      return 'MRR por línea';
    default:
      return informe;
  }
}

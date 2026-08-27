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

const VACIA: CargaInforme = {
  estado: 'carga',
  error: null,
  data: [],
  meta: {},
};

@Component({
  selector: 'app-pantalla-z-suscripciones',
  standalone: true,
  imports: [
    DecimalPipe,
    PeriodoSelectorComponent,
    ApoyoPlegableComponent,
    BarChartComponent,
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

  /** D8: el mes sale del envelope, nunca se deriva del rango pedido. */
  readonly mesDeclarado = computed(() => {
    const directa = this.cargaHeroe().meta;
    if (directa.mes || directa.nota_periodo) {
      return { mes: directa.mes ?? '', nota: directa.nota_periodo ?? '' };
    }
    for (const carga of Object.values(this.cargas())) {
      if (carga.meta.mes || carga.meta.nota_periodo) {
        return { mes: carga.meta.mes ?? '', nota: carga.meta.nota_periodo ?? '' };
      }
    }
    return null;
  });

  readonly filaHeroe = computed(() => this.cargaHeroe().data[0] ?? {});
  readonly notaDimension = computed(() => {
    const fila = this.cargaVisual().data.find((f) => texto(f['nota_dimension_pendiente']));
    return texto(fila?.['nota_dimension_pendiente'] || this.cargaVisual().meta.nota);
  });

  readonly num = num;
  readonly texto = texto;

  // ── Adaptadores a gráficos (design-system.md §5.1) ────────────────────

  /** Ingreso por plan: categorías nominales, un solo color. */
  readonly barrasCobro = computed<BarDatum[]>(() =>
    this.cargaVisual().data.map((f) => {
      const tipo = texto(f['tipo_cliente']);
      return {
        etiqueta: (texto(f['plan']) || 'Plan') + (tipo ? ` · ${tipo}` : ''),
        valor: num(f['ingreso_neto']),
        nota: texto(f['moneda']),
      };
    }),
  );

  /**
   * Movimientos de plan: el delta de ingreso lleva SIGNO.
   *
   * ⚠️ Antes se dibujaba con `Math.abs()`, así que un downgrade de −200 y un
   * upgrade de +200 salían con la misma barra: la única información que
   * distingue un movimiento del contrario se perdía justo en el gráfico que
   * existe para compararlos. En escala divergente el brazo sale del centro
   * hacia un lado u otro, y el signo se ve antes de leer la cifra.
   */
  readonly barrasMovimientos = computed<BarDatum[]>(() =>
    this.cargaVisual().data.map((f) => ({
      etiqueta: texto(f['tipo_movimiento']),
      valor: num(f['delta_ingreso_total']),
      nota: `· ${num(f['solicitudes']) ?? 0} solicitudes`,
    })),
  );

  /**
   * Utilización de límites: cada plan aporta DOS medidores (unidades y
   * usuarios), porque son dos cupos independientes y uno puede estar
   * excedido con el otro holgado.
   */
  readonly medidoresCatalogo = computed(() =>
    this.cargaVisual().data.map((f) => ({
      plan: texto(f['plan']) || 'Plan',
      unidadesUsadas: num(f['unidades_usadas']) ?? 0,
      unidadesLimite: num(f['unidades_limite']),
      usuariosUsados: num(f['usuarios_usados']) ?? 0,
      usuariosLimite: num(f['usuarios_limite']),
    })),
  );

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
  if (informe === 'tasa-renovacion') {
    return data.every((f) => num(f['pct_renovacion']) === null);
  }
  if (informe === 'nrr') {
    return data.every((f) => num(f['nrr']) === null);
  }
  return false;
}

function etiquetaApoyo(informe: string): string {
  switch (informe) {
    case 'cobro-primer-intento':
      return 'Cobro al primer intento';
    case 'efectividad-dunning':
      return 'Efectividad del dunning';
    case 'clientes-sin-metodo-pago':
      return 'Clientes sin método';
    case 'suspension-reactivacion':
      return 'Suspensión y reactivación';
    default:
      return informe;
  }
}

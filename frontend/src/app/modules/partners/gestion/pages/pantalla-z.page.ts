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
  selector: 'app-pantalla-z-partners',
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

  readonly notaMuestras = computed(() => {
    const directa = this.cargaHeroe().meta.nota_muestras;
    if (directa) {
      return directa;
    }
    for (const carga of Object.values(this.cargas())) {
      if (carga.meta.nota_muestras) {
        return carga.meta.nota_muestras;
      }
    }
    return '';
  });

  readonly filaIntegracion = computed(() => this.cargaHeroe().data[0]);

  readonly num = num;

  // ── Adaptadores a gráficos (design-system.md §5.1) ────────────────────
  // Clases de resultado, canales: categorías nominales -> un solo color,
  // porque ordenarlas de otra forma no cambiaría lo que significan.

  readonly barrasConsumo = computed<BarDatum[]>(() =>
    this.cargaVisual().data.map((f) => ({
      etiqueta: `${texto(f['clase_resultado'])} · ${texto(f['codigo_http'])}`,
      valor: num(f['pct']) === null ? null : (num(f['pct']) as number) * 100,
      nota: `· ${num(f['llamadas']) ?? 0} llamadas`,
    })),
  );

  readonly barrasEntrega = computed<BarDatum[]>(() =>
    this.cargaVisual().data.map((f) => ({
      etiqueta: this.etiquetaCanal(f),
      valor: num(f['expedientes']),
    })),
  );
  readonly texto = texto;

  /**
   * Etiqueta de una fila de «expedientes por canal».
   *
   * ⚠️ **`(portal)` no es el nombre de un cliente, es un centinela.** El hecho
   * de accidentes no trae `idcliente`, así que los expedientes del portal no se
   * pueden atribuir a nadie y la consulta los agrupa bajo ese literal. Pintado
   * junto al canal salía «portal · (portal)»: el mismo dato dos veces, y con
   * pinta de nombre propio.
   *
   * ⚠️ En el canal `api`, `cliente` llega como el **identificador en texto**
   * (`toString(idcliente)` en la consulta), no como razón social. Mientras
   * `hecho_llamada_api` esté vacío no se ve, pero en cuanto haya datos esta
   * lista mostrará un número donde se espera un nombre. Se marca como tal para
   * que no se lea como una empresa llamada «920001».
   */
  etiquetaCanal(fila: Record<string, unknown>): string {
    const canal = texto(fila['canal']);
    const cliente = texto(fila['cliente']);
    if (!cliente || cliente === '(portal)') {
      return canal || '—';
    }
    return /^\d+$/.test(cliente) ? `${canal} · cliente #${cliente}` : `${canal} · ${cliente}`;
  }

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


  noFiable(fila: Record<string, unknown>): boolean {
    return num(fila['percentil_fiable']) === 0;
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
  if (informe === 'clientes-integracion-activa') {
    return data.every((f) => num(f['pct']) === null);
  }
  if (informe === 'latencia-p95') {
    return data.every((f) => num(f['latencia_p95_ms']) === null);
  }
  return false;
}

function etiquetaApoyo(informe: string): string {
  switch (informe) {
    case 'metricas-consumo':
      return 'Métricas por partner';
    case 'reporte-mensual-consumo':
      return 'Reporte mensual';
    case 'consumo-por-endpoint':
      return 'Consumo por endpoint';
    case 'participacion-ingresos-api':
      return 'Participación de ingresos';
    case 'tasa-rechazo-produccion':
      return 'Rechazo de producción';
    default:
      return informe;
  }
}

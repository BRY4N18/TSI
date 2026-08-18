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

import { PeriodoSelectorComponent } from '../../../emergencias/pages/shared/periodo-selector.component';
import { PeriodoParams } from '../../../emergencias/services/models/informes-tacticos.types';
import { definicionDe, informesDe } from '../definiciones/pantallas-gestion.definiciones';
import { cargaDeEnvelope } from '../models/estado-zona';
import {
  AgruparCola,
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

const VACIA: CargaInforme = {
  estado: 'carga',
  error: null,
  data: [],
  declaraciones: [],
  meta: {},
};

const AGRUPAR: AgruparCola[] = ['estado', 'prioridad', 'tipo', 'agente'];

@Component({
  selector: 'app-pantalla-z-soporte',
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
  readonly agruparPor = signal<AgruparCola>('estado');
  readonly opcionesAgrupar = AGRUPAR;

  readonly idPantalla = computed(() => this.definicion()?.id ?? null);

  readonly cargaHeroe = computed(() => this.cargaDe(this.definicion()?.heroe.informes[0]));
  readonly cargaVisual = computed(() => this.cargaDe(this.definicion()?.visual.informes[0]));
  readonly cargaLectura = computed(() => this.cargaDe(this.definicion()?.lectura.informes[0]));

  readonly filaHeroe = computed(() => ultimaFila(this.cargaHeroe().data));
  readonly filaCarga = computed(() => ultimaFila(this.cargaHeroe().data));

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

  onAgrupar(valor: string): void {
    if (!AGRUPAR.includes(valor as AgruparCola)) {
      return;
    }
    this.agruparPor.set(valor as AgruparCola);
    const periodo = this.periodo();
    if (!periodo) {
      return;
    }
    this.pedir('tablero-cola', periodo, this.secuencia);
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
    return `${valor.toFixed(1)} %`;
  }

  saldo(fila: Record<string, unknown> | undefined): number | null {
    if (!fila) {
      return null;
    }
    const creados = num(fila['creados']);
    const resueltos = num(fila['resueltos']);
    if (creados === null || resueltos === null) {
      return null;
    }
    return creados - resueltos;
  }

  maxDe(filas: Record<string, unknown>[], campo: string): number {
    const vals = filas.map((f) => num(f[campo]) ?? 0);
    return Math.max(1, ...vals);
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

  motivo(fila: Record<string, unknown> | undefined, clave: string): number {
    const nido = fila?.['sin_compromiso_por_motivo'];
    if (!nido || typeof nido !== 'object') {
      return 0;
    }
    return num((nido as Record<string, unknown>)[clave]) ?? 0;
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
    const extra =
      informe === 'tablero-cola' ? { agrupar_por: this.agruparPor() } : undefined;
    this.api.obtener(informe, periodo, extra).subscribe({
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
          declaraciones: [],
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
  if (informe === 'cumplimiento-sla' || informe === 'cumplimiento-sla-por-plan') {
    const fila = ultimaFila(data);
    return fila ? num(fila['pct_cumplimiento']) === null : false;
  }
  if (informe === 'escalado-automatico') {
    return data.every((f) => num(f['pct_escalado_automatico']) === null);
  }
  if (informe === 'rendimiento-agentes') {
    return data.every((f) => num(f['media_resolucion_s']) === null);
  }
  return false;
}

function ultimaFila(
  filas: Record<string, unknown>[],
): Record<string, unknown> | undefined {
  if (!filas.length) {
    return undefined;
  }
  return filas[filas.length - 1];
}

function etiquetaApoyo(informe: string): string {
  if (informe === 'tickets-por-servicio') {
    return 'Tickets por servicio';
  }
  return informe;
}

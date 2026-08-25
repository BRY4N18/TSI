import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnInit,
  Output,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';

import { CatalogoItem } from '../../accidentes/services/models/accidente.types';
import { UbicacionCatalogoApiService } from '../../accidentes/services/ubicacion-catalogo-api.service';

/**
 * Preferencias operativas del cliente: las cuatro dimensiones del SRS §3.2.2 y
 * §3.2.3 — umbrales de alerta, canales de notificación, zonas geográficas de
 * interés y destinatarios de reportes.
 *
 * Vive aquí y no en cada pantalla porque se piden en dos sitios: la
 * incorporación guiada y la gestión de cuenta. Antes cada una capturaba un
 * subconjunto distinto y las tres dimensiones que faltaban no se podían
 * rellenar desde ninguna parte, pese a que la tabla y el endpoint ya las
 * soportaban. `zonas_geograficas` en particular es lo que decide qué
 * expedientes ve el cliente y qué puede consultar un partner: vacío significa
 * cero resultados, no «todo».
 */
export interface PreferenciasOperativas {
  /** Minutos máximos de llegada de la unidad antes de avisar al cliente. */
  tiempoLlegadaMaxMin: number | null;
  canales: 'email' | 'sms' | 'ambos';
  telefonoSms: string;
  /** Condados de interés, con su nombre para poder mostrarlos sin ids. */
  condados: CatalogoItem[];
  /** Correos separados por coma. */
  destinatarios: string;
}

/** Forma en que viajan las preferencias hacia el API. */
export interface PreferenciasSerializadas {
  umbrales_alerta: string;
  canales_notificacion: 'email' | 'sms' | 'ambos';
  telefono_sms: string;
  zonas_geograficas: string;
  destinatarios_reportes: string;
}

export function serializarPreferencias(v: PreferenciasOperativas): PreferenciasSerializadas {
  return {
    umbrales_alerta: JSON.stringify(
      v.tiempoLlegadaMaxMin == null ? {} : { tiempo_llegada_max_min: v.tiempoLlegadaMaxMin },
    ),
    canales_notificacion: v.canales,
    telefono_sms: v.telefonoSms ?? '',
    zonas_geograficas: JSON.stringify(v.condados.map((c) => c.id)),
    destinatarios_reportes: v.destinatarios ?? '',
  };
}

function parsearJson(raw: unknown): unknown {
  if (typeof raw !== 'string' || !raw.trim() || raw === 'null') {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

/** Lo que devuelve el API: los mismos campos, con nulos donde no hay valor. */
export type PreferenciasCrudas = {
  [K in keyof PreferenciasSerializadas]?: PreferenciasSerializadas[K] | null;
};

/** Reconstruye el formulario desde lo que devuelve el API. */
export function deserializarPreferencias(
  crudo: PreferenciasCrudas | null | undefined,
): PreferenciasOperativas {
  const umbrales = parsearJson(crudo?.umbrales_alerta) as
    | { tiempo_llegada_max_min?: number }
    | null;
  const zonas = parsearJson(crudo?.zonas_geograficas);
  const ids = Array.isArray(zonas) ? zonas.map(Number).filter((n) => Number.isFinite(n)) : [];

  return {
    tiempoLlegadaMaxMin: umbrales?.tiempo_llegada_max_min ?? null,
    canales: (crudo?.canales_notificacion as PreferenciasOperativas['canales']) ?? 'email',
    telefonoSms: crudo?.telefono_sms ?? '',
    // Sin nombre todavía: el componente los resuelve contra el catálogo al cargar.
    condados: ids.map((id) => ({ id, nombre: '' })),
    destinatarios: crudo?.destinatarios_reportes ?? '',
  };
}

@Component({
  selector: 'app-preferencias-operativas-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <form class="grid gap-5" (ngSubmit)="onSubmit()">
      <div class="grid gap-1.5">
        <label for="umbral" class="text-sm font-medium text-text-secondary">
          Avisarme si una unidad tarda más de (minutos)
        </label>
        <input
          id="umbral"
          type="number"
          min="1"
          data-testid="pref-umbral-llegada"
          class="tsi-input w-full"
          [(ngModel)]="valor.tiempoLlegadaMaxMin"
          name="umbral"
          placeholder="Ej. 0"
        />
        <p class="m-0 text-xs text-text-secondary">
          Déjalo vacío si no quieres avisos por tiempo de llegada.
        </p>
      </div>

      <div class="grid gap-1.5">
        <label for="canales" class="text-sm font-medium text-text-secondary">
          Canal de notificación
        </label>
        <select
          id="canales"
          data-testid="pref-canales"
          class="tsi-select w-full min-w-0"
          [(ngModel)]="valor.canales"
          name="canales"
        >
          <option value="email">Email</option>
          <option value="sms">SMS</option>
          <option value="ambos">Ambos</option>
        </select>
      </div>

      @if (valor.canales === 'sms' || valor.canales === 'ambos') {
        <div class="grid gap-1.5">
          <label for="telefono" class="text-sm font-medium text-text-secondary">Teléfono SMS</label>
          <input
            id="telefono"
            data-testid="pref-telefono"
            class="tsi-input w-full"
            [(ngModel)]="valor.telefonoSms"
            name="telefono"
          placeholder="+52 55 1234 5678"
        />
        </div>
      }

      <div class="grid gap-2 border-t border-border-default pt-5">
        <span class="text-sm font-medium text-text-secondary">Zonas geográficas de interés</span>
        <p class="m-0 text-xs text-text-secondary">
          Determinan qué expedientes puedes consultar. Sin zonas declaradas no verás ninguno.
        </p>

        <div class="grid gap-3 sm:grid-cols-3">
          <select
            data-testid="pref-pais"
            aria-label="País"
            class="tsi-select w-full min-w-0"
            [ngModel]="paisSel()"
            (ngModelChange)="onPais($event)"
            name="pais"
          >
            <option [ngValue]="null">— País —</option>
            @for (p of paises(); track p.id) {
              <option [ngValue]="p.id">{{ p.nombre }}</option>
            }
          </select>

          <select
            data-testid="pref-estado"
            aria-label="Estado o región"
            class="tsi-select w-full min-w-0"
            [ngModel]="estadoSel()"
            (ngModelChange)="onEstado($event)"
            [disabled]="!paisSel()"
            name="estado"
          >
            <option [ngValue]="null">— Estado —</option>
            @for (e of estados(); track e.id) {
              <option [ngValue]="e.id">{{ e.nombre }}</option>
            }
          </select>

          <select
            data-testid="pref-condado"
            aria-label="Condado"
            class="tsi-select w-full min-w-0"
            [ngModel]="condadoSel()"
            (ngModelChange)="agregarCondado($event)"
            [disabled]="!estadoSel()"
            name="condado"
          >
            <option [ngValue]="null">— Añadir condado —</option>
            @for (c of condados(); track c.id) {
              <option [ngValue]="c.id">{{ c.nombre }}</option>
            }
          </select>
        </div>

        <ul class="m-0 flex list-none flex-wrap gap-2 p-0" data-testid="pref-zonas-elegidas">
          @for (z of valor.condados; track z.id) {
            <li
              class="inline-flex items-center gap-2 rounded-full border border-border-default bg-bg-page px-3 py-1 text-sm text-text-primary"
            >
              {{ z.nombre || 'Condado sin nombre' }}
              <button
                type="button"
                class="text-text-secondary hover:text-alert-critical"
                (click)="quitarCondado(z.id)"
                [attr.aria-label]="'Quitar ' + z.nombre"
              >
                ×
              </button>
            </li>
          } @empty {
            <li class="text-sm text-text-secondary">Ninguna zona seleccionada todavía.</li>
          }
        </ul>
      </div>

      <div class="grid gap-1.5 border-t border-border-default pt-5">
        <label for="destinatarios" class="text-sm font-medium text-text-secondary">
          Destinatarios de los reportes
        </label>
        <input
          id="destinatarios"
          data-testid="pref-destinatarios"
          placeholder="correo@empresa.com, otro@empresa.com"
          class="tsi-input w-full"
          [(ngModel)]="valor.destinatarios"
          name="destinatarios"
        />
        <p class="m-0 text-xs text-text-secondary">Separa varios correos con comas.</p>
      </div>

      @if (error()) {
        <p class="m-0 text-sm text-alert-critical" role="alert">{{ error() }}</p>
      }

      <button
        type="submit"
        data-testid="pref-guardar"
        class="tsi-btn tsi-btn-primary w-fit"
      >
        {{ submitLabel }}
      </button>
    </form>
  `,
})
export class PreferenciasOperativasFormComponent implements OnInit {
  private readonly catalogo = inject(UbicacionCatalogoApiService);
  private readonly cdr = inject(ChangeDetectorRef);

  @Input({ required: true }) valor!: PreferenciasOperativas;
  @Input() submitLabel = 'Guardar';
  @Output() readonly guardar = new EventEmitter<PreferenciasSerializadas>();

  readonly paises = signal<CatalogoItem[]>([]);
  readonly estados = signal<CatalogoItem[]>([]);
  readonly condados = signal<CatalogoItem[]>([]);
  readonly paisSel = signal<number | null>(null);
  readonly estadoSel = signal<number | null>(null);
  readonly condadoSel = signal<number | null>(null);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.catalogo.listarPaises().subscribe((p) => {
      this.paises.set(p);
      this.cdr.markForCheck();
      this.resolverNombresPendientes(p);
    });
  }

  onPais(idpais: number | null): void {
    this.paisSel.set(idpais);
    this.estadoSel.set(null);
    this.condadoSel.set(null);
    this.estados.set([]);
    this.condados.set([]);
    if (idpais == null) return;
    this.catalogo.listarEstados(idpais).subscribe((e) => {
      this.estados.set(e);
      this.cdr.markForCheck();
    });
  }

  onEstado(idestado: number | null): void {
    this.estadoSel.set(idestado);
    this.condadoSel.set(null);
    this.condados.set([]);
    if (idestado == null) return;
    this.catalogo.listarCondados(idestado).subscribe((c) => {
      this.condados.set(c);
      this.cdr.markForCheck();
    });
  }

  agregarCondado(idcondado: number | null): void {
    if (idcondado == null) return;
    const elegido = this.condados().find((c) => c.id === idcondado);
    if (elegido && !this.valor.condados.some((z) => z.id === idcondado)) {
      this.valor.condados = [...this.valor.condados, elegido];
    }
    // El selector vuelve al placeholder: es un "añadir", no una selección fija.
    this.condadoSel.set(null);
    this.cdr.markForCheck();
  }

  quitarCondado(idcondado: number): void {
    this.valor.condados = this.valor.condados.filter((z) => z.id !== idcondado);
    this.cdr.markForCheck();
  }

  onSubmit(): void {
    if (
      (this.valor.canales === 'sms' || this.valor.canales === 'ambos') &&
      !this.valor.telefonoSms?.trim()
    ) {
      this.error.set('Indica un teléfono para poder enviarte SMS.');
      return;
    }
    this.error.set(null);
    this.guardar.emit(serializarPreferencias(this.valor));
  }

  /**
   * Las zonas ya guardadas llegan como ids sin nombre. Se recorre el catálogo
   * para poder mostrarlas por su nombre — un identificador no le dice nada a
   * quien revisa sus preferencias (§8 del design-system).
   */
  private resolverNombresPendientes(paises: CatalogoItem[]): void {
    const pendientes = this.valor.condados.filter((z) => !z.nombre);
    if (!pendientes.length) return;

    for (const pais of paises) {
      this.catalogo.listarEstados(pais.id).subscribe((estados) => {
        for (const estado of estados) {
          this.catalogo.listarCondados(estado.id).subscribe((condados) => {
            let cambio = false;
            this.valor.condados = this.valor.condados.map((z) => {
              if (z.nombre) return z;
              const hallado = condados.find((c) => c.id === z.id);
              if (!hallado) return z;
              cambio = true;
              return hallado;
            });
            if (cambio) this.cdr.markForCheck();
          });
        }
      });
    }
  }
}

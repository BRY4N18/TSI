/**
 * Tabla de un listado táctico simple: estados, alcance y paginación.
 *
 * Las 32 páginas declaran columnas; esto las pinta. Maquetar 32 `<table>` a mano
 * garantiza que se desalineen y que alguna se olvide de lo de abajo.
 *
 * Tres cosas que este componente existe para no perder:
 *
 * 1. **el aviso de alcance**, también con la lista vacía;
 * 2. **el `400` como error legible**, nunca como tabla vacía;
 * 3. **el valor ausente como ausente**, nunca como cero.
 *
 * Contrato: `specs/002-tactico/contrato-informes-simples-frontend.md`.
 */

import { DatePipe, DecimalPipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  Input,
  LOCALE_ID,
  computed,
  inject,
  input,
} from '@angular/core';

import { advertenciaDeContenido, avisoDeAlcance } from './informes-alcance';
import { ColumnaListado, ErrorListado, AcotadoA } from './informes-listado.types';
import { TablerIconComponent } from '../ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../ui/list-states/list-empty-state.component';
import { ListLoadingSkeletonComponent } from '../ui/list-states/list-loading-skeleton.component';
import { duracionLegible } from './duracion';
import { humanizar } from './informes-opciones';
import {
  LIST_MOBILE_CARD_CLASS,
  LIST_ROW_CLASS,
  LIST_TABLE_CLASS,
  LIST_TABLE_TD_CLASS,
  LIST_TABLE_TD_PRIMARY_CLASS,
  LIST_TABLE_TH_CLASS,
  LIST_TABLE_TH_RIGHT_CLASS,
} from '../ui/list-states/list-table.styles';

/** Lo que se pinta cuando el backend devolvió ausencia. **Nunca un cero.** */
export const AUSENTE = '—';

@Component({
  selector: 'app-informes-listado',
  standalone: true,
  imports: [TablerIconComponent, ListEmptyStateComponent, ListLoadingSkeletonComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (advertencia() !== null) {
      <!--
        ⚠️ Distinto del aviso de acotamiento: este dice **qué describe** el
        listado, y se muestra SIEMPRE —también con la lista vacía— porque
        advierte de una lectura equivocada, no de un recorte de datos.
      -->
      <p
        class="mb-4 flex items-start gap-2 rounded-md border border-alert-warning bg-alert-warning-bg px-4 py-3 text-sm text-alert-warning"
        data-testid="advertencia-contenido"
        role="status"
      >
        <app-tabler-icon name="alert-triangle" [size]="16" />
        <span>{{ advertencia() }}</span>
      </p>
    }

    @if (aviso() !== null) {
      <p
        class="mb-4 flex items-start gap-2 rounded-md border border-border-default bg-bg-surface px-4 py-3 text-sm text-text-secondary"
        data-testid="aviso-alcance"
        role="status"
      >
        <app-tabler-icon name="info-circle" [size]="16" />
        <span>{{ aviso() }}</span>
      </p>
    }

    @if (cargando()) {
      <app-list-loading-skeleton [count]="4" />
    } @else if (error() !== null) {
      <!-- El alias "as" no se admite en un @else if; el error se lee del input. -->
      <div
        class="grid place-items-center gap-3 rounded-md border border-alert-critical bg-alert-critical-bg p-10 text-center"
        [attr.data-testid]="'error-' + error()!.tipo"
        role="alert"
      >
        <app-tabler-icon name="alert-triangle" [size]="32" />
        <p class="m-0 text-sm text-alert-critical" data-testid="error-detalle">
          {{ error()!.mensaje }}
        </p>
        @if (error()!.reintentable) {
          <button
            type="button"
            data-testid="btn-reintentar"
            class="inline-flex items-center gap-2 rounded-md border border-alert-critical px-4 py-2 text-sm font-medium text-alert-critical hover:bg-alert-critical-bg"
            (click)="reintentar()"
          >
            <app-tabler-icon name="refresh" [size]="16" />
            Reintentar
          </button>
        }
      </div>
    } @else if (filas().length === 0) {
      <app-list-empty-state [message]="mensajeVacioEfectivo()" />
    } @else {
      <table [class]="tablaClass" data-testid="tabla-informe">
        <thead>
          <tr>
            @for (columna of columnas(); track columna.campo) {
              <th
                scope="col"
                [class]="columna.alineacion === 'derecha' ? thDerechaClass : thClass"
              >
                {{ columna.etiqueta }}
              </th>
            }
          </tr>
        </thead>
        <tbody>
          @for (fila of filas(); track $index) {
            <tr [class]="filaClass" data-testid="fila-informe">
              @for (columna of columnas(); track columna.campo) {
                <td [class]="claseDeCelda(columna)">{{ celda(fila, columna) }}</td>
              }
            </tr>
          }
        </tbody>
      </table>

      <div class="grid gap-3 md:hidden" data-testid="tarjetas-informe">
        @for (fila of filas(); track $index) {
          <div [class]="tarjetaClass">
            @for (columna of columnas(); track columna.campo) {
              @if (!columna.soloEscritorio) {
                <p class="m-0 flex justify-between gap-4 py-1 text-sm">
                  <span class="text-text-secondary">{{ columna.etiqueta }}</span>
                  <span class="text-text-primary">{{ celda(fila, columna) }}</span>
                </p>
              }
            }
          </div>
        }
      </div>

      <nav
        class="mt-4 flex items-center justify-between gap-4"
        data-testid="paginacion"
        aria-label="Paginación del informe"
      >
        <button
          type="button"
          data-testid="btn-anterior"
          class="inline-flex items-center gap-2 rounded-md border border-border-default px-4 py-2 text-sm text-text-primary disabled:opacity-40"
          [disabled]="!hayAnterior()"
          (click)="anterior()"
        >
          <app-tabler-icon name="chevron-left" [size]="16" />
          Anterior
        </button>

        <!--
          Sin números de página ni total: el cursor es opaco y no hay recuento.
          Inventarlo obligaría a contar filas, que es lo que la paginación
          keyset evita para no repetir ni perder registros.
        -->
        <span class="text-sm text-text-secondary" data-testid="pagina-actual">
          Página {{ pagina() }}
        </span>

        <button
          type="button"
          data-testid="btn-siguiente"
          class="inline-flex items-center gap-2 rounded-md border border-border-default px-4 py-2 text-sm text-text-primary disabled:opacity-40"
          [disabled]="!haySiguiente()"
          (click)="siguiente()"
        >
          Siguiente
          <app-tabler-icon name="chevron-right" [size]="16" />
        </button>
      </nav>
    }
  `,
})
export class InformesListadoComponent<T extends Record<string, unknown>> {
  readonly columnas = input.required<ColumnaListado<T>[]>();
  readonly filas = input.required<T[]>();
  readonly cargando = input(false);
  readonly error = input<ErrorListado | null>(null);
  readonly acotadoA = input<AcotadoA | undefined>(undefined);
  /** `meta.alcance`: qué describe el listado, cuando podría malinterpretarse. */
  readonly alcance = input<string | undefined>(undefined);
  readonly mensajeVacio = input('No hay resultados.');
  readonly hayAnterior = input(false);
  readonly haySiguiente = input(false);
  readonly pagina = input(1);

  @Input() onSiguiente: () => void = () => {};
  @Input() onAnterior: () => void = () => {};
  @Input() onReintentar: () => void = () => {};

  readonly tablaClass = LIST_TABLE_CLASS;
  readonly thClass = LIST_TABLE_TH_CLASS;
  readonly thDerechaClass = LIST_TABLE_TH_RIGHT_CLASS;
  readonly filaClass = LIST_ROW_CLASS;
  readonly tarjetaClass = LIST_MOBILE_CARD_CLASS;

  // Se usa el locale que la aplicacion tenga configurado, no uno fijo: fijar
  // 'es' aqui exige registrar sus datos, y sin ellos el pipe lanza en tiempo de
  // render — es decir, la tabla se cae al pintar un numero.
  private readonly locale = inject(LOCALE_ID);
  private readonly datePipe = new DatePipe(this.locale);
  private readonly decimalPipe = new DecimalPipe(this.locale);

  /** Ausente con lista llena y con lista vacía: es cuando más importa. */
  readonly aviso = computed(() => {
    const aviso = avisoDeAlcance(this.acotadoA());
    if (!aviso) {
      return null;
    }
    return this.filas().length === 0 && !this.cargando() ? null : aviso.texto;
  });

  /**
   * Se muestra **siempre**, incluso sin filas: advierte de una lectura
   * equivocada del listado, no de un recorte de los datos.
   */
  readonly advertencia = computed(() => advertenciaDeContenido(this.alcance()));

  readonly mensajeVacioEfectivo = computed(() => {
    const aviso = avisoDeAlcance(this.acotadoA());
    // ⚠️ El estado vacío lleva el alcance **dentro del texto**. Es justo cuando
    // no hay filas cuando «no hay» y «no hay de los tuyos» se leen igual.
    return aviso ? `${this.mensajeVacio()} ${aviso.textoVacio}` : this.mensajeVacio();
  });

  claseDeCelda(columna: ColumnaListado<T>): string {
    const base = columna.principal ? LIST_TABLE_TD_PRIMARY_CLASS : LIST_TABLE_TD_CLASS;
    return columna.alineacion === 'derecha' ? `${base} text-right` : base;
  }

  /**
   * ⚠️ Un valor ausente se pinta como ausente, **nunca como cero**.
   *
   * El backend devuelve `null` de forma deliberada: una calificación sin poner
   * no es la nota mínima, una hora de fin ausente no es 1970, un cupo ausente
   * no es cero llamadas. Rellenarlo aquí desharía esa distinción justo en el
   * último paso.
   */
  celda(fila: T, columna: ColumnaListado<T>): string {
    const valor = fila[columna.campo];
    if (valor === null || valor === undefined || valor === '') {
      return AUSENTE;
    }
    // Un arreglo vacío es ausencia, no una lista de cero elementos: quien no
    // tiene roles no tiene «cero roles», no los tiene.
    if (Array.isArray(valor) && valor.length === 0) {
      return AUSENTE;
    }

    switch (columna.formato) {
      case 'lista':
        return (Array.isArray(valor) ? valor : [valor]).join(', ');
      case 'booleano':
        return valor ? 'Sí' : 'No';
      case 'enumeracion':
        return humanizar(String(valor));
      case 'duracion_minutos':
        return duracionLegible(Number(valor));
      case 'numero':
        return this.decimalPipe.transform(valor as number) ?? AUSENTE;
      // Dos decimales exactos, ni uno menos: es lo que permite comparar una
      // columna de importes leyendo hacia abajo. Sin divisa — el backend no la
      // publica, y ponerla aqui seria inventarla.
      case 'moneda':
        return this.decimalPipe.transform(valor as number, '1.2-2') ?? AUSENTE;
      case 'fecha':
        return this.datePipe.transform(valor as string, 'dd/MM/yyyy') ?? String(valor);
      case 'fecha_hora':
        return this.datePipe.transform(valor as string, 'dd/MM/yyyy HH:mm') ?? String(valor);
      default:
        return String(valor);
    }
  }

  siguiente(): void {
    this.onSiguiente();
  }

  anterior(): void {
    this.onAnterior();
  }

  reintentar(): void {
    this.onReintentar();
  }
}

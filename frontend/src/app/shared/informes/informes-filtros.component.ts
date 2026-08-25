/**
 * Barra de filtros de un listado táctico, armada desde su declaración.
 *
 * Dos decisiones que valen la explicación:
 *
 * **Las enumeraciones se pintan como desplegable.** No es estética: es la mejor
 * forma de que el `400` **no llegue a producirse**. El backend rechaza un valor
 * desconocido nombrando los válidos, y ofrecer solo los válidos evita el viaje.
 *
 * **El rango de fechas solo aparece donde el listado lo admite.** El backend
 * distingue estado actual —que rechaza `desde`/`hasta` con `400`— de hechos del
 * período. Pintar el selector en un listado de estado actual sería ofrecer un
 * control que solo sirve para provocar un error.
 *
 * Contrato: `specs/002-tactico/contrato-informes-simples-frontend.md` §3.2-3.3.
 */

import { ChangeDetectionStrategy, Component, EventEmitter, Output, input } from '@angular/core';
import { FormsModule } from '@angular/forms';

import {
  Catalogos,
  FiltroListado,
  OpcionCatalogo,
  ValoresFiltro,
} from './informes-listado.types';
import { TablerIconComponent } from '../ui/icon/tabler-icon.component';
import { LIST_FILTER_CONTROL_CLASS, LIST_FILTER_SELECT_CLASS } from '../ui/list-states/list-table.styles';
import { humanizar } from './informes-opciones';

@Component({
  selector: 'app-informes-filtros',
  standalone: true,
  imports: [FormsModule, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <form
      class="mb-6 grid gap-4 tsi-panel p-4 md:grid-cols-3"
      data-testid="filtros-informe"
      (ngSubmit)="aplicar()"
    >
      @for (filtro of filtros(); track filtro.nombre) {
        <label class="grid gap-1.5 text-sm">
          <span class="text-text-secondary">{{ filtro.etiqueta }}</span>

          @switch (filtro.tipo) {
            @case ('enumeracion') {
              <select
                [class]="controlClassSelect"
                [attr.data-testid]="'filtro-' + filtro.nombre"
                [ngModel]="valorDe(filtro.nombre)"
                [name]="filtro.nombre"
                (ngModelChange)="cambiar(filtro.nombre, $event)"
              >
                <option [ngValue]="null">Todos</option>
                @for (opcion of filtro.opciones ?? []; track opcion.valor) {
                  <option [ngValue]="opcion.valor">{{ opcion.etiqueta }}</option>
                }
              </select>
            }
            @case ('catalogo') {
              <select
                [class]="controlClassSelect"
                [attr.data-testid]="'filtro-' + filtro.nombre"
                [disabled]="cargandoCatalogos()"
                [ngModel]="valorDe(filtro.nombre)"
                [name]="filtro.nombre"
                (ngModelChange)="cambiar(filtro.nombre, $event)"
              >
                <!-- ⚠️ Mientras el catálogo carga se dice que está cargando. Un
                     desplegable vacío se lee como «no hay condados», que es una
                     afirmación sobre los datos y no sobre la petición. -->
                @if (cargandoCatalogos()) {
                  <option [ngValue]="null">Cargando…</option>
                } @else {
                  <option [ngValue]="null">Todos</option>
                  <!-- Se humaniza igual que las enumeraciones declaradas: hay
                       catálogos cuyo nombre es el literal del origen
                       (Escalado_zona, en Dim_OrigenDespacho). Aquí es seguro
                       porque lo que viaja es el id, no el texto. -->
                  @for (opcion of opcionesDe(filtro); track opcion.id) {
                    <option [ngValue]="String(opcion.id)">{{ humanizar(opcion.nombre) }}</option>
                  }
                }
              </select>
            }
            @case ('booleano') {
              <select
                [class]="controlClassSelect"
                [attr.data-testid]="'filtro-' + filtro.nombre"
                [ngModel]="valorDe(filtro.nombre)"
                [name]="filtro.nombre"
                (ngModelChange)="cambiar(filtro.nombre, $event)"
              >
                <option [ngValue]="null">Todos</option>
                <option [ngValue]="'true'">Sí</option>
                <option [ngValue]="'false'">No</option>
              </select>
            }
            @case ('numero') {
              <input
                type="number"
                [class]="controlClass"
                [attr.data-testid]="'filtro-' + filtro.nombre"
                [ngModel]="valorDe(filtro.nombre)"
                [name]="filtro.nombre"
                (ngModelChange)="cambiar(filtro.nombre, $event)"
          placeholder="Escribe para filtrar…"
        />
            }
            @case ('fecha') {
              <input
                type="date"
                [class]="controlClass"
                [attr.data-testid]="'filtro-' + filtro.nombre"
                [ngModel]="valorDe(filtro.nombre)"
                [name]="filtro.nombre"
                (ngModelChange)="cambiar(filtro.nombre, $event)"
          placeholder="Escribe para filtrar…"
        />
            }
            @default {
              <input
                type="text"
                [class]="controlClass"
                [attr.data-testid]="'filtro-' + filtro.nombre"
                [ngModel]="valorDe(filtro.nombre)"
                [name]="filtro.nombre"
                (ngModelChange)="cambiar(filtro.nombre, $event)"
          placeholder="Escribe para filtrar…"
        />
            }
          }

          @if (filtro.ayuda) {
            <span class="text-xs text-text-secondary">{{ filtro.ayuda }}</span>
          }
        </label>
      }

      @if (admiteRango()) {
        <label class="grid gap-1.5 text-sm">
          <span class="text-text-secondary">Desde</span>
          <input
            type="date"
            [class]="controlClass"
            data-testid="filtro-desde"
            name="desde"
            [ngModel]="valorDe('desde')"
            (ngModelChange)="cambiar('desde', $event)"
          placeholder="Escribe para filtrar…"
        />
        </label>
        <label class="grid gap-1.5 text-sm">
          <span class="text-text-secondary">Hasta</span>
          <input
            type="date"
            [class]="controlClass"
            data-testid="filtro-hasta"
            name="hasta"
            [ngModel]="valorDe('hasta')"
            (ngModelChange)="cambiar('hasta', $event)"
          placeholder="Escribe para filtrar…"
        />
        </label>
      }

      <div class="flex items-end gap-2">
        <button
          type="submit"
          data-testid="btn-aplicar-filtros"
          class="inline-flex items-center gap-2 rounded-md bg-accent-primary px-4 py-2.5 text-sm font-medium text-white"
        >
          <app-tabler-icon name="filter" [size]="16" />
          Aplicar
        </button>
        <button
          type="button"
          data-testid="btn-limpiar-filtros"
          class="inline-flex items-center gap-2 rounded-md border border-border-default px-4 py-2.5 text-sm text-text-primary"
          (click)="limpiar()"
        >
          Limpiar
        </button>
      </div>
    </form>
  `,
})
export class InformesFiltrosComponent {
  readonly filtros = input.required<FiltroListado[]>();
  /** `false` en los listados de estado actual: el backend rechaza el rango. */
  readonly admiteRango = input(false);
  /**
   * Catálogos ya resueltos, por clave. Vacío mientras cargan — y por eso hace
   * falta `cargandoCatalogos`: «aún no llegó» y «llegó vacío» se ven igual, y
   * uno es un cliente sin zonas contratadas.
   */
  readonly catalogos = input<Catalogos>({});
  readonly cargandoCatalogos = input(false);

  @Output() readonly aplicados = new EventEmitter<ValoresFiltro>();

  readonly controlClass = LIST_FILTER_CONTROL_CLASS;
  readonly controlClassSelect = LIST_FILTER_SELECT_CLASS;

  private valores: ValoresFiltro = {};

  /** Alias para poder llamar a `String()` desde la plantilla. */
  readonly String = String;

  readonly humanizar = humanizar;

  /**
   * Opciones de un filtro de catálogo.
   *
   * Un catálogo que no llegó devuelve lista vacía, no revienta: el desplegable
   * se queda con «Todos» y el listado sigue siendo usable sin ese filtro.
   */
  opcionesDe(filtro: FiltroListado): OpcionCatalogo[] {
    return this.catalogos()[filtro.catalogo ?? ''] ?? [];
  }

  valorDe(nombre: string): string | number | boolean | null {
    return this.valores[nombre] ?? null;
  }

  cambiar(nombre: string, valor: unknown): void {
    // `''` y `null` significan lo mismo aquí —«sin filtrar»— y el servicio
    // descarta ambos: un filtro vacío **no viaja**.
    this.valores = {
      ...this.valores,
      [nombre]: valor === '' || valor === undefined ? null : (valor as string),
    };
  }

  aplicar(): void {
    this.aplicados.emit({ ...this.valores });
  }

  limpiar(): void {
    this.valores = {};
    this.aplicados.emit({});
  }
}

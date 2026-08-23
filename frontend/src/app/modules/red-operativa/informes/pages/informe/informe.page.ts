/**
 * Una sola página para los listados tácticos de Red Operativa.
 *
 * Mismo patrón que el piloto de Cuentas y Clientes, y por el mismo motivo: los
 * listados se diferencian solo en su declaración, y una copia por listado sería
 * la que algún día se olvidara del aviso de alcance.
 *
 * La ruta lleva el identificador, la página resuelve su definición del catálogo
 * y se la pasa a la capa compartida. **No implementa tabla, paginación ni manejo
 * de error propios**: si hiciera falta, la capa compartida quedó corta y la
 * corrección va allí.
 */

import { ChangeDetectionStrategy, Component, OnInit, computed, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';

import { INFORMES_RED_OPERATIVA } from '../../definiciones/informes-red-operativa.definiciones';
import { InformesFiltrosComponent } from '../../../../../shared/informes/informes-filtros.component';
import { InformesListadoComponent } from '../../../../../shared/informes/informes-listado.component';
import { InformesListadoStore } from '../../../../../shared/informes/informes-listado.store';
import { ValoresFiltro } from '../../../../../shared/informes/informes-listado.types';
import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../../shared/ui/list-states/list-table.styles';

@Component({
  selector: 'app-informe-red-operativa',
  standalone: true,
  imports: [
    RouterLink,
    TablerIconComponent,
    InformesFiltrosComponent,
    InformesListadoComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [InformesListadoStore],
  template: `
    <section [class]="shellClass">
      <a
        routerLink="/red-operativa/informes"
        class="mb-4 inline-flex items-center gap-2 text-sm text-text-secondary"
        data-testid="volver-indice"
      >
        <app-tabler-icon name="arrow-left" [size]="16" />
        Informes de Red Operativa
      </a>

      <h1 class="mb-6 text-2xl font-semibold text-text-primary" data-testid="titulo-informe">
        {{ definicion().titulo }}
      </h1>

      @if (definicion().filtros?.length || definicion().admiteRango) {
        <app-informes-filtros
          [filtros]="definicion().filtros ?? []"
          [admiteRango]="definicion().admiteRango ?? false"
          [catalogos]="store.catalogos()"
          [cargandoCatalogos]="store.cargandoCatalogos()"
          (aplicados)="aplicar($event)"
        />
      }

      <app-informes-listado
        [columnas]="definicion().columnas"
        [filas]="store.filas()"
        [cargando]="store.cargando()"
        [error]="store.error()"
        [acotadoA]="store.acotadoA()"
        [alcance]="store.alcance()"
        [mensajeVacio]="definicion().mensajeVacio"
        [hayAnterior]="store.hayPaginaAnterior()"
        [haySiguiente]="store.hayPaginaSiguiente()"
        [pagina]="store.numeroDePagina()"
        [onSiguiente]="siguiente"
        [onAnterior]="anterior"
        [onReintentar]="reintentar"
      />
    </section>
  `,
})
export class InformeRedOperativaPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  readonly store = inject(InformesListadoStore);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;

  private readonly params = toSignal(this.route.paramMap, {
    initialValue: this.route.snapshot.paramMap,
  });

  readonly definicion = computed(() => {
    // ⚠️ Dos orígenes: la ruta genérica lo trae como parámetro y la de accesos
    // técnicos —que tiene `path` literal, por su guard propio— lo trae en
    // `data`. Leer solo el parámetro dejaría esa pantalla sin definición.
    const id =
      this.params().get('informe') ?? (this.route.snapshot.data['informe'] as string) ?? '';
    const definicion = INFORMES_RED_OPERATIVA[id];
    if (!definicion) {
      // La ruta solo se genera desde el catálogo, así que llegar aquí con un
      // identificador desconocido significa que alguien escribió la URL a mano.
      throw new Error(`Informe desconocido: '${id}'.`);
    }
    return definicion;
  });

  ngOnInit(): void {
    this.store.configurar(this.definicion().ruta);
    // Solo se pide el catálogo si algún filtro lo necesita: los listados que no
    // declaran ninguno no tienen endpoint de catálogos, y pedirlo sería un 404
    // por cada pantalla.
    if (this.definicion().filtros?.some((f) => f.tipo === 'catalogo')) {
      this.store.cargarCatalogos();
    }
    this.store.aplicarFiltros({});
  }

  aplicar(valores: ValoresFiltro): void {
    this.store.aplicarFiltros(valores);
  }

  // Se pasan como referencia estable: el componente común los invoca sin
  // conocer el store.
  readonly siguiente = (): void => this.store.siguiente();
  readonly anterior = (): void => this.store.anterior();
  readonly reintentar = (): void => this.store.recargar();
}

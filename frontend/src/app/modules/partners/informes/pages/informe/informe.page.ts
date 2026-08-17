/**
 * Una sola página para los cinco listados de Partners y API.
 *
 * Declara columnas y filtros; la tabla, la paginación y el error los pinta la
 * capa compartida. El filtro `partner` se omite cuando el actor es Partner:
 * mostrárselo es ofrecerle un control cuyo único efecto útil es un 403.
 */

import { ChangeDetectionStrategy, Component, OnInit, computed, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';

import { INFORMES_PARTNERS } from '../../definiciones/informes-partners.definiciones';
import { ROLES_INFORMES_CONTRATO } from '../../guards/informes-partners.guard';
import { AuthApiService } from '../../../../cuentas-clientes/auth/services/auth-api.service';
import { InformesFiltrosComponent } from '../../../../../shared/informes/informes-filtros.component';
import { InformesListadoComponent } from '../../../../../shared/informes/informes-listado.component';
import { InformesListadoStore } from '../../../../../shared/informes/informes-listado.store';
import { ValoresFiltro } from '../../../../../shared/informes/informes-listado.types';
import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../../shared/ui/list-states/list-table.styles';

@Component({
  selector: 'app-informe-partners',
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
        routerLink="/partners/informes"
        class="mb-4 inline-flex items-center gap-2 text-sm text-text-secondary"
        data-testid="volver-indice"
      >
        <app-tabler-icon name="arrow-left" [size]="16" />
        Volver a los informes
      </a>

      <h1 class="mb-6 text-2xl font-semibold text-text-primary" data-testid="titulo-informe">
        {{ definicion().titulo }}
      </h1>

      @if (filtrosVisibles().length || definicion().admiteRango) {
        <app-informes-filtros
          [filtros]="filtrosVisibles()"
          [admiteRango]="definicion().admiteRango ?? false"
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
export class InformePartnersPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly authApi = inject(AuthApiService);
  readonly store = inject(InformesListadoStore);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;

  private readonly params = toSignal(this.route.paramMap, {
    initialValue: this.route.snapshot.paramMap,
  });

  readonly definicion = computed(() => {
    const id =
      this.params().get('informe') ?? (this.route.snapshot.data['informe'] as string) ?? '';
    const definicion = INFORMES_PARTNERS[id];
    if (!definicion) {
      throw new Error(`Informe desconocido: '${id}'.`);
    }
    return definicion;
  });

  readonly filtrosVisibles = computed(() => {
    const filtros = this.definicion().filtros ?? [];
    const esGestor = ROLES_INFORMES_CONTRATO.some((rol) => this.authApi.hasRole(rol));
    if (esGestor) {
      return filtros;
    }
    return filtros.filter((filtro) => filtro.nombre !== 'partner');
  });

  ngOnInit(): void {
    this.store.configurar(this.definicion().ruta);
    this.store.aplicarFiltros({});
  }

  aplicar(valores: ValoresFiltro): void {
    this.store.aplicarFiltros(valores);
  }

  readonly siguiente = (): void => this.store.siguiente();
  readonly anterior = (): void => this.store.anterior();
  readonly reintentar = (): void => this.store.recargar();
}

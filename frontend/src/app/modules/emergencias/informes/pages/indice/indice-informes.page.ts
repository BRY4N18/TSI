/**
 * Índice de los informes tácticos simples de Emergencias.
 *
 * Se genera del mismo catálogo que las páginas, y **filtra por rol**: a un
 * Cliente solo le ofrece los casos, que es lo único a lo que su guard le deja
 * entrar. Los otros cuatro son operación interna.
 */

import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import {
  INFORMES_EMERGENCIAS,
  INFORME_CASOS,
} from '../../definiciones/informes-emergencias.definiciones';
import { ROLES_INTERNOS_EMERGENCIAS } from '../../guards/informes-emergencias-simples.guard';
import { AuthApiService } from '../../../../cuentas-clientes/auth/services/auth-api.service';
import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../../shared/ui/list-states/list-table.styles';

@Component({
  selector: 'app-indice-informes-emergencias',
  standalone: true,
  imports: [RouterLink, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <h1 class="tsi-display mb-2 text-3xl font-semibold text-text-primary">
        Informes de Emergencias
      </h1>
<div class="tsi-rail-h mt-2 w-24" aria-hidden="true"></div>
      <p class="mb-6 text-sm text-text-secondary">
        Listados de solo lectura sobre casos, despachos, evidencia y cierres.
      </p>

      <ul class="grid gap-3 md:grid-cols-2" data-testid="indice-informes">
        @for (informe of visibles(); track informe.id) {
          <li>
            <a
              [routerLink]="['/emergencias/informes-simples', informe.id]"
              [attr.data-testid]="'enlace-' + informe.id"
              class="flex items-center gap-3 tsi-panel p-4 text-text-primary hover:border-accent-primary"
            >
              <app-tabler-icon name="list" [size]="20" />
              <span class="text-sm font-medium">{{ informe.titulo }}</span>
            </a>
          </li>
        }
      </ul>
    </section>
  `,
})
export class IndiceInformesEmergenciasPage {
  private readonly authApi = inject(AuthApiService);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;

  readonly visibles = computed(() => {
    const esInterno = ROLES_INTERNOS_EMERGENCIAS.some((rol) => this.authApi.hasRole(rol));
    return Object.entries(INFORMES_EMERGENCIAS)
      .filter(([id]) => esInterno || id === INFORME_CASOS)
      .map(([id, definicion]) => ({ id, titulo: definicion.titulo }));
  });
}

/**
 * Índice de los informes tácticos de Red Operativa.
 *
 * Se genera del mismo catálogo que las páginas y **filtra por rol**: solo ofrece
 * los listados a los que el guard deja entrar. Un enlace que el guard rechaza no
 * sería una fuga —sigue cerrando— pero sí una interfaz que promete lo que no
 * cumple.
 */

import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';

import { INFORMES_RED_OPERATIVA } from '../../definiciones/informes-red-operativa.definiciones';
import { listadosVisiblesPara } from '../../guards/informes-red-operativa.guard';
import { AuthApiService } from '../../../../cuentas-clientes/auth/services/auth-api.service';
import { ReportTileComponent } from '../../../../../shared/ui/report-tile/report-tile.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../../shared/ui/list-states/list-table.styles';

@Component({
  selector: 'app-indice-informes-red-operativa',
  standalone: true,
  imports: [ReportTileComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <h1 class="tsi-display mb-2 text-3xl font-semibold text-text-primary">
        Informes de Red Operativa
      </h1>
<div class="tsi-rail-h mt-2 w-24" aria-hidden="true"></div>
      <p class="mb-6 text-sm text-text-secondary">
        Listados de solo lectura del departamento.
      </p>

      <ul class="grid gap-3 md:grid-cols-2" data-testid="indice-informes">
        @for (informe of visibles(); track informe.id) {
          <li>
            <app-report-tile
              [link]="['/red-operativa/informes', informe.id]"
              [testId]="'enlace-' + informe.id"
              [titulo]="informe.titulo"
            />
          </li>
        }
      </ul>
    </section>
  `,
})
export class IndiceInformesRedOperativaPage {
  private readonly authApi = inject(AuthApiService);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;

  readonly visibles = computed(() => {
    const permitidos = listadosVisiblesPara((rol) => this.authApi.hasRole(rol));
    return Object.entries(INFORMES_RED_OPERATIVA)
      .filter(([id]) => permitidos.includes(id))
      .map(([id, definicion]) => ({ id, titulo: definicion.titulo }));
  });
}

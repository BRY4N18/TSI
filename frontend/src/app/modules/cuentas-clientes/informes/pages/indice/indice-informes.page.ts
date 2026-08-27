/**
 * Índice de los informes tácticos de Cuentas y Clientes.
 *
 * Se genera **del mismo catálogo** que las páginas. Mantener una lista aparte
 * garantizaría que algún día ofreciera un informe que ya no existe, o que
 * faltara uno recién añadido.
 */

import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';

import {
  INFORMES_CUENTAS,
  INFORME_ACCESOS_TECNICOS,
} from '../../definiciones/informes-cuentas.definiciones';
import { AuthApiService } from '../../../auth/services/auth-api.service';
import { ReportTileComponent } from '../../../../../shared/ui/report-tile/report-tile.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../../shared/ui/list-states/list-table.styles';

@Component({
  selector: 'app-indice-informes-cuentas',
  standalone: true,
  imports: [ReportTileComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <h1 class="tsi-display mb-2 text-3xl font-semibold text-text-primary">
        Informes de Cuentas y Clientes
      </h1>
<div class="tsi-rail-h mt-2 w-24" aria-hidden="true"></div>
      <p class="mb-6 text-sm text-text-secondary">
        Listados de solo lectura sobre cuentas, incorporación, usuarios y accesos.
      </p>

      <ul class="grid gap-3 md:grid-cols-2" data-testid="indice-informes">
        @for (informe of visibles(); track informe.id) {
          <li>
            <app-report-tile
              [link]="['/cuentas-clientes/informes', informe.id]"
              [testId]="'enlace-' + informe.id"
              [titulo]="informe.titulo"
            />
          </li>
        }
      </ul>
    </section>
  `,
})
export class IndiceInformesCuentasPage {
  private readonly authApi = inject(AuthApiService);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;

  /**
   * ⚠️ El Director Tecnológico entra **solo** a accesos técnicos.
   *
   * Ofrecerle los otros siete en el índice le mostraría enlaces que su guard
   * rechaza: no sería una fuga —el guard sigue cerrando— pero sí una interfaz
   * que promete lo que no cumple.
   */
  readonly visibles = computed(() => {
    const esAdmin = this.authApi.hasRole('Administrador');
    return Object.entries(INFORMES_CUENTAS)
      .filter(([id]) => esAdmin || id === INFORME_ACCESOS_TECNICOS)
      .map(([id, definicion]) => ({ id, titulo: definicion.titulo }));
  });
}

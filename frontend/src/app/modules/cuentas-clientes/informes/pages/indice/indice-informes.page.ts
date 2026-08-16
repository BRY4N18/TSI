/**
 * Índice de los informes tácticos de Cuentas y Clientes.
 *
 * Se genera **del mismo catálogo** que las páginas. Mantener una lista aparte
 * garantizaría que algún día ofreciera un informe que ya no existe, o que
 * faltara uno recién añadido.
 */

import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import {
  INFORMES_CUENTAS,
  INFORME_ACCESOS_TECNICOS,
} from '../../definiciones/informes-cuentas.definiciones';
import { AuthApiService } from '../../../auth/services/auth-api.service';
import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../../shared/ui/list-states/list-table.styles';

@Component({
  selector: 'app-indice-informes-cuentas',
  standalone: true,
  imports: [RouterLink, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <h1 class="mb-2 text-2xl font-semibold text-text-primary">
        Informes de Cuentas y Clientes
      </h1>
      <p class="mb-6 text-sm text-text-secondary">
        Listados de solo lectura sobre cuentas, incorporación, usuarios y accesos.
      </p>

      <ul class="grid gap-3 md:grid-cols-2" data-testid="indice-informes">
        @for (informe of visibles(); track informe.id) {
          <li>
            <a
              [routerLink]="['/cuentas-clientes/informes', informe.id]"
              [attr.data-testid]="'enlace-' + informe.id"
              class="flex items-center gap-3 rounded-lg border border-border-default bg-bg-surface p-4 text-text-primary hover:border-accent-primary"
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

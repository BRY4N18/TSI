/**
 * Índice de los informes tácticos de Red Operativa.
 *
 * Se genera del mismo catálogo que las páginas y **filtra por rol**: solo ofrece
 * los listados a los que el guard deja entrar. Un enlace que el guard rechaza no
 * sería una fuga —sigue cerrando— pero sí una interfaz que promete lo que no
 * cumple.
 */

import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { INFORMES_RED_OPERATIVA } from '../../definiciones/informes-red-operativa.definiciones';
import { listadosVisiblesPara } from '../../guards/informes-red-operativa.guard';
import { AuthApiService } from '../../../../cuentas-clientes/auth/services/auth-api.service';
import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../../shared/ui/list-states/list-table.styles';

@Component({
  selector: 'app-indice-informes-red-operativa',
  standalone: true,
  imports: [RouterLink, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <h1 class="mb-2 text-2xl font-semibold text-text-primary">
        Informes de Red Operativa
      </h1>
      <p class="mb-6 text-sm text-text-secondary">
        Listados de solo lectura del departamento.
      </p>

      <ul class="grid gap-3 md:grid-cols-2" data-testid="indice-informes">
        @for (informe of visibles(); track informe.id) {
          <li>
            <a
              [routerLink]="['/red-operativa/informes', informe.id]"
              [attr.data-testid]="'enlace-' + informe.id"
              class="flex items-center gap-3 rounded-md border border-border-default bg-bg-surface p-4 text-text-primary hover:border-accent-primary"
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

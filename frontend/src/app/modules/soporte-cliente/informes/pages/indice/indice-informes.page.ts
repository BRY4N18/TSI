/**
 * Índice de los informes tácticos de Soporte al Cliente.
 *
 * Se genera del mismo catálogo que las páginas, y **filtra por rol**: a un
 * reportador no le ofrece los escalados, que su guard rechaza. Ofrecerle un
 * enlace que no puede seguir no sería una fuga —el guard sigue cerrando— pero sí
 * una interfaz que promete lo que no cumple.
 */

import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import {
  INFORMES_SOPORTE,
  INFORME_ESCALADOS,
} from '../../definiciones/informes-soporte.definiciones';
import { ROLES_INFORMES_ATENCION } from '../../guards/informes-soporte.guard';
import { AuthApiService } from '../../../../cuentas-clientes/auth/services/auth-api.service';
import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../../shared/ui/list-states/list-table.styles';

@Component({
  selector: 'app-indice-informes-soporte',
  standalone: true,
  imports: [RouterLink, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <h1 class="mb-2 text-2xl font-semibold text-text-primary">
        Informes de Soporte al Cliente
      </h1>
      <p class="mb-6 text-sm text-text-secondary">
        Listados de solo lectura sobre la cola de tickets y los escalados.
      </p>

      <ul class="grid gap-3 md:grid-cols-2" data-testid="indice-informes">
        @for (informe of visibles(); track informe.id) {
          <li>
            <a
              [routerLink]="['/soporte-cliente/informes', informe.id]"
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
export class IndiceInformesSoportePage {
  private readonly authApi = inject(AuthApiService);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;

  readonly visibles = computed(() => {
    const atiende = ROLES_INFORMES_ATENCION.some((rol) => this.authApi.hasRole(rol));
    return Object.entries(INFORMES_SOPORTE)
      .filter(([id]) => atiende || id !== INFORME_ESCALADOS)
      .map(([id, definicion]) => ({ id, titulo: definicion.titulo }));
  });
}

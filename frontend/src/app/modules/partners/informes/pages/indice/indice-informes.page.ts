/**
 * Índice de los informes tácticos de Partners y API.
 *
 * Se genera del mismo catálogo que las páginas y **filtra por rol**: al Partner
 * no le ofrece versiones ni alcance. Ofrecerle un enlace que su guard rechaza
 * no sería una fuga, pero sí una interfaz que promete lo que no cumple.
 *
 * Dos audiencias, un índice: el título cambia para no fusionar consola y portal.
 */

import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import {
  INFORMES_CONTRATO,
  INFORMES_PARTNERS,
} from '../../definiciones/informes-partners.definiciones';
import { ROLES_INFORMES_CONTRATO } from '../../guards/informes-partners.guard';
import { AuthApiService } from '../../../../cuentas-clientes/auth/services/auth-api.service';
import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../../shared/ui/list-states/list-table.styles';

@Component({
  selector: 'app-indice-informes-partners',
  standalone: true,
  imports: [RouterLink, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <h1 class="mb-2 text-2xl font-semibold text-text-primary" data-testid="titulo-indice">
        {{ titulo() }}
      </h1>
      <p class="mb-6 text-sm text-text-secondary">
        {{ subtitulo() }}
      </p>

      <ul class="grid gap-3 md:grid-cols-2" data-testid="indice-informes">
        @for (informe of visibles(); track informe.id) {
          <li>
            <a
              [routerLink]="['/partners/informes', informe.id]"
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
export class IndiceInformesPartnersPage {
  private readonly authApi = inject(AuthApiService);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;

  readonly esGestorInformes = computed(() =>
    ROLES_INFORMES_CONTRATO.some((rol) => this.authApi.hasRole(rol)),
  );

  readonly titulo = computed(() =>
    this.esGestorInformes() ? 'Informes de Partners y API' : 'Estado de mi acceso',
  );

  readonly subtitulo = computed(() =>
    this.esGestorInformes()
      ? 'Listados de solo lectura sobre partners, credenciales, bitácora, contrato y alcance.'
      : 'Tus partners, tus credenciales y los cambios de tu acceso.',
  );

  readonly visibles = computed(() => {
    const gestor = this.esGestorInformes();
    return Object.entries(INFORMES_PARTNERS)
      .filter(([id]) => gestor || !(INFORMES_CONTRATO as readonly string[]).includes(id))
      .map(([id, definicion]) => ({ id, titulo: definicion.titulo }));
  });
}

/**
 * Índice de los informes tácticos de Soporte al Cliente.
 *
 * Se genera del mismo catálogo que las páginas, y **filtra por rol**: a un
 * reportador no le ofrece los escalados, que su guard rechaza. Ofrecerle un
 * enlace que no puede seguir no sería una fuga —el guard sigue cerrando— pero sí
 * una interfaz que promete lo que no cumple.
 */

import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';

import {
  INFORMES_SOPORTE,
  INFORME_ESCALADOS,
} from '../../definiciones/informes-soporte.definiciones';
import { ROLES_INFORMES_ATENCION } from '../../guards/informes-soporte.guard';
import { AuthApiService } from '../../../../cuentas-clientes/auth/services/auth-api.service';
import { ReportTileComponent } from '../../../../../shared/ui/report-tile/report-tile.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../../shared/ui/list-states/list-table.styles';

@Component({
  selector: 'app-indice-informes-soporte',
  standalone: true,
  imports: [ReportTileComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <h1 class="tsi-display mb-2 text-3xl font-semibold text-text-primary">
        Informes de Soporte al Cliente
      </h1>
<div class="tsi-rail-h mt-2 w-24" aria-hidden="true"></div>
      <p class="mb-6 text-sm text-text-secondary">
        Listados de solo lectura sobre la cola de tickets y los escalados.
      </p>

      <ul class="grid gap-3 md:grid-cols-2" data-testid="indice-informes">
        @for (informe of visibles(); track informe.id) {
          <li>
            <app-report-tile
              [link]="['/soporte-cliente/informes', informe.id]"
              [testId]="'enlace-' + informe.id"
              [titulo]="informe.titulo"
            />
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

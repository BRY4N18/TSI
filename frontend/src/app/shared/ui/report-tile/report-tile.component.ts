import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { TablerIconComponent, TablerIconName } from '../icon/tabler-icon.component';

/**
 * Placa de un informe en el índice de un departamento (design-system.md
 * §3.1/v9). Reemplaza la fila genérica "ícono de lista + texto" — el mismo
 * ícono `list` en las nueve entradas del índice no distinguía un informe de
 * otro; el hex-shield de esta placa sí porta el ícono propio de cada informe
 * (el que ya declara su `definicion`), y la esquina doble lo lee como
 * señalización del sistema en vez de un link de tabla de contenidos.
 */
@Component({
  selector: 'app-report-tile',
  standalone: true,
  imports: [RouterLink, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <a
      [routerLink]="link()"
      [attr.data-testid]="testId()"
      class="tsi-panel tsi-panel--placa flex items-center gap-3 p-4 text-text-primary no-underline hover:border-accent-primary"
    >
      <span class="tsi-node flex h-9 w-8 shrink-0 items-center justify-center bg-accent-primary/10 text-accent-primary">
        <app-tabler-icon [name]="icon()" [size]="18" />
      </span>
      <span class="text-sm font-medium">{{ titulo() }}</span>
    </a>
  `,
})
export class ReportTileComponent {
  readonly link = input.required<unknown[]>();
  readonly titulo = input.required<string>();
  readonly testId = input.required<string>();
  readonly icon = input<TablerIconName>('list');
}

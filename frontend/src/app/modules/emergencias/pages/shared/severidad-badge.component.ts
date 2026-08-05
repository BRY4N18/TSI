import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { SEVERIDAD_INFO } from '../../../accidentes/severidad.constants';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';

/**
 * Iconografía semántica de severidad (design-system.md §5): mismo ícono+tono
 * en toda la app, nunca el número crudo de `idseveridad` como dato principal.
 */
@Component({
  selector: 'app-severidad-badge',
  standalone: true,
  imports: [TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span
      class="inline-flex items-center gap-1.5 text-sm font-medium"
      [class.text-alert-success]="info().tone === 'success'"
      [class.text-alert-warning]="info().tone === 'warning'"
      [class.text-alert-urgent]="info().tone === 'urgent'"
      [class.text-alert-critical]="info().tone === 'critical'"
    >
      <app-tabler-icon [name]="info().icon" [size]="16" />
      {{ info().label }}
    </span>
  `,
})
export class SeveridadBadgeComponent {
  readonly idseveridad = input.required<number>();

  info() {
    return (
      SEVERIDAD_INFO[this.idseveridad()] ?? {
        value: this.idseveridad(),
        label: `Severidad ${this.idseveridad()}`,
        icon: 'alert-circle' as const,
        tone: 'success' as const,
      }
    );
  }
}

import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

/**
 * Isotipo Nodo Integral. El wordmark "Tráfico Seguro Integral" se pinta al lado
 * en el chrome (no va dentro de esta imagen) para poder truncarlo en viewports
 * estrechos. Fondo blanco mínimo para que el navy del nodo se lea en tema oscuro.
 */
@Component({
  selector: 'app-brand-mark',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <img
      src="/brand/tsi-isotype.png"
      width="36"
      height="33"
      [class]="imgClass()"
      [alt]="decorative() ? '' : 'TSI — Tráfico Seguro Integral'"
      [attr.aria-hidden]="decorative() ? true : null"
    />
  `,
})
export class BrandMarkComponent {
  /** True cuando el wordmark visible ya nombra el producto. */
  readonly decorative = input(false);
  readonly size = input<'sm' | 'md' | 'lg'>('md');

  readonly imgClass = computed(() => {
    const box = this.size() === 'sm' ? 'h-8 w-8' : this.size() === 'lg' ? 'h-10 w-10' : 'h-9 w-9';
    return `${box} shrink-0 rounded-md bg-white object-contain p-0.5`;
  });
}

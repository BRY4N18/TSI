import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  effect,
  inject,
  viewChild,
} from '@angular/core';

import { NotificationService } from './notification.service';

/**
 * Host del Alert modal (`design-system.md` §Alert, §12).
 *
 * El overlay cubre la pantalla y **captura los clics**: si no se anuncia como
 * diálogo, para un lector de pantalla o una navegación por teclado la pantalla
 * simplemente deja de responder sin explicación. De ahí `role="alertdialog"`,
 * `aria-modal`, el foco inicial en el botón y el cierre con Escape.
 */
@Component({
  selector: 'app-alert-host',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (notifications.activeAlert(); as a) {
      <div
        class="fixed inset-0 z-[2000] grid place-items-center bg-black/40 p-4"
        (keydown.escape)="notifications.dismissAlert()"
      >
        <div
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="app-alert-title"
          aria-describedby="app-alert-message"
          class="w-full max-w-md rounded-md border border-border-default bg-bg-surface p-6 shadow-xl"
        >
          <h2 id="app-alert-title" class="m-0 mb-2 text-lg font-semibold text-text-primary">
            {{ a.title }}
          </h2>
          <p id="app-alert-message" class="m-0 mb-5 text-sm text-text-secondary">{{ a.message }}</p>
          <div class="flex justify-end">
            <button
              #aceptar
              type="button"
              class="min-h-[44px] rounded-md bg-accent-primary px-4 py-2 text-sm font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover"
              (click)="notifications.dismissAlert()"
            >
              Aceptar
            </button>
          </div>
        </div>
      </div>
    }
  `,
})
export class AlertHostComponent {
  readonly notifications = inject(NotificationService);
  private readonly aceptar = viewChild<ElementRef<HTMLButtonElement>>('aceptar');

  constructor() {
    // Al abrirse, el foco pasa al botón: sin esto queda en el elemento que
    // disparó la acción, detrás del overlay, y el Escape del contenedor nunca
    // recibe la tecla.
    effect(() => this.aceptar()?.nativeElement.focus());
  }
}

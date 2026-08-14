import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  effect,
  inject,
  viewChild,
} from '@angular/core';

import { ConfirmDialogService } from './confirm-dialog.service';

/**
 * Host del Alert modal de confirmación (`design-system.md` §Alert, §12).
 * Mismo criterio de accesibilidad que `AlertHostComponent`: el overlay bloquea
 * la pantalla, así que tiene que anunciarse como diálogo, recibir el foco y
 * poder cerrarse con Escape. Escape equivale a **cancelar**, nunca a confirmar.
 */
@Component({
  selector: 'app-confirm-dialog-host',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (dialog.active(); as d) {
      <div
        class="fixed inset-0 z-[2000] grid place-items-center bg-black/40 p-4"
        (keydown.escape)="dialog.resolve(false)"
      >
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="app-confirm-title"
          aria-describedby="app-confirm-message"
          class="w-full max-w-md rounded-lg border border-border-default bg-bg-surface p-6 shadow-xl"
        >
          <h2 id="app-confirm-title" class="m-0 mb-2 text-lg font-semibold text-text-primary">
            {{ d.title }}
          </h2>
          <p id="app-confirm-message" class="m-0 mb-5 text-sm text-text-secondary">
            {{ d.message }}
          </p>
          <div class="flex flex-col-reverse justify-end gap-2 sm:flex-row">
            @if (d.tone === 'danger') {
              <button
                type="button"
                class="min-h-[44px] rounded-md px-4 py-2 text-sm font-semibold text-alert-critical [&:hover:not(:disabled)]:bg-black/5"
                (click)="dialog.resolve(true)"
              >
                {{ d.confirmLabel ?? 'Confirmar' }}
              </button>
              <button
                #inicial
                type="button"
                class="min-h-[44px] rounded-md bg-accent-primary px-4 py-2 text-sm font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover"
                (click)="dialog.resolve(false)"
              >
                {{ d.cancelLabel ?? 'Cancelar' }}
              </button>
            } @else {
              <button
                type="button"
                class="min-h-[44px] rounded-md border border-accent-primary px-4 py-2 text-sm font-semibold text-accent-primary"
                (click)="dialog.resolve(false)"
              >
                {{ d.cancelLabel ?? 'Cancelar' }}
              </button>
              <button
                #inicial
                type="button"
                class="min-h-[44px] rounded-md bg-accent-primary px-4 py-2 text-sm font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover"
                (click)="dialog.resolve(true)"
              >
                {{ d.confirmLabel ?? 'Aceptar' }}
              </button>
            }
          </div>
        </div>
      </div>
    }
  `,
})
export class ConfirmDialogHostComponent {
  readonly dialog = inject(ConfirmDialogService);
  // El foco inicial va siempre al botón **no destructivo**: en tono `danger`
  // ese es Cancelar, no Confirmar.
  private readonly inicial = viewChild<ElementRef<HTMLButtonElement>>('inicial');

  constructor() {
    effect(() => this.inicial()?.nativeElement.focus());
  }
}

import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { NotificationService } from './notification.service';

@Component({
  selector: 'app-alert-host',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (notifications.activeAlert(); as a) {
      <div class="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
        <div class="w-full max-w-md rounded-lg border border-border-default bg-bg-surface p-6 shadow-xl">
          <h2 class="m-0 mb-2 text-lg font-semibold text-text-primary">{{ a.title }}</h2>
          <p class="m-0 mb-5 text-sm text-text-secondary">{{ a.message }}</p>
          <div class="flex justify-end">
            <button
              type="button"
              class="rounded-md bg-accent-primary px-4 py-2 text-sm font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover"
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
}

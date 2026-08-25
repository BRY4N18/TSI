import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { TablerIconComponent, TablerIconName } from '../ui/icon/tabler-icon.component';
import { NotificationService, ToastTone } from './notification.service';

const TONE_ICON: Record<ToastTone, TablerIconName> = {
  critical: 'alert-octagon',
  urgent: 'alert-triangle',
  warning: 'alert-circle',
  success: 'circle-check',
  info: 'info-circle',
};

@Component({
  selector: 'app-toast-host',
  standalone: true,
  imports: [TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="pointer-events-none fixed inset-x-4 bottom-4 z-[2000] flex flex-col items-stretch gap-2 sm:inset-x-auto sm:right-4 sm:w-[360px]"
      aria-live="polite"
      aria-relevant="additions"
    >
      @for (t of notifications.toasts(); track t.id) {
        <div
          class="tsi-toast pointer-events-auto"
          [class.tsi-toast--success]="t.tone === 'success'"
          [class.tsi-toast--info]="t.tone === 'info'"
          [class.tsi-toast--warning]="t.tone === 'warning'"
          [class.tsi-toast--urgent]="t.tone === 'urgent'"
          [class.tsi-toast--critical]="t.tone === 'critical'"
          role="status"
          data-testid="app-toast"
          [attr.data-tone]="t.tone"
        >
          <span class="tsi-toast__icon" aria-hidden="true">
            <app-tabler-icon [name]="toneIcon[t.tone]" [size]="18" />
          </span>
          <span class="min-w-0 flex-1 text-text-primary">{{ t.message }}</span>
          @if (t.actionLabel && t.onAction) {
            <button
              type="button"
              class="shrink-0 text-sm font-semibold text-accent-primary hover:text-accent-hover"
              (click)="t.onAction()"
            >
              {{ t.actionLabel }}
            </button>
          }
          <button
            type="button"
            class="shrink-0 text-text-secondary hover:text-text-primary"
            aria-label="Cerrar notificación"
            (click)="notifications.dismissToast(t.id)"
          >
            <app-tabler-icon name="x" [size]="16" />
          </button>
        </div>
      }
    </div>
  `,
})
export class ToastHostComponent {
  readonly notifications = inject(NotificationService);
  readonly toneIcon = TONE_ICON;
}

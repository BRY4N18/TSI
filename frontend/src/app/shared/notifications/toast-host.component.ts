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
    <div class="fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2 sm:max-w-[400px]">
      @for (t of notifications.toasts(); track t.id) {
        <div
          class="flex items-start gap-2 rounded-md border-l-4 bg-bg-surface p-3 text-sm shadow-md"
          [class.border-alert-critical]="t.tone === 'critical'"
          [class.text-alert-critical]="t.tone === 'critical'"
          [class.border-alert-urgent]="t.tone === 'urgent'"
          [class.text-alert-urgent]="t.tone === 'urgent'"
          [class.border-alert-warning]="t.tone === 'warning'"
          [class.text-alert-warning]="t.tone === 'warning'"
          [class.border-alert-success]="t.tone === 'success'"
          [class.text-alert-success]="t.tone === 'success'"
          [class.border-alert-info]="t.tone === 'info'"
          [class.text-alert-info]="t.tone === 'info'"
        >
          <app-tabler-icon [name]="toneIcon[t.tone]" [size]="18" />
          <span class="flex-1 text-text-primary">{{ t.message }}</span>
          <button
            type="button"
            class="text-text-secondary hover:text-text-primary"
            aria-label="Cerrar notificación"
            (click)="notifications.dismissToast(t.id)"
          >
            ×
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

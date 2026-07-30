import { Injectable, signal } from '@angular/core';

export type ToastTone = 'critical' | 'urgent' | 'warning' | 'success' | 'info';

export interface ToastMessage {
  id: number;
  message: string;
  tone: ToastTone;
  actionLabel?: string;
  onAction?: () => void;
}

export interface AlertMessage {
  title: string;
  message: string;
}

const AUTO_DISMISS_MS: Record<ToastTone, number> = {
  critical: 7000,
  urgent: 5500,
  warning: 5000,
  success: 5000,
  info: 5000,
};

const ACTION_TOAST_MS = 8000;

/**
 * Sistema de feedback global (Toast/Alert) según design-system.md §5.
 * Snackbar con [Deshacer] para CU-O32 / CU-O41 vía `toastWithAction`.
 */
@Injectable({ providedIn: 'root' })
export class NotificationService {
  private nextId = 1;

  readonly toasts = signal<ToastMessage[]>([]);
  readonly activeAlert = signal<AlertMessage | null>(null);

  toast(message: string, tone: ToastTone = 'info'): void {
    const id = this.nextId++;
    this.toasts.update((list) => [...list, { id, message, tone }]);
    setTimeout(() => this.dismissToast(id), AUTO_DISMISS_MS[tone]);
  }

  toastWithAction(
    message: string,
    tone: ToastTone,
    actionLabel: string,
    onAction: () => void,
  ): void {
    const id = this.nextId++;
    this.toasts.update((list) => [
      ...list,
      {
        id,
        message,
        tone,
        actionLabel,
        onAction: () => {
          this.dismissToast(id);
          onAction();
        },
      },
    ]);
    setTimeout(() => this.dismissToast(id), ACTION_TOAST_MS);
  }

  dismissToast(id: number): void {
    this.toasts.update((list) => list.filter((t) => t.id !== id));
  }

  alert(message: string, title = 'Atención'): void {
    this.activeAlert.set({ title, message });
  }

  dismissAlert(): void {
    this.activeAlert.set(null);
  }
}

import { Injectable, signal } from '@angular/core';

export type ToastTone = 'critical' | 'urgent' | 'warning' | 'success' | 'info';

export interface ToastMessage {
  id: number;
  message: string;
  tone: ToastTone;
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

/**
 * Sistema de feedback global (Toast/Alert) según design-system.md §5.
 * Snackbar con [Deshacer] queda pendiente hasta que exista un endpoint de
 * reversión para descarte (CU-O32) / fusión (CU-O41) — ver tasks.md.
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

import { Injectable, signal } from '@angular/core';

export interface ConfirmRequest {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  /** 'danger' = acción destructiva (design-system.md §Botones: confirmación en 2 pasos). */
  tone?: 'default' | 'danger';
}

/**
 * Alert modal de confirmación en 2 pasos (design-system.md §Alert, §Botones).
 * Reemplaza `window.confirm` nativo por el modal propio del sistema, con la
 * misma arquitectura signal-based que `NotificationService.alert`.
 */
@Injectable({ providedIn: 'root' })
export class ConfirmDialogService {
  readonly active = signal<ConfirmRequest | null>(null);
  private resolver: ((value: boolean) => void) | null = null;

  confirm(request: ConfirmRequest): Promise<boolean> {
    this.active.set(request);
    return new Promise<boolean>((resolve) => {
      this.resolver = resolve;
    });
  }

  resolve(value: boolean): void {
    this.active.set(null);
    this.resolver?.(value);
    this.resolver = null;
  }
}

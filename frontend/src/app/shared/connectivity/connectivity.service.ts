import { Injectable, OnDestroy, signal } from '@angular/core';

/**
 * Indicador de conexión según design-system.md §5 ("Indicador de
 * sincronización/conexión") — punto de estado + texto junto a módulos que
 * dependen de datos en tiempo real, y banner de resiliencia de captura en
 * campo (§2) para formularios del Técnico de Campo.
 */
@Injectable({ providedIn: 'root' })
export class ConnectivityService implements OnDestroy {
  readonly online = signal(navigator.onLine);

  private readonly handleOnline = () => this.online.set(true);
  private readonly handleOffline = () => this.online.set(false);

  constructor() {
    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);
  }

  ngOnDestroy(): void {
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
  }
}

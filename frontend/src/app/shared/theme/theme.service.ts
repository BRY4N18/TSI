import { Injectable, computed, effect, signal } from '@angular/core';

export type Theme = 'light' | 'dark';

export const THEME_STORAGE_KEY = 'tsi.theme';

/**
 * Persistencia por navegador/dispositivo (localStorage), no por cuenta de usuario en backend.
 * design-system.md §6 exige que el tema "no reinicie en cada sesión" — localStorage ya cumple
 * eso para un mismo dispositivo. No hay hoy endpoint de preferencias de usuario (el único
 * existente, PreferenciasData, es de notificaciones/alertas, no de tema visual) para sincronizar
 * entre dispositivos; si se agrega esa infraestructura, este servicio debe leer/escribir ahí
 * también, sin cambiar su API pública (theme/isDark/toggle/setTheme).
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly _theme = signal<Theme>(this.resolveInitialTheme());

  readonly theme = this._theme.asReadonly();
  readonly isDark = computed(() => this._theme() === 'dark');

  constructor() {
    effect(() => this.applyTheme(this._theme()));
  }

  toggle(): void {
    this._theme.set(this._theme() === 'dark' ? 'light' : 'dark');
  }

  setTheme(theme: Theme): void {
    this._theme.set(theme);
  }

  private resolveInitialTheme(): Theme {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') {
      return stored;
    }
    const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches;
    return prefersDark ? 'dark' : 'light';
  }

  private applyTheme(theme: Theme): void {
    document.documentElement.dataset['theme'] = theme;
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }
}

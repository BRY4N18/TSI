import { Injectable } from '@angular/core';

const STORAGE_KEY = 'tsi.alta-unidades.lista.lastId';

interface ListaSeleccionPayload {
  lastId: string | null;
  updatedAt?: string;
}

/**
 * Estado de UI (última fila activa en catálogo de flota).
 * No es dato de dominio — solo orientación del Proveedor (FR-UI-005).
 */
@Injectable({ providedIn: 'root' })
export class ListaSeleccionStorage {
  get(): string | null {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return null;
      }
      const parsed = JSON.parse(raw) as ListaSeleccionPayload | string;
      if (typeof parsed === 'string') {
        return parsed || null;
      }
      return parsed.lastId ?? null;
    } catch {
      return null;
    }
  }

  set(idunidademergencia: string): void {
    const payload: ListaSeleccionPayload = {
      lastId: idunidademergencia,
      updatedAt: new Date().toISOString(),
    };
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  }

  clear(): void {
    sessionStorage.removeItem(STORAGE_KEY);
  }
}

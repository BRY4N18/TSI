import { Injectable } from '@angular/core';

const STORAGE_KEY = 'tsi.accidentes.lista.lastId';

interface ListaSeleccionPayload {
  lastId: string | null;
  updatedAt?: string;
}

/**
 * Estado de UI (última fila activa en lista de accidentes).
 * No es dato de dominio — solo orientación del Operador (FR-007).
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

  set(idaccidente: string): void {
    const payload: ListaSeleccionPayload = {
      lastId: idaccidente,
      updatedAt: new Date().toISOString(),
    };
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  }

  clear(): void {
    sessionStorage.removeItem(STORAGE_KEY);
  }
}

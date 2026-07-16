import { Injectable } from '@angular/core';

const DRAFT_STORAGE_KEY = 'tsi.registro-accidente.draft';

@Injectable({ providedIn: 'root' })
export class RegistroAccidenteDraftService {
  guardar(value: unknown): void {
    try {
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(value));
    } catch {
      // localStorage no disponible (modo privado, cuota excedida, etc.) — no bloquea el registro.
    }
  }

  restaurar(): unknown | null {
    let raw: string | null = null;
    try {
      raw = localStorage.getItem(DRAFT_STORAGE_KEY);
    } catch {
      return null;
    }
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw);
    } catch {
      // Borrador corrupto — se ignora silenciosamente.
      return null;
    }
  }

  limpiar(): void {
    try {
      localStorage.removeItem(DRAFT_STORAGE_KEY);
    } catch {
      // No-op si localStorage no está disponible.
    }
  }
}

import { Injectable } from '@angular/core';

import {
  OfflineFotoRecord,
  OfflineNotaRecord,
  TipoNotaCampo,
} from './models/evidencia-unidad.types';

const DB_NAME = 'tsi-evidencia-offline';
const DB_VERSION = 1;
const FOTOS_STORE = 'fotos_pendientes';
const NOTAS_STORE = 'notas_pendientes';

@Injectable({ providedIn: 'root' })
export class EvidenciaOfflineStoreService {
  private dbPromise: Promise<IDBDatabase> | null = null;

  async guardarFotoPendiente(
    idaccidente: string,
    blob: Blob,
    contentType: string,
    fechahora: number,
    localId: string = crypto.randomUUID(),
  ): Promise<OfflineFotoRecord> {
    const record: OfflineFotoRecord = {
      local_id: localId,
      idaccidente,
      blob,
      content_type: contentType,
      fechahora,
      object_url: URL.createObjectURL(blob),
    };
    await this.put(FOTOS_STORE, record);
    return record;
  }

  async guardarNotaPendiente(
    idaccidente: string,
    nota: string,
    tipo: TipoNotaCampo,
    fechahora: number,
    localId: string = crypto.randomUUID(),
  ): Promise<OfflineNotaRecord> {
    const record: OfflineNotaRecord = {
      local_id: localId,
      idaccidente,
      nota,
      tipo,
      fechahora,
    };
    await this.put(NOTAS_STORE, record);
    return record;
  }

  async listarPendientes(idaccidente: string): Promise<{
    fotos: OfflineFotoRecord[];
    notas: OfflineNotaRecord[];
  }> {
    const [fotos, notas] = await Promise.all([
      this.listByAccidente<OfflineFotoRecord>(FOTOS_STORE, idaccidente),
      this.listByAccidente<OfflineNotaRecord>(NOTAS_STORE, idaccidente),
    ]);
    return { fotos, notas };
  }

  async eliminarFoto(localId: string): Promise<void> {
    const record = await this.get<OfflineFotoRecord>(FOTOS_STORE, localId);
    if (record?.object_url) {
      URL.revokeObjectURL(record.object_url);
    }
    await this.delete(FOTOS_STORE, localId);
  }

  async eliminarNota(localId: string): Promise<void> {
    await this.delete(NOTAS_STORE, localId);
  }

  async contarPendientes(idaccidente: string): Promise<number> {
    const { fotos, notas } = await this.listarPendientes(idaccidente);
    return fotos.length + notas.length;
  }

  async listarIdsAccidentesPendientes(): Promise<string[]> {
    const [fotos, notas] = await Promise.all([
      this.listAll<OfflineFotoRecord>(FOTOS_STORE),
      this.listAll<OfflineNotaRecord>(NOTAS_STORE),
    ]);
    const ids = new Set<string>();
    for (const row of [...fotos, ...notas]) {
      ids.add(row.idaccidente);
    }
    return Array.from(ids);
  }

  private openDb(): Promise<IDBDatabase> {
    if (this.dbPromise) {
      return this.dbPromise;
    }

    this.dbPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onerror = () => reject(request.error ?? new Error('IndexedDB open failed'));
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(FOTOS_STORE)) {
          db.createObjectStore(FOTOS_STORE, { keyPath: 'local_id' });
        }
        if (!db.objectStoreNames.contains(NOTAS_STORE)) {
          db.createObjectStore(NOTAS_STORE, { keyPath: 'local_id' });
        }
      };
      request.onsuccess = () => resolve(request.result);
    });

    return this.dbPromise;
  }

  private async put<T extends { local_id: string }>(storeName: string, record: T): Promise<void> {
    const db = await this.openDb();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error ?? new Error('IndexedDB write failed'));
      tx.objectStore(storeName).put(record);
    });
  }

  private async get<T>(storeName: string, localId: string): Promise<T | undefined> {
    const db = await this.openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const request = tx.objectStore(storeName).get(localId);
      request.onsuccess = () => resolve(request.result as T | undefined);
      request.onerror = () => reject(request.error ?? new Error('IndexedDB read failed'));
    });
  }

  private async delete(storeName: string, localId: string): Promise<void> {
    const db = await this.openDb();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error ?? new Error('IndexedDB delete failed'));
      tx.objectStore(storeName).delete(localId);
    });
  }

  private async listByAccidente<T extends { idaccidente: string }>(
    storeName: string,
    idaccidente: string,
  ): Promise<T[]> {
    const rows = await this.listAll<T>(storeName);
    return rows.filter((row) => row.idaccidente === idaccidente);
  }

  private async listAll<T>(storeName: string): Promise<T[]> {
    const db = await this.openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const request = tx.objectStore(storeName).getAll();
      request.onsuccess = () => resolve(request.result as T[]);
      request.onerror = () => reject(request.error ?? new Error('IndexedDB list failed'));
    });
  }
}

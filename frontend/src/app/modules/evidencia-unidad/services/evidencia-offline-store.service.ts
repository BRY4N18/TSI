import { Injectable } from '@angular/core';

import {
  ConductorPayload,
  DecryptedConductorPendiente,
  DecryptedImplicadoPendiente,
  OfflineClimaRecord,
  OfflineConductorRecord,
  OfflineFisicoRecord,
  OfflineFotoRecord,
  OfflineImplicadoRecord,
  OfflineNotaRecord,
  RegistrarImplicadoRequest,
  TipoNotaCampo,
  VehiculoPayload,
} from './models/evidencia-unidad.types';

const DB_NAME = 'tsi-evidencia-offline';
const DB_VERSION = 3;
const FOTOS_STORE = 'fotos_pendientes';
const NOTAS_STORE = 'notas_pendientes';
const CLIMA_STORE = 'clima_pendientes';
const FISICO_STORE = 'fisico_pendientes';
const CONDUCTOR_STORE = 'conductor_pendientes';
const IMPLICADO_STORE = 'implicado_pendientes';
const PII_KEY_STORAGE = 'tsi-evidencia-pii-session-key';

@Injectable({ providedIn: 'root' })
export class EvidenciaOfflineStoreService {
  private dbPromise: Promise<IDBDatabase> | null = null;
  private cryptoKeyPromise: Promise<CryptoKey> | null = null;

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

  async guardarClimaPendiente(
    idaccidente: string,
    idperiododia: number | null,
    idestadoclima: number | null,
    fechahora: number = Date.now(),
    localId: string = crypto.randomUUID(),
  ): Promise<OfflineClimaRecord> {
    const record: OfflineClimaRecord = {
      local_id: localId,
      idaccidente,
      idperiododia,
      idestadoclima,
      fechahora,
    };
    await this.put(CLIMA_STORE, record);
    return record;
  }

  async guardarFisicoPendiente(
    idaccidente: string,
    idelementofisico: number,
    fechahora: number = Date.now(),
    localId: string = crypto.randomUUID(),
  ): Promise<OfflineFisicoRecord> {
    const record: OfflineFisicoRecord = {
      local_id: localId,
      idaccidente,
      idelementofisico,
      fechahora,
    };
    await this.put(FISICO_STORE, record);
    return record;
  }

  async guardarConductorPendiente(
    idaccidente: string,
    conductor: ConductorPayload,
    idestadoconductor: number,
    vehiculo: VehiculoPayload,
    fechahora: number = Date.now(),
    localId: string = crypto.randomUUID(),
  ): Promise<OfflineConductorRecord> {
    const { ciphertext, iv } = await this.encryptPii({
      identificacion: conductor.identificacion,
      nombres: conductor.nombres,
      apellidos: conductor.apellidos,
      genero: conductor.genero ?? null,
      tipolicencia: conductor.tipolicencia ?? null,
      estadolicencia: conductor.estadolicencia ?? null,
      ciudadresidencia: conductor.ciudadresidencia ?? null,
      aniosexperiencia: conductor.aniosexperiencia ?? null,
    });
    const record: OfflineConductorRecord = {
      local_id: localId,
      idaccidente,
      idestadoconductor,
      tipovehiculo: vehiculo.tipovehiculo,
      modelovehiculo: vehiculo.modelovehiculo ?? null,
      ciphertext,
      iv,
      fechahora,
    };
    await this.put(CONDUCTOR_STORE, record);
    return record;
  }

  async guardarImplicadoPendiente(
    idaccidente: string,
    payload: RegistrarImplicadoRequest,
    fechahora: number = Date.now(),
    localId: string = crypto.randomUUID(),
  ): Promise<OfflineImplicadoRecord> {
    const record: OfflineImplicadoRecord = {
      local_id: localId,
      idaccidente,
      tipoimplicado: payload.tipoimplicado,
      estadoimplicado: payload.estadoimplicado,
      genero: payload.genero ?? null,
      edad: payload.edad ?? null,
      fechahora,
    };
    await this.put(IMPLICADO_STORE, record);
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

  async listarEnriquecimientoPendiente(idaccidente: string): Promise<{
    clima: OfflineClimaRecord | null;
    elementos_fisicos: OfflineFisicoRecord[];
    conductores: DecryptedConductorPendiente[];
    implicados: DecryptedImplicadoPendiente[];
  }> {
    const [climas, fisicos, encrypted, encryptedImp] = await Promise.all([
      this.listByAccidente<OfflineClimaRecord>(CLIMA_STORE, idaccidente),
      this.listByAccidente<OfflineFisicoRecord>(FISICO_STORE, idaccidente),
      this.listByAccidente<OfflineConductorRecord>(CONDUCTOR_STORE, idaccidente),
      this.listByAccidente<OfflineImplicadoRecord>(IMPLICADO_STORE, idaccidente),
    ]);
    const conductores: DecryptedConductorPendiente[] = [];
    for (const row of encrypted) {
      const pii = await this.decryptPii(row.ciphertext, row.iv);
      conductores.push({
        local_id: row.local_id,
        idaccidente: row.idaccidente,
        idestadoconductor: row.idestadoconductor,
        conductor: pii,
        vehiculo: {
          tipovehiculo: row.tipovehiculo,
          modelovehiculo: row.modelovehiculo ?? null,
        },
        fechahora: row.fechahora,
      });
    }
    const implicados: DecryptedImplicadoPendiente[] = encryptedImp.map((row) => ({
      local_id: row.local_id,
      idaccidente: row.idaccidente,
      payload: {
        tipoimplicado: row.tipoimplicado,
        estadoimplicado: row.estadoimplicado,
        genero: row.genero,
        edad: row.edad,
      },
      fechahora: row.fechahora,
    }));
    return {
      clima: climas.sort((a, b) => b.fechahora - a.fechahora)[0] ?? null,
      elementos_fisicos: fisicos,
      conductores,
      implicados,
    };
  }

  /** Lectura cruda para tests de no-persistencia PII en claro. */
  async listarConductoresCifradosRaw(idaccidente: string): Promise<OfflineConductorRecord[]> {
    return this.listByAccidente<OfflineConductorRecord>(CONDUCTOR_STORE, idaccidente);
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

  async eliminarClima(localId: string): Promise<void> {
    await this.delete(CLIMA_STORE, localId);
  }

  async eliminarFisico(localId: string): Promise<void> {
    await this.delete(FISICO_STORE, localId);
  }

  async eliminarConductor(localId: string): Promise<void> {
    await this.delete(CONDUCTOR_STORE, localId);
  }

  async eliminarImplicado(localId: string): Promise<void> {
    await this.delete(IMPLICADO_STORE, localId);
  }

  async contarPendientes(idaccidente: string): Promise<number> {
    const { fotos, notas } = await this.listarPendientes(idaccidente);
    const enrich = await this.listarEnriquecimientoPendiente(idaccidente);
    return (
      fotos.length +
      notas.length +
      (enrich.clima ? 1 : 0) +
      enrich.elementos_fisicos.length +
      enrich.conductores.length +
      enrich.implicados.length
    );
  }

  async listarIdsAccidentesPendientes(): Promise<string[]> {
    const [fotos, notas, climas, fisicos, conductores, implicados] = await Promise.all([
      this.listAll<OfflineFotoRecord>(FOTOS_STORE),
      this.listAll<OfflineNotaRecord>(NOTAS_STORE),
      this.listAll<OfflineClimaRecord>(CLIMA_STORE),
      this.listAll<OfflineFisicoRecord>(FISICO_STORE),
      this.listAll<OfflineConductorRecord>(CONDUCTOR_STORE),
      this.listAll<OfflineImplicadoRecord>(IMPLICADO_STORE),
    ]);
    const ids = new Set<string>();
    for (const row of [...fotos, ...notas, ...climas, ...fisicos, ...conductores, ...implicados]) {
      ids.add(row.idaccidente);
    }
    return Array.from(ids);
  }

  private async getCryptoKey(): Promise<CryptoKey> {
    if (this.cryptoKeyPromise) {
      return this.cryptoKeyPromise;
    }
    this.cryptoKeyPromise = (async () => {
      const existing = sessionStorage.getItem(PII_KEY_STORAGE);
      if (existing) {
        const raw = Uint8Array.from(atob(existing), (c) => c.charCodeAt(0));
        return crypto.subtle.importKey('raw', raw, 'AES-GCM', false, [
          'encrypt',
          'decrypt',
        ]);
      }
      const key = await crypto.subtle.generateKey(
        { name: 'AES-GCM', length: 256 },
        true,
        ['encrypt', 'decrypt'],
      );
      const exported = await crypto.subtle.exportKey('raw', key);
      sessionStorage.setItem(
        PII_KEY_STORAGE,
        btoa(String.fromCharCode(...new Uint8Array(exported))),
      );
      return key;
    })();
    return this.cryptoKeyPromise;
  }

  private async encryptPii(payload: ConductorPayload): Promise<{ ciphertext: string; iv: string }> {
    const key = await this.getCryptoKey();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encoded = new TextEncoder().encode(JSON.stringify(payload));
    const cipherBuf = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, encoded);
    return {
      ciphertext: btoa(String.fromCharCode(...new Uint8Array(cipherBuf))),
      iv: btoa(String.fromCharCode(...iv)),
    };
  }

  private async decryptPii(ciphertext: string, ivB64: string): Promise<ConductorPayload> {
    const key = await this.getCryptoKey();
    const iv = Uint8Array.from(atob(ivB64), (c) => c.charCodeAt(0));
    const data = Uint8Array.from(atob(ciphertext), (c) => c.charCodeAt(0));
    const plainBuf = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, data);
    return JSON.parse(new TextDecoder().decode(plainBuf)) as ConductorPayload;
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
        for (const store of [
          FOTOS_STORE,
          NOTAS_STORE,
          CLIMA_STORE,
          FISICO_STORE,
          CONDUCTOR_STORE,
          IMPLICADO_STORE,
        ]) {
          if (!db.objectStoreNames.contains(store)) {
            db.createObjectStore(store, { keyPath: 'local_id' });
          }
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
      tx.objectStore(storeName).put(record);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error ?? new Error('IndexedDB put failed'));
    });
  }

  private async get<T>(storeName: string, localId: string): Promise<T | undefined> {
    const db = await this.openDb();
    return new Promise<T | undefined>((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const req = tx.objectStore(storeName).get(localId);
      req.onsuccess = () => resolve(req.result as T | undefined);
      req.onerror = () => reject(req.error ?? new Error('IndexedDB get failed'));
    });
  }

  private async delete(storeName: string, localId: string): Promise<void> {
    const db = await this.openDb();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      tx.objectStore(storeName).delete(localId);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error ?? new Error('IndexedDB delete failed'));
    });
  }

  private async listByAccidente<T extends { idaccidente: string }>(
    storeName: string,
    idaccidente: string,
  ): Promise<T[]> {
    const all = await this.listAll<T>(storeName);
    return all.filter((row) => row.idaccidente === idaccidente);
  }

  private async listAll<T>(storeName: string): Promise<T[]> {
    const db = await this.openDb();
    return new Promise<T[]>((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const req = tx.objectStore(storeName).getAll();
      req.onsuccess = () => resolve((req.result as T[]) ?? []);
      req.onerror = () => reject(req.error ?? new Error('IndexedDB getAll failed'));
    });
  }
}

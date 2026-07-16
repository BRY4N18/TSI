import { Injectable, OnDestroy, inject } from '@angular/core';
import { Subject, filter, from, fromEvent, merge, switchMap, takeUntil } from 'rxjs';

import { EvidenciaApiService } from './evidencia-api.service';
import { EvidenciaOfflineStoreService } from './evidencia-offline-store.service';

@Injectable({ providedIn: 'root' })
export class EvidenciaSyncSchedulerService implements OnDestroy {
  private readonly evidenciaApi = inject(EvidenciaApiService);
  private readonly offlineStore = inject(EvidenciaOfflineStoreService);
  private readonly destroy$ = new Subject<void>();
  private casosMonitoreados = new Set<string>();
  private autoSyncIniciado = false;

  iniciarAutoSync(): void {
    if (this.autoSyncIniciado) {
      return;
    }
    this.autoSyncIniciado = true;

    const online$ = fromEvent(window, 'online');

    merge(online$)
      .pipe(
        filter(() => navigator.onLine),
        switchMap(() => from(this.sincronizarTodosLosCasos())),
        takeUntil(this.destroy$),
      )
      .subscribe();

    if (navigator.onLine) {
      void this.sincronizarTodosLosCasos();
    }
  }

  registrarCaso(idaccidente: string): void {
    this.casosMonitoreados.add(idaccidente);
    if (navigator.onLine) {
      this.evidenciaApi.sincronizarPendientes(idaccidente).subscribe();
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private async sincronizarTodosLosCasos(): Promise<void> {
    const pendientes = await this.offlineStore.listarIdsAccidentesPendientes();
    const casos = new Set([...this.casosMonitoreados, ...pendientes]);
    for (const idaccidente of casos) {
      await new Promise<void>((resolve) => {
        this.evidenciaApi.sincronizarPendientes(idaccidente).subscribe({
          next: () => resolve(),
          error: () => resolve(),
        });
      });
    }
  }
}

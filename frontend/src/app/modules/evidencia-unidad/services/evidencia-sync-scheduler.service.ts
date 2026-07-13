import { Injectable, OnDestroy, inject } from '@angular/core';
import { Subject, filter, from, fromEvent, merge, switchMap, takeUntil } from 'rxjs';

import { EvidenciaApiService } from './evidencia-api.service';

@Injectable({ providedIn: 'root' })
export class EvidenciaSyncSchedulerService implements OnDestroy {
  private readonly evidenciaApi = inject(EvidenciaApiService);
  private readonly destroy$ = new Subject<void>();
  private casosMonitoreados = new Set<string>();

  iniciarAutoSync(): void {
    const online$ = fromEvent(window, 'online');

    merge(online$)
      .pipe(
        filter(() => navigator.onLine),
        switchMap(() => from(this.sincronizarTodosLosCasos())),
        takeUntil(this.destroy$),
      )
      .subscribe();
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
    const casos = Array.from(this.casosMonitoreados);
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

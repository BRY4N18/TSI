import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { estadoInfo } from '../../../accidentes/estado.constants';
import { estadoDespachoTono } from '../../despacho-tono.constants';
import { DespachoApiService } from '../../services/despacho-api.service';
import { DespachoSseService } from '../../services/despacho-sse.service';
import { EstadoDespachoData, IntentoDespacho } from '../../services/models/despacho.types';

type SyncStatus = 'live' | 'reconnecting' | 'offline';

const SYNC_LABEL: Record<SyncStatus, string> = {
  live: 'En vivo',
  reconnecting: 'Conectando…',
  offline: 'Sin conexión en vivo',
};

@Component({
  selector: 'app-monitoreo-despacho',
  standalone: true,
  imports: [RouterLink, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './monitoreo-despacho.page.html',
})
export class MonitoreoDespachoPage implements OnInit {
  private readonly api = inject(DespachoApiService);
  private readonly sse = inject(DespachoSseService);
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);

  idaccidente = '';
  readonly estado = signal<EstadoDespachoData | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly syncStatus = signal<SyncStatus>('reconnecting');
  readonly tiempoTranscurrido = signal(0);

  readonly estado_ = estadoInfo;
  readonly intentoTono = estadoDespachoTono;

  ngOnInit(): void {
    this.idaccidente = this.route.snapshot.paramMap.get('idaccidente') ?? '';
    this.cargar();
    this.conectarSse();

    const tick = setInterval(() => this.tiempoTranscurrido.update((v) => v + 1), 1000);
    this.destroyRef.onDestroy(() => clearInterval(tick));
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.obtenerEstado(this.idaccidente).subscribe({
      next: (res) => {
        this.estado.set(res.data);
        this.tiempoTranscurrido.set(res.data.tiempo_transcurrido_seg);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar el estado del despacho.');
        this.loading.set(false);
      },
    });
  }

  private conectarSse(): void {
    this.sse
      .streamDespacho(this.idaccidente)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.syncStatus.set('live');
          this.cargar();
        },
        error: () => this.syncStatus.set('offline'),
      });
  }

  syncLabel(status: SyncStatus): string {
    return SYNC_LABEL[status];
  }

  ordenados(intentos: IntentoDespacho[]): IntentoDespacho[] {
    return [...intentos].sort((a, b) => b.fechahoradespacho - a.fechahoradespacho);
  }

  formatTiempo(segundos: number): string {
    const h = Math.floor(segundos / 3600)
      .toString()
      .padStart(2, '0');
    const m = Math.floor((segundos % 3600) / 60)
      .toString()
      .padStart(2, '0');
    const s = Math.floor(segundos % 60)
      .toString()
      .padStart(2, '0');
    return `${h}:${m}:${s}`;
  }
}

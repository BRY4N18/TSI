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
  template: `
    <div class="mx-auto max-w-4xl p-8">
      <a
        routerLink="/despacho/monitoreo"
        class="mb-6 inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-text-primary"
      >
        <app-tabler-icon name="arrow-left" [size]="16" />
        Volver al monitoreo
      </a>

      @if (loading()) {
        <div class="grid gap-2" data-testid="loading-skeleton">
          @for (i of [1, 2, 3]; track i) {
            <div class="h-16 animate-pulse rounded-lg bg-bg-surface"></div>
          }
        </div>
      } @else if (error()) {
        <div
          class="grid place-items-center gap-3 rounded-lg border border-alert-critical bg-alert-critical-bg p-10 text-center"
          data-testid="error-state"
        >
          <app-tabler-icon name="alert-triangle" [size]="32" />
          <p class="m-0 text-sm text-alert-critical">{{ error() }}</p>
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-md border border-alert-critical px-4 py-2 text-sm font-medium text-alert-critical hover:bg-alert-critical-bg"
            (click)="cargar()"
          >
            <app-tabler-icon name="refresh" [size]="16" />
            Reintentar
          </button>
        </div>
      } @else if (estado()) {
        @let e = estado()!;
        <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 class="m-0 mb-1 text-2xl font-bold text-text-primary">{{ idaccidente }}</h1>
            <span
              class="inline-flex items-center rounded-md px-3 py-1.5 text-sm font-semibold"
              [class.bg-alert-warning-bg]="estado_(e.estado_caso).tone === 'warning'"
              [class.text-alert-warning]="estado_(e.estado_caso).tone === 'warning'"
              [class.bg-alert-success-bg]="estado_(e.estado_caso).tone === 'success'"
              [class.text-alert-success]="estado_(e.estado_caso).tone === 'success'"
              [class.bg-alert-info-bg]="estado_(e.estado_caso).tone === 'info'"
              [class.text-alert-info]="estado_(e.estado_caso).tone === 'info'"
            >
              {{ estado_(e.estado_caso).label }}
            </span>
          </div>

          <div class="flex items-center gap-4">
            <div class="text-right">
              <p class="m-0 text-xs font-medium uppercase tracking-wide text-text-secondary">
                Tiempo transcurrido
              </p>
              <p class="m-0 font-mono text-lg font-semibold text-text-primary">
                {{ formatTiempo(tiempoTranscurrido()) }}
              </p>
            </div>
            <span class="flex items-center gap-1.5 text-xs font-medium text-text-secondary">
              <span
                class="h-2 w-2 rounded-full"
                [class.bg-alert-success]="syncStatus() === 'live'"
                [class.bg-alert-warning]="syncStatus() === 'reconnecting'"
                [class.bg-alert-critical]="syncStatus() === 'offline'"
              ></span>
              {{ syncLabel(syncStatus()) }}
            </span>
          </div>
        </div>

        @if (e.mensaje) {
          <div class="mb-4 rounded-md border border-alert-info bg-alert-info-bg px-4 py-3 text-sm text-alert-info">
            {{ e.mensaje }}
          </div>
        }

        <section class="mb-4 rounded-lg border border-border-default bg-bg-surface p-6">
          <h2 class="m-0 mb-4 text-base font-semibold text-text-primary">Unidades activas</h2>
          @if (!e.unidades_activas.length) {
            <p class="m-0 text-sm text-text-secondary">Todavía no hay ninguna unidad confirmada.</p>
          } @else {
            <ul class="m-0 grid gap-3">
              @for (u of e.unidades_activas; track u.iddespacho) {
                <li class="flex items-center justify-between gap-2 text-sm">
                  <div>
                    <p class="m-0 font-medium text-text-primary">{{ u.unidademergencia }}</p>
                    @if (u.tipounidademergencia) {
                      <p class="m-0 text-xs text-text-secondary">{{ u.tipounidademergencia }}</p>
                    }
                  </div>
                  <span
                    class="inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold"
                    [class.bg-alert-success-bg]="intentoTono(u.estado) === 'success'"
                    [class.text-alert-success]="intentoTono(u.estado) === 'success'"
                    [class.bg-alert-warning-bg]="intentoTono(u.estado) === 'warning'"
                    [class.text-alert-warning]="intentoTono(u.estado) === 'warning'"
                    [class.bg-alert-critical-bg]="intentoTono(u.estado) === 'critical'"
                    [class.text-alert-critical]="intentoTono(u.estado) === 'critical'"
                    [class.bg-alert-info-bg]="intentoTono(u.estado) === 'info'"
                    [class.text-alert-info]="intentoTono(u.estado) === 'info'"
                  >
                    {{ u.estado }}
                  </span>
                </li>
              }
            </ul>
          }
        </section>

        <section class="rounded-lg border border-border-default bg-bg-surface p-6">
          <h2 class="m-0 mb-4 text-base font-semibold text-text-primary">Historial de intentos</h2>
          @if (!e.intentos.length) {
            <p class="m-0 text-sm text-text-secondary">Todavía no se ha intentado despachar ninguna unidad.</p>
          } @else {
            <ol class="m-0 grid gap-4 border-l-2 border-border-default pl-4">
              @for (i of ordenados(e.intentos); track i.iddespacho) {
                <li class="relative text-sm">
                  <span
                    class="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full border-2 border-bg-surface"
                    [class.bg-alert-success]="intentoTono(i.estado) === 'success'"
                    [class.bg-alert-warning]="intentoTono(i.estado) === 'warning'"
                    [class.bg-alert-critical]="intentoTono(i.estado) === 'critical'"
                    [class.bg-alert-info]="intentoTono(i.estado) === 'info'"
                  ></span>
                  <div class="flex items-center justify-between gap-2">
                    <p class="m-0 font-medium text-text-primary">{{ i.unidademergencia }}</p>
                    <span
                      class="inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold"
                      [class.bg-alert-success-bg]="intentoTono(i.estado) === 'success'"
                      [class.text-alert-success]="intentoTono(i.estado) === 'success'"
                      [class.bg-alert-warning-bg]="intentoTono(i.estado) === 'warning'"
                      [class.text-alert-warning]="intentoTono(i.estado) === 'warning'"
                      [class.bg-alert-critical-bg]="intentoTono(i.estado) === 'critical'"
                      [class.text-alert-critical]="intentoTono(i.estado) === 'critical'"
                      [class.bg-alert-info-bg]="intentoTono(i.estado) === 'info'"
                      [class.text-alert-info]="intentoTono(i.estado) === 'info'"
                    >
                      {{ i.estado }}
                    </span>
                  </div>
                  <p class="m-0 mt-0.5 text-xs text-text-secondary">
                    {{ i.origen }}
                    @if (i.motivo) {
                      — {{ i.motivo }}
                    }
                  </p>
                </li>
              }
            </ol>
          }
        </section>
      }
    </div>
  `,
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

import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ConnectivityService } from '../../../../shared/connectivity/connectivity.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { EvidenciaApiService } from '../../services/evidencia-api.service';
import { EvidenciaSyncSchedulerService } from '../../services/evidencia-sync-scheduler.service';
import { EvidenciaFotoItem, EvidenciaItem } from '../../services/models/evidencia-unidad.types';
import { EvidenciaCapturaModal } from './evidencia-captura.modal';
import { EvidenciaVisorModal } from './evidencia-visor.modal';

@Component({
  selector: 'app-galeria-evidencias',
  standalone: true,
  imports: [RouterLink, DatePipe, TablerIconComponent, EvidenciaCapturaModal, EvidenciaVisorModal],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="mx-auto max-w-6xl p-8">
      <a
        [routerLink]="['/accidentes', idaccidente]"
        class="mb-6 inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-text-primary"
      >
        <app-tabler-icon name="arrow-left" [size]="16" />
        Volver al accidente
      </a>

      <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2">
            <h1 class="m-0 text-2xl font-bold text-text-primary">Galería de evidencias</h1>
            <span class="flex items-center gap-1.5 text-xs font-medium text-text-secondary" data-testid="conexion">
              <span
                class="h-2 w-2 rounded-full"
                [class.bg-alert-success]="connectivity.online()"
                [class.bg-text-secondary]="!connectivity.online()"
              ></span>
              {{ connectivity.online() ? 'En vivo' : 'Sin conexión' }}
            </span>
          </div>
          <p class="m-0 mt-1 text-sm text-text-secondary" data-testid="caso">
            Caso: {{ idaccidente }}
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          @if (items().length) {
            <span
              class="rounded-md bg-bg-page px-2.5 py-1 text-xs font-medium text-text-secondary"
            >
              {{ items().length }} elemento(s)
            </span>
          }
          <button
            type="button"
            (click)="mostrarSubida.set(!mostrarSubida())"
            class="inline-flex items-center gap-2 rounded-md bg-accent-primary px-4 py-2.5 text-sm font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover"
          >
            <app-tabler-icon name="camera" [size]="16" />
            Subir evidencia
          </button>
          <button
            type="button"
            (click)="recargar()"
            class="inline-flex items-center gap-2 rounded-md border border-border-default px-4 py-2 text-sm font-medium text-text-secondary hover:bg-bg-page"
          >
            <app-tabler-icon name="refresh" [size]="16" />
            Recargar
          </button>
          <button
            type="button"
            (click)="sincronizar()"
            [disabled]="sincronizando()"
            class="inline-flex items-center gap-2 rounded-md border border-border-default px-4 py-2 text-sm font-medium text-text-secondary hover:bg-bg-page disabled:cursor-not-allowed disabled:opacity-50"
          >
            @if (sincronizando()) {
              <app-tabler-icon name="refresh" [size]="16" class="animate-spin" />
              Sincronizando…
            } @else {
              Sincronizar pendientes
            }
          </button>
        </div>
      </div>

      @if (mostrarSubida()) {
        <app-evidencia-captura-modal
          [idaccidente]="idaccidente"
          (cerrar)="mostrarSubida.set(false)"
          (guardado)="onEvidenciaGuardada()"
        />
      }

      <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div class="grid gap-4 lg:col-span-2">
          @if (cargando()) {
            <div class="grid grid-cols-2 gap-3 sm:grid-cols-3" data-testid="loading-skeleton">
              @for (i of [1, 2, 3, 4, 5, 6]; track i) {
                <div class="aspect-square animate-pulse rounded-md bg-bg-surface"></div>
              }
            </div>
          } @else if (error()) {
            <div
              class="grid place-items-center gap-3 rounded-lg border border-alert-warning bg-alert-warning-bg p-10 text-center"
              data-testid="error"
            >
              <app-tabler-icon name="alert-triangle" [size]="32" />
              <p class="m-0 text-sm text-alert-warning">{{ error() }}</p>
              <button
                type="button"
                (click)="recargar()"
                class="inline-flex items-center gap-2 rounded-md border border-alert-warning px-4 py-2 text-sm font-medium text-alert-warning hover:bg-alert-warning-bg"
              >
                <app-tabler-icon name="refresh" [size]="16" />
                Reintentar
              </button>
            </div>
          } @else if (!fotos().length) {
            <div class="grid place-items-center gap-3 rounded-lg border border-border-default bg-bg-surface p-10 text-center">
              <app-tabler-icon name="camera" [size]="28" />
              <p class="m-0 text-sm text-text-secondary">Sin evidencia fotográfica todavía.</p>
              <button
                type="button"
                (click)="mostrarSubida.set(true)"
                class="inline-flex items-center gap-2 rounded-md bg-accent-primary px-4 py-2 text-sm font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover"
              >
                <app-tabler-icon name="camera" [size]="16" />
                Subir evidencia
              </button>
            </div>
          } @else {
            <div class="grid grid-cols-2 gap-3 sm:grid-cols-3" data-testid="galeria">
              @for (item of fotos(); track trackItem(item)) {
                @if (item.sincronizado) {
                  <button
                    type="button"
                    (click)="abrirVisor(item)"
                    class="relative overflow-hidden rounded-md border border-border-default focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-accent-primary"
                  >
                    <img
                      [src]="item.urlevidenciafoto"
                      alt="Evidencia fotográfica"
                      class="aspect-square w-full object-cover"
                    />
                    <span
                      class="absolute right-2 top-2 inline-flex items-center gap-1 rounded-md bg-alert-success-bg px-2 py-1 text-xs font-semibold text-alert-success"
                    >
                      <app-tabler-icon name="circle-check" [size]="14" />
                      Sincronizado
                    </span>
                  </button>
                } @else {
                  <div class="relative overflow-hidden rounded-md border border-border-default">
                    <img
                      [src]="item.urlevidenciafoto"
                      alt="Evidencia fotográfica"
                      class="aspect-square w-full object-cover"
                    />
                    <span
                      class="absolute right-2 top-2 inline-flex items-center gap-1 rounded-md bg-alert-warning-bg px-2 py-1 text-xs font-semibold text-alert-warning"
                    >
                      <em data-testid="pendiente" class="not-italic">Pendiente</em>
                    </span>
                  </div>
                }
              }
            </div>

            @if (fotoVisorIndice() !== null) {
              <app-evidencia-visor-modal
                [fotos]="fotosSincronizadas()"
                [indiceInicial]="fotoVisorIndice()!"
                (cerrar)="fotoVisorIndice.set(null)"
              />
            }
          }
        </div>

        <div class="grid gap-4">
          <div class="rounded-lg border border-border-default bg-bg-surface p-6">
            <div class="mb-4 flex items-center justify-between">
              <h2 class="m-0 text-base font-semibold text-text-primary">Notas de campo</h2>
              <button
                type="button"
                (click)="mostrarSubida.set(!mostrarSubida())"
                aria-label="Agregar nota de campo"
                class="inline-flex h-7 w-7 items-center justify-center rounded-md border border-border-default text-text-secondary hover:bg-bg-page"
              >
                +
              </button>
            </div>

            @if (!notas().length) {
              <p class="m-0 text-sm text-text-secondary">Sin notas de campo todavía.</p>
            } @else {
              <ul class="m-0 grid gap-4 border-l-2 border-border-default pl-4">
                @for (item of notas(); track trackItem(item)) {
                  <li class="relative">
                    <span
                      class="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full border-2 border-bg-surface bg-accent-primary"
                    ></span>
                    <div class="flex items-center justify-between gap-2">
                      <span class="text-xs font-medium uppercase tracking-wide text-text-secondary">
                        {{ item.tipo }}
                      </span>
                      @if (!item.sincronizado) {
                        <span
                          class="inline-flex items-center rounded-md bg-alert-warning-bg px-2 py-1 text-xs font-semibold text-alert-warning"
                          data-testid="pendiente"
                        >
                          Pendiente
                        </span>
                      }
                    </div>
                    <p class="m-0 mt-1 text-sm text-text-primary">{{ item.nota }}</p>
                    <span class="text-xs text-text-secondary">
                      {{ item.fechahora | date: 'dd/MM/yyyy HH:mm' }}
                    </span>
                  </li>
                }
              </ul>
            }
          </div>
        </div>
      </div>
    </div>
  `,
})
export class GaleriaEvidenciasPage implements OnInit {
  readonly evidenciaApi = inject(EvidenciaApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly syncScheduler = inject(EvidenciaSyncSchedulerService);
  private readonly notifications = inject(NotificationService);
  readonly connectivity = inject(ConnectivityService);

  idaccidente = '';
  readonly items = signal<EvidenciaItem[]>([]);
  readonly error = signal('');
  readonly cargando = signal(true);
  readonly sincronizando = signal(false);
  readonly mostrarSubida = signal(false);
  readonly fotoVisorIndice = signal<number | null>(null);

  fotos() {
    return this.items().filter((item) => this.evidenciaApi.isFotoItem(item));
  }

  fotosSincronizadas(): EvidenciaFotoItem[] {
    return this.fotos().filter((item): item is EvidenciaFotoItem => item.sincronizado);
  }

  notas() {
    return this.items().filter((item) => this.evidenciaApi.isNotaItem(item));
  }

  abrirVisor(item: EvidenciaFotoItem): void {
    const indice = this.fotosSincronizadas().indexOf(item);
    if (indice !== -1) {
      this.fotoVisorIndice.set(indice);
    }
  }

  ngOnInit(): void {
    this.idaccidente = this.route.snapshot.paramMap.get('idaccidente') ?? '';
    this.syncScheduler.registrarCaso(this.idaccidente);
    this.recargar();
  }

  onEvidenciaGuardada(): void {
    this.mostrarSubida.set(false);
    this.recargar();
  }

  recargar(): void {
    this.error.set('');
    this.cargando.set(true);
    this.evidenciaApi.listarConPendientesLocales(this.idaccidente).subscribe({
      next: (items) => {
        this.items.set(items);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar la galería');
        this.cargando.set(false);
      },
    });
  }

  sincronizar(): void {
    this.sincronizando.set(true);
    this.evidenciaApi.sincronizarPendientes(this.idaccidente).subscribe({
      next: (res) => {
        this.notifications.toast(
          `Sincronizados: ${res.data.sincronizados}, pendientes: ${res.data.pendientes}`,
          'success',
        );
        this.sincronizando.set(false);
        this.recargar();
      },
      error: () => {
        this.sincronizando.set(false);
        this.notifications.alert('No se pudo sincronizar la evidencia pendiente.', 'Error al sincronizar');
      },
    });
  }

  trackItem(item: EvidenciaItem): string | number {
    if ('local_id' in item) {
      return item.local_id;
    }
    if ('idevidenciafoto' in item) {
      return item.idevidenciafoto;
    }
    return item.idnotaaccidentes;
  }
}

import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { catchError, of } from 'rxjs';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { AccidenteApiService } from '../../services/accidente-api.service';
import { AccidenteDetalle } from '../../services/models/accidente.types';
import { SEVERIDAD_INFO, SeveridadInfo } from '../../severidad.constants';
import { estadoInfo } from '../../estado.constants';
import { EscalarSeveridadPanel } from './escalar-severidad.panel';
import { EvidenciaApiService } from '../../../evidencia-unidad/services/evidencia-api.service';
import { EvidenciaFotoItem } from '../../../evidencia-unidad/services/models/evidencia-unidad.types';
import { estadoDespachoTono } from '../../../despacho/despacho-tono.constants';
import { DespachoApiService } from '../../../despacho/services/despacho-api.service';
import { IntentoDespacho } from '../../../despacho/services/models/despacho.types';

@Component({
  selector: 'app-detalle-accidente',
  standalone: true,
  imports: [RouterLink, FormsModule, EscalarSeveridadPanel, TablerIconComponent, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="mx-auto max-w-6xl p-8">
      <a
        routerLink="/accidentes/lista"
        class="mb-6 inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-text-primary"
      >
        <app-tabler-icon name="arrow-left" [size]="16" />
        Volver a la lista
      </a>

      @if (loading()) {
        <div class="mt-4 grid gap-2" data-testid="loading-skeleton">
          @for (i of [1, 2, 3]; track i) {
            <div class="h-16 animate-pulse rounded-lg bg-bg-surface"></div>
          }
        </div>
      } @else if (loadError()) {
        <div
          class="mt-4 grid place-items-center gap-3 rounded-lg border border-alert-critical bg-alert-critical-bg p-10 text-center"
          data-testid="error-state"
        >
          <app-tabler-icon name="alert-triangle" [size]="32" />
          <p class="m-0 text-sm text-alert-critical">{{ loadError() }}</p>
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-md border border-alert-critical px-4 py-2 text-sm font-medium text-alert-critical hover:bg-alert-critical-bg"
            (click)="cargar()"
          >
            <app-tabler-icon name="refresh" [size]="16" />
            Reintentar
          </button>
        </div>
      } @else if (accidente()) {
        @let a = accidente()!;
        <div class="mt-4 flex items-center justify-between">
          <h1 class="m-0 text-2xl font-bold text-text-primary">{{ a.idaccidente }}</h1>
          <span
            class="inline-flex items-center rounded-md px-3 py-1.5 text-sm font-semibold"
            [class.bg-alert-success-bg]="estado(a.estado_actual).tone === 'success'"
            [class.text-alert-success]="estado(a.estado_actual).tone === 'success'"
            [class.bg-alert-warning-bg]="estado(a.estado_actual).tone === 'warning'"
            [class.text-alert-warning]="estado(a.estado_actual).tone === 'warning'"
            [class.bg-alert-urgent-bg]="estado(a.estado_actual).tone === 'urgent'"
            [class.text-alert-urgent]="estado(a.estado_actual).tone === 'urgent'"
            [class.bg-alert-info-bg]="estado(a.estado_actual).tone === 'info'"
            [class.text-alert-info]="estado(a.estado_actual).tone === 'info'"
          >
            {{ estado(a.estado_actual).label }}
          </span>
        </div>

        <div class="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <!-- Columna principal: datos del caso -->
          <div class="grid gap-4 lg:col-span-2">
            <section class="rounded-lg border border-border-default bg-bg-surface p-6">
              <h2 class="m-0 mb-4 text-base font-semibold text-text-primary">Información del incidente</h2>
              <dl class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Severidad</dt>
                  <dd class="mt-1 flex items-center gap-1.5 text-sm font-medium">
                    <span
                      [class.text-alert-success]="severidad(a.idseveridad).tone === 'success'"
                      [class.text-alert-warning]="severidad(a.idseveridad).tone === 'warning'"
                      [class.text-alert-urgent]="severidad(a.idseveridad).tone === 'urgent'"
                      [class.text-alert-critical]="severidad(a.idseveridad).tone === 'critical'"
                      class="inline-flex items-center gap-1.5"
                    >
                      <app-tabler-icon [name]="severidad(a.idseveridad).icon" [size]="16" />
                      {{ severidad(a.idseveridad).label }}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Ubicación</dt>
                  <dd class="mt-1 text-sm text-text-primary">
                    {{ a.ubicacion?.calle ?? (a.ubicacion?.idcalle ? 'Calle #' + a.ubicacion.idcalle : '—') }}
                    @if (a.ubicacion?.ciudad) {
                      , {{ a.ubicacion?.ciudad }}
                    }
                    @if (a.ubicacion?.estado) {
                      , {{ a.ubicacion?.estado }}
                    }
                  </dd>
                </div>
                <div class="sm:col-span-2">
                  <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Descripción</dt>
                  <dd class="mt-1 text-sm text-text-primary">{{ a.descripcion }}</dd>
                </div>
              </dl>
            </section>

            <section class="rounded-lg border border-border-default bg-bg-surface p-6">
              <h2 class="m-0 mb-4 text-base font-semibold text-text-primary">Impacto</h2>
              <form (ngSubmit)="guardar()" class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div class="grid gap-1.5">
                  <label for="numvehiculos" class="text-sm font-medium text-text-secondary">
                    Vehículos involucrados
                  </label>
                  <input
                    id="numvehiculos"
                    type="number"
                    min="0"
                    class="w-full [appearance:textfield] rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                    [(ngModel)]="numvehiculos"
                    name="numvehiculos"
                  />
                </div>
                <div class="grid gap-1.5">
                  <label for="numheridos" class="text-sm font-medium text-text-secondary">Heridos</label>
                  <input
                    id="numheridos"
                    type="number"
                    min="0"
                    class="w-full [appearance:textfield] rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                    [(ngModel)]="numheridos"
                    name="numheridos"
                  />
                </div>
                <div class="grid gap-1.5">
                  <label for="numfallecidos" class="text-sm font-medium text-text-secondary">Fallecidos</label>
                  <input
                    id="numfallecidos"
                    type="number"
                    min="0"
                    class="w-full [appearance:textfield] rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                    [(ngModel)]="numfallecidos"
                    name="numfallecidos"
                  />
                </div>
                <div class="grid gap-1.5 sm:col-span-2">
                  <label for="descripcion" class="text-sm font-medium text-text-secondary">Descripción</label>
                  <textarea
                    id="descripcion"
                    rows="3"
                    class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
                    [(ngModel)]="descripcion"
                    name="descripcion"
                  ></textarea>
                </div>
                <div class="flex items-end sm:col-span-2">
                  <button
                    type="submit"
                    class="inline-flex items-center gap-2 rounded-md bg-accent-primary px-5 py-2.5 font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover"
                  >
                    Guardar cambios
                  </button>
                </div>
              </form>
            </section>

            <section class="rounded-lg border border-border-default bg-bg-surface p-6">
              <div class="mb-4 flex items-center justify-between">
                <h2 class="m-0 text-base font-semibold text-text-primary">Evidencia</h2>
                @if (evidencias().length) {
                  <span class="rounded-md bg-bg-page px-2.5 py-1 text-xs font-medium text-text-secondary">
                    {{ evidencias().length }} elemento(s)
                  </span>
                }
                <a
                  [routerLink]="['/evidencia-unidad/accidentes', a.idaccidente, 'galeria']"
                  class="text-sm font-medium text-accent-primary hover:underline"
                >
                  Ver galería completa →
                </a>
              </div>
              @if (evidenciasError()) {
                <p class="m-0 text-sm text-alert-critical">{{ evidenciasError() }}</p>
              } @else if (!evidencias().length) {
                <p class="m-0 text-sm text-text-secondary">Sin evidencia fotográfica todavía.</p>
              } @else {
                <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
                  @for (foto of evidencias(); track foto.idevidenciafoto) {
                    <img
                      [src]="foto.urlevidenciafoto"
                      alt="Evidencia fotográfica del caso"
                      class="aspect-square w-full rounded-md border border-border-default object-cover"
                    />
                  }
                </div>
              }
            </section>

            @if (a.estado_actual === 'BORRADOR') {
              <div>
                <button
                  type="button"
                  class="inline-flex items-center gap-2 rounded-md border border-alert-warning px-4 py-2 text-sm font-medium text-alert-warning hover:bg-alert-warning-bg"
                  (click)="descartar()"
                >
                  Descartar caso
                </button>
              </div>
            }
          </div>

          <!-- Columna lateral: actividad del caso -->
          <div class="grid gap-4">
            <section class="rounded-lg border border-border-default bg-bg-surface p-6">
              <h2 class="m-0 mb-4 text-base font-semibold text-text-primary">Historial</h2>
              @if (a.historial_estados.length) {
                <ol class="m-0 grid gap-4 border-l-2 border-border-default pl-4">
                  @for (h of a.historial_estados; track h.fechahoramodificado) {
                    <li class="relative text-sm text-text-secondary">
                      <span
                        class="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full border-2 border-bg-surface bg-accent-primary"
                      ></span>
                      <p class="m-0 font-medium text-text-primary">{{ h.estado }}</p>
                      <p class="m-0 text-xs text-text-secondary">
                        {{ h.fechahoramodificado | date: 'dd/MM/yyyy HH:mm' }}
                      </p>
                    </li>
                  }
                </ol>
              } @else {
                <p class="m-0 text-sm text-text-secondary">Sin historial todavía.</p>
              }
            </section>

            @if (puedeVerDespacho()) {
            <section class="rounded-lg border border-border-default bg-bg-surface p-6">
              <h2 class="m-0 mb-4 text-base font-semibold text-text-primary">Unidades involucradas</h2>
              @if (!unidades().length) {
                <p class="m-0 text-sm text-text-secondary">Sin unidades asignadas todavía.</p>
              } @else {
                <ul class="m-0 grid gap-3">
                  @for (u of unidades(); track u.iddespacho) {
                    <li class="flex items-center justify-between gap-2 text-sm">
                      <div>
                        <p class="m-0 font-medium text-text-primary">{{ u.unidademergencia }}</p>
                        @if (u.tipounidademergencia) {
                          <p class="m-0 text-xs text-text-secondary">{{ u.tipounidademergencia }}</p>
                        }
                      </div>
                      <span
                        class="inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold"
                        [class.bg-alert-success-bg]="despachoTono(u.estado) === 'success'"
                        [class.text-alert-success]="despachoTono(u.estado) === 'success'"
                        [class.bg-alert-warning-bg]="despachoTono(u.estado) === 'warning'"
                        [class.text-alert-warning]="despachoTono(u.estado) === 'warning'"
                        [class.bg-alert-critical-bg]="despachoTono(u.estado) === 'critical'"
                        [class.text-alert-critical]="despachoTono(u.estado) === 'critical'"
                        [class.bg-alert-info-bg]="despachoTono(u.estado) === 'info'"
                        [class.text-alert-info]="despachoTono(u.estado) === 'info'"
                      >
                        {{ u.estado }}
                      </span>
                    </li>
                  }
                </ul>
              }
            </section>
            }

            @if (a.estado_actual === 'ASIGNADO' || a.estado_actual === 'EN_ATENCIÓN') {
              <app-escalar-severidad-panel [idaccidente]="a.idaccidente" />
            }
          </div>
        </div>
      }
    </div>
  `,
})
export class DetalleAccidentePage implements OnInit {
  private readonly api = inject(AccidenteApiService);
  private readonly evidenciaApi = inject(EvidenciaApiService);
  private readonly despachoApi = inject(DespachoApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly notifications = inject(NotificationService);
  private readonly authApi = inject(AuthApiService);

  readonly accidente = signal<AccidenteDetalle | null>(null);
  readonly loading = signal(false);
  readonly loadError = signal<string | null>(null);
  numvehiculos = 0;
  numheridos = 0;
  numfallecidos = 0;
  descripcion = '';

  readonly evidencias = signal<EvidenciaFotoItem[]>([]);
  readonly evidenciasError = signal<string | null>(null);
  readonly unidades = signal<IntentoDespacho[]>([]);

  readonly estado = estadoInfo;
  readonly despachoTono = estadoDespachoTono;

  ngOnInit(): void {
    this.cargar();
  }

  severidad(idseveridad: number): SeveridadInfo {
    return (
      SEVERIDAD_INFO[idseveridad] ?? {
        value: idseveridad,
        label: `Sev. ${idseveridad}`,
        icon: 'info-circle',
        tone: 'success',
      }
    );
  }

  puedeVerDespacho(): boolean {
    return this.authApi.hasAnyRole(['Operador', 'Despacho', 'Administrador']);
  }

  private idaccidente(): string {
    return this.route.snapshot.paramMap.get('idaccidente') ?? '';
  }

  cargar(): void {
    this.loading.set(true);
    this.loadError.set(null);
    this.api.detalle(this.idaccidente()).subscribe({
      next: (res) => {
        this.accidente.set(res.data);
        this.numvehiculos = res.data.numvehiculos ?? 0;
        this.numheridos = res.data.numheridos ?? 0;
        this.numfallecidos = res.data.numfallecidos ?? 0;
        this.descripcion = res.data.descripcion ?? '';
        this.loading.set(false);
        this.cargarEvidencias();
        if (this.puedeVerDespacho()) {
          this.cargarUnidades();
        }
      },
      error: () => {
        this.loadError.set('No se pudo cargar el detalle del accidente.');
        this.loading.set(false);
      },
    });
  }

  private cargarEvidencias(): void {
    this.evidenciaApi
      .listarServidor(this.idaccidente(), { limit: 6 })
      .pipe(catchError(() => of(null)))
      .subscribe((res) => {
        if (!res) {
          this.evidenciasError.set('No se pudo cargar la evidencia.');
          return;
        }
        this.evidenciasError.set(null);
        this.evidencias.set(
          res.data.items.filter((item): item is EvidenciaFotoItem => this.evidenciaApi.isFotoItem(item)),
        );
      });
  }

  private cargarUnidades(): void {
    this.despachoApi
      .obtenerEstado(this.idaccidente())
      .pipe(catchError(() => of(null)))
      .subscribe((res) => {
        if (!res) {
          this.unidades.set([]);
          return;
        }
        this.unidades.set(res.data.unidades_activas.length ? res.data.unidades_activas : res.data.intentos);
      });
  }

  guardar(): void {
    this.api
      .actualizar(this.idaccidente(), {
        numvehiculos: this.numvehiculos,
        numheridos: this.numheridos,
        numfallecidos: this.numfallecidos,
        descripcion: this.descripcion,
      })
      .subscribe({
        next: () => {
          this.notifications.toast('Actualizado', 'success');
          this.cargar();
        },
        error: (err: HttpErrorResponse) => {
          const detail = typeof err.error?.detail === 'string' ? err.error.detail : null;
          this.notifications.alert(detail ?? 'No se pudo guardar el cambio.', 'Error al actualizar');
        },
      });
  }

  descartar(): void {
    this.api.descartar(this.idaccidente(), { motivo: 'Descartado por operador' }).subscribe({
      next: () => {
        this.notifications.toast('Caso descartado', 'success');
        this.cargar();
      },
      error: () => this.notifications.alert('No se pudo descartar el caso.', 'Error al descartar'),
    });
  }
}

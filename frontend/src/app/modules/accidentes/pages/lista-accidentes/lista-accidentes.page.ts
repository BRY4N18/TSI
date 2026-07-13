import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { debounceTime } from 'rxjs';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { AccidenteApiService } from '../../services/accidente-api.service';
import {
  AccidenteListItem,
  CatalogoItem,
  EstadoAccidente,
  UbicacionLegible,
} from '../../services/models/accidente.types';
import { UbicacionCatalogoApiService } from '../../services/ubicacion-catalogo-api.service';
import { SEVERIDAD_INFO, SeveridadInfo } from '../../severidad.constants';
import { ESTADOS, EstadoInfo, estadoInfo as estadoInfoOf } from '../../estado.constants';

@Component({
  selector: 'app-lista-accidentes',
  standalone: true,
  imports: [RouterLink, ReactiveFormsModule, TablerIconComponent, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="mx-auto max-w-6xl p-8">
      <div class="mb-6 flex items-center justify-between">
        <h1 class="m-0 text-2xl font-bold text-text-primary">Accidentes activos</h1>
        @if (puedeRegistrar()) {
          <a
            routerLink="/accidentes/registro"
            class="inline-flex items-center gap-2 rounded-md bg-accent-primary px-4 py-2.5 text-sm font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover"
          >
            Nuevo registro
          </a>
        }
      </div>

      <form [formGroup]="filtros" class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-7">
        <div class="grid gap-1.5">
          <label for="filtroPais" class="text-sm font-medium text-text-secondary">País</label>
          <select
            id="filtroPais"
            class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            formControlName="idpais"
          >
            <option [ngValue]="null">Todos</option>
            @for (p of paises(); track p.id) {
              <option [ngValue]="p.id">{{ p.nombre }}</option>
            }
          </select>
        </div>

        <div class="grid gap-1.5">
          <label for="filtroEstadoRegion" class="text-sm font-medium text-text-secondary">Estado/Región</label>
          <select
            id="filtroEstadoRegion"
            class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            formControlName="idestadoregion"
          >
            <option [ngValue]="null">Todos</option>
            @for (e of estadosRegion(); track e.id) {
              <option [ngValue]="e.id">{{ e.nombre }}</option>
            }
          </select>
        </div>

        <div class="grid gap-1.5">
          <label for="filtroSeveridad" class="text-sm font-medium text-text-secondary">Severidad</label>
          <select
            id="filtroSeveridad"
            class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            formControlName="idseveridad"
          >
            <option [ngValue]="null">Todas</option>
            @for (s of severidadOptions; track s.value) {
              <option [ngValue]="s.value">{{ s.label }}</option>
            }
          </select>
        </div>

        <div class="grid gap-1.5">
          <label for="filtroEstado" class="text-sm font-medium text-text-secondary">Estado</label>
          <select
            id="filtroEstado"
            class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            formControlName="estado"
          >
            <option [ngValue]="null">Todos</option>
            @for (e of estados; track e) {
              <option [ngValue]="e">{{ e }}</option>
            }
          </select>
        </div>

        <div class="grid gap-1.5">
          <label for="filtroFechaDesde" class="text-sm font-medium text-text-secondary">Desde</label>
          <input
            id="filtroFechaDesde"
            type="date"
            class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            formControlName="fechaDesde"
          />
        </div>

        <div class="grid gap-1.5">
          <label for="filtroFechaHasta" class="text-sm font-medium text-text-secondary">Hasta</label>
          <input
            id="filtroFechaHasta"
            type="date"
            class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            formControlName="fechaHasta"
          />
        </div>

        <div class="flex items-end gap-2 pb-2.5">
          <input id="filtroActivo" type="checkbox" formControlName="activo" />
          <label for="filtroActivo" class="text-sm text-text-primary">Solo activos</label>
        </div>
      </form>

      @if (loading()) {
        <div class="grid gap-2" data-testid="loading-skeleton">
          @for (i of [1, 2, 3, 4]; track i) {
            <div class="h-12 animate-pulse rounded-md bg-bg-surface"></div>
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
      } @else if (!accidentes().length) {
        <div
          class="grid place-items-center gap-3 rounded-lg border border-border-default bg-bg-surface p-10 text-center"
          data-testid="empty-state"
        >
          <app-tabler-icon name="car-crash" [size]="32" />
          <p class="m-0 text-sm text-text-secondary">Sin accidentes activos</p>
          <a
            routerLink="/accidentes/registro"
            class="inline-flex items-center gap-2 rounded-md bg-accent-primary px-4 py-2 text-sm font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover"
          >
            Registrar nuevo caso
          </a>
        </div>
      } @else {
        <!-- Desktop/tablet: tabla -->
        <table class="hidden w-full border-collapse overflow-hidden rounded-lg border border-border-default md:table">
          <thead>
            <tr class="bg-bg-surface">
              <th class="border-b border-border-default px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-primary">
                ID
              </th>
              <th class="border-b border-border-default px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-primary">
                Fecha/Hora
              </th>
              <th class="border-b border-border-default px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-primary">
                Severidad
              </th>
              <th class="border-b border-border-default px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-primary">
                Ubicación
              </th>
              <th class="border-b border-border-default px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-primary">
                Estado
              </th>
              <th class="border-b border-border-default px-4 py-3 text-right text-xs font-medium uppercase tracking-wide text-text-primary">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody>
            @for (a of accidentes(); track a.idaccidente) {
              <tr class="border-b border-border-default last:border-b-0">
                <td class="px-4 py-3 text-sm">
                  <a [routerLink]="['/accidentes', a.idaccidente]" class="font-semibold text-accent-primary hover:underline">
                    {{ a.idaccidente }}
                  </a>
                </td>
                <td class="whitespace-nowrap px-4 py-3 text-sm text-text-secondary">
                  {{ a.fechahoraaccidente | date: 'dd/MM/yyyy — HH:mm:ss' }}
                </td>
                <td class="px-4 py-3">
                  <span
                    class="inline-flex items-center gap-1.5 text-sm font-medium"
                    [class.text-alert-success]="severidadInfo(a.idseveridad).tone === 'success'"
                    [class.text-alert-warning]="severidadInfo(a.idseveridad).tone === 'warning'"
                    [class.text-alert-urgent]="severidadInfo(a.idseveridad).tone === 'urgent'"
                    [class.text-alert-critical]="severidadInfo(a.idseveridad).tone === 'critical'"
                  >
                    <app-tabler-icon [name]="severidadInfo(a.idseveridad).icon" [size]="16" />
                    {{ severidadInfo(a.idseveridad).label }}
                  </span>
                </td>
                <td class="max-w-[16rem] truncate px-4 py-3 text-sm text-text-secondary">
                  {{ ubicacionLabel(a.ubicacion) }}
                </td>
                <td class="px-4 py-3">
                  <span
                    class="inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold"
                    [class.bg-alert-success-bg]="estadoInfo(a.estado_actual).tone === 'success'"
                    [class.text-alert-success]="estadoInfo(a.estado_actual).tone === 'success'"
                    [class.bg-alert-warning-bg]="estadoInfo(a.estado_actual).tone === 'warning'"
                    [class.text-alert-warning]="estadoInfo(a.estado_actual).tone === 'warning'"
                    [class.bg-alert-urgent-bg]="estadoInfo(a.estado_actual).tone === 'urgent'"
                    [class.text-alert-urgent]="estadoInfo(a.estado_actual).tone === 'urgent'"
                    [class.bg-alert-info-bg]="estadoInfo(a.estado_actual).tone === 'info'"
                    [class.text-alert-info]="estadoInfo(a.estado_actual).tone === 'info'"
                  >
                    {{ estadoInfo(a.estado_actual).label }}
                  </span>
                </td>
                <td class="px-4 py-3 text-right">
                  <a
                    [routerLink]="['/accidentes', a.idaccidente]"
                    class="inline-flex h-11 w-11 items-center justify-center rounded-md text-text-secondary hover:bg-bg-page hover:text-text-primary"
                    aria-label="Ver detalles"
                    title="Ver detalles"
                  >
                    <app-tabler-icon name="eye" [size]="18" />
                  </a>
                </td>
              </tr>
            }
          </tbody>
        </table>

        <div class="hidden items-center justify-between px-1 py-3 text-sm text-text-secondary md:flex">
          <span>Mostrando {{ accidentes().length }} resultado(s)</span>
        </div>

        <!-- Mobile: cards apiladas -->
        <div class="grid gap-3 md:hidden">
          @for (a of accidentes(); track a.idaccidente) {
            <div class="rounded-lg border border-border-default bg-bg-surface p-4">
              <div class="mb-2 flex items-center justify-between">
                <a [routerLink]="['/accidentes', a.idaccidente]" class="text-sm font-semibold text-accent-primary hover:underline">
                  {{ a.idaccidente }}
                </a>
                <a
                  [routerLink]="['/accidentes', a.idaccidente]"
                  class="inline-flex h-11 w-11 items-center justify-center rounded-md text-text-secondary hover:bg-bg-page hover:text-text-primary"
                  aria-label="Ver detalles"
                  title="Ver detalles"
                >
                  <app-tabler-icon name="eye" [size]="18" />
                </a>
              </div>
              <dl class="grid gap-1 text-sm">
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">Fecha/Hora</dt>
                  <dd class="font-medium text-text-primary">{{ a.fechahoraaccidente | date: 'dd/MM/yyyy HH:mm' }}</dd>
                </div>
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">Severidad</dt>
                  <dd class="font-medium text-text-primary">{{ severidadInfo(a.idseveridad).label }}</dd>
                </div>
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">Ubicación</dt>
                  <dd class="truncate font-medium text-text-primary">{{ ubicacionLabel(a.ubicacion) }}</dd>
                </div>
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">Estado</dt>
                  <dd class="font-medium text-text-primary">{{ estadoInfo(a.estado_actual).label }}</dd>
                </div>
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">Descripción</dt>
                  <dd class="truncate font-medium text-text-primary">{{ a.descripcion }}</dd>
                </div>
              </dl>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class ListaAccidentesPage implements OnInit {
  private readonly api = inject(AccidenteApiService);
  private readonly ubicacionCatalogo = inject(UbicacionCatalogoApiService);
  private readonly fb = inject(FormBuilder);
  private readonly authApi = inject(AuthApiService);

  puedeRegistrar(): boolean {
    return this.authApi.hasAnyRole(['Operador', 'Administrador']);
  }

  readonly severidadOptions = Object.entries(SEVERIDAD_INFO).map(([value, info]) => ({
    value: Number(value),
    label: info.label,
  }));
  readonly estados = ESTADOS;

  readonly paises = signal<CatalogoItem[]>([]);
  readonly estadosRegion = signal<CatalogoItem[]>([]);

  readonly accidentes = signal<AccidenteListItem[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly filtros = this.fb.group({
    idpais: [null as number | null],
    idestadoregion: [null as number | null],
    idseveridad: [null as number | null],
    estado: [null as EstadoAccidente | null],
    fechaDesde: [''],
    fechaHasta: [''],
    activo: [true],
  });

  ngOnInit(): void {
    this.cargar();
    this.ubicacionCatalogo.listarPaises().subscribe((paises) => this.paises.set(paises));

    this.filtros.controls.idpais.valueChanges.subscribe((idpais) => {
      this.filtros.controls.idestadoregion.setValue(null, { emitEvent: false });
      this.estadosRegion.set([]);
      if (idpais) {
        this.ubicacionCatalogo.listarEstados(idpais).subscribe((estados) => this.estadosRegion.set(estados));
      }
    });

    this.filtros.valueChanges.pipe(debounceTime(300)).subscribe(() => this.cargar());
  }

  severidadInfo(idseveridad: number): SeveridadInfo {
    return (
      SEVERIDAD_INFO[idseveridad] ?? {
        value: idseveridad,
        label: `Sev. ${idseveridad}`,
        icon: 'info-circle',
        tone: 'success',
      }
    );
  }

  estadoInfo(estado: EstadoAccidente | null | undefined): EstadoInfo {
    return estadoInfoOf(estado);
  }

  ubicacionLabel(ubicacion: UbicacionLegible | null | undefined): string {
    if (!ubicacion) {
      return '—';
    }
    return [ubicacion.calle, ubicacion.ciudad].filter(Boolean).join(', ') || '—';
  }

  cargar(): void {
    const raw = this.filtros.getRawValue();
    this.loading.set(true);
    this.error.set(null);

    this.api
      .listar({
        idseveridad: raw.idseveridad ?? undefined,
        estado: raw.estado ?? undefined,
        activo: raw.activo ?? undefined,
        fechaDesde: raw.fechaDesde ? new Date(raw.fechaDesde).getTime() : undefined,
        fechaHasta: raw.fechaHasta ? new Date(raw.fechaHasta).getTime() : undefined,
        idestadoregion: raw.idestadoregion ?? undefined,
      })
      .subscribe({
        next: (res) => {
          this.accidentes.set(res.data);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('No se pudo cargar la lista de accidentes.');
          this.loading.set(false);
        },
      });
  }
}

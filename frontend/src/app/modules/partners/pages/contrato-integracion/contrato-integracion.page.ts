import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import {
  LIST_FILTER_CONTROL_CLASS,
  LIST_PAGE_SHELL_CLASS,
} from '../../../../shared/ui/list-states/list-table.styles';
import { ContratoApiService } from '../../services/contrato-api.service';
import {
  formatearFechaRetiro,
  tieneSpecPublicada,
} from '../../services/models/centinelas';
import type { ContratoIntegracion, VersionContrato } from '../../services/models/partner.types';

/**
 * Servicios del catálogo que exponen contrato de API.
 *
 * Se eligen por NOMBRE legible: pedir `id_servicio` al usuario está prohibido
 * (FR-UI-032). Coincide con lo que siembra `database/seed_versiones_contrato.py`,
 * que acota la siembra a los servicios de tipo `api` — un portal web no tiene
 * contrato versionado que un partner integre.
 */
const SERVICIOS = [
  { id: 1, nombre: 'API Despacho' },
  { id: 2, nombre: 'API Registro de accidentes' },
] as const;

/**
 * Contrato de integración versionado (CU-O50, RF-PON-011).
 *
 * El versionado es POR SERVICIO: dos servicios pueden tener ambos una «v1» sin
 * que sean la misma cosa. Por eso el selector de servicio es obligatorio y no
 * hay una vista de «la versión vigente» a secas.
 */
@Component({
  selector: 'app-contrato-integracion',
  standalone: true,
  imports: [
    FormsModule,
    ListEmptyStateComponent,
    ListErrorStateComponent,
    ListLoadingSkeletonComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <header class="mb-6">
        <h1 class="m-0 text-2xl font-bold text-text-primary">Contrato de integración</h1>
        <p class="mt-1 text-sm text-text-secondary">
          Versión vigente y versiones soportadas de cada API
        </p>
      </header>

      <div class="mb-6 max-w-sm">
        <label class="mb-1 block text-sm font-medium text-text-secondary" for="servicio">
          Servicio
        </label>
        <select
          id="servicio"
          data-testid="selector-servicio"
          [class]="filtroClass"
          [ngModel]="idServicio()"
          (ngModelChange)="cambiarServicio($event)"
        >
          @for (s of servicios; track s.id) {
            <option [ngValue]="s.id">{{ s.nombre }}</option>
          }
        </select>
      </div>

      @if (cargando()) {
        <app-list-loading-skeleton [count]="3" />
      } @else if (error()) {
        <app-list-error-state [message]="error()!" (retry)="cargar()" />
      } @else {
        <!-- El alias "as" solo se admite en el @if primario, no en un @else if -->
        @if (contrato(); as c) {
        <div
          class="rounded-lg border border-accent-primary bg-bg-surface p-6"
          data-testid="version-vigente"
        >
          <p class="m-0 text-xs font-medium uppercase tracking-wide text-text-secondary">
            Versión vigente
          </p>
          <p class="m-0 mt-1 font-mono text-2xl font-bold text-text-primary">{{ c.version }}</p>
          @if (tieneSpec(c)) {
            <a
              [href]="c.spec_url"
              target="_blank"
              rel="noopener"
              data-testid="link-spec"
              class="mt-3 inline-block text-sm font-medium text-accent-primary underline"
            >
              Ver documentación
            </a>
          } @else {
            <p class="mt-3 text-sm text-text-secondary" data-testid="sin-spec">
              Todavía no hay documento publicado para esta versión.
            </p>
          }
        </div>

        <h2 class="mb-3 mt-6 text-lg font-semibold text-text-primary">Todas las versiones</h2>
        @if (c.versiones.length === 0) {
          <app-list-empty-state
            message="Este servicio todavía no tiene una versión publicada."
            icon="license"
          />
        } @else {
          <ul class="grid gap-2" data-testid="lista-versiones">
            @for (v of c.versiones; track v.idversion) {
              <li
                class="flex flex-wrap items-center gap-3 rounded-lg border border-border-default bg-bg-surface p-4 text-sm"
                [attr.data-testid]="'version-' + v.idversion"
              >
                <span class="font-mono font-semibold text-text-primary">{{ v.version }}</span>
                <span
                  class="rounded-md px-2 py-1 text-xs font-medium"
                  [class]="tonoEstado(v)"
                  [attr.data-testid]="'estado-' + v.idversion"
                >
                  {{ v.estado }}
                </span>
                <span class="text-text-secondary" [attr.data-testid]="'retiro-' + v.idversion">
                  Retiro: {{ retiro(v) }}
                </span>
              </li>
            }
          </ul>
        }
        }
      }
    </section>
  `,
})
export class ContratoIntegracionPage implements OnInit {
  private readonly api = inject(ContratoApiService);

  readonly contrato = signal<ContratoIntegracion | null>(null);
  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);
  readonly idServicio = signal<number>(SERVICIOS[0].id);

  readonly servicios = SERVICIOS;
  readonly shellClass = LIST_PAGE_SHELL_CLASS;
  readonly filtroClass = LIST_FILTER_CONTROL_CLASS;

  ngOnInit(): void {
    this.cargar();
  }

  /** `0` es el centinela de «sin retiro»; mostrarlo sería 01/01/1970. */
  retiro(v: VersionContrato): string {
    return formatearFechaRetiro(v.fecha_retiro);
  }

  /** `''` significa que no hay documento: no se renderiza un enlace roto. */
  tieneSpec(c: ContratoIntegracion): boolean {
    return tieneSpecPublicada(c.spec_url);
  }

  tonoEstado(v: VersionContrato): string {
    if (v.estado === 'vigente') {
      return 'bg-lime-50 text-lime-800 dark:bg-lime-950 dark:text-lime-200';
    }
    if (v.estado === 'soportada') {
      return 'bg-sky-50 text-sky-800 dark:bg-sky-950 dark:text-sky-200';
    }
    return 'bg-amber-50 text-amber-900 dark:bg-amber-950 dark:text-amber-200';
  }

  cambiarServicio(id: number): void {
    this.idServicio.set(Number(id));
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.error.set(null);
    this.contrato.set(null);
    this.api.consultar(this.idServicio()).subscribe({
      next: (res) => {
        this.contrato.set(res.data);
        this.cargando.set(false);
      },
      error: (err) => {
        const status = (err as { status?: number })?.status;
        this.error.set(
          status === 404
            ? 'Este servicio todavía no tiene una versión publicada.'
            : 'No se pudo cargar el contrato de integración.',
        );
        this.cargando.set(false);
      },
    });
  }
}

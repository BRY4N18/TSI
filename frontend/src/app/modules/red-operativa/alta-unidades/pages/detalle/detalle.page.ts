import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../../shared/ui/list-states/list-table.styles';
import { AuthApiService } from '../../../../cuentas-clientes/auth/services/auth-api.service';
import { UbicacionCatalogoApiService } from '../../../../accidentes/services/ubicacion-catalogo-api.service';
import { ListaSeleccionStorage } from '../../lista-seleccion.storage';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';
import { UnidadEmergenciaData } from '../../models/unidad-emergencia.contract';

@Component({
  selector: 'app-alta-unidades-detalle-page',
  standalone: true,
  imports: [CommonModule, TablerIconComponent],
  template: `
    <div [class]="pageShellClass" data-testid="detalle-page">
      <header class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 class="text-[28px] font-bold text-text-primary">Detalles</h1>
          @if (unidad) {
            <p class="mt-1 font-mono text-sm text-text-secondary">
              #{{ unidad.idunidademergencia }} · {{ unidad.placa }}
            </p>
          }
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            (click)="volver()"
            class="inline-flex h-11 items-center gap-2 rounded-md border border-border-default px-4 text-sm font-medium text-text-primary hover:bg-bg-page"
          >
            <app-tabler-icon name="arrow-left" [size]="18" />
            Volver
          </button>
          @if (unidad) {
            <button
              type="button"
              data-testid="btn-editar-desde-detalle"
              (click)="irEditar()"
              class="inline-flex h-11 items-center gap-2 rounded-md bg-accent-primary px-4 text-sm font-semibold text-white hover:bg-accent-hover"
            >
              <app-tabler-icon name="pencil" [size]="18" />
              Editar
            </button>
          }
        </div>
      </header>

      @if (cargando) {
        <div
          class="mt-6 space-y-3 rounded-lg border border-border-default bg-bg-surface p-6"
          data-testid="detalle-loading"
        >
          <p class="text-sm text-text-secondary">Cargando unidad…</p>
          <div class="h-10 animate-pulse rounded-md bg-bg-page"></div>
          <div class="h-10 animate-pulse rounded-md bg-bg-page"></div>
          <div class="h-10 animate-pulse rounded-md bg-bg-page"></div>
        </div>
      } @else if (errorMensaje) {
        <div
          role="alert"
          class="mt-6 rounded-md border-l-4 border-alert-critical bg-alert-critical-bg px-4 py-3 text-sm text-alert-critical"
        >
          {{ errorMensaje }}
        </div>
      } @else if (unidad) {
        <dl
          class="mt-6 grid grid-cols-1 gap-4 rounded-lg border border-border-default bg-bg-surface p-6 sm:grid-cols-2"
          data-testid="detalle-campos"
        >
          <div class="sm:col-span-2">
            <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Dueño</dt>
            <dd class="mt-1 text-sm text-text-primary">{{ duenioLabel }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Condado</dt>
            <dd class="mt-1 text-sm text-text-primary">{{ condadoLabel }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Tipo de propiedad</dt>
            <dd class="mt-1 text-sm text-text-primary">{{ unidad.tipopropiedad }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Placa</dt>
            <dd class="mt-1 font-mono text-sm text-text-primary">{{ unidad.placa }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Capacidad</dt>
            <dd class="mt-1 text-sm text-text-primary">{{ unidad.capacidad ?? '—' }}</dd>
          </div>
          <div class="sm:col-span-2">
            <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Contacto proveedor</dt>
            <dd class="mt-1 text-sm text-text-primary">{{ unidad.contactoproveedor ?? '—' }}</dd>
          </div>
          <div class="sm:col-span-2">
            <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Nombre de la unidad</dt>
            <dd class="mt-1 text-sm text-text-primary">{{ unidad.unidademergencia }}</dd>
          </div>
          <div class="sm:col-span-2">
            <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Tipo de unidad</dt>
            <dd class="mt-1 text-sm text-text-primary">{{ unidad.tipounidademergencia }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Estado</dt>
            <dd class="mt-1">
              <span
                [class]="
                  unidad.activo
                    ? 'inline-flex rounded-md bg-alert-success-bg px-2 py-1 text-xs text-alert-success'
                    : 'inline-flex rounded-md bg-alert-critical-bg px-2 py-1 text-xs text-alert-critical'
                "
              >
                {{ unidad.activo ? 'Activa' : 'Baja' }}
              </span>
            </dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Usuario login</dt>
            <dd class="mt-1 text-sm text-text-primary">{{ unidad.idusuario ?? '—' }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Latitud</dt>
            <dd class="mt-1 text-sm text-text-primary">{{ unidad.latitud ?? '—' }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Longitud</dt>
            <dd class="mt-1 text-sm text-text-primary">{{ unidad.longitud ?? '—' }}</dd>
          </div>
        </dl>
        <p class="mt-3 text-xs text-text-secondary" data-testid="detalle-sin-guardar">
          Solo lectura — use Editar para modificar.
        </p>
      }
    </div>
  `,
})
export class DetallePage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly facade = inject(UnidadEmergenciaFacadeService);
  private readonly listaSeleccion = inject(ListaSeleccionStorage);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly ubicacionCatalogo = inject(UbicacionCatalogoApiService);
  private readonly auth = inject(AuthApiService);

  readonly pageShellClass = LIST_PAGE_SHELL_CLASS;

  unidad: UnidadEmergenciaData | null = null;
  cargando = false;
  errorMensaje: string | null = null;
  duenioLabel = 'Cuenta proveedor (sesión)';
  condadoLabel = '—';

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('idunidademergencia'));
    if (!Number.isFinite(id) || id <= 0) {
      this.errorMensaje = 'Identificador de unidad inválido.';
      return;
    }
    this.listaSeleccion.set(String(id));
    this.cargando = true;
    this.cdr.markForCheck();
    this.facade.obtener(id).subscribe((result) => {
      this.cargando = false;
      if (result.ok && result.data) {
        this.unidad = result.data;
        this.errorMensaje = null;
        this.duenioLabel = this.auth.getProfile()?.gmail ?? 'Cuenta proveedor (sesión)';
        this.condadoLabel = `Condado #${result.data.idcondado}`;
        this.resolverCondado(result.data.idcondado);
      } else {
        this.errorMensaje = result.error ?? 'No se pudo cargar la unidad';
      }
      this.cdr.markForCheck();
    });
  }

  /**
   * Resuelve el nombre legible del condado recorriendo país→estados→condados
   * (catálogo geográfico acotado). Si no encuentra coincidencia, conserva el
   * fallback "Condado #N" ya asignado.
   */
  private resolverCondado(idcondado: number): void {
    this.ubicacionCatalogo.listarPaises().subscribe((paises) => {
      for (const pais of paises) {
        this.ubicacionCatalogo.listarEstados(pais.id).subscribe((estados) => {
          for (const estado of estados) {
            this.ubicacionCatalogo.listarCondados(estado.id).subscribe((condados) => {
              const match = condados.find((c) => c.id === idcondado);
              if (match) {
                this.condadoLabel = `${match.nombre} (${estado.nombre}, ${pais.nombre})`;
                this.cdr.markForCheck();
              }
            });
          }
        });
      }
    });
  }

  volver(): void {
    void this.router.navigate(['/red-operativa/alta-unidades/catalogo']);
  }

  irEditar(): void {
    if (!this.unidad) return;
    void this.router.navigate([
      '/red-operativa/alta-unidades/editar',
      this.unidad.idunidademergencia,
    ]);
  }
}

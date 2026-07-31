import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { ListaSeleccionStorage } from '../../lista-seleccion.storage';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';
import { UnidadEmergenciaData } from '../../models/unidad-emergencia.contract';

@Component({
  selector: 'app-alta-unidades-detalle-page',
  standalone: true,
  imports: [CommonModule, TablerIconComponent],
  template: `
    <div class="mx-auto w-full max-w-3xl space-y-6 p-6" data-testid="detalle-page">
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
          class="space-y-3 rounded-lg border border-border-default bg-bg-surface p-6"
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
          class="rounded-md border-l-4 border-alert-critical bg-alert-critical-bg px-4 py-3 text-sm text-alert-critical"
        >
          {{ errorMensaje }}
        </div>
      } @else if (unidad) {
        <div
          class="grid grid-cols-1 gap-4 rounded-lg border border-border-default bg-bg-surface p-6 sm:grid-cols-2"
          data-testid="detalle-campos"
        >
          <label class="block sm:col-span-2">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Cliente (dueño)</span>
            <input
              type="number"
              [value]="unidad.idcliente"
              disabled
              class="w-full rounded-md border border-border-default bg-bg-page px-3.5 py-2.5 text-text-secondary opacity-80"
            />
          </label>
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Condado (ID)</span>
            <input
              type="number"
              [value]="unidad.idcondado"
              disabled
              class="w-full rounded-md border border-border-default bg-bg-page px-3.5 py-2.5 opacity-80"
            />
          </label>
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Tipo de propiedad</span>
            <input
              [value]="unidad.tipopropiedad"
              disabled
              class="w-full rounded-md border border-border-default bg-bg-page px-3.5 py-2.5 opacity-80"
            />
          </label>
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Placa</span>
            <input
              [value]="unidad.placa"
              disabled
              class="w-full rounded-md border border-border-default bg-bg-page px-3.5 py-2.5 font-mono opacity-80"
            />
          </label>
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Capacidad</span>
            <input
              [value]="unidad.capacidad ?? ''"
              disabled
              class="w-full rounded-md border border-border-default bg-bg-page px-3.5 py-2.5 opacity-80"
            />
          </label>
          <label class="block sm:col-span-2">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Contacto proveedor</span>
            <input
              [value]="unidad.contactoproveedor ?? ''"
              disabled
              class="w-full rounded-md border border-border-default bg-bg-page px-3.5 py-2.5 opacity-80"
            />
          </label>
          <label class="block sm:col-span-2">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Nombre de la unidad</span>
            <input
              [value]="unidad.unidademergencia"
              disabled
              class="w-full rounded-md border border-border-default bg-bg-page px-3.5 py-2.5 opacity-80"
            />
          </label>
          <label class="block sm:col-span-2">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Tipo de unidad</span>
            <input
              [value]="unidad.tipounidademergencia"
              disabled
              class="w-full rounded-md border border-border-default bg-bg-page px-3.5 py-2.5 opacity-80"
            />
          </label>
          <div class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Estado</span>
            <span
              [class]="
                unidad.activo
                  ? 'inline-flex rounded-md bg-alert-success-bg px-2 py-1 text-xs text-alert-success'
                  : 'inline-flex rounded-md bg-alert-critical-bg px-2 py-1 text-xs text-alert-critical'
              "
            >
              {{ unidad.activo ? 'Activa' : 'Baja' }}
            </span>
          </div>
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Usuario login</span>
            <input
              [value]="unidad.idusuario ?? '—'"
              disabled
              class="w-full rounded-md border border-border-default bg-bg-page px-3.5 py-2.5 opacity-80"
            />
          </label>
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Latitud</span>
            <input
              [value]="unidad.latitud ?? ''"
              disabled
              class="w-full rounded-md border border-border-default bg-bg-page px-3.5 py-2.5 opacity-80"
            />
          </label>
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Longitud</span>
            <input
              [value]="unidad.longitud ?? ''"
              disabled
              class="w-full rounded-md border border-border-default bg-bg-page px-3.5 py-2.5 opacity-80"
            />
          </label>
        </div>
        <p class="text-xs text-text-secondary" data-testid="detalle-sin-guardar">
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

  unidad: UnidadEmergenciaData | null = null;
  cargando = false;
  errorMensaje: string | null = null;

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
      } else {
        this.errorMensaje = result.error ?? 'No se pudo cargar la unidad';
      }
      this.cdr.markForCheck();
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

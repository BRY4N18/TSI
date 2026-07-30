import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';
import {
  ImportacionLoteData,
  TipoPropiedad,
  TipoUnidadEmergencia,
  UnidadCreateRequest,
  UnidadCreatedData,
  UnidadEmergenciaData,
} from '../../models/unidad-emergencia.contract';

interface NuevaUnidadForm {
  idcondado: number | null;
  tipopropiedad: TipoPropiedad;
  placa: string;
  capacidad: string;
  contactoproveedor: string;
  unidademergencia: string;
  tipounidademergencia: TipoUnidadEmergencia;
  gmail: string;
}

const FORM_INICIAL: NuevaUnidadForm = {
  idcondado: null,
  tipopropiedad: 'Externa',
  placa: '',
  capacidad: '',
  contactoproveedor: '',
  unidademergencia: '',
  tipounidademergencia: 'Ambulancia',
  gmail: '',
};

const CSV_PLANTILLA =
  'idcondado,tipopropiedad,placa,contactoproveedor,unidademergencia,tipounidademergencia,gmail';

@Component({
  selector: 'app-red-operativa-catalogo-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TablerIconComponent],
  template: `
    <div class="mx-auto max-w-4xl space-y-8 p-6">
      <header>
        <h1 class="text-[28px] font-bold text-text-primary">Catálogo de unidades de emergencia</h1>
        <p class="mt-1 text-sm text-text-secondary">
          Registrar unidades de su flota (Proveedor) individualmente o en lote.
        </p>
      </header>

      <section class="space-y-4 rounded-lg border border-border-default bg-bg-surface p-6">
        <div class="flex items-center justify-between gap-3">
          <h2 class="text-lg font-semibold text-text-primary">Mis unidades</h2>
          <button
            type="button"
            (click)="cargarUnidades()"
            class="rounded-md border border-accent-primary px-4 py-2 text-sm font-medium text-accent-primary hover:bg-accent-primary/5"
          >
            Actualizar
          </button>
        </div>
        @if (unidadesError) {
          <p class="text-sm text-alert-critical">{{ unidadesError }}</p>
        }
        @if (unidades.length === 0 && !unidadesError) {
          <p class="text-sm text-text-secondary">Aún no hay unidades registradas.</p>
        }
        @if (unidades.length > 0) {
          <div class="overflow-x-auto rounded-lg border border-border-default">
            <table class="w-full text-left text-sm">
              <thead class="bg-bg-page">
                <tr>
                  <th class="px-4 py-3 text-xs font-medium uppercase text-text-primary">ID</th>
                  <th class="px-4 py-3 text-xs font-medium uppercase text-text-primary">Placa</th>
                  <th class="px-4 py-3 text-xs font-medium uppercase text-text-primary">Nombre</th>
                  <th class="px-4 py-3 text-xs font-medium uppercase text-text-primary">Estado</th>
                  <th class="px-4 py-3 text-xs font-medium uppercase text-text-primary">Acciones</th>
                </tr>
              </thead>
              <tbody>
                @for (u of unidades; track u.idunidademergencia) {
                  <tr class="border-t border-border-default">
                    <td class="px-4 py-3 text-text-primary">{{ u.idunidademergencia }}</td>
                    <td class="px-4 py-3 text-text-primary">{{ u.placa }}</td>
                    <td class="px-4 py-3 text-text-secondary">{{ u.unidademergencia }}</td>
                    <td class="px-4 py-3">
                      <span
                        [class]="
                          u.activo
                            ? 'rounded-md bg-alert-success-bg px-2 py-1 text-xs text-alert-success'
                            : 'rounded-md bg-alert-critical-bg px-2 py-1 text-xs text-alert-critical'
                        "
                      >
                        {{ u.activo ? 'Activa' : 'Baja' }}
                      </span>
                    </td>
                    <td class="space-x-3 px-4 py-3">
                      <a
                        [routerLink]="['/red-operativa/alta-unidades/editar', u.idunidademergencia]"
                        class="text-accent-primary hover:underline"
                        >Editar</a
                      >
                      <a
                        [routerLink]="['/red-operativa/alta-unidades/baja', u.idunidademergencia]"
                        class="text-alert-critical hover:underline"
                        >Baja</a
                      >
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        }
      </section>

      <section class="space-y-4 rounded-lg border border-border-default bg-bg-surface p-6">
        <h2 class="text-lg font-semibold text-text-primary">Alta individual</h2>
        <form (ngSubmit)="registrar()" class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Condado (ID)</span>
            <input
              type="number"
              [(ngModel)]="form.idcondado"
              name="idcondado"
              required
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
            />
          </label>
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Tipo de propiedad</span>
            <select
              [(ngModel)]="form.tipopropiedad"
              name="tipopropiedad"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none"
            >
              <option value="Propia">Propia</option>
              <option value="Externa">Externa</option>
            </select>
          </label>
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Placa</span>
            <input
              [(ngModel)]="form.placa"
              name="placa"
              required
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
            />
          </label>
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Capacidad</span>
            <input
              [(ngModel)]="form.capacidad"
              name="capacidad"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
            />
          </label>
          @if (form.tipopropiedad === 'Externa') {
            <label class="block">
              <span class="mb-1 block text-sm font-medium text-text-secondary">Contacto proveedor</span>
              <input
                [(ngModel)]="form.contactoproveedor"
                name="contactoproveedor"
                required
                class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
              />
            </label>
          }
          <label class="block sm:col-span-2">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Nombre de la unidad</span>
            <input
              [(ngModel)]="form.unidademergencia"
              name="unidademergencia"
              required
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
            />
          </label>
          <label class="block sm:col-span-2">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Tipo de unidad</span>
            <select
              [(ngModel)]="form.tipounidademergencia"
              name="tipounidademergencia"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none"
            >
              <option value="Ambulancia">Ambulancia</option>
              <option value="Grúa">Grúa</option>
              <option value="Patrulla">Patrulla</option>
              <option value="Bomberos">Bomberos</option>
              <option value="Defensa Civil">Defensa Civil</option>
            </select>
          </label>
          <label class="block sm:col-span-2">
            <span class="mb-1 block text-sm font-medium text-text-secondary">
              Gmail unidad (opcional — habilita login CU-O30)
            </span>
            <input
              type="email"
              [(ngModel)]="form.gmail"
              name="gmail"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
            />
          </label>
          <div class="sm:col-span-2">
            <button
              type="submit"
              [disabled]="guardando"
              class="rounded-md bg-accent-primary px-5 py-2.5 font-medium text-white transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
            >
              {{ guardando ? 'Registrando…' : 'Registrar unidad' }}
            </button>
          </div>
        </form>

        @if (errorMensaje) {
          <div
            role="alert"
            class="flex items-center gap-2 rounded-md border-l-4 border-alert-critical bg-alert-critical-bg px-4 py-3 text-sm text-alert-critical"
          >
            <app-tabler-icon name="alert-triangle" [size]="18" />
            <span>{{ errorMensaje }}</span>
          </div>
        }

        @if (ultimaUnidadCreada) {
          <div
            class="flex items-center gap-2 rounded-md border-l-4 border-alert-success bg-alert-success-bg px-4 py-3 text-sm text-alert-success"
          >
            <app-tabler-icon name="circle-check" [size]="18" />
            <span>
              Unidad #{{ ultimaUnidadCreada.idunidademergencia }} ({{ ultimaUnidadCreada.placa }})
              registrada correctamente.
            </span>
          </div>
        }
      </section>

      <section class="space-y-4 rounded-lg border border-border-default bg-bg-surface p-6">
        <h2 class="text-lg font-semibold text-text-primary">Importación en lote (CSV)</h2>
        <p class="text-sm text-text-secondary">
          Columnas:
          <code class="rounded bg-bg-muted px-1 text-xs">{{ csvPlantilla }}</code>. Todo-o-nada; liga
          idusuario a cada unidad.
        </p>
        <div class="flex flex-wrap items-center gap-3">
          <input
            type="file"
            accept=".csv"
            (change)="onArchivoSeleccionado($event)"
            class="text-sm text-text-secondary file:mr-3 file:rounded-md file:border-0 file:bg-accent-primary/10 file:px-3.5 file:py-2 file:text-sm file:font-medium file:text-accent-primary hover:file:bg-accent-primary/15"
          />
          <button
            type="button"
            [disabled]="!archivoSeleccionado || importando"
            (click)="importarLote()"
            class="rounded-md border border-accent-primary px-5 py-2.5 font-medium text-accent-primary transition-colors hover:bg-accent-primary/5 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {{ importando ? 'Importando…' : 'Importar' }}
          </button>
        </div>
        @if (loteResultado) {
          <p class="text-sm text-text-primary">
            {{ loteResultado.insertadas }} insertadas
            @if (loteResultado.usuarios_creados != null) {
              ({{ loteResultado.usuarios_creados }} usuarios)
            }
          </p>
          @if (loteResultado.fallidas.length > 0) {
            <ul class="list-inside list-disc text-sm text-alert-critical">
              @for (fallida of loteResultado.fallidas; track fallida.fila) {
                <li>Fila {{ fallida.fila }}: {{ fallida.motivo }}</li>
              }
            </ul>
          }
        }
        @if (loteError) {
          <p class="text-sm text-alert-critical">{{ loteError }}</p>
        }
      </section>
    </div>
  `,
})
export class CatalogoPage implements OnInit {
  private readonly facade = inject(UnidadEmergenciaFacadeService);

  readonly csvPlantilla = CSV_PLANTILLA;

  form: NuevaUnidadForm = { ...FORM_INICIAL };
  guardando = false;
  errorMensaje: string | null = null;
  ultimaUnidadCreada: UnidadCreatedData | null = null;

  unidades: UnidadEmergenciaData[] = [];
  unidadesError: string | null = null;

  archivoSeleccionado: File | null = null;
  importando = false;
  loteResultado: ImportacionLoteData | null = null;
  loteError: string | null = null;

  ngOnInit(): void {
    this.cargarUnidades();
  }

  cargarUnidades(): void {
    this.unidadesError = null;
    this.facade.listar().subscribe((result) => {
      if (result.ok && result.data) {
        this.unidades = result.data;
      } else {
        this.unidadesError = result.error ?? 'No se pudo cargar el catálogo';
      }
    });
  }

  onArchivoSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.archivoSeleccionado = input.files?.[0] ?? null;
  }

  importarLote(): void {
    if (!this.archivoSeleccionado) return;
    this.loteError = null;
    this.loteResultado = null;
    this.importando = true;
    this.facade.importarLote(this.archivoSeleccionado).subscribe((result) => {
      this.importando = false;
      if (result.ok && result.data) {
        this.loteResultado = result.data;
        this.cargarUnidades();
      } else {
        this.loteError = result.error ?? 'Error al importar el archivo';
      }
    });
  }

  registrar(): void {
    this.errorMensaje = null;
    this.ultimaUnidadCreada = null;

    if (!this.form.idcondado || !this.form.placa || !this.form.unidademergencia) {
      this.errorMensaje = 'Completa todos los campos requeridos.';
      return;
    }

    const body: UnidadCreateRequest = {
      idcondado: this.form.idcondado,
      tipopropiedad: this.form.tipopropiedad,
      placa: this.form.placa,
      capacidad: this.form.capacidad || undefined,
      contactoproveedor: this.form.contactoproveedor || undefined,
      unidademergencia: this.form.unidademergencia,
      tipounidademergencia: this.form.tipounidademergencia,
      gmail: this.form.gmail.trim() || undefined,
    };

    this.guardando = true;
    this.facade.registrar(body).subscribe((result) => {
      this.guardando = false;
      if (result.ok && result.data) {
        this.ultimaUnidadCreada = result.data;
        this.form = { ...FORM_INICIAL };
        this.cargarUnidades();
      } else {
        this.errorMensaje = result.error ?? 'Error al registrar la unidad';
      }
    });
  }
}

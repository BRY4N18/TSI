import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';
import {
  ImportacionLoteData,
  TipoPropiedad,
  TipoUnidadEmergencia,
  UnidadCreateRequest,
  UnidadCreatedData,
} from '../../models/unidad-emergencia.contract';

interface NuevaUnidadForm {
  idcliente: number | null;
  idcondado: number | null;
  tipopropiedad: TipoPropiedad;
  placa: string;
  capacidad: string;
  contactoproveedor: string;
  unidademergencia: string;
  tipounidademergencia: TipoUnidadEmergencia;
}

const FORM_INICIAL: NuevaUnidadForm = {
  idcliente: null,
  idcondado: null,
  tipopropiedad: 'Externa',
  placa: '',
  capacidad: '',
  contactoproveedor: '',
  unidademergencia: '',
  tipounidademergencia: 'Ambulancia',
};

@Component({
  selector: 'app-red-operativa-catalogo-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TablerIconComponent],
  template: `
    <div class="mx-auto max-w-2xl space-y-8 p-6">
      <header>
        <h1 class="text-[28px] font-bold text-text-primary">Catálogo de unidades de emergencia</h1>
        <p class="mt-1 text-sm text-text-secondary">Registrar unidades individualmente o en lote.</p>
      </header>

      <section class="space-y-4 rounded-lg border border-border-default bg-bg-surface p-6">
        <h2 class="text-lg font-semibold text-text-primary">Alta individual</h2>
        <form (ngSubmit)="registrar()" class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Cliente (ID)</span>
            <input
              type="number"
              [(ngModel)]="form.idcliente"
              name="idcliente"
              required
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
            />
          </label>
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
            <app-tabler-icon name="upload" [size]="16" class="mr-1 inline-block align-text-bottom" />
            {{ importando ? 'Importando…' : 'Importar' }}
          </button>
        </div>

        @if (loteResultado) {
          <div class="space-y-2 text-sm text-text-primary">
            <p>{{ loteResultado.insertadas }} unidades insertadas.</p>
            @if (loteResultado.fallidas.length > 0) {
              <ul class="list-inside list-disc space-y-1 text-alert-critical">
                @for (fallida of loteResultado.fallidas; track fallida.fila) {
                  <li>Fila {{ fallida.fila }}: {{ fallida.motivo }}</li>
                }
              </ul>
            }
          </div>
        }
        @if (loteError) {
          <div
            role="alert"
            class="flex items-center gap-2 rounded-md border-l-4 border-alert-critical bg-alert-critical-bg px-4 py-3 text-sm text-alert-critical"
          >
            <app-tabler-icon name="alert-triangle" [size]="18" />
            <span>{{ loteError }}</span>
          </div>
        }
      </section>
    </div>
  `,
})
export class CatalogoPage implements OnInit {
  private readonly facade = inject(UnidadEmergenciaFacadeService);

  form: NuevaUnidadForm = { ...FORM_INICIAL };
  guardando = false;
  errorMensaje: string | null = null;
  ultimaUnidadCreada: UnidadCreatedData | null = null;

  archivoSeleccionado: File | null = null;
  importando = false;
  loteResultado: ImportacionLoteData | null = null;
  loteError: string | null = null;

  ngOnInit(): void {}

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
      } else {
        this.loteError = result.error ?? 'Error al importar el archivo';
      }
    });
  }

  registrar(): void {
    this.errorMensaje = null;
    this.ultimaUnidadCreada = null;

    if (!this.form.idcliente || !this.form.idcondado || !this.form.placa || !this.form.unidademergencia) {
      this.errorMensaje = 'Completa todos los campos requeridos.';
      return;
    }

    const body: UnidadCreateRequest = {
      idcliente: this.form.idcliente,
      idcondado: this.form.idcondado,
      tipopropiedad: this.form.tipopropiedad,
      placa: this.form.placa,
      capacidad: this.form.capacidad || undefined,
      contactoproveedor: this.form.contactoproveedor || undefined,
      unidademergencia: this.form.unidademergencia,
      tipounidademergencia: this.form.tipounidademergencia,
    };

    this.guardando = true;
    this.facade.registrar(body).subscribe((result) => {
      this.guardando = false;
      if (result.ok && result.data) {
        this.ultimaUnidadCreada = result.data;
        this.form = { ...FORM_INICIAL };
      } else {
        this.errorMensaje = result.error ?? 'Error al registrar la unidad';
      }
    });
  }
}

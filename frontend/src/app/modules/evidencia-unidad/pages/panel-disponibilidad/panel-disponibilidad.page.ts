import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { DisponibilidadUnidadApiService } from '../../services/disponibilidad-unidad-api.service';
import {
  DisponibilidadUnidadData,
  EstadoDisponibilidadUnidad,
} from '../../services/models/evidencia-unidad.types';

@Component({
  selector: 'app-panel-disponibilidad',
  standalone: true,
  imports: [FormsModule],
  template: `
    <section>
      <h1>Disponibilidad de unidad</h1>
      @if (error()) {
        <p data-testid="error">{{ error() }}</p>
      }
      @if (disponibilidad()) {
        <p data-testid="estado-actual">
          Estado actual: <strong>{{ disponibilidad()!.estado_actual }}</strong>
        </p>
        <p data-testid="incluido-despacho">
          Incluido en despacho: {{ disponibilidad()!.incluido_en_despacho ? 'Sí' : 'No' }}
        </p>
      }
      <form (ngSubmit)="declararEstado()">
        <label>
          Nuevo estado
          <select name="estado" [(ngModel)]="estadoSeleccionado" required>
            @for (estado of estados; track estado) {
              <option [value]="estado">{{ estado }}</option>
            }
          </select>
        </label>
        <button type="submit" [disabled]="cargando()">Actualizar disponibilidad</button>
      </form>
      @if (mensaje()) {
        <p data-testid="mensaje">{{ mensaje() }}</p>
      }
    </section>
  `,
})
export class PanelDisponibilidadPage {
  private readonly disponibilidadApi = inject(DisponibilidadUnidadApiService);

  readonly estados: EstadoDisponibilidadUnidad[] = ['Activa', 'Ocupada', 'Fuera de servicio'];
  estadoSeleccionado: EstadoDisponibilidadUnidad = 'Activa';
  readonly disponibilidad = signal<DisponibilidadUnidadData | null>(null);
  readonly mensaje = signal('');
  readonly error = signal('');
  readonly cargando = signal(false);

  constructor() {
    this.cargar();
  }

  cargar(): void {
    this.disponibilidadApi.consultarMiDisponibilidad().subscribe({
      next: (res) => {
        this.disponibilidad.set(res.data);
        this.estadoSeleccionado = res.data.estado_actual;
      },
      error: () => this.error.set('No se pudo consultar la disponibilidad'),
    });
  }

  declararEstado(): void {
    this.cargando.set(true);
    this.mensaje.set('');
    this.error.set('');
    this.disponibilidadApi.declararMiEstado({ estadonuevo: this.estadoSeleccionado }).subscribe({
      next: (res) => {
        this.mensaje.set(`Estado actualizado: ${res.data.estadonuevo}`);
        this.cargar();
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudo declarar el nuevo estado');
        this.cargando.set(false);
      },
    });
  }
}

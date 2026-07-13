import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { DespachoParametrosApiService } from '../../services/despacho-parametros-api.service';
import { ParametrosDespachoData } from '../../services/models/despacho.types';

@Component({
  selector: 'app-parametros-algoritmo',
  standalone: true,
  imports: [FormsModule],
  template: `
    <section>
      <h1>Parámetros del algoritmo</h1>
      @if (parametros()) {
        <label>
          Timeout (s)
          <input type="number" [(ngModel)]="timeout" min="30" max="300" />
        </label>
        <button type="button" (click)="guardar()">Guardar</button>
      }
      @if (mensaje()) {
        <p data-testid="mensaje">{{ mensaje() }}</p>
      }
    </section>
  `,
})
export class ParametrosAlgoritmoPage {
  private readonly api = inject(DespachoParametrosApiService);

  readonly parametros = signal<ParametrosDespachoData | null>(null);
  readonly mensaje = signal('');
  timeout = 90;

  constructor() {
    this.api.obtener().subscribe({
      next: (res) => {
        this.parametros.set(res.data);
        this.timeout = res.data.timeout_respuesta_seg;
      },
    });
  }

  guardar(): void {
    this.api.actualizar({ timeout_respuesta_seg: this.timeout }).subscribe({
      next: () => this.mensaje.set('Parámetros actualizados'),
      error: () => this.mensaje.set('Error al guardar'),
    });
  }
}

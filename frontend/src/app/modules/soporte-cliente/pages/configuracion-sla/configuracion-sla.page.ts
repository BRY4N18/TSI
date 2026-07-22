import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { SlaConfigApiService } from '../../services/sla-config-api.service';
import { SLAConfig } from '../../services/models/soporte.types';

@Component({
  selector: 'app-configuracion-sla',
  standalone: true,
  imports: [FormsModule],
  template: `
    <section>
      <h1>Configuración de SLA</h1>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Plan</th>
            <th>Tipo</th>
            <th>Prioridad</th>
            <th>Respuesta (s)</th>
            <th>Resolución (s)</th>
            <th>Activo</th>
          </tr>
        </thead>
        <tbody>
          @for (r of reglas(); track r.idslaconfig) {
            <tr>
              <td>{{ r.idslaconfig }}</td>
              <td>{{ r.idplan }}</td>
              <td>{{ r.tipoincidencia }}</td>
              <td>{{ r.prioridad }}</td>
              <td>{{ r.tiemporespuestamax }}</td>
              <td>{{ r.tiemporesolucionmax }}</td>
              <td>{{ r.activo ? 'Sí' : 'No' }}</td>
            </tr>
          }
        </tbody>
      </table>

      <h2>Nueva regla</h2>
      <form (ngSubmit)="crear()">
        <label>Plan (ID) <input type="number" name="idplan" [(ngModel)]="idplan" /></label>
        <label>Tipo de incidencia <input name="tipoincidencia" [(ngModel)]="tipoincidencia" /></label>
        <label>Prioridad <input name="prioridad" [(ngModel)]="prioridad" /></label>
        <label>
          Tiempo respuesta (seg) <input type="number" name="tiemporespuestamax" [(ngModel)]="tiemporespuestamax" />
        </label>
        <label>
          Tiempo resolución (seg) <input type="number" name="tiemporesolucionmax" [(ngModel)]="tiemporesolucionmax" />
        </label>
        <button type="submit">Crear regla</button>
      </form>
      @if (mensaje()) {
        <p data-testid="mensaje">{{ mensaje() }}</p>
      }
    </section>
  `,
})
export class ConfiguracionSlaPage {
  private readonly api = inject(SlaConfigApiService);

  readonly reglas = signal<SLAConfig[]>([]);
  readonly mensaje = signal('');
  idplan = 1;
  tipoincidencia = '';
  prioridad = '';
  tiemporespuestamax = 3600;
  tiemporesolucionmax = 86400;

  constructor() {
    this.cargar();
  }

  private cargar(): void {
    this.api.listar().subscribe({ next: (res) => this.reglas.set(res.data.items) });
  }

  crear(): void {
    if (!this.tipoincidencia || !this.prioridad) {
      return;
    }
    this.api
      .crear({
        idplan: this.idplan,
        tipoincidencia: this.tipoincidencia,
        prioridad: this.prioridad,
        tiemporespuestamax: this.tiemporespuestamax,
        tiemporesolucionmax: this.tiemporesolucionmax,
      })
      .subscribe({
        next: () => {
          this.mensaje.set('Regla creada');
          this.cargar();
        },
        error: () => this.mensaje.set('Error al crear la regla'),
      });
  }
}

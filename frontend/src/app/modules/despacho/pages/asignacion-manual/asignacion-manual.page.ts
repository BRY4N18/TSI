import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { DespachoApiService } from '../../services/despacho-api.service';
import { UnidadCandidata } from '../../services/models/despacho.types';

@Component({
  selector: 'app-asignacion-manual',
  standalone: true,
  imports: [FormsModule],
  template: `
    <section>
      <h1>Asignación manual</h1>
      @if (candidatas().length) {
        <label>
          Unidad
          <select [(ngModel)]="unidadSeleccionada">
            @for (c of candidatas(); track c.idunidademergencia) {
              <option [ngValue]="c.idunidademergencia">
                {{ c.unidademergencia }} ({{ c.puntuacion }})
              </option>
            }
          </select>
        </label>
        <button type="button" (click)="asignar()">Asignar</button>
      }
      @if (mensaje()) {
        <p data-testid="mensaje">{{ mensaje() }}</p>
      }
    </section>
  `,
})
export class AsignacionManualPage {
  private readonly api = inject(DespachoApiService);
  private readonly route = inject(ActivatedRoute);

  readonly candidatas = signal<UnidadCandidata[]>([]);
  readonly mensaje = signal('');
  unidadSeleccionada = 0;

  constructor() {
    const idaccidente = this.route.snapshot.paramMap.get('idaccidente') ?? 'ACC-EVI-TEST-1';
    this.api.listarCandidatas(idaccidente).subscribe({
      next: (res) => {
        this.candidatas.set(res.data.candidatas);
        if (res.data.candidatas.length) {
          this.unidadSeleccionada = res.data.candidatas[0].idunidademergencia;
        }
      },
    });
  }

  asignar(): void {
    const idaccidente = this.route.snapshot.paramMap.get('idaccidente') ?? 'ACC-EVI-TEST-1';
    this.api.asignarManual(idaccidente, this.unidadSeleccionada).subscribe({
      next: (res) => this.mensaje.set(res.data.message),
      error: () => this.mensaje.set('Error al asignar'),
    });
  }
}

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Prospecto } from '../../models/prospectos.types';
import { ProspectoApiService } from '../../services/prospecto-api.service';

@Component({
  selector: 'app-pipeline-board',
  standalone: true,
  imports: [CommonModule, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="page">
      <h1>Pipeline</h1>
      @if (loading()) {
        <p class="skeleton">Cargando tablero…</p>
      } @else if (error()) {
        <p class="err">{{ error() }}</p>
        <button type="button" (click)="cargar()">Reintentar</button>
      } @else if (items().length === 0) {
        <p>Sin prospectos activos.</p>
      } @else {
        <div class="board">
          @for (col of columnas; track col) {
            <div class="col">
              <h2>{{ col }}</h2>
              @for (p of byEtapa(col); track p.idprospecto) {
                <a [routerLink]="['/ventas-crm/prospectos', p.idprospecto]">{{ p.empresa }}</a>
              }
            </div>
          }
        </div>
      }
    </section>
  `,
  styles: `
    .board {
      display: grid;
      grid-template-columns: repeat(5, minmax(8rem, 1fr));
      gap: 0.75rem;
    }
    .col {
      border: 1px solid #ccc;
      padding: 0.5rem;
      display: grid;
      gap: 0.35rem;
    }
    .err {
      color: #b00020;
    }
  `,
})
export class PipelineBoardPage implements OnInit {
  private readonly api = inject(ProspectoApiService);
  readonly columnas = ['Nuevo', 'Contactado', 'Calificado', 'Propuesta', 'Negociación'] as const;
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly items = signal<Prospecto[]>([]);

  ngOnInit(): void {
    this.cargar();
  }

  byEtapa(etapa: string): Prospecto[] {
    return this.items().filter((p) => p.activo && p.etapa_actual === etapa);
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listar({ activo: true, limit: 100 }).subscribe({
      next: (res) => {
        this.items.set(res.data ?? []);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Error al cargar pipeline');
        this.loading.set(false);
      },
    });
  }
}

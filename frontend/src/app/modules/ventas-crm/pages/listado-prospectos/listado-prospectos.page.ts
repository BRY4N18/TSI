import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Prospecto } from '../../models/prospectos.types';
import { ProspectoApiService } from '../../services/prospecto-api.service';

@Component({
  selector: 'app-listado-prospectos',
  standalone: true,
  imports: [CommonModule, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="page">
      <h1>Prospectos</h1>
      @if (loading()) {
        <div class="skeleton" aria-busy="true">Cargando listado…</div>
      } @else if (error()) {
        <p class="err" role="alert">{{ error() }}</p>
        <button type="button" (click)="cargar()">Reintentar</button>
      } @else if (items().length === 0) {
        <p>No hay prospectos asignados.</p>
        <a routerLink="/ventas-crm/registro">Registrar prospecto</a>
      } @else {
        <ul>
          @for (p of items(); track p.idprospecto) {
            <li>
              <a [routerLink]="['/ventas-crm/prospectos', p.idprospecto]">
                {{ p.nombres }} {{ p.apellidos }} — {{ p.empresa }} ({{ p.etapa_actual }})
              </a>
            </li>
          }
        </ul>
      }
    </section>
  `,
  styles: `
    .page {
      padding: 1.5rem;
    }
    .skeleton {
      opacity: 0.6;
    }
    .err {
      color: #b00020;
    }
  `,
})
export class ListadoProspectosPage implements OnInit {
  private readonly api = inject(ProspectoApiService);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly items = signal<Prospecto[]>([]);

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listar({ limit: 50 }).subscribe({
      next: (res) => {
        this.items.set(res.data ?? []);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Error al cargar prospectos');
        this.loading.set(false);
      },
    });
  }
}

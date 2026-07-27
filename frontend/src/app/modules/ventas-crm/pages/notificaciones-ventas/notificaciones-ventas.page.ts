import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';

import { NotificacionVentas } from '../../models/notificacion-ventas.types';
import { NotificacionApiService } from '../../services/notificacion-api.service';

@Component({
  selector: 'app-notificaciones-ventas',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="page">
      <h1>Notificaciones de ventas</h1>
      @if (loading()) {
        <div class="skeleton" aria-busy="true">Cargando notificaciones…</div>
      } @else if (error()) {
        <p class="err" role="alert">{{ error() }}</p>
        <button type="button" (click)="cargar()">Reintentar</button>
      } @else if (items().length === 0) {
        <p>No hay notificaciones todavía.</p>
        <button type="button" (click)="cargar()">Actualizar</button>
      } @else {
        <ul>
          @for (n of items(); track n.idnotificacion) {
            <li>
              #{{ n.idnotificacion }} — prospecto {{ n.id_prospecto }} —
              {{ n.regladisparada }} ({{ n.canal }})
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
export class NotificacionesVentasPage implements OnInit {
  private readonly api = inject(NotificacionApiService);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly items = signal<NotificacionVentas[]>([]);

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
        this.error.set(err?.error?.detail ?? 'Error al cargar notificaciones');
        this.loading.set(false);
      },
    });
  }
}

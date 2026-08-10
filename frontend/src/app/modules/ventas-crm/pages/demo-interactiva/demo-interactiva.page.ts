import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { DemoApiService } from '../../services/demo-api.service';
import {
  clearDemoSessionToken,
  storeDemoSessionToken,
} from '../../interceptors/demo-session.interceptor';
import {
  DEMO_QUERY_PARAM_GRANT,
  DEMO_QUERY_PARAM_IDPROSPECTO,
} from '../../models/notificacion-ventas.types';

@Component({
  selector: 'app-demo-interactiva',
  standalone: true,
  imports: [CommonModule, FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="page">
      <h1>Demo interactiva</h1>
      @if (loading()) {
        <div class="skeleton" aria-busy="true">Procesando…</div>
      } @else if (error()) {
        <p class="err" role="alert">{{ error() }}</p>
        <button type="button" (click)="error.set(null)">Cerrar error</button>
      }
      <label>
        idprospecto
        <input type="number" [(ngModel)]="idprospecto" />
      </label>
      <label>
        demo_grant
        <input type="text" [(ngModel)]="demoGrant" />
      </label>
      <button type="button" (click)="abrir()">Abrir / reanudar sesión</button>
      @if (token()) {
        <p>Sesión activa hasta {{ expiracion() }}</p>
        <button type="button" (click)="enviarClick()">Registrar click precios</button>
        <button type="button" (click)="cerrar()">Cerrar sesión local</button>
      }
    </section>
  `,
  styles: `
    .page {
      padding: 1.5rem;
      display: grid;
      gap: 0.75rem;
      max-width: 32rem;
    }
    .err {
      color: #b00020;
    }
    .skeleton {
      opacity: 0.6;
    }
  `,
})
export class DemoInteractivaPage implements OnInit {
  private readonly api = inject(DemoApiService);
  private readonly route = inject(ActivatedRoute);
  idprospecto = 0;
  demoGrant = '';
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly token = signal<string | null>(null);
  readonly expiracion = signal<string | null>(null);

  ngOnInit(): void {
    const params = this.route.snapshot.queryParamMap;
    const idprospecto = params.get(DEMO_QUERY_PARAM_IDPROSPECTO);
    const grant = params.get(DEMO_QUERY_PARAM_GRANT);
    if (idprospecto && grant) {
      this.idprospecto = Number(idprospecto);
      this.demoGrant = grant;
      this.abrir();
    }
  }

  abrir(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.abrirSesion({ idprospecto: this.idprospecto, demo_grant: this.demoGrant }).subscribe({
      next: (res) => {
        storeDemoSessionToken(res.data.demo_session_token);
        this.token.set(res.data.demo_session_token);
        this.expiracion.set(res.data.demo_expiracion);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'No se pudo abrir la demo');
        this.loading.set(false);
      },
    });
  }

  enviarClick(): void {
    this.loading.set(true);
    this.api
      .registrarInteraccion({
        idprospecto: this.idprospecto,
        tipo_evento: 'click',
        seccion: 'precios',
        timestamp_evento: Date.now(),
      })
      .subscribe({
        next: () => this.loading.set(false),
        error: (err) => {
          this.error.set(err?.error?.detail ?? 'Error al registrar interacción');
          this.loading.set(false);
        },
      });
  }

  cerrar(): void {
    clearDemoSessionToken();
    this.token.set(null);
    this.expiracion.set(null);
  }
}

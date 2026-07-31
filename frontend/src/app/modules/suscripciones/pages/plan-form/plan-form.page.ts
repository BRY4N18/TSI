import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import {
  NivelPlan,
  Plan,
  PlanLimites,
  PlanPatchRequest,
  PlanRequest,
} from '../../services/models/suscripciones.types';
import { PlanApiService } from '../../services/plan-api.service';

@Component({
  selector: 'app-plan-form-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './plan-form.page.html',
})
export class PlanFormPage implements OnInit {
  private readonly api = inject(PlanApiService);
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly notifications = inject(NotificationService);

  readonly enviando = signal(false);
  readonly cargando = signal(false);
  readonly error = signal<string | null>(null);
  readonly esEdicion = signal(false);
  readonly idplan = signal<number | null>(null);

  readonly niveles: NivelPlan[] = ['Básico', 'Profesional', 'Empresarial'];

  readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.minLength(2)]],
    precio: [0, [Validators.required, Validators.min(0)]],
    nivel: ['Básico' as NivelPlan, Validators.required],
    unidades_max: [1, [Validators.required, Validators.min(0)]],
    usuarios_max: [1, [Validators.required, Validators.min(0)]],
    api_calls_mes: [100, [Validators.required, Validators.min(0)]],
  });

  ngOnInit(): void {
    const idRaw = this.route.snapshot.paramMap.get('idplan');
    if (idRaw) {
      const id = Number(idRaw);
      if (!Number.isFinite(id) || id <= 0) {
        this.error.set('Identificador de plan inválido.');
        return;
      }
      this.esEdicion.set(true);
      this.idplan.set(id);
      this.cargarPlan(id);
    }
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    if (this.esEdicion()) {
      this.actualizar();
    } else {
      this.crear();
    }
  }

  isInvalid(control: string): boolean {
    const c = this.form.get(control);
    return Boolean(c && c.invalid && (c.dirty || c.touched));
  }

  private crear(): void {
    const body = this.toRequest();
    this.enviando.set(true);
    this.error.set(null);
    this.api.crear(body, crypto.randomUUID()).subscribe({
      next: () => {
        this.enviando.set(false);
        this.notifications.toast('Plan creado. Ya está en el catálogo.', 'success');
        void this.router.navigate(['/suscripciones/catalogo-planes']);
      },
      error: (err) => {
        this.enviando.set(false);
        this.error.set(err?.error?.detail ?? 'No se pudo crear el plan.');
      },
    });
  }

  private actualizar(): void {
    const id = this.idplan();
    if (id == null) return;
    const body: PlanPatchRequest = this.toRequest();
    this.enviando.set(true);
    this.error.set(null);
    this.api.actualizar(id, body, crypto.randomUUID()).subscribe({
      next: () => {
        this.enviando.set(false);
        this.notifications.toast('Plan actualizado correctamente.', 'success');
        void this.router.navigate(['/suscripciones/catalogo-planes']);
      },
      error: (err) => {
        this.enviando.set(false);
        this.error.set(err?.error?.detail ?? 'No se pudo actualizar el plan.');
      },
    });
  }

  private cargarPlan(id: number): void {
    this.cargando.set(true);
    this.api.buscarPorId(id).subscribe({
      next: (plan) => {
        this.cargando.set(false);
        if (!plan) {
          this.error.set('No se encontró el plan.');
          return;
        }
        this.patchFromPlan(plan);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(err?.error?.detail ?? 'Error al cargar el plan.');
      },
    });
  }

  private patchFromPlan(plan: Plan): void {
    const lim = this.parseLimites(plan.limites);
    this.form.setValue({
      nombre: plan.nombre ?? '',
      precio: Number(plan.precio ?? 0),
      nivel: (plan.nivel as NivelPlan) || 'Básico',
      unidades_max: lim.unidades_max,
      usuarios_max: lim.usuarios_max,
      api_calls_mes: lim.api_calls_mes,
    });
  }

  private toRequest(): PlanRequest {
    const v = this.form.getRawValue();
    return {
      nombre: v.nombre.trim(),
      precio: Number(v.precio),
      nivel: v.nivel,
      limites: {
        unidades_max: Number(v.unidades_max),
        usuarios_max: Number(v.usuarios_max),
        api_calls_mes: Number(v.api_calls_mes),
      },
    };
  }

  private parseLimites(limites?: PlanLimites | string): PlanLimites {
    if (!limites) {
      return { unidades_max: 0, usuarios_max: 0, api_calls_mes: 0 };
    }
    if (typeof limites === 'string') {
      try {
        return this.parseLimites(JSON.parse(limites) as PlanLimites);
      } catch {
        return { unidades_max: 0, usuarios_max: 0, api_calls_mes: 0 };
      }
    }
    return {
      unidades_max: Number(limites.unidades_max ?? 0),
      usuarios_max: Number(limites.usuarios_max ?? 0),
      api_calls_mes: Number(limites.api_calls_mes ?? 0),
    };
  }
}

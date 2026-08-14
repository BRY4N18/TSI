import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import {
  NivelPlan,
  PeriodicidadPlan,
  Plan,
  PlanLimites,
  PlanPatchRequest,
  PlanRequest,
  SeveridadCatalogo,
  SeveridadPlan,
} from '../../services/models/suscripciones.types';
import { PlanApiService } from '../../services/plan-api.service';

function safeJson(raw: string): unknown {
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

@Component({
  selector: 'app-plan-form-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, ListLoadingSkeletonComponent],
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
  readonly periodicidades: PeriodicidadPlan[] = ['Mensual', 'Anual'];

  /**
   * Catálogo de severidades leído de `Dim_Severidad`. Antes eran tres opciones
   * escritas en duro ('Baja'/'Media'/'Alta') que no correspondían a ninguna fila
   * del catálogo real; añadir o retirar una severidad exigía tocar el código.
   */
  readonly severidadesCatalogo = signal<SeveridadCatalogo[]>([]);
  /** Ids de severidad marcados. Vive fuera del form porque la lista es dinámica. */
  private readonly seleccion = signal<ReadonlySet<number>>(new Set<number>());

  readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.minLength(2)]],
    precio: [0, [Validators.required, Validators.min(0)]],
    precio_excedente_llamada: [0, [Validators.required, Validators.min(0)]],
    nivel: ['Básico' as NivelPlan, Validators.required],
    periodicidad: ['Mensual' as PeriodicidadPlan, Validators.required],
    carga_lote_habilitada: [false],
    unidades_max: [1, [Validators.required, Validators.min(0)]],
    usuarios_max: [1, [Validators.required, Validators.min(0)]],
    api_calls_mes: [100, [Validators.required, Validators.min(0)]],
    api_calls_minuto: [30, [Validators.required, Validators.min(0)]],
  });

  ngOnInit(): void {
    this.api.listarSeveridades().subscribe({
      next: (items) => {
        this.severidadesCatalogo.set(items);
        // Sin selección previa (alta), se marca la más leve: es el plan mínimo
        // razonable y evita publicar un plan que no cubre nada.
        if (!this.esEdicion() && this.seleccion().size === 0 && items.length) {
          this.seleccion.set(new Set([items[0].idseveridad]));
        }
      },
      error: () => this.error.set('No se pudo cargar el catálogo de severidades.'),
    });

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
    if (this.severidadesSeleccionadas().length === 0) {
      this.error.set('Selecciona al menos una severidad atendible.');
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
    this.seleccion.set(new Set(this.parseSeveridades(plan.severidades_desbloqueadas)));
    this.form.setValue({
      nombre: plan.nombre ?? '',
      precio: Number(plan.precio ?? 0),
      precio_excedente_llamada: Number(plan.precio_excedente_llamada ?? 0),
      nivel: (plan.nivel as NivelPlan) || 'Básico',
      periodicidad: (plan.periodicidad as PeriodicidadPlan) || 'Mensual',
      carga_lote_habilitada: Boolean(plan.carga_lote_habilitada),
      unidades_max: lim.unidades_max,
      usuarios_max: lim.usuarios_max,
      api_calls_mes: lim.api_calls_mes,
      api_calls_minuto: lim.api_calls_minuto,
    });
  }

  estaSeleccionada(idseveridad: number): boolean {
    return this.seleccion().has(idseveridad);
  }

  alternarSeveridad(idseveridad: number): void {
    const siguiente = new Set(this.seleccion());
    if (!siguiente.delete(idseveridad)) siguiente.add(idseveridad);
    this.seleccion.set(siguiente);
  }

  severidadesSeleccionadas(): SeveridadPlan[] {
    return [...this.seleccion()].sort((a, b) => a - b);
  }

  private parseSeveridades(raw?: SeveridadPlan[] | string): SeveridadPlan[] {
    const bruto: unknown = typeof raw === 'string' && raw.trim() ? safeJson(raw) : raw;
    if (!Array.isArray(bruto)) return [];
    return bruto.map(Number).filter((n) => Number.isFinite(n));
  }

  private toRequest(): PlanRequest {
    const v = this.form.getRawValue();
    return {
      nombre: v.nombre.trim(),
      precio: Number(v.precio),
      precio_excedente_llamada: Number(v.precio_excedente_llamada),
      nivel: v.nivel,
      periodicidad: v.periodicidad,
      severidades_desbloqueadas: this.severidadesSeleccionadas(),
      carga_lote_habilitada: v.carga_lote_habilitada,
      limites: {
        unidades_max: Number(v.unidades_max),
        usuarios_max: Number(v.usuarios_max),
        api_calls_mes: Number(v.api_calls_mes),
        api_calls_minuto: Number(v.api_calls_minuto),
      },
    };
  }

  private parseLimites(limites?: PlanLimites | string): PlanLimites {
    if (!limites) {
      return { unidades_max: 0, usuarios_max: 0, api_calls_mes: 0, api_calls_minuto: 0 };
    }
    if (typeof limites === 'string') {
      try {
        return this.parseLimites(JSON.parse(limites) as PlanLimites);
      } catch {
        return { unidades_max: 0, usuarios_max: 0, api_calls_mes: 0, api_calls_minuto: 0 };
      }
    }
    return {
      unidades_max: Number(limites.unidades_max ?? 0),
      usuarios_max: Number(limites.usuarios_max ?? 0),
      api_calls_mes: Number(limites.api_calls_mes ?? 0),
      api_calls_minuto: Number(limites.api_calls_minuto ?? 0),
    };
  }
}

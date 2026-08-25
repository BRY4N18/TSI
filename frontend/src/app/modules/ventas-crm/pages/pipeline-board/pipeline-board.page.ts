import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { EtapaPipeline, Prospecto } from '../../models/prospectos.types';
import { PipelineApiService } from '../../services/pipeline-api.service';
import { ProspectoApiService } from '../../services/prospecto-api.service';

const NEXT: Partial<
  Record<EtapaPipeline, 'Contactado' | 'Calificado' | 'Propuesta' | 'Negociación'>
> = {
  Nuevo: 'Contactado',
  Contactado: 'Calificado',
  Calificado: 'Propuesta',
  Propuesta: 'Negociación',
};

const BOARD_LIMIT = 100;

@Component({
  selector: 'app-pipeline-board',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    ReactiveFormsModule,
    TablerIconComponent,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="grid gap-6 pb-8 text-text-primary">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 class="tsi-display m-0 text-xl font-semibold">Pipeline</h1>
<div class="tsi-rail-h mt-2 w-24" aria-hidden="true"></div>
          <p class="m-0 mt-1 text-sm text-text-secondary">
            Avance adyacente con botones · sin arrastrar tarjetas
          </p>
        </div>
        <button
          type="button"
          data-testid="btn-actualizar-board"
          class="tsi-btn tsi-btn-secondary"
          (click)="cargar()"
        >
          Actualizar
        </button>
      </div>

      @if (loading()) {
        <app-list-loading-skeleton />
      } @else if (error()) {
        <app-list-error-state [message]="error()!" (retry)="cargar()" />
      } @else if (items().length === 0) {
        <app-list-empty-state message="Sin prospectos activos en el tablero." icon="list" />
      } @else {
        <div
          class="grid gap-3 overflow-x-auto md:grid-cols-5"
          data-testid="pipeline-board-columns"
        >
          @for (col of columnas; track col) {
            <div class="min-w-[12rem] rounded-md border border-border-default bg-bg-surface p-3">
              <h2 class="tsi-display m-0 mb-3 text-xs font-medium uppercase tracking-wide text-text-secondary">
                {{ col }}
              </h2>
              <div class="grid gap-2">
                @for (p of byEtapa(col); track p.idprospecto) {
                  <article
                    class="grid gap-2 rounded-md border border-border-default bg-bg-page p-3"
                    data-testid="pipeline-card"
                  >
                    <p class="m-0 text-sm font-medium text-text-primary">{{ p.empresa }}</p>
                    <p class="m-0 text-xs text-text-secondary">
                      {{ p.nombres }} {{ p.apellidos }}
                    </p>
                    <div class="flex flex-wrap items-center gap-1">
                      <a
                        [routerLink]="['/ventas-crm/prospectos', p.idprospecto]"
                        data-testid="btn-ver-prospecto-board"
                        class="inline-flex h-11 w-11 items-center justify-center rounded-md text-text-secondary no-underline hover:bg-bg-surface"
                        aria-label="Ver detalles"
                        title="Ver detalles"
                      >
                        <app-tabler-icon name="eye" [size]="18" />
                      </a>
                      @if (nextOf(p)) {
                        <button
                          type="button"
                          class="tsi-btn tsi-btn-primary"
                          [disabled]="busyId() === p.idprospecto"
                          (click)="avanzar(p)"
                        >
                          → {{ nextOf(p) }}
                        </button>
                      }
                      <button
                        type="button"
                        class="inline-flex min-h-11 items-center rounded-md px-2 text-xs font-medium text-alert-critical hover:bg-alert-critical-bg disabled:opacity-40"
                        [disabled]="busyId() === p.idprospecto"
                        (click)="pedirPerdido(p)"
                      >
                        Perdido
                      </button>
                    </div>
                  </article>
                }
              </div>
            </div>
          }
        </div>
      }

      @if (actionError()) {
        <div
          class="flex flex-wrap items-center gap-3 rounded-md border border-l-4 border-border-default border-l-alert-warning bg-alert-warning-bg p-4"
          role="alert"
        >
          <p class="m-0 flex-1 text-sm">{{ actionError() }}</p>
          <button
            type="button"
            data-testid="btn-refrescar-board"
            class="tsi-btn tsi-btn-secondary"
            (click)="cargar()"
          >
            Refrescar
          </button>
        </div>
      }
    </section>

    @if (perdidoTarget(); as target) {
      <div
        class="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4"
        role="dialog"
        aria-modal="true"
      >
        <div class="w-full max-w-md tsi-panel p-6">
          <h2 class="tsi-display m-0 mb-2 text-lg font-semibold">Marcar perdido — {{ target.empresa }}</h2>
          <form [formGroup]="perdidaForm" (ngSubmit)="confirmarPerdido()" class="grid gap-3">
            <input
              formControlName="motivo_perdida"
              placeholder="Motivo obligatorio"
              class="tsi-input"
            />
            <div class="flex justify-end gap-2">
              <button
                type="button"
                class="tsi-btn tsi-btn-primary"
                (click)="perdidoTarget.set(null)"
              >
                Cancelar
              </button>
              <button
                type="submit"
                class="tsi-btn border border-alert-critical bg-transparent text-alert-critical hover:bg-alert-critical-bg"
                [disabled]="perdidaForm.invalid || busyId() != null"
              >
                Confirmar
              </button>
            </div>
          </form>
        </div>
      </div>
    }
  `,
})
export class PipelineBoardPage implements OnInit {
  private readonly api = inject(ProspectoApiService);
  private readonly pipelineApi = inject(PipelineApiService);
  private readonly notifications = inject(NotificationService);
  private readonly fb = inject(FormBuilder);
  private readonly cdr = inject(ChangeDetectorRef);

  readonly columnas = ['Nuevo', 'Contactado', 'Calificado', 'Propuesta', 'Negociación'] as const;
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly actionError = signal<string | null>(null);
  readonly items = signal<Prospecto[]>([]);
  readonly busyId = signal<number | null>(null);
  readonly perdidoTarget = signal<Prospecto | null>(null);

  readonly perdidaForm = this.fb.nonNullable.group({
    motivo_perdida: ['', Validators.required],
  });

  ngOnInit(): void {
    this.cargar();
  }

  byEtapa(etapa: string): Prospecto[] {
    return this.items().filter((p) => p.activo && p.etapa_actual === etapa);
  }

  nextOf(p: Prospecto): 'Contactado' | 'Calificado' | 'Propuesta' | 'Negociación' | null {
    return NEXT[p.etapa_actual] ?? null;
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.actionError.set(null);
    this.api.listar({ activo: true, limit: BOARD_LIMIT }).subscribe({
      next: (res) => {
        this.items.set(res.data ?? []);
        this.loading.set(false);
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Error al cargar pipeline');
        this.loading.set(false);
        this.cdr.markForCheck();
      },
    });
  }

  avanzar(p: Prospecto): void {
    const next = this.nextOf(p);
    if (!next) return;
    this.busyId.set(p.idprospecto);
    this.actionError.set(null);
    this.pipelineApi
      .registrarTransicion(p.idprospecto, {
        etapa_nueva: next,
        etapa_actual_esperada: p.etapa_actual,
      })
      .subscribe({
        next: () => {
          this.busyId.set(null);
          this.notifications.toast('Etapa actualizada.', 'success');
          this.cargar();
        },
        error: (err) => this.handleErr(err, 'Conflicto o error de transición'),
      });
  }

  pedirPerdido(p: Prospecto): void {
    this.perdidaForm.reset({ motivo_perdida: '' });
    this.perdidoTarget.set(p);
  }

  confirmarPerdido(): void {
    const p = this.perdidoTarget();
    if (!p || this.perdidaForm.invalid) return;
    this.busyId.set(p.idprospecto);
    this.pipelineApi
      .registrarTransicion(p.idprospecto, {
        etapa_nueva: 'Perdido',
        etapa_actual_esperada: p.etapa_actual,
        motivo_perdida: this.perdidaForm.controls.motivo_perdida.value,
      })
      .subscribe({
        next: () => {
          this.busyId.set(null);
          this.perdidoTarget.set(null);
          this.notifications.toast('Marcado como perdido.', 'success');
          this.cargar();
        },
        error: (err) => this.handleErr(err, 'No se pudo marcar perdido'),
      });
  }

  private handleErr(err: { status?: number; error?: { detail?: string } }, fallback: string): void {
    this.busyId.set(null);
    this.perdidoTarget.set(null);
    const detail = err?.error?.detail ?? fallback;
    this.actionError.set(detail);
    this.notifications.toast(detail, err?.status === 409 ? 'warning' : 'critical');
    if (err?.status === 409) this.cargar();
    this.cdr.markForCheck();
  }
}

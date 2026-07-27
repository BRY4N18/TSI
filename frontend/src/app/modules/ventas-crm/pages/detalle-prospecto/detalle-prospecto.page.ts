import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { EtapaPipeline, Prospecto } from '../../models/prospectos.types';
import { ConversionApiService } from '../../services/conversion-api.service';
import { PipelineApiService } from '../../services/pipeline-api.service';
import { ProspectoApiService } from '../../services/prospecto-api.service';

const NEXT: Partial<Record<EtapaPipeline, EtapaPipeline>> = {
  Nuevo: 'Contactado',
  Contactado: 'Calificado',
  Calificado: 'Propuesta',
  Propuesta: 'Negociación',
};

@Component({
  selector: 'app-detalle-prospecto',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="page">
      @if (loading()) {
        <p>Cargando…</p>
      } @else if (error()) {
        <p class="err">{{ error() }}</p>
        <button type="button" (click)="cargar()">Reintentar</button>
      } @else if (prospecto()) {
        @let p = prospecto()!;
        <h1>{{ p.nombres }} {{ p.apellidos }}</h1>
        <p>{{ p.empresa }} · {{ p.etapa_actual }} · activo={{ p.activo }}</p>

        @if (p.activo && nextEtapa()) {
          <button type="button" [disabled]="busy()" (click)="avanzar()">
            Avanzar a {{ nextEtapa() }}
          </button>
        }
        @if (p.activo) {
          <form [formGroup]="perdidaForm" (ngSubmit)="marcarPerdido()">
            <input formControlName="motivo_perdida" placeholder="Motivo pérdida" />
            <button type="submit" [disabled]="busy() || perdidaForm.invalid">Marcar perdido</button>
          </form>
        }
        @if (p.activo && p.etapa_actual === 'Negociación') {
          <form [formGroup]="convForm" (ngSubmit)="convertir()">
            <select formControlName="tipo">
              <option value="Aseguradora">Aseguradora</option>
              <option value="Municipio">Municipio</option>
              <option value="Proveedor">Proveedor</option>
              <option value="Smart City">Smart City</option>
            </select>
            <input formControlName="nit_identificacion" placeholder="NIT" />
            <button type="submit" [disabled]="busy() || convForm.invalid">Convertir</button>
          </form>
        }
        @if (actionError()) {
          <p class="err">{{ actionError() }}</p>
        }
      }
    </section>
  `,
  styles: `
    .page {
      padding: 1.5rem;
      display: grid;
      gap: 0.75rem;
    }
    .err {
      color: #b00020;
    }
  `,
})
export class DetalleProspectoPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly prospectoApi = inject(ProspectoApiService);
  private readonly pipelineApi = inject(PipelineApiService);
  private readonly conversionApi = inject(ConversionApiService);
  private readonly fb = inject(FormBuilder);

  readonly loading = signal(true);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly actionError = signal<string | null>(null);
  readonly prospecto = signal<Prospecto | null>(null);

  readonly perdidaForm = this.fb.nonNullable.group({
    motivo_perdida: ['', Validators.required],
  });
  readonly convForm = this.fb.nonNullable.group({
    tipo: ['Aseguradora' as const, Validators.required],
    nit_identificacion: ['', Validators.required],
  });

  private id = 0;

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('idprospecto'));
    this.cargar();
  }

  nextEtapa(): EtapaPipeline | null {
    const p = this.prospecto();
    if (!p) return null;
    return (NEXT[p.etapa_actual] as EtapaPipeline) ?? null;
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.prospectoApi.obtener(this.id).subscribe({
      next: (res) => {
        this.prospecto.set(res.data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'No se pudo cargar');
        this.loading.set(false);
      },
    });
  }

  avanzar(): void {
    const p = this.prospecto();
    const next = this.nextEtapa();
    if (!p || !next || next === 'Ganado' || next === 'Perdido' || next === 'Nuevo') return;
    this.busy.set(true);
    this.actionError.set(null);
    this.pipelineApi
      .registrarTransicion(p.idprospecto, {
        etapa_nueva: next,
        etapa_actual_esperada: p.etapa_actual,
      })
      .subscribe({
        next: (res) => {
          this.prospecto.set(res.data.prospecto);
          this.busy.set(false);
        },
        error: (err) => {
          this.actionError.set(err?.error?.detail ?? 'Conflicto o error de transición');
          this.busy.set(false);
          if (err?.status === 409) this.cargar();
        },
      });
  }

  marcarPerdido(): void {
    const p = this.prospecto();
    if (!p || this.perdidaForm.invalid) return;
    this.busy.set(true);
    this.pipelineApi
      .registrarTransicion(p.idprospecto, {
        etapa_nueva: 'Perdido',
        etapa_actual_esperada: p.etapa_actual,
        motivo_perdida: this.perdidaForm.controls.motivo_perdida.value,
      })
      .subscribe({
        next: (res) => {
          this.prospecto.set(res.data.prospecto);
          this.busy.set(false);
        },
        error: (err) => {
          this.actionError.set(err?.error?.detail ?? 'No se pudo marcar perdido');
          this.busy.set(false);
        },
      });
  }

  convertir(): void {
    const p = this.prospecto();
    if (!p || this.convForm.invalid) return;
    this.busy.set(true);
    const v = this.convForm.getRawValue();
    this.conversionApi
      .convertir(
        p.idprospecto,
        {
          tipo: v.tipo,
          nit_identificacion: v.nit_identificacion,
          etapa_actual_esperada: 'Negociación',
        },
        crypto.randomUUID(),
      )
      .subscribe({
        next: (res) => {
          this.prospecto.set(res.data.prospecto);
          this.busy.set(false);
        },
        error: (err) => {
          this.actionError.set(err?.error?.detail ?? 'Conversión fallida');
          this.busy.set(false);
          if (err?.status === 409) this.cargar();
        },
      });
  }
}

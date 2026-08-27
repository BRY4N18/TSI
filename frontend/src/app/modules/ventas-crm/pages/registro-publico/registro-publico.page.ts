import { ChangeDetectionStrategy, Component, computed, inject, OnInit, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { RouterLink } from '@angular/router';

import { DEMO_QUERY_PARAM_GRANT, DEMO_QUERY_PARAM_IDPROSPECTO } from '../../models/notificacion-ventas.types';

import { BrandMarkComponent } from '../../../../shared/brand/brand-mark.component';
import { BrandPanelComponent } from '../../../../shared/brand/brand-panel.component';
import { ProspectoApiService } from '../../services/prospecto-api.service';
import { RegistroProspectoRequest, TipoOrganizacion } from '../../models/prospectos.types';

const TELEFONO_RE = /^\+?[0-9]{7,15}$/;
const TEXTO_LETRAS_RE = /^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s'-]+$/;
const CARGO_RE = /^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s/.-]+$/;
const EMAIL_RE = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

export const FUENTES_CONOCIMIENTO = [
  'Web / catálogo de planes',
  'Referido',
  'Redes sociales',
  'Google / búsqueda',
  'Evento / feria',
  'Llamada / ejecutivo',
  'Otro',
] as const;

export type FuenteConocimiento = (typeof FUENTES_CONOCIMIENTO)[number];

function telefonoValidator(control: AbstractControl): ValidationErrors | null {
  const raw = String(control.value ?? '')
    .trim()
    .replace(/[\s\-()]/g, '');
  if (!raw) return { required: true };
  return TELEFONO_RE.test(raw) ? null : { telefono: true };
}

@Component({
  selector: 'app-registro-publico',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, BrandMarkComponent, BrandPanelComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './registro-publico.page.html',
})
export class RegistroPublicoPage implements OnInit {
  private readonly api = inject(ProspectoApiService);
  private readonly fb = inject(FormBuilder);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal(false);
  readonly fuentes = FUENTES_CONOCIMIENTO;
  /** Capturados de la respuesta de registro para continuar hacia la demo (SRS §3.1.2). */
  readonly demoIdprospecto = signal<number | null>(null);
  readonly demoGrant = signal<string | null>(null);
  readonly demoQueryParamIdprospecto = DEMO_QUERY_PARAM_IDPROSPECTO;
  readonly demoQueryParamGrant = DEMO_QUERY_PARAM_GRANT;

  /**
   * Las plantillas de Angular no admiten claves computadas (`{ [k]: v }`), así
   * que el objeto de query params del enlace a la demo se arma aquí.
   */
  readonly demoQueryParams = computed(() => ({
    [DEMO_QUERY_PARAM_IDPROSPECTO]: this.demoIdprospecto(),
    [DEMO_QUERY_PARAM_GRANT]: this.demoGrant(),
  }));

  readonly form = this.fb.nonNullable.group({
    nombres: ['', [Validators.required, Validators.minLength(2), Validators.pattern(TEXTO_LETRAS_RE)]],
    apellidos: ['', [Validators.required, Validators.minLength(2), Validators.pattern(TEXTO_LETRAS_RE)]],
    gmail: ['', [Validators.required, Validators.pattern(EMAIL_RE)]],
    empresa: ['', [Validators.required, Validators.minLength(2)]],
    tipo_organizacion: ['Privado' as TipoOrganizacion, Validators.required],
    cargo: ['', [Validators.required, Validators.minLength(2), Validators.pattern(CARGO_RE)]],
    telefono: ['', [Validators.required, telefonoValidator]],
    fuente: ['' as '' | FuenteConocimiento, Validators.required],
    fuente_otro: [''],
  });

  ngOnInit(): void {
    this.form.controls.fuente.valueChanges.subscribe((fuente) => {
      const otro = this.form.controls.fuente_otro;
      if (fuente === 'Otro') {
        otro.setValidators([Validators.required, Validators.minLength(2)]);
      } else {
        otro.clearValidators();
        otro.setValue('');
      }
      otro.updateValueAndValidity({ emitEvent: false });
    });
  }

  onTextoInput(event: Event, field: 'nombres' | 'apellidos'): void {
    const input = event.target as HTMLInputElement;
    const clean = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s'-]/g, '');
    if (input.value !== clean) {
      input.value = clean;
      this.form.controls[field].setValue(clean);
    }
  }

  onCargoInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const clean = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s/.-]/g, '');
    if (input.value !== clean) {
      input.value = clean;
      this.form.controls.cargo.setValue(clean);
    }
  }

  onEmailInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const clean = input.value.replace(/\s+/g, '').toLowerCase();
    if (input.value !== clean) {
      input.value = clean;
      this.form.controls.gmail.setValue(clean);
    }
  }

  onTelefonoInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const val = input.value;
    const hasPlus = val.startsWith('+');
    const digitsOnly = val.replace(/[^0-9]/g, '');
    const clean = (hasPlus ? '+' : '') + digitsOnly;
    if (input.value !== clean) {
      input.value = clean;
      this.form.controls.telefono.setValue(clean);
    }
  }

  esOtro(): boolean {
    return this.form.controls.fuente.value === 'Otro';
  }

  fieldError(name: 'nombres' | 'apellidos' | 'gmail' | 'empresa' | 'cargo' | 'telefono' | 'fuente' | 'fuente_otro'): string | null {
    const ctrl = this.form.controls[name];
    if (!ctrl || !(ctrl.touched || ctrl.dirty) || ctrl.valid) return null;
    if (ctrl.hasError('required')) return 'Campo obligatorio.';
    if (ctrl.hasError('pattern') && (name === 'nombres' || name === 'apellidos')) {
      return 'Solo letras y espacios.';
    }
    if (ctrl.hasError('pattern') && name === 'cargo') {
      return 'Solo letras y caracteres de cargo válidos.';
    }
    if (ctrl.hasError('pattern') && name === 'gmail' || ctrl.hasError('email')) {
      return 'Ingresa un correo válido (ej. usuario@empresa.com).';
    }
    if (ctrl.hasError('minlength')) return 'Mínimo 2 caracteres.';
    if (ctrl.hasError('telefono')) {
      return 'Solo dígitos (opcional + al inicio), entre 7 y 15.';
    }
    return 'Valor inválido.';
  }

  inputClass(
    name: 'nombres' | 'apellidos' | 'gmail' | 'empresa' | 'cargo' | 'telefono' | 'fuente' | 'fuente_otro',
  ): string {
    // `.tsi-input` (design-system.md §5) ya resuelve alto, radio, foco y tema;
    // aqui solo se anade el estado invalido, que la clase canonica no cubre.
    const base = 'tsi-input w-full';
    return this.fieldError(name)
      ? `${base} border-alert-critical focus:border-alert-critical`
      : base;
  }

  selectClass(name: 'fuente' | 'tipo_organizacion'): string {
    // `.tsi-select` trae el chevron por tema; el que habia aqui era un SVG gris
    // fijo en la plantilla, invisible sobre fondo oscuro.
    const base = 'tsi-select w-full min-w-0';
    const invalid = name === 'fuente' ? this.fieldError('fuente') : null;
    return invalid ? `${base} border-alert-critical focus:border-alert-critical` : base;
  }

  private resolverComoNosConocio(): string {
    const { fuente, fuente_otro } = this.form.getRawValue();
    if (fuente === 'Otro') {
      return `Otro: ${fuente_otro.trim()}`;
    }
    return String(fuente).trim();
  }

  enviar(): void {
    this.form.markAllAsTouched();
    if (this.form.invalid || this.loading()) return;
    this.loading.set(true);
    this.error.set(null);
    const raw = this.form.getRawValue();
    const body: RegistroProspectoRequest = {
      nombres: raw.nombres.trim(),
      apellidos: raw.apellidos.trim(),
      gmail: raw.gmail.trim().toLowerCase(),
      empresa: raw.empresa.trim(),
      tipo_organizacion: raw.tipo_organizacion,
      cargo: raw.cargo.trim(),
      telefono: raw.telefono.trim().replace(/[\s\-()]/g, ''),
      como_nos_conocio: this.resolverComoNosConocio(),
    };
    this.api.registrar(body).subscribe({
      next: (res) => {
        this.loading.set(false);
        this.success.set(true);
        this.demoIdprospecto.set(res.data.idprospecto ?? null);
        this.demoGrant.set(res.data.demo_grant ?? null);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(
          err?.error?.detail ?? err?.error?.message ?? 'No se pudo registrar. Intenta de nuevo.',
        );
      },
    });
  }
}

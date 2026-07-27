import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ProspectoApiService } from '../../services/prospecto-api.service';
import { RegistroProspectoRequest, TipoOrganizacion } from '../../models/prospectos.types';

const TELEFONO_RE = /^\+?[0-9]{7,15}$/;

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
  imports: [ReactiveFormsModule, RouterLink],
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

  readonly form = this.fb.nonNullable.group({
    nombres: ['', [Validators.required, Validators.minLength(2)]],
    apellidos: ['', [Validators.required, Validators.minLength(2)]],
    gmail: ['', [Validators.required, Validators.email]],
    empresa: ['', [Validators.required, Validators.minLength(2)]],
    tipo_organizacion: ['Privado' as TipoOrganizacion, Validators.required],
    cargo: ['', [Validators.required, Validators.minLength(2)]],
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

  esOtro(): boolean {
    return this.form.controls.fuente.value === 'Otro';
  }

  fieldError(name: 'nombres' | 'apellidos' | 'gmail' | 'empresa' | 'cargo' | 'telefono' | 'fuente' | 'fuente_otro'): string | null {
    const ctrl = this.form.controls[name];
    if (!ctrl || !(ctrl.touched || ctrl.dirty) || ctrl.valid) return null;
    if (ctrl.hasError('required')) return 'Campo obligatorio.';
    if (ctrl.hasError('email')) return 'Correo inválido.';
    if (ctrl.hasError('minlength')) return 'Mínimo 2 caracteres.';
    if (ctrl.hasError('telefono')) {
      return 'Solo dígitos (opcional + al inicio), entre 7 y 15.';
    }
    return 'Valor inválido.';
  }

  inputClass(
    name: 'nombres' | 'apellidos' | 'gmail' | 'empresa' | 'cargo' | 'telefono' | 'fuente' | 'fuente_otro',
  ): string {
    const base =
      'box-border h-11 w-full min-w-0 rounded-md border bg-bg-page px-3 text-sm text-text-primary outline-none transition-[border-color,box-shadow] focus:shadow-[0_0_0_3px_rgba(46,111,242,0.15)]';
    const invalid = this.fieldError(name);
    return invalid
      ? `${base} border-alert-critical focus:border-alert-critical`
      : `${base} border-border-default focus:border-accent-primary`;
  }

  selectClass(name: 'fuente' | 'tipo_organizacion'): string {
    const base =
      'box-border h-11 w-full min-w-0 appearance-none rounded-md border bg-bg-page bg-[length:1rem] bg-[position:right_0.75rem_center] bg-no-repeat px-3 pr-10 text-sm text-text-primary outline-none transition-[border-color,box-shadow] focus:shadow-[0_0_0_3px_rgba(46,111,242,0.15)]';
    const invalid =
      name === 'fuente' ? this.fieldError('fuente') : null;
    const border = invalid
      ? 'border-alert-critical focus:border-alert-critical'
      : 'border-border-default focus:border-accent-primary';
    return `${base} ${border}`;
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
      next: () => {
        this.loading.set(false);
        this.success.set(true);
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

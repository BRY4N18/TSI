import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
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
export class RegistroPublicoPage {
  private readonly api = inject(ProspectoApiService);
  private readonly fb = inject(FormBuilder);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal(false);

  readonly form = this.fb.nonNullable.group({
    nombres: ['', [Validators.required, Validators.minLength(2)]],
    apellidos: ['', [Validators.required, Validators.minLength(2)]],
    gmail: ['', [Validators.required, Validators.email]],
    empresa: ['', [Validators.required, Validators.minLength(2)]],
    tipo_organizacion: ['Privado' as TipoOrganizacion, Validators.required],
    cargo: ['', [Validators.required, Validators.minLength(2)]],
    telefono: ['', [Validators.required, telefonoValidator]],
    como_nos_conocio: ['', [Validators.required, Validators.minLength(2)]],
  });

  fieldError(name: keyof RegistroPublicoPage['form']['controls']): string | null {
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

  inputClass(name: keyof RegistroPublicoPage['form']['controls']): string {
    const base =
      'box-border h-11 w-full min-w-0 rounded-md border bg-bg-page px-3 text-sm text-text-primary outline-none transition-[border-color,box-shadow] focus:shadow-[0_0_0_3px_rgba(46,111,242,0.15)]';
    const invalid = this.fieldError(name);
    return invalid
      ? `${base} border-alert-critical focus:border-alert-critical`
      : `${base} border-border-default focus:border-accent-primary`;
  }

  enviar(): void {
    this.form.markAllAsTouched();
    if (this.form.invalid || this.loading()) return;
    this.loading.set(true);
    this.error.set(null);
    const raw = this.form.getRawValue();
    const body: RegistroProspectoRequest = {
      ...raw,
      gmail: raw.gmail.trim().toLowerCase(),
      nombres: raw.nombres.trim(),
      apellidos: raw.apellidos.trim(),
      empresa: raw.empresa.trim(),
      cargo: raw.cargo.trim(),
      telefono: raw.telefono.trim().replace(/[\s\-()]/g, ''),
      como_nos_conocio: raw.como_nos_conocio.trim(),
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

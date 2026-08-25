import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { AuthApiService } from '../services/auth-api.service';
import { PasswordResetService } from '../services/password-reset.service';

/**
 * Dos flujos en una pantalla (FR-UI-007):
 *
 * - **Recuperación** (sin sesión): pide el correo y envía una contraseña temporal.
 * - **Cambio obligatorio** (`?forced=true`, con sesión): pide la contraseña
 *   temporal recibida y la definitiva.
 *
 * El segundo flujo no existía: quien entraba con una credencial temporal
 * aterrizaba aquí y solo podía pedirse **otra** temporal, así que no había forma
 * de terminar de activar la cuenta.
 */
@Component({
  selector: 'app-password-reset-page',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="grid min-h-screen place-items-center bg-bg-page p-6">
      <section
        class="grid w-full max-w-md gap-3 rounded-md border border-border-default bg-bg-surface p-8 shadow-[0_4px_24px_rgba(26,29,41,0.06)]"
        aria-labelledby="reset-title"
      >
        <h1 id="reset-title" class="tsi-display m-0 text-xl font-extrabold text-text-primary">
          {{ forcedChange() ? 'Cambio de contraseña obligatorio' : 'Recuperar contraseña' }}
        </h1>
<div class="tsi-rail-h mt-2 w-24" aria-hidden="true"></div>

        @if (forcedChange()) {
          <p class="m-0 text-sm text-text-secondary">
            Tu contraseña es temporal. Define una definitiva para continuar.
          </p>

          <form class="grid gap-2" [formGroup]="changeForm" (ngSubmit)="onChange()" novalidate>
            <label for="actual" class="text-sm font-semibold">Contraseña temporal</label>
            <input
              id="actual"
              type="password"
              class="tsi-input"
              formControlName="passwordActual"
              autocomplete="current-password"
            />

            <label for="nueva" class="text-sm font-semibold">Contraseña nueva</label>
            <input
              id="nueva"
              type="password"
              class="tsi-input"
              formControlName="passwordNueva"
              autocomplete="new-password"
            />
            <p class="m-0 text-xs text-text-secondary">Mínimo 8 caracteres.</p>

            <label for="repetir" class="text-sm font-semibold">Repetir contraseña nueva</label>
            <input
              id="repetir"
              type="password"
              class="tsi-input"
              formControlName="passwordRepetida"
              autocomplete="new-password"
            />

            @if (errorMessage()) {
              <p class="m-0 text-sm text-alert-critical" role="alert">{{ errorMessage() }}</p>
            }

            <button
              type="submit"
              data-testid="btn-cambiar-password"
              class="tsi-btn tsi-btn-primary mt-2"
              [disabled]="changeForm.invalid || loading()"
            >
              {{ loading() ? 'Guardando…' : 'Guardar contraseña' }}
            </button>
          </form>
        } @else {
          <p class="m-0 text-sm text-text-secondary">
            Ingresa tu correo registrado. Recibirás una contraseña temporal por email.
          </p>

          <form class="grid gap-2" [formGroup]="form" (ngSubmit)="onSubmit()" novalidate>
            <label for="gmail" class="text-sm font-semibold">Correo electrónico</label>
            <input
              id="gmail"
              type="email"
              class="tsi-input"
              formControlName="gmail"
              autocomplete="username"
              [attr.aria-invalid]="form.controls.gmail.invalid && form.controls.gmail.touched"
            />

            @if (errorMessage()) {
              <p class="m-0 text-sm text-alert-critical" role="alert">{{ errorMessage() }}</p>
            }

            @if (successMessage()) {
              <p class="m-0 text-sm text-alert-success" role="status">{{ successMessage() }}</p>
            }

            <button
              type="submit"
              class="tsi-btn tsi-btn-primary mt-2"
              [disabled]="form.invalid || loading()"
            >
              {{ loading() ? 'Enviando…' : 'Enviar contraseña temporal' }}
            </button>
          </form>
        }

        <a
          class="text-sm text-accent-primary no-underline hover:underline"
          routerLink="/cuentas-clientes/auth/login"
          >Volver al inicio de sesión</a
        >
      </section>
    </main>
  `,
})
export class PasswordResetPage implements OnInit {
  private readonly passwordResetService = inject(PasswordResetService);
  private readonly authApi = inject(AuthApiService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);

  readonly loading = signal(false);
  readonly forcedChange = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    gmail: ['', [Validators.required, Validators.email]],
  });

  readonly changeForm = this.fb.nonNullable.group({
    passwordActual: ['', [Validators.required]],
    passwordNueva: ['', [Validators.required, Validators.minLength(8)]],
    passwordRepetida: ['', [Validators.required]],
  });

  ngOnInit(): void {
    this.forcedChange.set(this.route.snapshot.queryParamMap.get('forced') === 'true');
  }

  onSubmit(): void {
    if (this.form.invalid || this.loading()) {
      return;
    }

    this.loading.set(true);
    this.errorMessage.set(null);
    this.successMessage.set(null);

    const { gmail } = this.form.getRawValue();

    this.passwordResetService
      .requestReset({ gmail })
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (response) => {
          this.successMessage.set(response.data.message);
          void this.router.navigate(['/cuentas-clientes/auth/login'], {
            queryParams: { reset: 'sent' },
          });
        },
        error: () => {
          this.errorMessage.set('No fue posible procesar la solicitud. Verifica tu correo.');
        },
      });
  }

  onChange(): void {
    if (this.changeForm.invalid || this.loading()) {
      return;
    }

    const { passwordActual, passwordNueva, passwordRepetida } = this.changeForm.getRawValue();
    if (passwordNueva !== passwordRepetida) {
      this.errorMessage.set('Las contraseñas nuevas no coinciden.');
      return;
    }

    this.loading.set(true);
    this.errorMessage.set(null);

    this.passwordResetService
      .changePassword({ password_actual: passwordActual, password_nueva: passwordNueva })
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: () => {
          // La sesión se abrió con la credencial temporal: se cierra para que el
          // usuario entre ya con la definitiva y el estado quede limpio.
          this.authApi.clearSession();
          void this.router.navigate(['/cuentas-clientes/auth/login'], {
            queryParams: { password: 'changed' },
          });
        },
        error: (err) => {
          this.errorMessage.set(
            err?.error?.detail ?? 'No fue posible actualizar la contraseña.',
          );
        },
      });
  }
}

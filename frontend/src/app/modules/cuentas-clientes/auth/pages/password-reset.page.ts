import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { PasswordResetService } from '../services/password-reset.service';

@Component({
  selector: 'app-password-reset-page',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="grid min-h-screen place-items-center bg-bg-page p-6">
      <section
        class="grid w-full max-w-md gap-3 rounded-lg border border-border-default bg-bg-surface p-8 shadow-[0_4px_24px_rgba(26,29,41,0.06)]"
        aria-labelledby="reset-title"
      >
        <h1 id="reset-title" class="m-0 text-xl font-bold text-text-primary">
          {{ forcedChange() ? 'Cambio de contraseña obligatorio' : 'Recuperar contraseña' }}
        </h1>

        @if (forcedChange()) {
          <p class="m-0 text-sm text-text-secondary">
            Debes solicitar una contraseña temporal y actualizarla antes de continuar.
          </p>
        } @else {
          <p class="m-0 text-sm text-text-secondary">
            Ingresa tu correo registrado. Recibirás una contraseña temporal por email.
          </p>
        }

        <form class="grid gap-2" [formGroup]="form" (ngSubmit)="onSubmit()" novalidate>
          <label for="gmail" class="text-sm font-semibold">Correo electrónico</label>
          <input
            id="gmail"
            type="email"
            class="rounded-md border border-border-default px-3 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
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
            class="mt-2 rounded-md bg-accent-primary p-3 font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-60"
            [disabled]="form.invalid || loading()"
          >
            {{ loading() ? 'Enviando…' : 'Enviar contraseña temporal' }}
          </button>
        </form>

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
}

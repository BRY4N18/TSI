import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { AuthApiService } from '../services/auth-api.service';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="grid min-h-screen place-items-center bg-bg-page p-6">
      <section
        class="grid w-full max-w-sm gap-3 rounded-lg border border-border-default bg-bg-surface p-8 shadow-[0_4px_24px_rgba(26,29,41,0.06)]"
        aria-labelledby="login-title"
      >
        <h1 id="login-title" class="m-0 text-2xl font-bold text-text-primary">Iniciar sesión</h1>
        <p class="m-0 mb-2 text-text-secondary">Tráfico Seguro Integral</p>

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

          <label for="password" class="text-sm font-semibold">Contraseña</label>
          <input
            id="password"
            type="password"
            class="rounded-md border border-border-default px-3 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            formControlName="password"
            autocomplete="current-password"
            [attr.aria-invalid]="form.controls.password.invalid && form.controls.password.touched"
          />

          @if (errorMessage()) {
            <p class="m-0 text-sm text-alert-critical" role="alert">{{ errorMessage() }}</p>
          }

          <button
            type="submit"
            class="mt-2 rounded-md bg-accent-primary p-3 font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-60"
            [disabled]="form.invalid || loading()"
          >
            {{ loading() ? 'Ingresando…' : 'Ingresar' }}
          </button>
        </form>

        <a
          class="text-sm text-accent-primary no-underline hover:underline"
          routerLink="/cuentas-clientes/auth/password-reset"
          >¿Olvidaste tu contraseña?</a
        >
      </section>
    </main>
  `,
})
export class LoginPage {
  private readonly authApi = inject(AuthApiService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);

  readonly loading = signal(false);
  readonly errorMessage = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    gmail: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  onSubmit(): void {
    if (this.form.invalid || this.loading()) {
      return;
    }

    this.loading.set(true);
    this.errorMessage.set(null);

    const { gmail, password } = this.form.getRawValue();

    this.authApi
      .login({ gmail, password })
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (response) => {
          const returnUrl =
            this.route.snapshot.queryParamMap.get('returnUrl') ?? '/cuentas-clientes';

          if (response.data.requiresPasswordChange) {
            void this.router.navigate(['/cuentas-clientes/auth/password-reset'], {
              queryParams: { forced: 'true' },
            });
            return;
          }

          void this.router.navigateByUrl(returnUrl);
        },
        error: () => {
          this.errorMessage.set('Credenciales inválidas o usuario inactivo.');
        },
      });
  }

  logout(): void {
    this.authApi.logout().subscribe({
      next: () => void this.router.navigate(['/cuentas-clientes/auth/login']),
      error: () => {
        this.authApi.clearSession();
        void this.router.navigate(['/cuentas-clientes/auth/login']);
      },
    });
  }
}

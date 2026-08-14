import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { AuthApiService } from '../services/auth-api.service';
import { resolvePostLoginPath } from '../services/post-login-home';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './login.page.html',
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
          const requestedReturn = this.route.snapshot.queryParamMap.get('returnUrl');

          if (response.data.requiresPasswordChange) {
            void this.router.navigate(['/cuentas-clientes/auth/password-reset'], {
              queryParams: { forced: 'true' },
            });
            return;
          }

          const target = resolvePostLoginPath(
            response.data.profile?.roles,
            requestedReturn,
            response.data.cuenta,
          );
          void this.router.navigateByUrl(target);
        },
        error: () => {
          this.errorMessage.set('Credenciales inválidas o usuario inactivo.');
        },
      });
  }
}

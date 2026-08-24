import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { MOTIVO_SESION_EXPIRADA } from '../../../../core/interceptors/sesion-expirada.interceptor';
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

  /**
   * Si el usuario llego aqui porque su sesion caduco con la pantalla abierta
   * (PG-UI-003), conviene decirselo: sin el aviso, la redireccion es
   * indistinguible de un cierre de sesion voluntario y parece que la
   * aplicacion se cerro sola.
   *
   * Se consume la marca al leerla — es un aviso de una vez, no un estado.
   */
  readonly sesionExpirada = signal(this.leerMotivoSesionExpirada());

  private leerMotivoSesionExpirada(): boolean {
    try {
      const marca = sessionStorage.getItem(MOTIVO_SESION_EXPIRADA);
      sessionStorage.removeItem(MOTIVO_SESION_EXPIRADA);
      return marca === '1';
    } catch {
      return false;
    }
  }

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
    this.sesionExpirada.set(false);

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

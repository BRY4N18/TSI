import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { AuthApiService } from '../services/auth-api.service';
import { homePathForRoles } from '../services/post-login-home';

/**
 * Acceso denegado por rol (HTTP 403 del lado de la navegación).
 *
 * 28 guards de rol ya redirigían aquí, pero la ruta no existía: el wildcard `**`
 * capturaba la navegación y llevaba al portal comercial público, donde un usuario
 * con sesión válida veía "Iniciar sesión / Registrarme" y parecía que se le había
 * caído la sesión. La página vive dentro del shell autenticado a propósito, para
 * que el usuario conserve su navegación y pueda irse a un módulo que sí le
 * corresponde (design-system §5, estados no felices: ícono + texto + acción).
 */
@Component({
  selector: 'app-access-denied',
  standalone: true,
  imports: [RouterLink, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="mx-auto max-w-6xl p-8">
      <div
        class="grid place-items-center gap-3 tsi-panel p-10 text-center"
        data-testid="access-denied"
        role="alert"
      >
        <span class="tsi-node h-14 w-12 bg-alert-warning-bg text-alert-warning" aria-hidden="true">
          <app-tabler-icon name="alert-triangle" [size]="24" />
        </span>
        <h1 class="tsi-display m-0 text-3xl font-extrabold text-text-primary">Acceso denegado</h1>
<div class="tsi-rail-h mt-2 w-24" aria-hidden="true"></div>
        <p class="m-0 max-w-md text-sm text-text-secondary">
          Tu sesión sigue activa, pero tu rol no tiene permiso para abrir esta sección.
          Si necesitas acceso, solicítalo al administrador de tu cuenta.
        </p>
        <p class="m-0 text-xs text-text-secondary" data-testid="rol-actual">
          Sesión: {{ gmail() }} · {{ roles() }}
        </p>
        <a
          [routerLink]="inicio()"
          data-testid="btn-volver-inicio"
          class="tsi-btn tsi-btn-primary mt-2 no-underline"
        >
          <app-tabler-icon name="arrow-left" [size]="16" />
          Volver a mi inicio
        </a>
      </div>
    </div>
  `,
})
export class AccessDeniedPage {
  private readonly authApi = inject(AuthApiService);
  private readonly router = inject(Router);

  gmail(): string {
    return this.authApi.getProfile()?.gmail ?? '—';
  }

  roles(): string {
    const roles = this.authApi.getProfile()?.roles ?? [];
    return roles.length ? roles.join(', ') : 'sin roles asignados';
  }

  inicio(): string {
    return homePathForRoles(this.authApi.getProfile()?.roles);
  }
}

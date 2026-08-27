import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter, map, startWith } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

@Component({
  selector: 'app-billing-shell',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './billing-shell.page.html',
})
export class BillingShellPage {
  private readonly auth = inject(AuthApiService);
  private readonly router = inject(Router);

  private readonly url = toSignal(
    this.router.events.pipe(
      filter((e): e is NavigationEnd => e instanceof NavigationEnd),
      map(() => this.router.url),
      startWith(this.router.url),
    ),
    { initialValue: this.router.url },
  );

  /** Formulario dedicado: sin header de módulo (un solo H1 en la página hija). */
  readonly isPlanFormRoute = computed(() => {
    const u = this.url();
    return /\/suscripciones\/planes(\/|$)/.test(u);
  });

  readonly showModuleHeader = computed(() => !this.isPlanFormRoute());

  readonly isDirectorOnly = computed(() => {
    const roles = this.auth.getProfile()?.roles ?? [];
    return roles.includes('DirectorEstrategia') && !roles.includes('Administrador');
  });
}

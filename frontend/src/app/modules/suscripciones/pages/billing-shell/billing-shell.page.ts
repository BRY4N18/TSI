import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter, map, startWith } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

interface BillingTab {
  label: string;
  path: string;
  roles: string[];
}

@Component({
  selector: 'app-billing-shell',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './billing-shell.page.html',
})
export class BillingShellPage {
  private readonly auth = inject(AuthApiService);
  private readonly router = inject(Router);

  private readonly allTabs: BillingTab[] = [
    { label: 'Mi suscripción', path: '/suscripciones/mi-suscripcion', roles: ['Cliente', 'Proveedor'] },
    { label: 'Métodos de pago', path: '/suscripciones/metodos-pago', roles: ['Cliente', 'Proveedor'] },
    { label: 'Facturas', path: '/suscripciones/historial-facturas', roles: ['Cliente', 'Proveedor'] },
    { label: 'Cambio de plan', path: '/suscripciones/cambio-plan', roles: ['Cliente', 'Proveedor'] },
    {
      label: 'Catálogo',
      path: '/suscripciones/catalogo-planes',
      roles: ['Cliente', 'Proveedor', 'Administrador', 'DirectorEstrategia'],
    },
    {
      label: 'Aprobaciones',
      path: '/suscripciones/aprobaciones-downgrade',
      roles: ['Administrador'],
    },
  ];

  private readonly url = toSignal(
    this.router.events.pipe(
      filter((e): e is NavigationEnd => e instanceof NavigationEnd),
      map(() => this.router.url),
      startWith(this.router.url),
    ),
    { initialValue: this.router.url },
  );

  readonly tabs = computed(() => {
    const roles = this.auth.getProfile()?.roles ?? [];
    if (!roles.length) {
      return this.allTabs.filter((t) => t.path.includes('catalogo'));
    }
    return this.allTabs.filter((t) => t.roles.some((r) => roles.includes(r)));
  });

  /** Formulario dedicado: sin header de módulo ni tabs (un solo H1 en la página hija). */
  readonly isPlanFormRoute = computed(() => {
    const u = this.url();
    return /\/suscripciones\/planes(\/|$)/.test(u);
  });

  readonly showTabs = computed(() => !this.isPlanFormRoute() && this.tabs().length > 1);

  readonly showModuleHeader = computed(() => !this.isPlanFormRoute());

  readonly isDirectorOnly = computed(() => {
    const roles = this.auth.getProfile()?.roles ?? [];
    return roles.includes('DirectorEstrategia') && !roles.includes('Administrador');
  });
}

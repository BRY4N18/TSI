import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

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

  private readonly allTabs: BillingTab[] = [
    { label: 'Mi suscripción', path: '/suscripciones/mi-suscripcion', roles: ['Cliente', 'Proveedor'] },
    { label: 'Métodos de pago', path: '/suscripciones/metodos-pago', roles: ['Cliente', 'Proveedor'] },
    { label: 'Facturas', path: '/suscripciones/historial-facturas', roles: ['Cliente', 'Proveedor'] },
    { label: 'Cambio de plan', path: '/suscripciones/cambio-plan', roles: ['Cliente', 'Proveedor'] },
    {
      label: 'Catálogo',
      path: '/suscripciones/catalogo-planes',
      roles: ['Cliente', 'Proveedor', 'Administrador'],
    },
    {
      label: 'Aprobaciones',
      path: '/suscripciones/aprobaciones-downgrade',
      roles: ['Administrador'],
    },
  ];

  readonly tabs = computed(() => {
    const roles = this.auth.getProfile()?.roles ?? [];
    if (!roles.length) {
      return this.allTabs.filter((t) => t.path.includes('catalogo'));
    }
    return this.allTabs.filter((t) => t.roles.some((r) => roles.includes(r)));
  });
}

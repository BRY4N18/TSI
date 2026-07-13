import { Routes } from '@angular/router';

import { roleGuard } from '../auth/guards/role.guard';
import { sessionGuard } from '../auth/guards/session.guard';
import { adminLocalOnboardingGuard } from './guards/admin-local-onboarding.guard';
import { onboardingPendienteGuard } from './guards/onboarding-pendiente.guard';
import { ConfiguracionPage } from './pages/configuracion/configuracion.page';
import { OnboardingWizardPage } from './pages/onboarding-wizard/onboarding-wizard.page';
import { RegistroPage } from './pages/registro/registro.page';

export const INCORPORACION_CLIENTES_ROUTES: Routes = [
  {
    path: 'registro',
    component: RegistroPage,
    canActivate: [sessionGuard, roleGuard],
    data: { roles: ['Administrador'] },
  },
  {
    path: ':idcliente',
    canActivate: [sessionGuard],
    children: [
      {
        path: 'configuracion',
        component: ConfiguracionPage,
        canActivate: [roleGuard],
        data: { roles: ['Administrador'] },
      },
      {
        path: 'onboarding',
        component: OnboardingWizardPage,
        canActivate: [adminLocalOnboardingGuard, onboardingPendienteGuard],
      },
      { path: '', redirectTo: 'configuracion', pathMatch: 'full' },
    ],
  },
];

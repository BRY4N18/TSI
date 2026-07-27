import { Routes } from '@angular/router';

import { roleGuard } from '../auth/guards/role.guard';
import { sessionGuard } from '../auth/guards/session.guard';
import { adminLocalOnboardingGuard } from './guards/admin-local-onboarding.guard';
import { onboardingPendienteGuard } from './guards/onboarding-pendiente.guard';
import { AprobacionSolicitudesPage } from './pages/aprobacion-solicitudes/aprobacion-solicitudes.page';
import { OnboardingWizardPage } from './pages/onboarding-wizard/onboarding-wizard.page';

export const INCORPORACION_CLIENTES_ROUTES: Routes = [
  // CU-O14 público vive en app.routes (fuera de sessionGuard)
  {
    path: 'solicitudes',
    component: AprobacionSolicitudesPage,
    canActivate: [sessionGuard, roleGuard],
    data: { roles: ['Administrador'] },
  },
  {
    path: ':idcliente',
    canActivate: [sessionGuard],
    children: [
      {
        path: 'onboarding',
        component: OnboardingWizardPage,
        canActivate: [adminLocalOnboardingGuard, onboardingPendienteGuard],
      },
      { path: '', redirectTo: 'onboarding', pathMatch: 'full' },
    ],
  },
];

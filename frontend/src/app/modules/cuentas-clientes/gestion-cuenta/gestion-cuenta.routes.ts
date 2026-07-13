import { Routes } from '@angular/router';

import { roleGuard } from '../auth/guards/role.guard';
import { sessionGuard } from '../auth/guards/session.guard';
import { adminLocalGuard } from './guards/admin-local.guard';
import { cuentaActivaGuard } from './guards/cuenta-activa.guard';
import { cuentaScopeGuard } from './guards/cuenta-scope.guard';
import { BajaPage } from './pages/baja/baja.page';
import { PerfilPage } from './pages/perfil/perfil.page';
import { PreferenciasPage } from './pages/preferencias/preferencias.page';
import { TransferenciaPage } from './pages/transferencia/transferencia.page';

export const GESTION_CUENTA_ROUTES: Routes = [
  {
    path: ':idcliente',
    canActivate: [sessionGuard, cuentaScopeGuard, cuentaActivaGuard],
    children: [
      { path: 'perfil', component: PerfilPage },
      { path: 'preferencias', component: PreferenciasPage },
      {
        path: 'transferencia',
        component: TransferenciaPage,
        canActivate: [adminLocalGuard],
      },
      {
        path: 'baja',
        component: BajaPage,
        canActivate: [roleGuard],
        data: { roles: ['Administrador'] },
      },
      { path: '', redirectTo: 'perfil', pathMatch: 'full' },
    ],
  },
];

import { Routes } from '@angular/router';

import { administradorSlaGuard } from './guards/administrador-sla.guard';
import { agenteSoporteGuard } from './guards/agente-soporte.guard';
import { clienteSoporteGuard } from './guards/cliente-soporte.guard';

export const SOPORTE_CLIENTE_ROUTES: Routes = [
  {
    path: 'mis-tickets',
    canActivate: [clienteSoporteGuard],
    loadComponent: () =>
      import('./pages/mis-tickets/mis-tickets.page').then((m) => m.MisTicketsPage),
  },
  {
    path: 'cola',
    canActivate: [agenteSoporteGuard],
    loadComponent: () =>
      import('./pages/cola-agente/cola-agente.page').then((m) => m.ColaAgentePage),
  },
  {
    // Sin guard de rol propio: Cliente y agentes comparten esta vista (filtrada
    // internamente por rol); la sesión ya se valida en el AppShellComponent padre
    // y el backend aplica ownership/permiso por rol en cada acción.
    path: 'tickets/:idReclamo',
    loadComponent: () =>
      import('./pages/detalle-ticket/detalle-ticket.page').then((m) => m.DetalleTicketPage),
  },
  {
    path: 'configuracion-sla',
    canActivate: [administradorSlaGuard],
    loadComponent: () =>
      import('./pages/configuracion-sla/configuracion-sla.page').then(
        (m) => m.ConfiguracionSlaPage,
      ),
  },
  {
    path: 'dashboard',
    canActivate: [agenteSoporteGuard],
    loadComponent: () =>
      import('./pages/dashboard-soporte/dashboard-soporte.page').then(
        (m) => m.DashboardSoportePage,
      ),
  },
  { path: '', pathMatch: 'full', redirectTo: 'mis-tickets' },
];

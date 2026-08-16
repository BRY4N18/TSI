/**
 * Rutas de los informes tácticos de suscripciones.
 *
 * ⚠️ **Dos autoridades distintas.** Facturas y métodos de pago son materia de
 * Finanzas; suscripciones y solicitudes, de Estrategia. Van antes de la ruta
 * genérica con su guard propio, porque el genérico daría a cada director el
 * área del otro.
 *
 * El índice usa el guard más permisivo —no muestra datos, solo enlaces— y filtra
 * por rol lo que ofrece.
 */

import { Routes } from '@angular/router';

import {
  informesCatalogoGuard,
  informesFinanzasGuard,
} from './guards/informes-suscripciones.guard';

export const SUSCRIPCIONES_INFORMES_ROUTES: Routes = [
  {
    path: '',
    canActivate: [informesCatalogoGuard],
    loadComponent: () =>
      import('./pages/indice/indice-informes.page').then((m) => m.IndiceInformesSuscripcionesPage),
  },
  {
    path: 'facturas',
    canActivate: [informesFinanzasGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformeSuscripcionesPage),
    data: { informe: 'facturas' },
  },
  {
    path: 'metodos-pago',
    canActivate: [informesFinanzasGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformeSuscripcionesPage),
    data: { informe: 'metodos-pago' },
  },
  {
    path: ':informe',
    canActivate: [informesCatalogoGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformeSuscripcionesPage),
  },
];

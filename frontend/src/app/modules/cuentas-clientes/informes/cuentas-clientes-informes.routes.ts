/**
 * Rutas de los informes tácticos de Cuentas y Clientes.
 *
 * Dos detalles que costaron una corrección al escribirlas:
 *
 * ⚠️ **`accesos-tecnicos` va antes de la ruta genérica y con su propio guard.**
 * Es el único que el Director Tecnológico puede ver. Con la genérica primero,
 * Angular la resolvería y aplicaría el guard de Administrador, dejándolo fuera
 * de lo único a lo que sí tiene acceso. Y como su `path` es literal, el
 * identificador viaja por `data` en vez de por el parámetro de ruta.
 *
 * ⚠️ **El índice lo protege el guard amplio.** Guardarlo solo con Administrador
 * dejaría al Director Tecnológico sin ninguna forma de llegar a su informe. El
 * índice no muestra datos —solo enlaces— y filtra por rol lo que ofrece.
 */

import { Routes } from '@angular/router';

import { INFORME_ACCESOS_TECNICOS } from './definiciones/informes-cuentas.definiciones';
import {
  informesAccesosTecnicosGuard,
  informesCuentasGuard,
} from './guards/informes-cuentas.guard';

export const CUENTAS_CLIENTES_INFORMES_ROUTES: Routes = [
  {
    path: '',
    canActivate: [informesAccesosTecnicosGuard],
    loadComponent: () =>
      import('./pages/indice/indice-informes.page').then((m) => m.IndiceInformesCuentasPage),
  },
  {
    path: INFORME_ACCESOS_TECNICOS,
    canActivate: [informesAccesosTecnicosGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformeCuentasPage),
    data: { informe: INFORME_ACCESOS_TECNICOS },
  },
  {
    path: ':informe',
    canActivate: [informesCuentasGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformeCuentasPage),
  },
];

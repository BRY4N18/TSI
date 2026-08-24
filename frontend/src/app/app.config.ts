import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter, withRouterConfig } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { authInterceptor } from './core/interceptors/auth.interceptor';
import { sesionExpiradaInterceptor } from './core/interceptors/sesion-expirada.interceptor';
import { demoSessionInterceptor } from './modules/ventas-crm/interceptors/demo-session.interceptor';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes, withRouterConfig({ paramsInheritanceStrategy: 'always' })),
    // demoSession after auth so demo Bearer overrides user JWT on /demo/interacciones
    provideHttpClient(withInterceptors([authInterceptor, demoSessionInterceptor, sesionExpiradaInterceptor])),
  ],
};

import { HttpInterceptorFn } from '@angular/common/http';

import { AUTH_STORAGE_KEYS } from '../../modules/cuentas-clientes/auth/services/auth-api.types';

const PUBLIC_AUTH_PATHS = ['/api/v1/auth/login', '/api/v1/auth/password-reset'];

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = localStorage.getItem(AUTH_STORAGE_KEYS.accessToken);
  const isPublicAuthRequest = PUBLIC_AUTH_PATHS.some((path) => req.url.includes(path));

  if (!token || isPublicAuthRequest) {
    return next(req);
  }

  return next(
    req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    }),
  );
};

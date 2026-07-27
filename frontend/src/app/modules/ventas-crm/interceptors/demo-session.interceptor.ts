import { HttpInterceptorFn } from '@angular/common/http';

const STORAGE_KEY = 'tsi.demo_session_token';

export const demoSessionInterceptor: HttpInterceptorFn = (req, next) => {
  if (!req.url.includes('/ventas-crm/demo/interacciones')) {
    return next(req);
  }
  const token =
    typeof localStorage !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null;
  if (!token) {
    return next(req);
  }
  return next(
    req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    }),
  );
};

export function storeDemoSessionToken(token: string): void {
  localStorage.setItem(STORAGE_KEY, token);
}

export function clearDemoSessionToken(): void {
  localStorage.removeItem(STORAGE_KEY);
}

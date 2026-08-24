import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { AuthApiService } from '../../modules/cuentas-clientes/auth/services/auth-api.service';

/**
 * PG-UI-003 — qué pasa cuando la sesión caduca con la pantalla abierta.
 *
 * **Antes de esto, nada.** No había una sola línea en todo el frontend que
 * mirara un `401`: cada componente recibía un error genérico y lo mostraba a su
 * manera —o no lo mostraba—, así que el usuario se quedaba en una pantalla que
 * había dejado de funcionar sin saber por qué, pulsando botones que ya no
 * hacían nada. Ni redirección, ni aviso.
 *
 * **Lo que este interceptor NO hace, y es lo importante.** No llama a
 * `localStorage.clear()`. Borra las cinco claves de sesión una a una
 * (`clearSession()`) y deja intacto todo lo demás — en particular
 * `tsi.registro-accidente.draft`, el borrador de un parte a medio escribir. Un
 * `clear()` sería una línea más corta y tiraría por el desagüe el trabajo del
 * usuario en el momento exacto en que la regla dice que hay que conservarlo.
 */

/**
 * En estas rutas un `401` significa «credenciales incorrectas», no «tu sesión
 * caducó». Redirigir al login desde el login sería un bucle, y ocultaría el
 * mensaje real que el usuario necesita leer.
 */
const RUTAS_DE_AUTENTICACION = ['/api/v1/auth/login', '/api/v1/auth/password-reset'];

/** Clave donde queda anotado por qué se llegó al login. */
export const MOTIVO_SESION_EXPIRADA = 'tsi.auth.sesionExpirada';

export const sesionExpiradaInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const authApi = inject(AuthApiService);

  return next(req).pipe(
    catchError((error: unknown) => {
      const esExpiracion =
        error instanceof HttpErrorResponse &&
        error.status === 401 &&
        !RUTAS_DE_AUTENTICACION.some((ruta) => req.url.includes(ruta));

      if (!esExpiracion) {
        return throwError(() => error);
      }

      authApi.clearSession();

      try {
        // Para poder explicar en el login *por qué* está ahí. Sin esto, la
        // redirección es indistinguible de un cierre de sesión voluntario.
        sessionStorage.setItem(MOTIVO_SESION_EXPIRADA, '1');
      } catch {
        // sessionStorage no disponible (modo privado): el aviso se pierde, la
        // redirección no.
      }

      // `returnUrl` para volver a donde estaba tras reautenticarse. Solo se
      // guarda si no estamos ya en el login, para no encadenarlos.
      const destino = router.url;
      const queryParams =
        destino && !destino.includes('/auth/login') ? { returnUrl: destino } : {};

      void router.navigate(['/cuentas-clientes/auth/login'], { queryParams });

      return throwError(() => error);
    }),
  );
};

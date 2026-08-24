/** @marker unit */
/**
 * PG-UI-003 — la sesión caduca con la pantalla abierta.
 *
 * **El estado anterior era «nada».** No había una sola referencia a `401` en
 * todo el frontend fuera de los specs: la sesión expiraba y cada componente
 * mostraba —o no— un error genérico, dejando al usuario en una pantalla muerta
 * pulsando botones que ya no hacían nada.
 *
 * El aserto que da sentido a la regla es el del borrador: redirigir al login es
 * fácil, y `localStorage.clear()` es una línea más corta que borrar las cinco
 * claves de sesión. Esa línea más corta se llevaría por delante el parte de
 * accidente a medio escribir, justo en el momento en que hay que conservarlo.
 */
import {
  HttpErrorResponse,
  HttpEvent,
  HttpHandlerFn,
  HttpRequest,
  HttpResponse,
} from '@angular/common/http';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { Observable, of, throwError } from 'rxjs';

import { AuthApiService } from '../../modules/cuentas-clientes/auth/services/auth-api.service';
import { AUTH_STORAGE_KEYS } from '../../modules/cuentas-clientes/auth/services/auth-api.types';
import {
  MOTIVO_SESION_EXPIRADA,
  sesionExpiradaInterceptor,
} from './sesion-expirada.interceptor';

const CLAVE_BORRADOR = 'tsi.registro-accidente.draft';

describe('sesionExpiradaInterceptor', () => {
  let router: jasmine.SpyObj<Router>;
  let authApi: AuthApiService;

  /** Ejecuta el interceptor con un handler que devuelve el error indicado. */
  function ejecutar(url: string, status: number): Observable<unknown> {
    const req = new HttpRequest('GET', url);
    const next: HttpHandlerFn = () =>
      status === 200
        ? of<HttpEvent<unknown>>(new HttpResponse({ status: 200, url }))
        : throwError(() => new HttpErrorResponse({ status, url }));
    return TestBed.runInInjectionContext(() => sesionExpiradaInterceptor(req, next));
  }

  beforeEach(() => {
    router = jasmine.createSpyObj('Router', ['navigate'], { url: '/despacho/monitoreo/ACC-1' });
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), AuthApiService, { provide: Router, useValue: router }],
    });
    authApi = TestBed.inject(AuthApiService);

    localStorage.setItem(AUTH_STORAGE_KEYS.accessToken, 'token-vivo');
    localStorage.setItem(CLAVE_BORRADOR, JSON.stringify({ descripcion: 'choque en la vía 5' }));
    sessionStorage.removeItem(MOTIVO_SESION_EXPIRADA);
  });

  afterEach(() => {
    localStorage.removeItem(AUTH_STORAGE_KEYS.accessToken);
    localStorage.removeItem(CLAVE_BORRADOR);
    sessionStorage.removeItem(MOTIVO_SESION_EXPIRADA);
  });

  it('cuando_llega_un_401_conserva_el_borrador_del_usuario', (done) => {
    // **El aserto que importa de esta regla.**
    ejecutar('/api/v1/accidentes/ACC-1', 401).subscribe({
      error: () => {
        expect(localStorage.getItem(CLAVE_BORRADOR)).toBe(
          JSON.stringify({ descripcion: 'choque en la vía 5' }),
        );
        done();
      },
    });
  });

  it('cuando_llega_un_401_borra_la_sesion_y_redirige_al_login', (done) => {
    ejecutar('/api/v1/accidentes/ACC-1', 401).subscribe({
      error: () => {
        expect(localStorage.getItem(AUTH_STORAGE_KEYS.accessToken)).toBeNull();
        expect(router.navigate).toHaveBeenCalledWith(
          ['/cuentas-clientes/auth/login'],
          { queryParams: { returnUrl: '/despacho/monitoreo/ACC-1' } },
        );
        done();
      },
    });
  });

  it('cuando_llega_un_401_deja_anotado_por_que_para_poder_explicarlo', (done) => {
    // Sin la marca, la redirección es indistinguible de un cierre voluntario y
    // la aplicación parece cerrarse sola.
    ejecutar('/api/v1/accidentes/ACC-1', 401).subscribe({
      error: () => {
        expect(sessionStorage.getItem(MOTIVO_SESION_EXPIRADA)).toBe('1');
        done();
      },
    });
  });

  it('cuando_el_401_viene_del_login_no_redirige', (done) => {
    // Ahí un 401 significa «credenciales incorrectas». Redirigir sería un bucle
    // y taparía el mensaje que el usuario necesita leer.
    ejecutar('/api/v1/auth/login', 401).subscribe({
      error: () => {
        expect(router.navigate).not.toHaveBeenCalled();
        expect(localStorage.getItem(AUTH_STORAGE_KEYS.accessToken)).toBe('token-vivo');
        done();
      },
    });
  });

  it('cuando_llega_un_403_no_hace_nada', (done) => {
    // Un 403 es «esto no te corresponde», con la sesión perfectamente viva.
    // Cerrarla expulsaría al usuario por pulsar donde no debía.
    ejecutar('/api/v1/partners/9', 403).subscribe({
      error: () => {
        expect(router.navigate).not.toHaveBeenCalled();
        expect(localStorage.getItem(AUTH_STORAGE_KEYS.accessToken)).toBe('token-vivo');
        done();
      },
    });
  });

  it('cuando_la_peticion_va_bien_no_toca_nada', (done) => {
    ejecutar('/api/v1/accidentes/ACC-1', 200).subscribe(() => {
      expect(router.navigate).not.toHaveBeenCalled();
      expect(localStorage.getItem(AUTH_STORAGE_KEYS.accessToken)).toBe('token-vivo');
      done();
    });
  });

  it('cuando_el_error_se_propaga_el_componente_todavia_puede_reaccionar', (done) => {
    // El interceptor no consume el error: lo relanza. Si lo tragara, un
    // componente que muestra su propio aviso se quedaría en «cargando…» para
    // siempre mientras la redirección ocurre por debajo.
    ejecutar('/api/v1/accidentes/ACC-1', 401).subscribe({
      next: () => fail('el error no debe convertirse en éxito'),
      error: (err: unknown) => {
        expect(err instanceof HttpErrorResponse).toBeTrue();
        expect((err as HttpErrorResponse).status).toBe(401);
        done();
      },
    });
  });
});

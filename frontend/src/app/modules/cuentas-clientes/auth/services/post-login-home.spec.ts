/** @marker unit */
import {
  homePathForRoles,
  onboardingPathForCuenta,
  resolvePostLoginPath,
} from './post-login-home';

describe('post-login-home', () => {
  it('homePathForRoles_unidad_goes_to_mi_despacho', () => {
    expect(homePathForRoles(['Unidad'])).toBe('/despacho/mi-despacho');
  });

  it('homePathForRoles_operador_goes_to_lista_accidentes', () => {
    expect(homePathForRoles(['Operador'])).toBe('/accidentes/lista');
  });

  it('resolvePostLoginPath_ignores_generic_cuentas_hub_for_unidad', () => {
    expect(resolvePostLoginPath(['Unidad'], '/cuentas-clientes')).toBe('/despacho/mi-despacho');
    expect(resolvePostLoginPath(['Unidad'], null)).toBe('/despacho/mi-despacho');
  });

  it('resolvePostLoginPath_keeps_explicit_deep_link', () => {
    expect(resolvePostLoginPath(['Unidad'], '/seguimiento/mi-seguimiento')).toBe(
      '/seguimiento/mi-seguimiento',
    );
  });

  describe('incorporación pendiente (SRS §3.2.2)', () => {
    const cuentaPendiente = { idcliente: 920003, onboardingPendiente: true };
    const cuentaCompletada = { idcliente: 920003, onboardingPendiente: false };

    it('lleva a la incorporación cuando la cuenta la tiene pendiente', () => {
      expect(onboardingPathForCuenta(cuentaPendiente)).toBe(
        '/cuentas-clientes/incorporacion-clientes/920003/onboarding',
      );
    });

    it('no desvía cuando la incorporación ya está completada', () => {
      expect(onboardingPathForCuenta(cuentaCompletada)).toBeNull();
      expect(onboardingPathForCuenta(null)).toBeNull();
    });

    it('la incorporación pendiente manda sobre el home del rol', () => {
      expect(resolvePostLoginPath(['Cliente'], null, cuentaCompletada)).toBe(
        '/soporte-cliente/mis-tickets',
      );
      expect(resolvePostLoginPath(['Cliente'], null, cuentaPendiente)).toBe(
        '/cuentas-clientes/incorporacion-clientes/920003/onboarding',
      );
    });

    it('un deep-link explícito sigue teniendo prioridad', () => {
      expect(
        resolvePostLoginPath(['Cliente'], '/suscripciones/mi-suscripcion', cuentaPendiente),
      ).toBe('/suscripciones/mi-suscripcion');
    });
  });
});

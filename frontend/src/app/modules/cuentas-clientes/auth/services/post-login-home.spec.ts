/** @marker unit */
import { homePathForRoles, resolvePostLoginPath } from './post-login-home';

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
});

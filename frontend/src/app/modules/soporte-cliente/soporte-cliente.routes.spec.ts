/** @marker unit */
import { SOPORTE_CLIENTE_ROUTES } from './soporte-cliente.routes';

describe('SOPORTE_CLIENTE_ROUTES', () => {
  it('defines_lazy_routes_with_guards', () => {
    expect(SOPORTE_CLIENTE_ROUTES.length).toBeGreaterThanOrEqual(5);
    expect(SOPORTE_CLIENTE_ROUTES[0].canActivate?.length).toBeGreaterThan(0);
  });
});

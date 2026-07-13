/** @marker unit */
import { DESPACHO_ROUTES } from './despacho.routes';

describe('DESPACHO_ROUTES', () => {
  it('defines_lazy_routes_with_guards', () => {
    expect(DESPACHO_ROUTES.length).toBeGreaterThanOrEqual(4);
    expect(DESPACHO_ROUTES[0].canActivate?.length).toBeGreaterThan(0);
  });
});

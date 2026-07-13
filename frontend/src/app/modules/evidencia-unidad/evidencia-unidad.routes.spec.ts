/** @marker unit */
import { EVIDENCIA_UNIDAD_ROUTES } from './evidencia-unidad.routes';

describe('EVIDENCIA_UNIDAD_ROUTES', () => {
  it('defines lazy routes with guards', () => {
    // Arrange
    const paths = EVIDENCIA_UNIDAD_ROUTES.map((route) => route.path);

    // Assert
    expect(paths).toContain('disponibilidad');
    expect(paths).toContain('accidentes/:idaccidente/galeria');
    expect(paths).toContain('flota');
  });
});

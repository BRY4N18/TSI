import { duracionLegible } from './duracion';

describe('duracionLegible', () => {
  it('no convierte una espera corta en cero', () => {
    // ⚠️ El defecto original: 19 minutos se publicaban como «0 días», y «0» se
    // lee como «instantáneo». La columna existe para ver cuál tarda.
    expect(duracionLegible(19)).toBe('19 min');
    expect(duracionLegible(5)).toBe('5 min');
  });

  it('distingue minutos de horas y de días', () => {
    expect(duracionLegible(90)).toBe('1.5 h');
    expect(duracionLegible(60 * 20)).toBe('20 h');
    expect(duracionLegible(60 * 24 * 3)).toBe('3.0 días');
  });

  it('dice «menos de 1 min» en vez de cero', () => {
    // Cero se lee como instantáneo; lo que pasó es que la espera fue más corta
    // que la unidad con la que se mide.
    expect(duracionLegible(0)).toBe('menos de 1 min');
  });

  it('la ausencia no es cero', () => {
    expect(duracionLegible(null)).toBe('—');
    expect(duracionLegible(undefined)).toBe('—');
  });
});

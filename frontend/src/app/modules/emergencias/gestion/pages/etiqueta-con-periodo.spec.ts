import { etiquetaConPeriodo } from './pantalla-z.page';

/**
 * ⚠️ Esta prueba existe porque el fallo llegó a pantalla.
 *
 * Cuando un informe agrupa por período, la misma unidad o el mismo condado
 * aparecen **una vez por período**. La tabla los pintaba con la etiqueta
 * desnuda: dos filas «TSI-001» con 71 s y 62 s, dos filas «Benito Juarez» con
 * 149 y 23. Se leía como un dato contradictorio, no como dos meses distintos.
 */
describe('etiquetaConPeriodo', () => {
  const conPeriodos = [
    { unidad: 'TSI-001', periodo: '2026-07' },
    { unidad: 'TSI-001', periodo: '2026-08' },
  ];

  it('añade el período cuando hay más de uno en la tabla', () => {
    expect(etiquetaConPeriodo(conPeriodos[0], 'unidad', conPeriodos)).toBe('TSI-001 · 2026-07');
    expect(etiquetaConPeriodo(conPeriodos[1], 'unidad', conPeriodos)).toBe('TSI-001 · 2026-08');
  });

  it('no lo añade cuando la tabla entera es de un solo período', () => {
    // Repetirlo en cada fila sería ruido: no distingue nada.
    const uno = [{ unidad: 'TSI-001', periodo: '2026-07' }];
    expect(etiquetaConPeriodo(uno[0], 'unidad', uno)).toBe('TSI-001');
  });

  it('no lo añade cuando el informe no agrupa por período', () => {
    const sin = [{ unidad: 'TSI-001' }, { unidad: 'TSI-002' }];
    expect(etiquetaConPeriodo(sin[0], 'unidad', sin)).toBe('TSI-001');
  });

  it('marca la ausencia del campo sin perder el período', () => {
    const filas = [{ periodo: '2026-07' }, { unidad: 'TSI-002', periodo: '2026-08' }];
    expect(etiquetaConPeriodo(filas[0], 'unidad', filas)).toBe('— · 2026-07');
  });
});

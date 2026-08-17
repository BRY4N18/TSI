import { num } from './informes-compuestos.types';

/**
 * D7: el SQL táctico pone `ratio` nulo cuando no hay unidades. Un 0 diría
 * «capacidad de sobra».
 */
export function esSinCapacidad(fila: Record<string, unknown>): boolean {
  const casos = num(fila['casos']) ?? 0;
  const unidades = num(fila['unidades_vigentes']);
  const ratio = num(fila['ratio']);
  if (casos <= 0) {
    return false;
  }
  return unidades === 0 || unidades === null || ratio === null;
}

/**
 * Opciones de los filtros de enumeración, comunes a los siete departamentos.
 *
 * ⚠️ **El valor no se toca nunca; solo la etiqueta.**
 *
 * Los valores de estas enumeraciones son los **literales que guarda el origen**
 * (`En_Validación`, `Pendiente_de_clasificacion`, `Producción activa`), y viajan
 * verbatim a la API como valor del filtro. Normalizarlos —quitar guiones bajos,
 * arreglar acentos, pasar a minúsculas— rompería el filtro en silencio: la
 * petición saldría con un valor que el origen no conoce y la respuesta sería una
 * lista vacía con 200, indistinguible de «no hay nada que mostrar».
 *
 * Por eso `humanizar` produce únicamente el texto que se pinta, y `valor` se
 * copia sin tocar.
 */

import { OpcionFiltro } from './informes-listado.types';

/**
 * Texto legible de un literal del origen.
 *
 * Se limita a dos cosas: guion bajo → espacio, y mayúscula inicial. **No añade
 * acentos que el literal no traiga** (`Pendiente_de_clasificacion` se pinta
 * «Pendiente de clasificacion», sin tilde): inventarlos aquí haría que la
 * pantalla y el dato dijeran cosas distintas, y quien buscara el valor en el
 * origen no lo encontraría.
 */
export function humanizar(valor: string): string {
  const texto = valor.replace(/_/g, ' ');
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

/** Construye las opciones de un filtro conservando el valor original. */
export function opciones(valores: readonly string[]): OpcionFiltro[] {
  return valores.map((valor) => ({ valor, etiqueta: humanizar(valor) }));
}

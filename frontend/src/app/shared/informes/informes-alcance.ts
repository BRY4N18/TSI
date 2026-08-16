/**
 * Cómo se dice en pantalla el alcance real de una respuesta.
 *
 * `meta.acotado_a` existe para que **un resultado vacío no sea ambiguo**: sin
 * él, un cliente no puede distinguir «no hubo accidentes graves» de «no hubo
 * accidentes graves *en mis zonas*». Si la tabla lo ignora, vuelve exactamente
 * la ambigüedad que costó construirlo en backend.
 *
 * Contrato: `specs/002-tactico/contrato-informes-simples-frontend.md` §2.1.
 */

import { AcotadoA } from './informes-listado.types';

export interface AvisoAlcance {
  /** Texto para una respuesta con filas. */
  texto: string;
  /** Texto para la respuesta vacía, que es donde la ambigüedad muerde. */
  textoVacio: string;
}

/**
 * ⚠️ `zonas_contratadas` **no** es `propios`.
 *
 * Los accidentes ocurridos en una zona contratada no pertenecen al cliente: son
 * hechos de terceros que ocurrieron donde él contrató cobertura. Un texto que
 * dijera «tus accidentes» afirmaría algo falso sobre datos de siniestralidad
 * ajenos, y por eso el backend le dio un valor propio en vez de reutilizar
 * `propios`.
 */
const AVISOS: Record<Exclude<AcotadoA, 'todos'>, AvisoAlcance> = {
  propios: {
    texto: 'Solo se muestran tus registros.',
    textoVacio: 'No hay resultados entre tus registros.',
  },
  zonas_contratadas: {
    texto: 'Solo se muestra lo ocurrido en las zonas que tienes contratadas.',
    textoVacio:
      'No hay resultados en las zonas que tienes contratadas. Puede haberlos en otras.',
  },
};

/**
 * Devuelve el aviso, o `null` cuando no hay nada que advertir.
 *
 * `todos` **no produce aviso**: es el caso normal, y un cartel permanente
 * diciendo «ves todo» sería ruido que enseñaría a ignorar la franja donde a
 * veces sí hay una advertencia real.
 */
export function avisoDeAlcance(acotado?: AcotadoA): AvisoAlcance | null {
  if (!acotado || acotado === 'todos') {
    return null;
  }
  return AVISOS[acotado] ?? null;
}

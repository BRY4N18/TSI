/**
 * Cómo se dice en pantalla el alcance real de una respuesta.
 *
 * Son **dos avisos distintos**, y conviene no confundirlos:
 *
 * * `meta.acotado_a` responde **a quién** pertenece lo que se ve. Sin él, un
 *   resultado vacío es ambiguo: «no hubo accidentes graves» y «no hubo
 *   accidentes graves *en mis zonas*» se leen igual.
 * * `meta.alcance` responde **qué describe el listado**, cuando su nombre podría
 *   leerse como otra cosa. Lo emite un solo listado, y su omisión sería peor que
 *   la del anterior: llevaría a decidir cobertura sobre unidades que no pueden
 *   acudir.
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
 * Qué describe un listado cuyo nombre podría leerse como otra cosa.
 *
 * ⚠️ **`composicion_de_flota` es el caso de mayor consecuencia de la serie.**
 * `dado_de_alta` significa que la unidad **existe**, no que pueda acudir: su
 * disponibilidad operativa —Activa, Ocupada, En Misión, Fuera de servicio— vive
 * en el histórico y **no está en ese listado**.
 *
 * Quien lo leyera como cobertura decidiría sobre unidades fuera de servicio,
 * ocupadas o ya en camino a otro accidente. El backend lo declara justo para que
 * la pantalla lo diga; perderlo aquí devolvería el riesgo entero.
 */
const ALCANCES: Record<string, string> = {
  composicion_de_flota:
    'Este listado describe qué unidades existen, no cuáles están disponibles ahora. ' +
    'Una unidad dada de alta puede estar ocupada, en misión o fuera de servicio.',
};

/**
 * Devuelve el aviso de titularidad, o `null` cuando no hay nada que advertir.
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

/**
 * Devuelve la advertencia sobre **qué describe** el listado, si la declara.
 *
 * Un valor desconocido devuelve `null` en vez de pintarse crudo: `meta.alcance`
 * es un identificador, no un texto para el usuario, y mostrarlo tal cual daría
 * una advertencia ilegible justo donde hace falta que se entienda.
 */
export function advertenciaDeContenido(alcance?: string): string | null {
  if (!alcance) {
    return null;
  }
  return ALCANCES[alcance] ?? null;
}

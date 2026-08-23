/**
 * Texto del estado vacío de las pantallas de gestión.
 *
 * ⚠️ **«Sin datos» y «no te toca verlos» no son lo mismo, y se veían igual.**
 *
 * Las pantallas pintaban «Sin datos en este período» siempre, incluso cuando la
 * respuesta venía acotada por titularidad. Un `Administrador` entra a los
 * informes de Ventas y CRM **acotado a lo suyo**, y no es dueño de ningún
 * prospecto: recibía cero filas en los trece informes y la pantalla le echaba la
 * culpa al período.
 *
 * El fallo no es que la cifra esté mal —cero es correcto— sino que **señala la
 * causa equivocada**: quien lee eso amplía el rango de fechas, y lo puede
 * ampliar hasta el principio de los tiempos sin que aparezca una sola fila. La
 * pantalla declara su alcance en un panel aparte, pero nadie relaciona las dos
 * cosas cuando una dice «período» con todas las letras.
 */

/** Alcance declarado en `meta.acotado_a`, o `null` si ninguno lo declara. */
export type AlcanceDeclarado = 'todos' | 'propios' | string | null;

export const VACIO_SIN_DATOS = 'Sin datos en este período.';

export function mensajeVacio(alcance: AlcanceDeclarado): string {
  if (alcance === 'propios') {
    return 'Sin datos en este período dentro de tu alcance: solo ves lo tuyo, y puede haber datos de otras personas que este informe no te muestra.';
  }
  if (alcance === 'zonas_contratadas') {
    return 'Sin datos en este período dentro de las zonas que tienes contratadas.';
  }
  return VACIO_SIN_DATOS;
}

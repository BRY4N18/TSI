/**
 * Duraciones que se leen según su magnitud.
 *
 * ⚠️ **Existe porque una espera de 19 minutos se publicaba como «0 días».**
 *
 * `solicitudes-cambio-plan` medía la espera con `// DIA_MS`, así que las seis
 * solicitudes del origen —resueltas en 5 y en 19 minutos— salían todas a cero.
 * Aritméticamente correcto e inútil: la columna existe para ver cuál tarda, y
 * no distinguía «resuelta en cinco minutos» de «resuelta en veinte horas».
 *
 * La regla es guardar preciso y formatear al mostrar. Truncar al guardar pierde
 * el dato para siempre; truncar al mostrar es una decisión de lectura que se
 * puede cambiar mañana.
 */

/** Texto de una duración dada en minutos. `null` es ausencia, no cero. */
export function duracionLegible(minutos: number | null | undefined): string {
  if (minutos === null || minutos === undefined || Number.isNaN(minutos)) {
    return '—';
  }
  if (minutos < 1) {
    // ⚠️ «menos de 1 min», no «0 min»: cero se lee como instantáneo, y lo que
    // pasó es que la espera fue más corta que la unidad con la que se mide.
    return 'menos de 1 min';
  }
  if (minutos < 60) {
    return `${Math.round(minutos)} min`;
  }
  if (minutos < 60 * 24) {
    const horas = minutos / 60;
    return `${horas.toFixed(horas < 10 ? 1 : 0)} h`;
  }
  const dias = minutos / (60 * 24);
  return `${dias.toFixed(dias < 10 ? 1 : 0)} días`;
}

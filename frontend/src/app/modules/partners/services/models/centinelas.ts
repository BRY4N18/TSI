/**
 * Traducción de los centinelas de Pinot a texto para personas.
 *
 * Pinot no almacena NULL en este proyecto: la ausencia de valor se materializa
 * como un centinela y llega intacta hasta la UI. Renderizarlos crudos produce
 * defectos visibles y ridículos —un cupo de `-1`, una credencial que vence en
 * el año 9999, un retiro planificado para el 01/01/1970—, así que toda la
 * traducción vive aquí y ningún componente compara contra el valor a mano.
 */

/** `Dim_Partner.planapi` sin plan asignado. */
export const SIN_PLAN = '';
/** `limitellamadasmes` / `limitellamadasminuto` sin cupo (0 sería válido). */
export const SIN_CUPO = -1;
/** `Dim_CredencialAPI.fecha_expiracion` de producción: año 9999, en el FUTURO. */
export const NUNCA_EXPIRA = 253402300799000;
/** `Dim_VersionContratoAPI.fecha_retiro` sin retiro planificado. */
export const SIN_FECHA_RETIRO = 0;
/** `spec_url` sin documento publicado. */
export const SIN_URL = '';

export const TEXTO_SIN_PLAN = 'Sin plan';
export const TEXTO_SIN_CUPO = 'Sin asignar';
export const TEXTO_NO_EXPIRA = 'No expira';
export const TEXTO_SIN_RETIRO = 'Sin retiro planificado';

/** El plan contratado, o «Sin plan» si aún no se le asignó ninguno. */
export function formatearPlan(planapi: string): string {
  return planapi === SIN_PLAN ? TEXTO_SIN_PLAN : planapi;
}

/** El cupo con separador de miles, o «Sin asignar» si vale el centinela. */
export function formatearCupo(limite: number): string {
  return limite === SIN_CUPO ? TEXTO_SIN_CUPO : limite.toLocaleString('es-EC');
}

/** `true` si la credencial pertenece a producción, que no vence nunca. */
export function noExpiraNunca(fechaExpiracion: number): boolean {
  return fechaExpiracion === NUNCA_EXPIRA;
}

/**
 * Vigencia legible. «No expira» para el centinela de producción; la fecha
 * local en cualquier otro caso.
 */
export function formatearVigencia(fechaExpiracion: number): string {
  if (noExpiraNunca(fechaExpiracion)) {
    return TEXTO_NO_EXPIRA;
  }
  return new Date(fechaExpiracion).toLocaleDateString('es-EC');
}

/**
 * Cálculo perezoso de vencimiento: una credencial está vencida en cuanto pasa
 * su fecha, aunque el job del backend todavía no la haya marcado (fail-safe).
 * Las de producción nunca lo están.
 */
export function estaVencida(credencial: { fecha_expiracion: number }, ahoraMs = Date.now()): boolean {
  return !noExpiraNunca(credencial.fecha_expiracion) && credencial.fecha_expiracion < ahoraMs;
}

/** Días que faltan para el vencimiento; `null` si no expira nunca. */
export function diasParaVencer(fechaExpiracion: number, ahoraMs = Date.now()): number | null {
  if (noExpiraNunca(fechaExpiracion)) {
    return null;
  }
  return Math.ceil((fechaExpiracion - ahoraMs) / 86_400_000);
}

/** Fecha de retiro de una versión del contrato, o «Sin retiro planificado». */
export function formatearFechaRetiro(fechaRetiro: number): string {
  return fechaRetiro === SIN_FECHA_RETIRO
    ? TEXTO_SIN_RETIRO
    : new Date(fechaRetiro).toLocaleDateString('es-EC');
}

/** `true` si hay documento publicado; evita renderizar un enlace roto. */
export function tieneSpecPublicada(specUrl: string): boolean {
  return specUrl !== SIN_URL;
}

/** El partner está suspendido: ninguna acción de habilitación debe ofrecerse. */
export function estaSuspendido(partner: { activo: boolean }): boolean {
  return !partner.activo;
}

/**
 * Reglas de formato compartidas por los formularios de captura.
 *
 * Motivación (revisión 24/08/2026, hallazgo #9)
 * ---------------------------------------------
 * "Varios campos no están validados, se pueden ingresar espacios en blanco,
 * caracteres especiales o letras en donde no debería, como por ejemplo el campo
 * cédula del apartado de enriquecimiento del sitio acepta letras."
 *
 * El problema no era un campo: era que cada formulario improvisaba su propia
 * comprobación —casi siempre un `.trim()` no vacío— y por eso el mismo dato se
 * validaba distinto en cada pantalla. Este módulo es la definición única.
 *
 * ⚠️ **Esto es la capa de conveniencia, no la de garantía.** El navegador se
 * salta llamando al endpoint directamente; cada regla de aquí tiene su espejo en
 * el servicio de backend correspondiente. Si cambia una, cambian las dos.
 */

/** Cédula ecuatoriana: exactamente 10 dígitos, sin letras ni separadores. */
export const PATRON_CEDULA = /^\d{10}$/;

/**
 * Nombres y apellidos: letras (con acentos y ñ), espacios, apóstrofo y guion.
 * Deja fuera dígitos y símbolos, que en un nombre siempre son un error de captura.
 */
export const PATRON_NOMBRE = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ '-]{1,49}$/;

/** Placa vehicular: 6 a 8 alfanuméricos, admite un guion intermedio. */
export const PATRON_PLACA = /^[A-Za-z0-9]{3}-?[A-Za-z0-9]{3,4}$/;

/** Teléfono: 7 a 15 dígitos, admite prefijo internacional. */
export const PATRON_TELEFONO = /^\+?\d{7,15}$/;

/** Correo: deliberadamente laxo, igual que el backend (`EMAIL_RE`). */
export const PATRON_EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export interface ResultadoValidacion {
  valido: boolean;
  /** Mensaje listo para mostrar; vacío cuando `valido` es true. */
  mensaje: string;
}

const OK: ResultadoValidacion = { valido: true, mensaje: '' };

function fallo(mensaje: string): ResultadoValidacion {
  return { valido: false, mensaje };
}

/** Texto obligatorio que no puede ser solo espacios. */
export function validarRequerido(valor: string, etiqueta: string): ResultadoValidacion {
  return valor.trim() ? OK : fallo(`${etiqueta} es obligatorio.`);
}

export function validarCedula(valor: string, { requerido = true } = {}): ResultadoValidacion {
  const limpio = valor.trim();
  if (!limpio) {
    return requerido ? fallo('La identificación es obligatoria.') : OK;
  }
  if (!PATRON_CEDULA.test(limpio)) {
    return fallo('La identificación debe tener exactamente 10 dígitos, sin letras ni símbolos.');
  }
  return OK;
}

export function validarNombre(
  valor: string,
  etiqueta: string,
  { requerido = true } = {},
): ResultadoValidacion {
  const limpio = valor.trim();
  if (!limpio) {
    return requerido ? fallo(`${etiqueta} es obligatorio.`) : OK;
  }
  if (!PATRON_NOMBRE.test(limpio)) {
    return fallo(`${etiqueta} solo admite letras, espacios, apóstrofo y guion (2 a 50 caracteres).`);
  }
  return OK;
}

export function validarPlaca(valor: string, { requerido = true } = {}): ResultadoValidacion {
  const limpio = valor.trim();
  if (!limpio) {
    return requerido ? fallo('La placa es obligatoria.') : OK;
  }
  if (!PATRON_PLACA.test(limpio)) {
    return fallo('La placa debe tener entre 6 y 8 caracteres alfanuméricos (ej. ABC-1234).');
  }
  return OK;
}

export function validarEmail(valor: string, { requerido = true } = {}): ResultadoValidacion {
  const limpio = valor.trim();
  if (!limpio) {
    return requerido ? fallo('El correo es obligatorio.') : OK;
  }
  return PATRON_EMAIL.test(limpio) ? OK : fallo('El correo no tiene un formato válido.');
}

export function validarTelefono(valor: string, { requerido = false } = {}): ResultadoValidacion {
  const limpio = valor.trim();
  if (!limpio) {
    return requerido ? fallo('El teléfono es obligatorio.') : OK;
  }
  return PATRON_TELEFONO.test(limpio)
    ? OK
    : fallo('El teléfono debe tener entre 7 y 15 dígitos.');
}

/** Entero dentro de un rango; `null`/vacío pasa cuando no es requerido. */
export function validarEntero(
  valor: number | null,
  etiqueta: string,
  { min = 0, max = Number.MAX_SAFE_INTEGER, requerido = false } = {},
): ResultadoValidacion {
  if (valor === null || valor === undefined || Number.isNaN(valor)) {
    return requerido ? fallo(`${etiqueta} es obligatorio.`) : OK;
  }
  if (!Number.isInteger(valor)) {
    return fallo(`${etiqueta} debe ser un número entero.`);
  }
  if (valor < min || valor > max) {
    return fallo(`${etiqueta} debe estar entre ${min} y ${max}.`);
  }
  return OK;
}

/**
 * Evalúa varias reglas y devuelve el primer fallo.
 *
 * Devolver solo el primero es deliberado: una lista de seis errores a la vez
 * pesa más de lo que ayuda, y al corregir el primero suelen caer los demás.
 */
export function primerError(...resultados: ResultadoValidacion[]): string {
  return resultados.find((r) => !r.valido)?.mensaje ?? '';
}

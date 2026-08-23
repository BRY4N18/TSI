import { VACIO_SIN_DATOS, mensajeVacio } from './mensaje-vacio';

describe('mensajeVacio', () => {
  it('culpa al período solo cuando el alcance no acota', () => {
    expect(mensajeVacio('todos')).toBe(VACIO_SIN_DATOS);
    expect(mensajeVacio(null)).toBe(VACIO_SIN_DATOS);
  });

  it('dice que el alcance puede ser la causa cuando está acotado a lo propio', () => {
    // ⚠️ El caso real: un Administrador entra a Ventas y CRM acotado a lo suyo y
    // no es dueño de ningún prospecto — cero filas en los trece informes. Con el
    // texto de período, ampliaría el rango indefinidamente sin ver una fila.
    const texto = mensajeVacio('propios');
    expect(texto).not.toBe(VACIO_SIN_DATOS);
    expect(texto).toContain('solo ves lo tuyo');
  });

  it('nombra las zonas contratadas en el eje de cobertura', () => {
    expect(mensajeVacio('zonas_contratadas')).toContain('zonas que tienes contratadas');
  });

  it('no inventa causa ante un alcance que no conoce', () => {
    expect(mensajeVacio('alcance_futuro')).toBe(VACIO_SIN_DATOS);
  });
});

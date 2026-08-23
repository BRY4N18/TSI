import { humanizar, opciones } from './informes-opciones';

describe('opciones de los filtros de enumeración', () => {
  it('copia el valor sin tocarlo, aunque la etiqueta cambie', () => {
    // ⚠️ Es la garantía que sostiene el filtro: estos literales son los que
    // guarda el origen. Si `valor` se normalizara, la petición saldría con algo
    // que el origen no conoce y la respuesta sería una lista vacía con 200 — no
    // un error, que es lo que hace el fallo invisible.
    const crudos = ['En_Validación', 'Pendiente_de_clasificacion', 'Producción activa'];
    expect(opciones(crudos).map((o) => o.valor)).toEqual(crudos);
  });

  it('sustituye el guion bajo y pone mayúscula inicial', () => {
    expect(humanizar('en_curso')).toBe('En curso');
    expect(humanizar('solicitud_promocion_produccion')).toBe('Solicitud promocion produccion');
  });

  it('deja intacto lo que ya viene legible', () => {
    expect(humanizar('Producción activa')).toBe('Producción activa');
  });

  it('no inventa acentos que el literal no trae', () => {
    // Pintar «clasificación» haría que la pantalla y el dato dijeran cosas
    // distintas, y quien buscara el valor en el origen no lo encontraría.
    expect(humanizar('Pendiente_de_clasificacion')).toBe('Pendiente de clasificacion');
  });
});

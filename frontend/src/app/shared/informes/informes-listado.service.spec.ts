/** @marker unit */
import { HttpErrorResponse } from '@angular/common/http';

import { clasificarError, construirParams } from './informes-listado.service';

describe('construirParams', () => {
  it('limit_when_no_se_indica_usa_el_defecto_del_backend', () => {
    const params = construirParams({ ruta: 'emergencias/casos' });

    expect(params.get('limit')).toBe('50');
  });

  it('filtro_vacio_when_es_null_o_cadena_vacia_no_viaja', () => {
    // Un filtro que no se aplicó no es un filtro con valor nulo: es un filtro
    // que no está. Enviarlo haría que `meta.filtros` lo reflejara como aplicado.
    const params = construirParams({
      ruta: 'emergencias/casos',
      filtros: { severidad: null, situacion: '', condado: 7201 },
    });

    expect(params.has('severidad')).toBeFalse();
    expect(params.has('situacion')).toBeFalse();
    expect(params.get('condado')).toBe('7201');
  });

  it('filtro_booleano_when_es_false_si_viaja', () => {
    // `false` es un valor pedido, no una ausencia: descartarlo devolvería el
    // listado entero justo cuando se pidió el complemento.
    const params = construirParams({
      ruta: 'emergencias/despachos',
      filtros: { en_transito: false },
    });

    expect(params.get('en_transito')).toBe('false');
  });

  it('cursor_when_viene_se_reenvia_tal_cual', () => {
    const cursor = '1786569480560|ACC-1786569480560-3023';

    const params = construirParams({ ruta: 'emergencias/casos', cursor });

    expect(params.get('cursor')).toBe(cursor);
  });

  it('cursor_when_es_null_no_viaja', () => {
    const params = construirParams({ ruta: 'emergencias/casos', cursor: null });

    expect(params.has('cursor')).toBeFalse();
  });
});

describe('clasificarError', () => {
  function httpError(status: number, detail?: string): HttpErrorResponse {
    return new HttpErrorResponse({
      status,
      error: detail ? { error: 'bad_request', detail, code: String(status) } : null,
    });
  }

  it('400_when_llega_conserva_el_detail_del_backend', () => {
    // El `detail` nombra los valores válidos: sustituirlo por un mensaje
    // genérico tira justo la información con la que se puede corregir.
    const detail = "El filtro 'situacion' no admite el valor 'borrador'; use uno de: cerrado, descartado.";

    const error = clasificarError(httpError(400, detail));

    expect(error.tipo).toBe('peticion');
    expect(error.mensaje).toBe(detail);
  });

  it('400_when_se_clasifica_no_es_reintentable', () => {
    // Repetir la misma petición devuelve el mismo 400. Ofrecer «Reintentar»
    // invitaría a insistir en vez de a corregir el filtro.
    const error = clasificarError(httpError(400, 'limit no puede superar 500'));

    expect(error.reintentable).toBeFalse();
  });

  it('403_when_se_clasifica_es_permiso_y_no_lista_vacia', () => {
    // No tener acceso es distinto de que no haya datos, y es la diferencia que
    // el backend eligió a propósito frente a devolver 200 con data vacía.
    const error = clasificarError(httpError(403, 'No puede consultar la cartera de otro titular.'));

    expect(error.tipo).toBe('permiso');
    expect(error.reintentable).toBeFalse();
  });

  it('500_when_se_clasifica_es_servidor_y_si_es_reintentable', () => {
    const error = clasificarError(httpError(500));

    expect(error.tipo).toBe('servidor');
    expect(error.reintentable).toBeTrue();
  });

  it('status_0_when_no_hay_respuesta_es_error_de_red', () => {
    const error = clasificarError(httpError(0));

    expect(error.tipo).toBe('red');
    expect(error.reintentable).toBeTrue();
  });

  it('400_when_no_trae_detail_usa_un_mensaje_propio', () => {
    const error = clasificarError(httpError(400));

    expect(error.tipo).toBe('peticion');
    expect(error.mensaje).toContain('filtro');
  });
});

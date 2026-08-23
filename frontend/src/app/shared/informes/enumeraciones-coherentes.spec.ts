/** @marker unit */
import { INFORMES_CUENTAS } from '../../modules/cuentas-clientes/informes/definiciones/informes-cuentas.definiciones';
import { INFORMES_EMERGENCIAS } from '../../modules/emergencias/informes/definiciones/informes-emergencias.definiciones';
import { INFORMES_PARTNERS } from '../../modules/partners/informes/definiciones/informes-partners.definiciones';
import { INFORMES_RED_OPERATIVA } from '../../modules/red-operativa/informes/definiciones/informes-red-operativa.definiciones';
import { INFORMES_SOPORTE } from '../../modules/soporte-cliente/informes/definiciones/informes-soporte.definiciones';
import { INFORMES_SUSCRIPCIONES } from '../../modules/suscripciones/informes/definiciones/informes-suscripciones.definiciones';
import { INFORMES_VENTAS } from '../../modules/ventas-crm/informes/definiciones/informes-ventas.definiciones';
import { DefinicionListado } from './informes-listado.types';

/**
 * ⚠️ **Esta prueba existe porque el fallo se veía en una sola pantalla.**
 *
 * En «Bajas de unidad», el desplegable ofrecía «Forzada con reasignación» y la
 * celda de la tabla pintaba `Forzada_con_reasignación`: el mismo valor escrito
 * de dos formas, a diez centímetros de distancia. No es cosmético — quien filtra
 * por una etiqueta y luego lee otra en la fila no sabe si está viendo lo que
 * pidió.
 *
 * Pasaba en 18 columnas de seis departamentos. La causa es estructural: las
 * opciones del filtro se humanizan al construirlas, y la columna solo se humaniza
 * si **declara** `formato: 'enumeracion'`. Olvidarlo no rompe nada visible salvo
 * en las enumeraciones que llevan guion bajo, así que se cuela.
 */
const CATALOGOS: Record<string, Record<string, DefinicionListado>> = {
  'cuentas-clientes': INFORMES_CUENTAS,
  emergencias: INFORMES_EMERGENCIAS,
  partners: INFORMES_PARTNERS,
  'red-operativa': INFORMES_RED_OPERATIVA,
  soporte: INFORMES_SOPORTE,
  suscripciones: INFORMES_SUSCRIPCIONES,
  ventas: INFORMES_VENTAS,
};

describe('coherencia entre filtros de enumeración y sus columnas', () => {
  for (const [departamento, catalogo] of Object.entries(CATALOGOS)) {
    it(`${departamento}_pinta_como_enumeracion_toda_columna_que_tambien_es_filtro`, () => {
      const incoherentes: string[] = [];

      for (const [id, definicion] of Object.entries(catalogo)) {
        const enumerados = new Set(
          (definicion.filtros ?? [])
            .filter((f) => f.tipo === 'enumeracion')
            .map((f) => f.nombre),
        );
        for (const columna of definicion.columnas) {
          if (enumerados.has(columna.campo as string) && columna.formato !== 'enumeracion') {
            incoherentes.push(`${id}.${String(columna.campo)}`);
          }
        }
      }

      expect(incoherentes).toEqual([]);
    });
  }
});

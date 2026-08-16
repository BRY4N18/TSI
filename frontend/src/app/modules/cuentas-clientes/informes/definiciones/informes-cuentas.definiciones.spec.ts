/** @marker unit */
import {
  INFORMES_CUENTAS,
  INFORMES_CUENTAS_IDS,
  INFORME_ACCESOS_TECNICOS,
} from './informes-cuentas.definiciones';

/**
 * Lo que el contrato OpenAPI del backend declara, transcrito aquí para poder
 * compararlo desde el navegador — Karma no lee ficheros del repositorio.
 *
 * ⚠️ Esta transcripción es el punto débil de la prueba: si alguien cambia el
 * contrato y no toca este fichero, la comparación seguiría pasando. Lo que sí
 * garantiza es que **definición y contrato no divergen por descuido al editar
 * una pantalla**, que es el caso frecuente.
 *
 * Fuente: `specs/002-tactico/Cuentas-Clientes/informes-tacticos-simples/backend/
 * contracts/informes-tacticos-simples.openapi.yaml`
 */
const CONTRATO: Record<string, { campos: string[]; rango: boolean }> = {
  'solicitudes-alta-pendientes': {
    campos: ['razon_social', 'tipo', 'fecha_solicitud', 'dias_transcurridos'],
    rango: false,
  },
  'onboarding-incompleto': {
    campos: ['razon_social', 'etapa', 'fecha_ultima_actualizacion', 'dias_detenido'],
    rango: false,
  },
  'cuentas-por-estado': {
    campos: [
      'razon_social',
      'tipo',
      'estado',
      'estado_onboarding',
      'fecha_inicio_contrato',
      'propietario',
    ],
    rango: false,
  },
  'transferencias-propiedad': {
    campos: ['razon_social', 'propietario_anterior', 'propietario_nuevo', 'fecha'],
    rango: true,
  },
  'usuarios-por-rol': { campos: ['nombre', 'gmail', 'activo', 'roles'], rango: false },
  'sesiones-activas': { campos: ['usuario', 'navegador', 'fecha_inicio'], rango: false },
  'credenciales-temporales': {
    campos: ['usuario', 'gmail', 'fecha_solicitud_cambio'],
    rango: false,
  },
  'accesos-tecnicos': {
    campos: ['usuario', 'usuario_servidor', 'roles_servidor', 'roles_negocio'],
    rango: false,
  },
};

/** El `enum` de `estado` en `cuentas-por-estado`, tal como lo declara el contrato. */
const ESTADOS_DEL_CONTRATO = [
  'Activo',
  'Pendiente',
  'Rechazado',
  'Rechazado_Anulado',
  'Dado de baja',
];

describe('Definiciones de informes de Cuentas y Clientes', () => {
  it('catalogo_when_se_declara_tiene_los_ocho_listados', () => {
    expect(INFORMES_CUENTAS_IDS.length).toBe(8);
    expect(INFORMES_CUENTAS_IDS.sort()).toEqual(Object.keys(CONTRATO).sort());
  });

  for (const [id, esperado] of Object.entries(CONTRATO)) {
    it(`columnas_when_es_${id}_coinciden_con_el_contrato`, () => {
      // Mostrar un campo que el backend no devuelve pinta una columna de
      // guiones; omitir uno que sí devuelve esconde información sin avisar.
      const declaradas = INFORMES_CUENTAS[id].columnas.map((c) => c.campo);

      expect(declaradas.sort()).toEqual([...esperado.campos].sort());
    });

    it(`rango_when_es_${id}_coincide_con_el_tipo_del_backend`, () => {
      // Pintar el selector de fechas en un listado de estado actual sería
      // ofrecer un control que solo sirve para provocar un 400.
      expect(INFORMES_CUENTAS[id].admiteRango ?? false).toBe(esperado.rango);
    });

    it(`mensaje_vacio_when_es_${id}_habla_de_su_dominio`, () => {
      const mensaje = INFORMES_CUENTAS[id].mensajeVacio;

      expect(mensaje.length).toBeGreaterThan(10);
      expect(mensaje.toLowerCase()).not.toContain('sin datos');
    });
  }

  it('enum_de_estado_when_se_declara_coincide_con_el_contrato', () => {
    // Es una copia inevitable —el backend no expone metadatos— y esta prueba es
    // lo único que evita que el desplegable se quede corto en silencio.
    const filtro = INFORMES_CUENTAS['cuentas-por-estado'].filtros?.find(
      (f) => f.nombre === 'estado',
    );

    expect(filtro?.opciones?.map((o) => o.valor)).toEqual(ESTADOS_DEL_CONTRATO);
  });

  it('transferencias_when_esta_vacio_explica_que_la_fuente_no_se_alimenta', () => {
    // Devolverá cero filas siempre mientras la decisión #28 siga abierta. Un
    // «no hay transferencias» genérico haría buscar el defecto en el código.
    const mensaje = INFORMES_CUENTAS['transferencias-propiedad'].mensajeVacio;

    expect(mensaje).toContain('aún no se alimenta');
    expect(mensaje).toContain('#28');
  });

  it('rutas_when_se_declaran_cuelgan_del_prefijo_del_departamento', () => {
    for (const id of INFORMES_CUENTAS_IDS) {
      expect(INFORMES_CUENTAS[id].ruta).toBe(`cuentas-clientes/${id}`);
    }
  });

  it('accesos_tecnicos_when_se_referencia_existe_en_el_catalogo', () => {
    expect(INFORMES_CUENTAS[INFORME_ACCESOS_TECNICOS]).toBeDefined();
  });

  it('campos_de_varios_valores_when_se_declaran_usan_formato_lista', () => {
    // `roles`, `roles_servidor` y `roles_negocio` son arreglos: sin este
    // formato se pintaban con las comas pegadas de String(['a','b']).
    const listas = [
      ['usuarios-por-rol', 'roles'],
      ['accesos-tecnicos', 'roles_servidor'],
      ['accesos-tecnicos', 'roles_negocio'],
    ];

    for (const [id, campo] of listas) {
      const columna = INFORMES_CUENTAS[id].columnas.find((c) => c.campo === campo);

      expect(columna?.formato).toBe('lista');
    }
  });
});

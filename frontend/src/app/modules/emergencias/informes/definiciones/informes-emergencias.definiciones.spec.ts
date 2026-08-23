/** @marker unit */
import {
  INFORMES_EMERGENCIAS,
  INFORMES_EMERGENCIAS_IDS,
  INFORME_CASOS,
  SITUACIONES_CASO,
} from './informes-emergencias.definiciones';

/**
 * Lo que el contrato OpenAPI del backend declara, transcrito para poder
 * compararlo desde el navegador.
 *
 * Fuente: `specs/002-tactico/Emergencias/informes-tacticos-simples/backend/
 * contracts/informes-tacticos-simples.openapi.yaml`
 */
const CONTRATO: Record<string, { campos: string[]; rango: boolean }> = {
  casos: {
    campos: [
      'numero_caso',
      'severidad',
      'calle',
      'ciudad',
      'condado',
      'tipo_reportado',
      'num_vehiculos',
      'num_heridos',
      'num_victimas',
      'num_fallecidos',
      'fecha_accidente',
      'activo',
      'hora_fin',
      'duracion_incidente_minutos',
      'duplicado_de',
      'situacion',
    ],
    rango: true,
  },
  despachos: {
    campos: [
      'numero_caso',
      'unidad',
      'origen_despacho',
      'fecha_despacho',
      'fecha_llegada',
      'fecha_retiro',
      'retiro_forzado',
      'en_transito',
    ],
    rango: true,
  },
  'evidencia-fotos': {
    campos: ['numero_caso', 'autor', 'url', 'sincronizado', 'hora_captura', 'hora_registro'],
    rango: true,
  },
  'notas-campo': {
    campos: [
      'numero_caso',
      'autor',
      'nota',
      'tipo',
      'sincronizado',
      'hora_captura',
      'hora_registro',
    ],
    rango: true,
  },
  cierres: {
    campos: ['numero_caso', 'resultado_atencion', 'calificacion', 'observaciones_finales'],
    // ⚠️ El único de estado actual: su tabla no tiene fecha propia.
    rango: false,
  },
};

/**
 * Campos que el backend **devuelve** y la tabla **no pinta a propósito**.
 *
 * `activo` es el único, y es deliberado: cerrado, descartado y duplicado son los
 * tres `activo = false`, así que la columna ponía «No» sobre tres desenlaces
 * distintos. La sustituye `situacion`, que los separa. El campo se sigue
 * devolviendo —quien consuma la API tiene los tres hechos enteros— pero pintarlo
 * junto a `situacion` solo devolvería la ambigüedad que se quitó.
 */
const NO_SE_PINTAN = ['activo'];

describe('Definiciones de informes de Emergencias', () => {
  it('catalogo_when_se_declara_tiene_los_cinco_listados', () => {
    expect(INFORMES_EMERGENCIAS_IDS.sort()).toEqual(Object.keys(CONTRATO).sort());
  });

  for (const [id, esperado] of Object.entries(CONTRATO)) {
    it(`columnas_when_es_${id}_coinciden_con_el_contrato`, () => {
      const declaradas = INFORMES_EMERGENCIAS[id].columnas.map((c) => c.campo);
      const mostrables = esperado.campos.filter((c) => !NO_SE_PINTAN.includes(c));

      expect(declaradas.sort()).toEqual([...mostrables].sort());
    });

    it(`columnas_when_es_${id}_no_inventan_campos_fuera_del_contrato`, () => {
      // La dirección que de verdad rompe la pantalla: una columna cuyo campo el
      // backend no devuelve se pinta «—» en todas las filas, y parece un dato
      // que falta en el origen en vez de un nombre mal escrito.
      const declaradas = INFORMES_EMERGENCIAS[id].columnas.map((c) => c.campo);

      expect(declaradas.filter((c) => !esperado.campos.includes(c))).toEqual([]);
    });

    it(`rango_when_es_${id}_coincide_con_el_tipo_del_backend`, () => {
      expect(INFORMES_EMERGENCIAS[id].admiteRango ?? false).toBe(esperado.rango);
    });
  }

  // ── La exclusión constitucional ──────────────────────────────────────────

  describe('ni coordenadas ni identidad de implicados', () => {
    const PROHIBIDAS = [
      'latitud',
      'longitud',
      'latitudinicio',
      'longitudinicio',
      'conductor',
      'implicado',
      'victima_nombre',
      'placa',
      'descripcion',
    ];

    it('columnas_when_se_declaran_no_incluyen_ninguna_prohibida', () => {
      // ⛔ No es una omisión: la constitución trata la geolocalización de
      // accidentes y la identidad de los implicados como dato sensible con su
      // propio control de acceso y auditoría. **La exención de la autoridad del
      // departamento no la levanta**: es una exclusión sobre el dato, no sobre
      // quién pregunta.
      //
      // Este catálogo es el sitio donde alguien la rompería sin querer,
      // añadiendo una columna «para el mapa».
      const campos = INFORMES_EMERGENCIAS_IDS.flatMap((id) =>
        INFORMES_EMERGENCIAS[id].columnas.map((c) => c.campo.toLowerCase()),
      );

      for (const prohibida of PROHIBIDAS) {
        expect(campos).not.toContain(prohibida);
      }
    });

    it('columnas_when_se_declaran_ninguna_contiene_latitud_ni_longitud', () => {
      const campos = INFORMES_EMERGENCIAS_IDS.flatMap((id) =>
        INFORMES_EMERGENCIAS[id].columnas.map((c) => c.campo.toLowerCase()),
      );

      expect(campos.some((c) => c.includes('latitud') || c.includes('longitud'))).toBeFalse();
    });

    it('filtros_when_se_declaran_ninguno_pide_coordenadas', () => {
      const filtros = INFORMES_EMERGENCIAS_IDS.flatMap((id) =>
        (INFORMES_EMERGENCIAS[id].filtros ?? []).map((f) => f.nombre.toLowerCase()),
      );

      expect(filtros.some((f) => f.includes('latitud') || f.includes('longitud'))).toBeFalse();
    });
  });

  // ── Los tres hechos, no un estado ────────────────────────────────────────

  describe('el caso publica su situación, y no la deriva la pantalla', () => {
    // ⚠️ **Estas dos pruebas cambiaron de sentido el 2026-08-22.** Afirmaban
    // que `casos` NO llevaba `situacion` y SÍ llevaba `activo`. El argumento de
    // entonces —no publicar un campo derivado que podría empezar a mentir— era
    // correcto, pero la conclusión no: la tabla pintaba `activo`, y cerrado,
    // descartado y duplicado son **los tres** `activo = false`. Tres filas que
    // ponían «No» significaban cosas distintas, y el filtro ofrecía cuatro
    // situaciones que la tabla no sabía mostrar. No publicarla no dejaba al
    // lector sin estado: lo dejaba con uno peor.

    it('casos_when_se_declara_no_tiene_columna_estado', () => {
      // Sigue sin haber columna «estado»: el estado formal del caso es del
      // módulo de fusión. `situacion` no es lo mismo — la calcula el backend
      // con la **misma** regla que ya usaba para filtrar, y devuelve
      // `inconsistente` cuando los tres hechos se contradicen en vez de elegir
      // el primero que encaje.
      const campos = INFORMES_EMERGENCIAS['casos'].columnas.map((c) => c.campo);

      expect(campos).not.toContain('estado');
    });

    it('casos_when_se_declara_lleva_situacion_en_lugar_de_activo', () => {
      const campos = INFORMES_EMERGENCIAS['casos'].columnas.map((c) => c.campo);

      expect(campos).toContain('situacion');
      // ⛔ La que causaba el defecto. Si vuelve, vuelve la ambigüedad.
      expect(campos).not.toContain('activo');
      // Los otros dos hechos siguen enteros y por separado.
      expect(campos).toContain('hora_fin');
      expect(campos).toContain('duplicado_de');
    });

    it('situacion_when_se_declara_no_la_deriva_la_pantalla', () => {
      // Se pinta como enumeración del origen: humanizada al mostrarla, con la
      // misma regla que las opciones del filtro, para que celda y desplegable
      // digan lo mismo. Derivarla aquí pondría una segunda copia de la regla,
      // libre de discrepar con la del filtro sin que nada fallara.
      const columna = INFORMES_EMERGENCIAS['casos'].columnas.find(
        (c) => c.campo === 'situacion',
      );

      expect(columna?.formato).toBe('enumeracion');
    });

    it('hora_fin_when_se_declara_se_formatea_como_fecha', () => {
      // El backend la normaliza a ISO. Antes la devolvía verbatim —epoch-ms como
      // texto— y en pantalla salía un número ilegible; el defecto lo encontró
      // este mismo módulo al mirarlo en el navegador.
      const columna = INFORMES_EMERGENCIAS['casos'].columnas.find(
        (c) => c.campo === 'hora_fin',
      );

      expect(columna?.formato).toBe('fecha_hora');
    });

    it('situacion_when_se_ofrece_como_filtro_tiene_las_cuatro_del_contrato', () => {
      // ⚠️ `borrador` **no está**: es un estado formal del histórico, y un caso
      // en borrador es indistinguible de cualquier otro activo.
      const filtro = INFORMES_EMERGENCIAS['casos'].filtros?.find(
        (f) => f.nombre === 'situacion',
      );

      expect(filtro?.opciones?.map((o) => o.valor)).toEqual([...SITUACIONES_CASO]);
      expect(filtro?.opciones?.map((o) => o.valor)).not.toContain('borrador');
    });
  });

  it('rutas_when_se_declaran_cuelgan_del_prefijo_del_departamento', () => {
    for (const id of INFORMES_EMERGENCIAS_IDS) {
      expect(INFORMES_EMERGENCIAS[id].ruta).toBe(`emergencias/${id}`);
    }
  });

  it('casos_when_se_referencia_existe_en_el_catalogo', () => {
    expect(INFORMES_EMERGENCIAS[INFORME_CASOS]).toBeDefined();
  });
});

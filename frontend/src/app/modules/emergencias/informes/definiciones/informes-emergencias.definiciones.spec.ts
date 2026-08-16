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
      'duracion_minutos',
      'duplicado_de',
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

describe('Definiciones de informes de Emergencias', () => {
  it('catalogo_when_se_declara_tiene_los_cinco_listados', () => {
    expect(INFORMES_EMERGENCIAS_IDS.sort()).toEqual(Object.keys(CONTRATO).sort());
  });

  for (const [id, esperado] of Object.entries(CONTRATO)) {
    it(`columnas_when_es_${id}_coinciden_con_el_contrato`, () => {
      const declaradas = INFORMES_EMERGENCIAS[id].columnas.map((c) => c.campo);

      expect(declaradas.sort()).toEqual([...esperado.campos].sort());
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

  describe('el caso no declara un estado calculado', () => {
    it('casos_when_se_declara_no_tiene_columna_estado', () => {
      // El backend devuelve los hechos y no un estado, porque la exclusividad
      // entre cerrado, descartado y fusionado la garantiza el módulo de fusión.
      // Derivar la etiqueta aquí repetiría en el último paso la inferencia que
      // el backend evitó a propósito.
      const campos = INFORMES_EMERGENCIAS['casos'].columnas.map((c) => c.campo);

      expect(campos).not.toContain('estado');
      expect(campos).not.toContain('situacion');
    });

    it('casos_when_se_declara_lleva_los_tres_hechos', () => {
      const campos = INFORMES_EMERGENCIAS['casos'].columnas.map((c) => c.campo);

      expect(campos).toContain('activo');
      expect(campos).toContain('hora_fin');
      expect(campos).toContain('duplicado_de');
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

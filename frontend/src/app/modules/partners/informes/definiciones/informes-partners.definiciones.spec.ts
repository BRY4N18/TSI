/** @marker unit */
import {
  ENTORNOS_CREDENCIAL,
  ESTADOS_PARTNER,
  ESTADOS_VERSION,
  INFORMES_CONTRATO,
  INFORMES_PARTNERS,
  INFORMES_PARTNERS_IDS,
  TIPOS_CAMBIO,
} from './informes-partners.definiciones';

/**
 * Transcripción del OpenAPI para comparar desde Karma.
 * Fuente: specs/002-tactico/Partners-API/informes-tacticos-simples/backend/contracts/
 */
const CONTRATO: Record<string, { campos: string[]; rango: boolean }> = {
  partners: {
    campos: [
      'cuenta',
      'nombre_partner',
      'estado_acceso',
      'plan_api',
      'limite_llamadas_mes',
      'limite_llamadas_minuto',
      'contacto_tecnico',
      'fecha_suspension',
      'motivo_suspension',
    ],
    rango: false,
  },
  credenciales: {
    campos: [
      'partner',
      'nombre_credencial',
      'entorno',
      'activa',
      'fecha_creacion',
      'fecha_expiracion',
      'dias_para_caducar',
    ],
    rango: false,
  },
  'cambios-acceso': {
    campos: [
      'partner',
      'credencial',
      'tipo_cambio',
      'estado_anterior',
      'estado_nuevo',
      'motivo',
      'ejecutado_por',
      'fecha',
    ],
    rango: true,
  },
  'versiones-contrato': {
    campos: ['servicio', 'version', 'estado', 'spec_url', 'fecha_publicacion', 'fecha_retiro'],
    rango: false,
  },
  'alcance-datos': {
    campos: [
      'cuenta',
      'zonas_geograficas',
      'frecuencia_reportes',
      'formato_reportes',
      'canales_notificacion',
      'destinatarios_reportes',
    ],
    rango: false,
  },
};

const CAMPOS_SECRETOS = ['motivo', 'client_secret', 'secret_hash', 'telefono_sms', 'secreto'];

describe('Definiciones de informes de Partners y API', () => {
  it('catalogo_when_se_declara_tiene_los_cinco_listados', () => {
    expect(INFORMES_PARTNERS_IDS.sort()).toEqual(Object.keys(CONTRATO).sort());
  });

  for (const [id, esperado] of Object.entries(CONTRATO)) {
    it(`columnas_when_es_${id}_coinciden_con_el_contrato`, () => {
      const declaradas = INFORMES_PARTNERS[id].columnas.map((c) => c.campo);
      expect(declaradas.sort()).toEqual([...esperado.campos].sort());
    });

    it(`rango_when_es_${id}_coincide_con_el_tipo_del_backend`, () => {
      expect(INFORMES_PARTNERS[id].admiteRango ?? false).toBe(esperado.rango);
    });

    it(`mensaje_vacio_when_es_${id}_habla_de_su_dominio`, () => {
      const mensaje = INFORMES_PARTNERS[id].mensajeVacio;
      expect(mensaje.length).toBeGreaterThan(10);
      expect(mensaje.toLowerCase()).not.toContain('sin datos');
    });
  }

  it('admiteRango_when_se_declara_solo_esta_en_cambios_acceso', () => {
    for (const id of INFORMES_PARTNERS_IDS) {
      expect(INFORMES_PARTNERS[id].admiteRango ?? false).toBe(id === 'cambios-acceso');
    }
  });

  it('caduca_en_dias_when_se_declara_solo_esta_en_credenciales', () => {
    for (const id of INFORMES_PARTNERS_IDS) {
      const tiene = INFORMES_PARTNERS[id].filtros?.some((f) => f.nombre === 'caduca_en_dias');
      expect(!!tiene).toBe(id === 'credenciales');
    }
  });

  it('filtro_partner_when_se_declara_solo_esta_en_los_tres_de_acceso', () => {
    for (const id of INFORMES_PARTNERS_IDS) {
      const tiene = INFORMES_PARTNERS[id].filtros?.some((f) => f.nombre === 'partner');
      expect(!!tiene).toBe(!(INFORMES_CONTRATO as readonly string[]).includes(id));
    }
  });

  it('enum_de_estado_partner_when_se_declara_coincide_con_el_dominio', () => {
    const filtro = INFORMES_PARTNERS['partners'].filtros?.find((f) => f.nombre === 'estado');
    expect(filtro?.opciones?.map((o) => o.valor)).toEqual([...ESTADOS_PARTNER]);
  });

  it('enum_de_entorno_when_se_declara_usa_produccion_con_tilde', () => {
    const filtro = INFORMES_PARTNERS['credenciales'].filtros?.find((f) => f.nombre === 'entorno');
    expect(filtro?.opciones?.map((o) => o.valor)).toEqual([...ENTORNOS_CREDENCIAL]);
    expect(filtro?.opciones?.map((o) => o.valor)).toContain('Producción');
    expect(filtro?.opciones?.map((o) => o.valor)).not.toContain('Produccion');
  });

  it('tipo_cambio_when_se_declara_no_agrupa_revocacion_con_cascada', () => {
    const valores = INFORMES_PARTNERS['cambios-acceso'].filtros?.find(
      (f) => f.nombre === 'tipo_cambio',
    )?.opciones?.map((o) => o.valor);
    expect(valores).toEqual([...TIPOS_CAMBIO]);
    expect(valores).toContain('revocacion_credencial');
    expect(valores).toContain('desactivacion_por_cascada');
    expect(valores?.some((v) => v === 'inactiva' || v.includes('inactiv'))).toBeFalse();
  });

  it('estados_version_when_se_declaran_coinciden_con_el_dominio', () => {
    const filtro = INFORMES_PARTNERS['versiones-contrato'].filtros?.find(
      (f) => f.nombre === 'estado',
    );
    expect(filtro?.opciones?.map((o) => o.valor)).toEqual([...ESTADOS_VERSION]);
  });

  it('credenciales_when_se_declaran_no_exponen_motivo_ni_secreto', () => {
    const campos = INFORMES_PARTNERS['credenciales'].columnas.map((c) => c.campo);
    for (const prohibido of CAMPOS_SECRETOS) {
      expect(campos).not.toContain(prohibido);
    }
  });

  it('ninguna_columna_when_se_une_incluye_secreto', () => {
    const campos = INFORMES_PARTNERS_IDS.flatMap((id) =>
      INFORMES_PARTNERS[id].columnas.map((c) => c.campo),
    );
    expect(campos).not.toContain('client_secret');
    expect(campos).not.toContain('secret_hash');
    expect(campos).not.toContain('telefono_sms');
  });

  it('informes_contrato_when_se_declaran_son_exactamente_dos', () => {
    expect([...INFORMES_CONTRATO].sort()).toEqual(['alcance-datos', 'versiones-contrato']);
  });

  it('listas_de_alcance_when_se_declaran_usan_formato_lista', () => {
    for (const campo of ['zonas_geograficas', 'canales_notificacion', 'destinatarios_reportes']) {
      const columna = INFORMES_PARTNERS['alcance-datos'].columnas.find((c) => c.campo === campo);
      expect(columna?.formato).toBe('lista');
    }
  });

  it('rutas_when_se_declaran_cuelgan_de_partners_api', () => {
    for (const id of INFORMES_PARTNERS_IDS) {
      expect(INFORMES_PARTNERS[id].ruta).toBe(`partners-api/${id}`);
    }
  });
});

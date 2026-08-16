/** @marker unit */
import { advertenciaDeContenido, avisoDeAlcance } from './informes-alcance';

describe('avisoDeAlcance', () => {
  it('todos_when_se_consulta_no_produce_aviso', () => {
    // Un cartel permanente diciendo «ves todo» sería ruido, y enseñaría a
    // ignorar la franja donde a veces sí hay una advertencia real.
    expect(avisoDeAlcance('todos')).toBeNull();
  });

  it('ausente_when_el_listado_no_acota_no_produce_aviso', () => {
    expect(avisoDeAlcance(undefined)).toBeNull();
  });

  it('propios_when_se_consulta_habla_de_registros_propios', () => {
    expect(avisoDeAlcance('propios')?.texto).toContain('tus registros');
  });

  it('zonas_when_se_consulta_NO_dice_que_los_datos_sean_del_cliente', () => {
    // Los accidentes de una zona contratada son hechos de terceros ocurridos
    // donde el cliente contrató cobertura: no le pertenecen.
    const aviso = avisoDeAlcance('zonas_contratadas');

    expect(aviso?.texto).toContain('zonas que tienes contratadas');
    expect(aviso?.texto).not.toContain('tus accidentes');
    expect(aviso?.textoVacio).toContain('otras');
  });

  it('los_dos_valores_when_se_comparan_tienen_textos_distintos', () => {
    // Si compartieran texto, `zonas_contratadas` no habría hecho falta.
    expect(avisoDeAlcance('propios')?.texto).not.toBe(
      avisoDeAlcance('zonas_contratadas')?.texto,
    );
  });
});

describe('advertenciaDeContenido', () => {
  it('composicion_de_flota_when_se_consulta_advierte_que_existir_no_es_estar_disponible', () => {
    // ⚠️ Es el caso de mayor consecuencia de la serie: quien leyera este listado
    // como cobertura decidiría sobre unidades fuera de servicio, ocupadas o ya
    // en camino a otro accidente.
    const texto = advertenciaDeContenido('composicion_de_flota') ?? '';

    expect(texto).toContain('existen');
    expect(texto).toContain('disponibles');
  });

  it('ausente_when_el_listado_no_lo_declara_no_advierte_nada', () => {
    // Solo lo declara el listado que lo necesita: añadirlo a todos convertiría
    // una advertencia deliberada en ruido.
    expect(advertenciaDeContenido(undefined)).toBeNull();
  });

  it('desconocido_when_llega_no_se_pinta_crudo', () => {
    // `meta.alcance` es un identificador, no un texto para el usuario: mostrarlo
    // tal cual daría una advertencia ilegible justo donde hace falta entenderla.
    expect(advertenciaDeContenido('valor_que_nadie_declaro')).toBeNull();
  });
});

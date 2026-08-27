/**
 * Los cuatro listados tácticos de Ventas y CRM, declarados.
 *
 * Columnas, filtros y enumeraciones salen del contrato OpenAPI del backend.
 */

import { DefinicionListado } from '../../../../shared/informes/informes-listado.types';
import { opciones } from '../../../../shared/informes/informes-opciones';

/**
 * ⚠️ **Son `Público` y `Privado`, y con acento y mayúscula inicial.**
 *
 * Hasta el 2026-08-19 esto declaraba `['aseguradora', 'municipio', 'proveedor']`:
 * tres valores que **no existen en ningún sitio**. El origen solo guarda
 * `Público` y `Privado` — es el mismo vocabulario con el que
 * `asignacion_automatica_service.ROLE_BY_ORG` decide a qué gerente va cada
 * prospecto.
 *
 * El fallo era invisible: las tres opciones devolvían **cero filas con HTTP
 * 200**, indistinguible de «no hay prospectos de ese tipo». No daba 400 porque
 * este filtro, a diferencia de `estado`, no valida contra un conjunto cerrado;
 * si lo hiciera, el error habría salido a la primera.
 */
export const TIPOS_ORGANIZACION = ['Público', 'Privado'] as const;

/**
 * ⚠️ **`perdido` no es «inactivo», y `convertido` no es una pérdida.**
 *
 * Un prospecto convertido es el desenlace bueno: se volvió cliente. Agruparlo
 * con los perdidos en un recuento de «no activos» presentaría el éxito y el
 * fracaso comercial como la misma cosa.
 */
export const ESTADOS_PROSPECTO = ['activo', 'perdido', 'convertido'] as const;

export const TIPOS_ASIGNACION = ['automatica', 'manual'] as const;
export const CANALES_NOTIFICACION = ['email', 'push', 'slack'] as const;

export const INFORMES_VENTAS: Record<string, DefinicionListado> = {
  prospectos: {
    ruta: 'ventas-crm/prospectos',
    titulo: 'Prospectos',
    mensajeVacio: 'No hay prospectos con esos criterios.',
    columnas: [
      { campo: 'empresa', etiqueta: 'Empresa', principal: true },
      { campo: 'nombre_contacto', etiqueta: 'Contacto' },
      { campo: 'cargo', etiqueta: 'Cargo', soloDetalle: true },
      { campo: 'tipo_organizacion', etiqueta: 'Tipo', formato: 'enumeracion' },
      { campo: 'canal_origen', etiqueta: 'Canal', soloDetalle: true },
      { campo: 'etapa_actual', etiqueta: 'Etapa', formato: 'enumeracion' },
      { campo: 'ejecutivo', etiqueta: 'Ejecutivo' },
      { campo: 'estado', etiqueta: 'Estado', formato: 'enumeracion' },
      { campo: 'motivo_perdida', etiqueta: 'Motivo de pérdida', soloDetalle: true },
      { campo: 'valor_estimado', etiqueta: 'Valor estimado', formato: 'moneda', alineacion: 'derecha', soloDetalle: true },
      { campo: 'fecha_registro', etiqueta: 'Registrado', formato: 'fecha_hora' },
    ],
    filtros: [
      {
        nombre: 'estado',
        etiqueta: 'Estado',
        tipo: 'enumeracion',
        opciones: opciones(ESTADOS_PROSPECTO),
        ayuda: '«convertido» es el desenlace bueno, no una pérdida.',
      },
      {
        nombre: 'tipo_organizacion',
        etiqueta: 'Tipo de organización',
        tipo: 'enumeracion',
        opciones: opciones(TIPOS_ORGANIZACION),
      },
      { nombre: 'etapa', etiqueta: 'Etapa', tipo: 'texto' },
      { nombre: 'canal', etiqueta: 'Canal', tipo: 'texto' },
      { nombre: 'ejecutivo', etiqueta: 'Ejecutivo', tipo: 'catalogo', catalogo: 'ejecutivo' },
    ],
  },

  // ⚠️ **Se titulaba «Reasignaciones de cartera» y no contenía ninguna.**
  //
  // Las doce filas del origen son **asignaciones iniciales**: `tipo_asignacion`
  // es `automatica` y `ejecutivo_anterior` viene vacío por definición —no había
  // uno antes—. Quien abría «Reasignaciones» leía una columna «Ejecutivo
  // anterior» entera en blanco y concluía que faltaba el dato, cuando lo que
  // pasa es que no aplica.
  //
  // El identificador técnico sigue siendo `reasignaciones` a propósito: es la
  // ruta publicada (`/informes/ventas-crm/reasignaciones`) y renombrarla rompería
  // a quien la consuma sin mejorar nada de lo que se lee en pantalla.
  reasignaciones: {
    ruta: 'ventas-crm/reasignaciones',
    titulo: 'Asignaciones de cartera',
    admiteRango: true,
    mensajeVacio: 'No hubo asignaciones de cartera en este período.',
    columnas: [
      { campo: 'empresa', etiqueta: 'Empresa', principal: true },
      // Ausente en una asignación inicial: no había ejecutivo antes. Se conserva
      // porque en una reasignación real es la mitad de la información.
      { campo: 'ejecutivo_anterior', etiqueta: 'Ejecutivo anterior' },
      { campo: 'ejecutivo_nuevo', etiqueta: 'Ejecutivo nuevo' },
      { campo: 'tipo_asignacion', etiqueta: 'Tipo', formato: 'enumeracion' },
      { campo: 'motivo', etiqueta: 'Motivo', soloDetalle: true },
      { campo: 'fecha', etiqueta: 'Fecha', formato: 'fecha_hora' },
    ],
    filtros: [
      {
        nombre: 'tipo_asignacion',
        etiqueta: 'Tipo de asignación',
        tipo: 'enumeracion',
        opciones: opciones(TIPOS_ASIGNACION),
      },
      { nombre: 'idprospecto', etiqueta: 'Prospecto', tipo: 'catalogo', catalogo: 'idprospecto' },
    ],
  },

  'demos-activas': {
    ruta: 'ventas-crm/demos-activas',
    titulo: 'Demos activas',
    mensajeVacio: 'No hay demos activas.',
    columnas: [
      { campo: 'empresa', etiqueta: 'Empresa', principal: true },
      { campo: 'nombre_contacto', etiqueta: 'Contacto' },
      { campo: 'ejecutivo', etiqueta: 'Ejecutivo' },
      { campo: 'expiracion', etiqueta: 'Expira', formato: 'fecha_hora' },
      { campo: 'dias_restantes', etiqueta: 'Días restantes', formato: 'numero', alineacion: 'derecha', soloDetalle: true },
    ],
    filtros: [{ nombre: 'ejecutivo', etiqueta: 'Ejecutivo', tipo: 'catalogo', catalogo: 'ejecutivo' }],
  },

  'notificaciones-enviadas': {
    ruta: 'ventas-crm/notificaciones-enviadas',
    titulo: 'Notificaciones enviadas',
    admiteRango: true,
    mensajeVacio: 'No se enviaron notificaciones en este período.',
    columnas: [
      { campo: 'empresa', etiqueta: 'Empresa', principal: true },
      { campo: 'ejecutivo_notificado', etiqueta: 'Ejecutivo notificado' },
      { campo: 'regla_disparada', etiqueta: 'Regla' },
      { campo: 'canal', etiqueta: 'Canal', formato: 'enumeracion' },
      { campo: 'fecha', etiqueta: 'Fecha', formato: 'fecha_hora' },
    ],
    filtros: [
      {
        nombre: 'canal',
        etiqueta: 'Canal',
        tipo: 'enumeracion',
        opciones: opciones(CANALES_NOTIFICACION),
      },
      { nombre: 'regla', etiqueta: 'Regla', tipo: 'texto' },
      { nombre: 'ejecutivo', etiqueta: 'Ejecutivo', tipo: 'catalogo', catalogo: 'ejecutivo' },
    ],
  },
};

export const INFORMES_VENTAS_IDS = Object.keys(INFORMES_VENTAS);

/**
 * ⚠️ **Supervisión pura.** El reparto de cartera es decisión de jefatura, no
 * herramienta del gerente cuya cartera se reparte: solo lo ven los roles
 * amplios.
 */
export const INFORME_REASIGNACIONES = 'reasignaciones';

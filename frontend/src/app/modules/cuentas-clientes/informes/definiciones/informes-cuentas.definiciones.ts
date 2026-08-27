/**
 * Los ocho listados tácticos de Cuentas y Clientes, declarados.
 *
 * Columnas y filtros salen **del contrato OpenAPI del backend**
 * (`specs/002-tactico/Cuentas-Clientes/informes-tacticos-simples/backend/contracts/`),
 * no de memoria. Una prueba los compara contra ese fichero.
 *
 * Añadir un listado nuevo es añadir una entrada aquí: la página, la ruta y el
 * índice salen de este catálogo.
 */

import { DefinicionListado } from '../../../../shared/informes/informes-listado.types';
import { opciones } from '../../../../shared/informes/informes-opciones';

/**
 * ⚠️ **Deuda declarada.** Estos valores los declara el `enum` del contrato de
 * backend, y aquí están **copiados**: el backend no expone un endpoint de
 * metadatos, así que no hay forma de leerlos en tiempo de ejecución.
 *
 * Es la misma clase de duplicación que el backend evitó importando constantes
 * del dominio; aquí no se puede evitar, así que se hace visible en vez de
 * disimularla. Una prueba compara esta lista contra el contrato para que la
 * desactualización salte en vez de manifestarse como un desplegable incompleto.
 */
const ESTADOS_CUENTA = [
  'Activo',
  'Pendiente',
  'Rechazado',
  'Rechazado_Anulado',
  'Dado de baja',
] as const;

/**
 * ⚠️ Faltaba `Aseguradora`, que sí existe en el origen: el desplegable no dejaba
 * aislar esas cuentas y devolvía las demás sin avisar de nada.
 *
 * ⚠️ El origen guarda **además** `aseguradora` en minúscula, en otra fila. Es el
 * mismo concepto escrito de dos formas, y el filtro distingue mayúsculas. No se
 * ofrecen las dos: el desplegable pintaría dos opciones con el mismo texto y
 * quien eligiera una no sabría cuál está eligiendo — el mismo problema que las
 * ciudades homónimas. La solución es limpiar el dato en el origen, no duplicar
 * la opción aquí.
 */
const TIPOS_CUENTA = ['Corporativo', 'Proveedor', 'Aseguradora'] as const;

export const INFORMES_CUENTAS: Record<string, DefinicionListado> = {
  'solicitudes-alta-pendientes': {
    ruta: 'cuentas-clientes/solicitudes-alta-pendientes',
    titulo: 'Solicitudes de alta pendientes',
    mensajeVacio: 'No hay solicitudes de alta pendientes.',
    columnas: [
      { campo: 'razon_social', etiqueta: 'Cuenta', principal: true },
      { campo: 'tipo', etiqueta: 'Tipo', formato: 'enumeracion' },
      { campo: 'fecha_solicitud', etiqueta: 'Solicitada', formato: 'fecha_hora' },
      {
        campo: 'dias_transcurridos',
        etiqueta: 'Días esperando',
        formato: 'numero',
        alineacion: 'derecha',
      },
    ],
    filtros: [
      { nombre: 'tipo', etiqueta: 'Tipo', tipo: 'enumeracion', opciones: opciones(TIPOS_CUENTA) },
      {
        nombre: 'dias_minimo',
        etiqueta: 'Días esperando (mínimo)',
        tipo: 'numero',
        ayuda: 'Deja las que llevan al menos ese tiempo sin resolver.',
      },
    ],
  },

  'onboarding-incompleto': {
    ruta: 'cuentas-clientes/onboarding-incompleto',
    titulo: 'Onboarding incompleto',
    mensajeVacio: 'No hay cuentas detenidas en el onboarding.',
    columnas: [
      { campo: 'razon_social', etiqueta: 'Cuenta', principal: true },
      { campo: 'etapa', etiqueta: 'Etapa' },
      {
        campo: 'fecha_ultima_actualizacion',
        etiqueta: 'Último avance',
        formato: 'fecha_hora',
      },
      {
        campo: 'dias_detenido',
        etiqueta: 'Días detenido',
        formato: 'numero',
        alineacion: 'derecha',
      },
    ],
    filtros: [
      { nombre: 'etapa', etiqueta: 'Etapa', tipo: 'texto' },
      { nombre: 'dias_minimo', etiqueta: 'Días detenido (mínimo)', tipo: 'numero' },
    ],
  },

  'cuentas-por-estado': {
    ruta: 'cuentas-clientes/cuentas-por-estado',
    titulo: 'Cuentas por estado',
    mensajeVacio: 'No hay cuentas con ese estado.',
    columnas: [
      { campo: 'razon_social', etiqueta: 'Cuenta', principal: true },
      { campo: 'tipo', etiqueta: 'Tipo', formato: 'enumeracion' },
      { campo: 'estado', etiqueta: 'Estado', formato: 'enumeracion' },
      { campo: 'estado_onboarding', etiqueta: 'Onboarding', soloDetalle: true },
      { campo: 'fecha_inicio_contrato', etiqueta: 'Inicio de contrato', formato: 'fecha', soloDetalle: true },
      { campo: 'propietario', etiqueta: 'Responsable' },
    ],
    filtros: [
      {
        nombre: 'estado',
        etiqueta: 'Estado',
        tipo: 'enumeracion',
        opciones: opciones(ESTADOS_CUENTA),
      },
      { nombre: 'tipo', etiqueta: 'Tipo', tipo: 'enumeracion', opciones: opciones(TIPOS_CUENTA) },
    ],
  },

  'transferencias-propiedad': {
    ruta: 'cuentas-clientes/transferencias-propiedad',
    titulo: 'Transferencias de propiedad',
    // ⚠️ **El único de hechos del período**: es el único que el backend declara
    // así, y por tanto el único donde la barra pinta el rango de fechas.
    admiteRango: true,
    // ⚠️ Este listado devuelve **cero filas siempre** mientras la decisión #28
    // siga abierta: `Fact_HistorialTransferenciaPropiedad` está declarada y
    // ningún código de producción la escribe. Un «no hay transferencias»
    // genérico haría que alguien buscara el defecto en el código.
    mensajeVacio:
      'Todavía no se registran transferencias: la fuente de este informe aún no se alimenta ' +
      '(decisión pendiente #28). No es un fallo de la pantalla.',
    columnas: [
      { campo: 'razon_social', etiqueta: 'Cuenta', principal: true },
      { campo: 'propietario_anterior', etiqueta: 'Responsable anterior' },
      { campo: 'propietario_nuevo', etiqueta: 'Responsable nuevo' },
      { campo: 'fecha', etiqueta: 'Fecha', formato: 'fecha_hora' },
    ],
    filtros: [{ nombre: 'idcliente', etiqueta: 'Cuenta', tipo: 'catalogo', catalogo: 'idcliente' }],
  },

  'usuarios-por-rol': {
    ruta: 'cuentas-clientes/usuarios-por-rol',
    titulo: 'Usuarios por rol',
    mensajeVacio: 'No hay usuarios con ese rol.',
    columnas: [
      { campo: 'nombre', etiqueta: 'Usuario', principal: true },
      { campo: 'gmail', etiqueta: 'Correo' },
      { campo: 'roles', etiqueta: 'Roles', formato: 'lista' },
      { campo: 'activo', etiqueta: 'Activo', formato: 'booleano' },
    ],
    filtros: [
      { nombre: 'rol', etiqueta: 'Rol', tipo: 'texto' },
      { nombre: 'activo', etiqueta: 'Activo', tipo: 'booleano' },
    ],
  },

  'sesiones-activas': {
    ruta: 'cuentas-clientes/sesiones-activas',
    titulo: 'Sesiones activas',
    mensajeVacio: 'No hay sesiones activas.',
    columnas: [
      { campo: 'usuario', etiqueta: 'Usuario', principal: true },
      { campo: 'navegador', etiqueta: 'Navegador' },
      { campo: 'fecha_inicio', etiqueta: 'Inicio', formato: 'fecha_hora' },
    ],
    filtros: [{ nombre: 'idusuario', etiqueta: 'Usuario', tipo: 'catalogo', catalogo: 'idusuario' }],
  },

  'credenciales-temporales': {
    ruta: 'cuentas-clientes/credenciales-temporales',
    titulo: 'Credenciales temporales',
    mensajeVacio: 'No hay credenciales temporales sin usar.',
    columnas: [
      { campo: 'usuario', etiqueta: 'Usuario', principal: true },
      { campo: 'gmail', etiqueta: 'Correo' },
      { campo: 'fecha_solicitud_cambio', etiqueta: 'Solicitada', formato: 'fecha_hora' },
    ],
  },

  'accesos-tecnicos': {
    ruta: 'cuentas-clientes/accesos-tecnicos',
    titulo: 'Accesos técnicos',
    mensajeVacio: 'No hay accesos técnicos registrados.',
    columnas: [
      { campo: 'usuario', etiqueta: 'Usuario', principal: true },
      { campo: 'usuario_servidor', etiqueta: 'Usuario de servidor' },
      { campo: 'roles_servidor', etiqueta: 'Roles de servidor', formato: 'lista' },
      { campo: 'roles_negocio', etiqueta: 'Roles de negocio', formato: 'lista', soloDetalle: true },
    ],
  },
};

/** Identificadores en el orden en que el índice los ofrece. */
export const INFORMES_CUENTAS_IDS = Object.keys(INFORMES_CUENTAS);

/**
 * ⚠️ El único con permiso distinto: el Director Tecnológico entra **solo aquí**.
 * Ampliarlo a los otros siete contradiría el §5.1 del SRS.
 */
export const INFORME_ACCESOS_TECNICOS = 'accesos-tecnicos';

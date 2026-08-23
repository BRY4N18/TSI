"""DDL idempotente del modelo analítico táctico (contracts/esquema-analitico.md).

Cada flujo llama a `ensure_*` al inicio de su corrida: `CREATE TABLE IF NOT
EXISTS` es seguro de repetir.

Dos bloques conviven a propósito
--------------------------------
1. **El modelo** — 5 dimensiones y 2 hechos de la primera fase.
2. **Las tres tablas por informe** del diseño anterior, al final del fichero.

Las segundas **no se borran todavía**. Se retiran en la fase 6 del módulo, y solo
cuando las consultas equivalentes sobre el modelo devuelvan las mismas cifras que
ellas (research D7). Retirarlas antes dejaría al sistema sin esos tres informes y
sin forma de comparar.

Dos convenciones que no son decorativas
---------------------------------------
**La ausencia se escribe `Nullable`, nunca 0 ni una fecha centinela.** Un hito no
alcanzado guardado como fecha cero convertiría todos los casos abiertos en
cerrados en 1970, y ningún promedio de duración volvería a ser creíble.

**Los hechos van particionados por mes.** No es una optimización: es lo que
permite recargar un período descartando su partición en vez de borrar filas por
condición, que en este almacén es una mutación (research D3).
"""

from __future__ import annotations

from lib.clickhouse_http_client import execute_clickhouse

# ───────────────────────────── Dimensiones ──────────────────────────────


def ensure_dim_tiempo() -> None:
    """Una fila por día. **Se genera, no se extrae** de ningún origen."""
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_tiempo (
            fecha            Date,
            anio             UInt16,
            trimestre        UInt8,
            mes              UInt8,
            nombre_mes       String,
            semana_iso       UInt8,
            dia_del_mes      UInt8,
            dia_semana       UInt8,
            nombre_dia       String,
            es_fin_de_semana UInt8,
            version          DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY fecha
        """
    )


def ensure_dim_geografia() -> None:
    """Una fila por calle **con sus ascendientes aplanados**.

    Agrupar por condado es así una columna y no tres saltos. Sin coordenadas:
    la ubicación se expresa por nombre (exclusión del §5 del contrato).
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_geografia (
            idcalle      Int32,
            calle        String,
            idciudad     Int32,
            ciudad       String,
            idcondado    Int32,
            condado      String,
            idestado     Int32,
            estado       String,
            idpais       Int32,
            pais         String,

            -- Red Operativa (US1). La vecindad es una **relacion estatica entre
            -- entidades ya modeladas**: no tiene instante ni grano propio, asi
            -- que es un atributo y no un hecho (research D3). Un hecho de
            -- vecindad seria una tabla de dos filas con su flujo y su DAG.
            --
            -- ⚠️ Vacio significa **sin vecinos declarados**, que es un dato y no
            -- una ausencia: un condado sin alternativas es la situacion mas
            -- grave que puede reportar la cobertura critica.
            condados_vecinos  Array(Int32),
            idregionoperativa Nullable(Int32),

            version      DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idcalle
        """
    )


def ensure_dim_severidad() -> None:
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_severidad (
            idseveridad  Int32,
            severidad    String,
            descripcion  Nullable(String),
            orden        UInt8,
            version      DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idseveridad
        """
    )


def ensure_dim_condado_vecino() -> None:
    """Adyacencia física entre condados. Única ampliación de OE3.

    No se versiona por atributo: si el mapa cambiara, sería otro mapa.
    Necesita su fila desconocida o los condados sin vecino resuelto
    desaparecen en la primera unión.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_condado_vecino (
            idcondado        Int32,
            condado          String,
            idcondadovecino  Int32,
            condado_vecino   String,
            version          DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY (idcondado, idcondadovecino)
        """
    )


def ensure_dim_origen_despacho() -> None:
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_origen_despacho (
            idorigendespacho Int32,
            origen           String,
            version          DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idorigendespacho
        """
    )


def ensure_dim_unidad() -> None:
    """Una fila por **versión** de unidad, no por unidad.

    Es la dimensión que resuelve la atribución histórica: dos despachos de la
    misma unidad en épocas distintas apuntan a `sk_unidad` distintos, y por eso
    cada uno conserva su proveedor correcto.

    `inicio_es_real = 0` marca que la fecha de inicio **no es un cambio
    observado** sino el momento en que el modelo empezó a mirar. Para la unidad
    lo será siempre: nada en el origen historiza el cambio de proveedor.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_unidad (
            sk_unidad          UInt64,
            idunidademergencia Int32,
            placa              String,
            nombre_unidad      Nullable(String),
            tipo_unidad        Nullable(String),
            capacidad          Nullable(Int32),
            idcliente          Int32,
            proveedor          String,
            idcondado          Nullable(Int32),
            condado            Nullable(String),
            zona_cobertura     Nullable(String),

            -- Red Operativa (US1). ⚠️ **No son atributos versionados**: el alta
            -- no cambia, y el primer acceso ocurre una vez. Versionarlos
            -- llenaria la dimension de versiones nuevas cada vez que una unidad
            -- entra por primera vez, sin que nada de negocio haya cambiado.
            fecha_alta         Nullable(DateTime),
            tuvo_primer_acceso UInt8 DEFAULT 0,

            valido_desde       DateTime,
            valido_hasta       Nullable(DateTime),
            es_vigente         UInt8,
            inicio_es_real     UInt8,
            version            DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY (idunidademergencia, valido_desde)
        """
    )


def ensure_dim_region() -> None:
    """Una fila por **version** de region operativa (Red Operativa, US1-US3).

    Versionada por la misma razon que la unidad: un informe de hace tres meses
    tiene que decir en que estado estaba la region entonces, no en cual esta hoy.

    ADVERTENCIA: `estado_ciclo_vida` y `estado_geo` son cosas distintas, y el
    origen las confunde
    ---------------------------------------------------------------------------
    * `estado_ciclo_vida` es `Definida`, `En validacion`, `Produccion` o
      `Despublicada`. Vive en `Dim_RegionOperativa.estadoregion`.
    * `estado_geo` es «Ciudad de Mexico». Vive en `Dim_EstadoRegion.estadoregion`,
      pese al nombre.

    La tabla del origen llamada `Dim_RegionOperativaEstadoRegion` relaciona la
    region con **el segundo**, aunque el catalogo de informes la citaba como
    fuente del primero. Se comprobo: `Dim_EstadoRegion` contiene «Ciudad de
    Mexico», no un estado de ciclo de vida.

    Nombrarlos distinto aqui es lo unico que impide repetir la confusion, y la
    confusion no seria inocua: un informe de regiones publicadas que leyera la
    geografia devolveria todas las regiones o ninguna, y las dos respuestas
    parecen plausibles.

    **Solo `estado_ciclo_vida` abre version.** La geografia de una region no
    cambia; si cambiara, seria otra region.

    `inicio_es_real = 0` en las versiones iniciales: el estado se conoce, pero no
    desde cuando.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_region (
            sk_region         UInt64,
            idregionoperativa Int32,
            nombre_region     String,
            estado_ciclo_vida String,
            idestado_geo      Nullable(Int32),
            estado_geo        Nullable(String),
            pais              Nullable(String),

            valido_desde      DateTime,
            valido_hasta      Nullable(DateTime),
            es_vigente        UInt8,
            inicio_es_real    UInt8,
            version           DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY (idregionoperativa, valido_desde)
        """
    )


def ensure_dim_prospecto() -> None:
    """Un prospecto del embudo comercial (Ventas y CRM).

    ⚠️ SIN NINGUN DATO PERSONAL, Y NO ES UN FILTRO: ES QUE NO ESTA
    ---------------------------------------------------------------
    `Dim_Prospecto` es la tabla con **mas dato personal del sistema**: nombres,
    apellidos, correo, telefono y cargo. Ninguna de esas columnas existe aqui.

    La diferencia entre no pedirlo y que no este es toda: un dato que la consulta
    no pide hoy vuelve en cuanto alguien anada un `SELECT`; un dato que no esta
    en la tabla no puede volver por descuido. Y ningun informe del catalogo
    necesita saber **quien** es el prospecto — necesita saber de que empresa
    viene, por que canal y en que acabo.

    ⚠️ `desenlace` TIENE TRES VALORES, Y `activo` SOLO DOS
    ------------------------------------------------------
    `Dim_Prospecto.activo` **no dice si el prospecto sigue en curso**: cubre a la
    vez a los que se convirtieron y a los que se perdieron. Medido hoy: de los
    tres con `activo = false`, **dos son convertidos y uno perdido**.

    Agrupar por esa columna juntaria el mejor desenlace con el peor y devolveria
    «3 inactivos», una cifra que no significa nada y que nadie cuestionaria
    porque suena a lo esperado.

    `desenlace` se deriva en la carga de `motivo_inactividad` y `etapa_actual`, y
    vale `convertido`, `perdido` o `en_curso`.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_prospecto (
            idprospecto        Int32,
            empresa            Nullable(String),
            tipo_organizacion  Nullable(String),
            idcanal            Int32,
            canal              String,
            etapa_actual       Nullable(String),
            desenlace          String,
            motivo_inactividad Nullable(String),
            valor_estimado     Nullable(Float64),
            fecha_registro     Nullable(DateTime),
            version            DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idprospecto
        """
    )


def ensure_dim_canal() -> None:
    """El canal por el que llego un prospecto (Ventas y CRM).

    El origen lo guarda como **texto libre** en `como_nos_conocio`, asi que la
    carga lo normaliza: sin eso, «Redes sociales», «redes sociales» y «RRSS»
    serian tres canales distintos y el informe de rendimiento por canal
    repartiria el mismo canal en tres filas con un tercio del volumen cada una.
    Ninguno pareceria importante.

    ⚠️ La fila desconocida **cuenta en los totales**. Un prospecto sin canal
    llego igual, y dejarlo fuera haria que los canales sumaran menos que el
    embudo sin que nada lo indicara.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_canal (
            idcanal    Int32,
            canal      String,
            version    DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idcanal
        """
    )


# ── Suscripciones y Facturación (dimensiones conformadas) ───────────────


def ensure_dim_plan() -> None:
    """Catálogo de planes con límites **desplegados**.

    El origen guarda `limites` como texto JSON. Interpretarlo en cada consulta
    repartiría esa lógica por el catálogo y la primera que lo lea distinto
    devolvería otra cifra para la misma pregunta.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_plan (
            idplan                    Int32,
            nombre                    String,
            nivel                     Nullable(String),
            periodicidad              Nullable(String),
            precio_lista              Nullable(Decimal(12, 2)),
            precio_excedente_llamada  Nullable(Decimal(12, 4)),
            limite_unidades           Nullable(Int32),
            limite_usuarios           Nullable(Int32),
            limite_llamadas_mes       Nullable(Int32),
            limite_llamadas_minuto    Nullable(Int32),
            severidades_habilitadas   Array(Int32),
            carga_lote_habilitada     UInt8,
            es_activo                 UInt8,
            version                   DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idplan
        """
    )


def ensure_dim_cliente() -> None:
    """Dimensión **conformada** de cliente: sin fiscal, sin contacto, sin medio.

    Se crea aquí porque este departamento es el primero que la necesita.
    Cuentas y Clientes **la ampliará, no la recreará**.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_cliente (
            idcliente          Int32,
            nombre_comercial   String,
            tipo               Nullable(String),
            estado_comercial   Nullable(String),
            estado_onboarding  Nullable(String),
            tiene_metodo_pago  UInt8,
            metodo_pago_caduca Nullable(Date),
            fecha_alta         Nullable(DateTime),
            cohorte_alta       Nullable(String),
            fecha_baja         Nullable(DateTime),
            motivo_baja        Nullable(String),
            etapa_onboarding_actual Nullable(String),
            onboarding_completo UInt8 DEFAULT 0,
            resultado_solicitud Nullable(String),
            version            DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idcliente
        """
    )


# ── Soporte al Cliente ──────────────────────────────────────────────────


def ensure_dim_sla_config() -> None:
    """SLA **versionado desde el origen**. Sin `inicio_es_real`.

    El origen ya guarda vigencia desde/hasta. Aplicar `versionado.py` reconstruiría
    una historia real y la marcaría como no real.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_sla_config (
            idslaconfig             Int32,
            idplan                  Int32,
            tipo_incidencia         String,
            prioridad               String,
            segundos_respuesta_max  Int32,
            segundos_resolucion_max Int32,
            valido_desde            DateTime,
            valido_hasta            Nullable(DateTime),
            es_vigente              UInt8,
            version                 DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY (idplan, tipo_incidencia, prioridad, valido_desde)
        """
    )


def ensure_dim_servicio() -> None:
    """Catálogo de servicios afectados. Hoy ningún ticket apunta aquí."""
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_servicio (
            id_servicio Int32,
            nombre      String,
            tipo        Nullable(String),
            es_activo   UInt8,
            version     DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY id_servicio
        """
    )


def ensure_dim_estado_soporte() -> None:
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_estado_soporte (
            id_estado_soporte Int32,
            nombre            String,
            es_activo         UInt8,
            version           DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY id_estado_soporte
        """
    )


def ensure_dim_usuario_organizacion() -> None:
    """Pertenencia usuario↔cliente **sin identidad**. Incluye a quien no tiene
    organización conocida (`tiene_pertenencia = 0`): sin eso no hay cobertura.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_usuario_organizacion (
            idusuario         Int32,
            idcliente         Nullable(Int32),
            tiene_pertenencia UInt8,
            es_activo         UInt8,
            version           DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idusuario
        """
    )


def ensure_dim_etapa_onboarding() -> None:
    """Catálogo **explícito** de etapas. No se infiere de lo observado."""
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_etapa_onboarding (
            idetapa        Int32,
            etapa          String,
            orden          UInt8,
            es_obligatoria UInt8,
            version        DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idetapa
        """
    )


def ensure_dim_rol() -> None:
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_rol (
            idrol       Int32,
            rol         String,
            descripcion Nullable(String),
            es_activo   UInt8,
            version     DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idrol
        """
    )


def ensure_dim_usuario_rol() -> None:
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_usuario_rol (
            idusuario Int32,
            idrol     Int32,
            rol       String,
            es_activo UInt8,
            version   DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY (idusuario, idrol)
        """
    )


def ensure_hecho_sesion() -> None:
    """Transacción, grano una sesión. **Sin token.** Duración ausente sin cierre."""
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_sesion (
            idsesion             Int32,
            fecha                Date,
            fechahora_inicio     DateTime,
            fechahora_cierre     Nullable(DateTime),
            idusuario            Int32,
            idcliente            Nullable(Int32),
            pertenencia_conocida UInt8,
            desenlace            String,
            navegador            Nullable(String),
            franja_horaria       String,
            duracion_segundos    Nullable(Int32),
            cargado_en           DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idusuario, fechahora_inicio)
        """
    )


def ensure_hecho_onboarding() -> None:
    """Transacción, grano **una etapa del onboarding de un cliente**.

    ⚠️ El grano era «una etapa **completada**» y por eso el abandono no estaba
    aquí: el origen solo publicaba filas completadas y un embudo calculado sobre
    lo observado daba **100 % de finalización** (decisión #45).

    Desde el 2026-08-23 el origen declara las etapas obligatorias al aprobar la
    cuenta, con `completado = False`, y esta tabla las recibe. `completada`
    distingue las dos cosas: **una etapa que llegó y sigue en 0 es el abandono
    observado**, sin inventar un umbral de inactividad.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_onboarding (
            idonboarding    Int32,
            fecha           Date,
            fechahora       DateTime,
            idcliente       Int32,
            tipo_cliente    Nullable(String),
            idetapa         Nullable(Int32),
            etapa           String,
            orden_etapa     Nullable(UInt8),
            completada      UInt8,
            dias_desde_alta Nullable(Int32),
            cargado_en      DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idcliente, idonboarding)
        """
    )


# ── Partners y API ──────────────────────────────────────────────────────


def ensure_dim_partner() -> None:
    """Partner sin contacto técnico. `plan_api` nulo, nunca el texto `'null'`."""
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_partner (
            idpartner              Int32,
            nombre_partner         String,
            idcliente              Nullable(Int32),
            plan_api               Nullable(String),
            limite_llamadas_mes    Nullable(Int32),
            limite_llamadas_minuto Nullable(Int32),
            estado                 String,
            fecha_suspension       Nullable(DateTime),
            sandbox_activado       Nullable(DateTime),
            sandbox_expiracion     Nullable(DateTime),
            version                DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idpartner
        """
    )


def ensure_dim_credencial_api() -> None:
    """Credencial sin hash de secreto. Motivo de inactividad derivado."""
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_credencial_api (
            idcredencial       Int32,
            idpartner          Int32,
            idcliente          Nullable(Int32),
            nombre_credencial  String,
            entorno            String,
            esta_activa        UInt8,
            motivo_inactividad Nullable(String),
            fecha_creacion     Nullable(DateTime),
            fecha_expiracion   Nullable(DateTime),
            nunca_expira       UInt8,
            version            DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idcredencial
        """
    )


def ensure_dim_version_contrato() -> None:
    """Clave (servicio, versión). `fecha_retiro` ausente sustituye la época cero."""
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_version_contrato (
            idversion         Int32,
            id_servicio       Int32,
            servicio          Nullable(String),
            version           String,
            estado            String,
            fecha_publicacion Nullable(DateTime),
            fecha_retiro      Nullable(DateTime),
            version_carga     DateTime
        ) ENGINE = ReplacingMergeTree(version_carga)
        ORDER BY (id_servicio, version)
        """
    )


def ensure_hecho_llamada_api() -> None:
    """Transacción, grano una llamada. **Sin IP.** Una sola fuente de consumo."""
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_llamada_api (
            idlog               Int32,
            fecha               Date,
            fechahora           DateTime,
            idpartner           Int32,
            partner             String,
            idcliente           Nullable(Int32),
            plan_api            Nullable(String),
            idcredencial        Nullable(Int32),
            entorno             Nullable(String),
            endpoint_path       String,
            metodo_http         String,
            codigo_http         UInt16,
            clase_resultado     String,
            latencia_ms         Int32,
            servicio            Nullable(String),
            version_contrato    Nullable(String),
            version_es_derivada UInt8,
            cargado_en          DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idpartner, endpoint_path)
        """
    )


def ensure_hecho_cambio_acceso() -> None:
    """Transacción, grano un cambio. **Sin ejecutado_por.**"""
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_cambio_acceso (
            idhistorial        Int32,
            fecha              Date,
            fechahora          DateTime,
            idpartner          Int32,
            partner            String,
            idcredencial       Nullable(Int32),
            tipo_cambio        String,
            estado_anterior    Nullable(String),
            estado_nuevo       Nullable(String),
            es_cambio_efectivo UInt8,
            motivo             Nullable(String),
            cargado_en         DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idpartner, idhistorial)
        """
    )


def ensure_hecho_suscripcion() -> None:
    """Instantánea acumulada. **Grano: una suscripción.**

    ⚠️ `estado_derivado` nunca sale de `activo`: el origen tiene canceladas con
    esa columna en verdadero, y usarla inflaría el MRR.

    ⚠️ Las consultas **deben** forzar `FINAL`. Sin eso, una suscripción
    actualizada cuenta dos veces.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_suscripcion (
            id_suscripcion           Int32,
            fecha                    Date,
            idcliente                Int32,
            tipo_cliente             Nullable(String),
            idplan                   Int32,
            plan                     String,
            nivel                    Nullable(String),
            fecha_alta               DateTime,
            fecha_fin_prevista       Nullable(DateTime),
            fecha_ultima_renovacion  Nullable(DateTime),
            fecha_suspension         Nullable(DateTime),
            fecha_reactivacion       Nullable(DateTime),
            fecha_cancelacion        Nullable(DateTime),
            estado_derivado          String,
            motivo_cancelacion       Nullable(String),
            precio                   Decimal(12, 2),
            periodicidad             Nullable(String),
            precio_mensualizado      Nullable(Decimal(12, 2)),
            renovacion_automatica    UInt8,
            idplan_programado        Nullable(Int32),
            severidades_contratadas  Array(Int32),
            vigencia_inconsistente   UInt8,
            cargado_en               DateTime,
            version                  DateTime
        ) ENGINE = ReplacingMergeTree(version)
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, id_suscripcion)
        """
    )


def ensure_hecho_factura() -> None:
    """Hecho de **transacción**. Grano: una factura o nota de crédito.

    ⚠️ Sin `idmetodopago`, sin `desglose_cargos` y sin `motivo_anulacion`.
    `monto_con_signo` existe para que sumar ingresos sea sumar: las notas restan
    solas. `FINAL` está **prohibido**.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_factura (
            id_factura              String,
            fecha                   Date,
            fecha_emision           DateTime,
            fecha_vencimiento       Nullable(DateTime),
            idcliente               Int32,
            tipo_cliente            Nullable(String),
            id_suscripcion          Nullable(Int32),
            idplan                  Nullable(Int32),
            plan                    Nullable(String),
            estado_pago             String,
            tipo                    Nullable(String),
            es_nota_credito         UInt8,
            id_factura_original     Nullable(String),
            signo                   Int8,
            monto_base              Decimal(12, 2),
            impuestos               Decimal(12, 2),
            monto_total             Decimal(12, 2),
            monto_con_signo         Decimal(12, 2),
            reintentos              UInt8,
            pagada_primer_intento   UInt8,
            dias_mora               Nullable(Int32),
            cargado_en              DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idcliente, id_factura)
        """
    )


def ensure_hecho_solicitud_cambio_plan() -> None:
    """Hecho de **transacción**. Grano: una solicitud de cambio de plan.

    ⚠️ Sin `idadminaprobador` y sin `motivo_rechazo`. El tipo de movimiento
    sale del **delta de precio**, no del nivel del plan.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_solicitud_cambio_plan (
            idsolicitud          Int32,
            fecha                Date,
            fecha_solicitud      DateTime,
            fecha_resolucion     Nullable(DateTime),
            idcliente            Int32,
            idplan_actual        Int32,
            plan_actual          String,
            idplan_solicitado    Int32,
            plan_solicitado      String,
            tipo_movimiento      String,
            delta_precio         Decimal(12, 2),
            estado               String,
            esta_resuelta        UInt8,
            segundos_resolucion  Nullable(Int32),
            cargado_en           DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idcliente, idsolicitud)
        """
    )


def ensure_hecho_ticket() -> None:
    """Instantánea acumulada. **Grano: un ticket.**

    ⚠️ Los hitos y métricas de tiempo son anulables: un `0` del origen es
    centinela de «aún no ocurrió», no una respuesta instantánea.

    ⚠️ Los límites de SLA se copian de la vigencia **al crearse** el ticket.
    Unir con la configuración actual reescribiría el cumplimiento pasado.

    ⚠️ Sin `asunto` ni `descripcion`.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_ticket (
            id_reclamo           Int32,
            fecha                Date,
            fechahora_creacion   DateTime,

            idcliente            Int32,
            tipo_cliente         Nullable(String),
            idplan               Nullable(Int32),
            plan                 Nullable(String),

            idagente             Nullable(Int32),
            tiene_agente         UInt8,

            tipo                 Nullable(String),
            tipo_incidencia      Nullable(String),
            prioridad            Nullable(String),
            idservicio           Nullable(Int32),
            servicio             Nullable(String),
            estado               String,

            idslaconfig          Nullable(Int32),
            tiene_compromiso     UInt8,
            motivo_sin_compromiso Nullable(String),
            segundos_respuesta_max  Nullable(Int32),
            segundos_resolucion_max Nullable(Int32),

            hora_primera_respuesta Nullable(DateTime),
            hora_resolucion      Nullable(DateTime),
            hora_cierre          Nullable(DateTime),
            hora_cierre_confirmado Nullable(DateTime),

            segundos_primera_respuesta Nullable(Int32),
            segundos_resolucion  Nullable(Int32),

            desenlace_sla        Nullable(String),
            fue_reabierto        UInt8,
            reaperturas          UInt8,

            cargado_en           DateTime,
            version              DateTime
        ) ENGINE = ReplacingMergeTree(version)
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, id_reclamo)
        """
    )


def ensure_hecho_accion_ticket() -> None:
    """Hecho de **transacción**. Grano: una acción del historial.

    ⚠️ Sin `mensaje` ni `es_nota_interna`. `FINAL` está prohibido: MergeTree
    de transacción, no ReplacingMergeTree.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_accion_ticket (
            id_historial     Int32,
            fecha            Date,
            fechahora        DateTime,

            id_reclamo       Int32,
            idcliente        Nullable(Int32),
            idagente         Nullable(Int32),

            tipo_accion      String,
            es_escalado      UInt8,
            es_escalado_automatico UInt8,
            estado_anterior  Nullable(String),
            estado_nuevo     Nullable(String),
            es_cambio_efectivo UInt8,

            cargado_en       DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, id_reclamo, id_historial)
        """
    )


# ── Ventas y CRM (transaccion) ──────────────────────────────────────────


def ensure_hecho_transicion_embudo() -> None:
    """Hecho de **transaccion**. Grano: un cambio de etapa del embudo.

    ⚠️ `notas` no se copia: es texto libre escrito por el ejecutivo.

    ⚠️ `segundos_en_etapa_anterior` va ausente en la primera transicion de cada
    prospecto. Cero afirmaria que paso al instante, y esa cifra encabezaria el
    informe de permanencia con una mentira.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_transicion_embudo (
            idtransicion       Int32,
            fecha              Date,
            fechahora          DateTime,

            idprospecto        Int32,
            empresa            String,
            canal              String,
            tipo_organizacion  Nullable(String),

            etapa_anterior     Nullable(String),
            etapa_nueva        String,
            es_avance          UInt8,
            es_terminal        UInt8,
            motivo_perdida     Nullable(String),

            segundos_en_etapa_anterior Nullable(Int32),

            cargado_en         DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idprospecto, idtransicion)
        """
    )


def ensure_hecho_asignacion_prospecto() -> None:
    """Hecho de **transaccion**. Grano: una asignacion de prospecto.

    Es el primer historial del proyecto que el origen si guarda bien: cada
    cambio trae su instante, y la atribucion por ejecutivo es exacta desde el
    primer dia. El acotamiento de los informes compuestos filtra por este hecho,
    no por la dimension: guardar el dueno alli reescribiria la carga historica
    al reasignar.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_asignacion_prospecto (
            idasignacion       Int32,
            fecha              Date,
            fechahora          DateTime,

            idprospecto        Int32,
            empresa            String,
            idejecutivo        Int32,
            idejecutivo_previo Nullable(Int32),
            tipo_asignacion    String,
            motivo             Nullable(String),

            cargado_en         DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idprospecto, idasignacion)
        """
    )


def ensure_hecho_interaccion_demo() -> None:
    """Hecho de **transaccion**. Grano: un evento de la demo.

    ⚠️ `metadata` no se copia: es un campo libre cuyo contenido nadie garantiza.
    La fuente puede estar vacia hoy (entorno, no diseno); el esquema existe para
    cuando haya demos.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_interaccion_demo (
            idinteraccion Int32,
            fecha         Date,
            fechahora     DateTime,
            idprospecto   Int32,
            empresa       String,
            canal         String,
            tipo_evento   String,
            seccion       Nullable(String),
            cargado_en    DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idprospecto, idinteraccion)
        """
    )


def ensure_hecho_notificacion_ventas() -> None:
    """Hecho de **transaccion**. Grano: un aviso disparado al ejecutivo.

    ⚠️ `hubo_avance = 0` y `segundos_a_reaccion` ausente es un aviso **sin
    reaccion**, no una reaccion instantanea. Contarlo como cero haria que los
    avisos ignorados mejoraran la latencia media.

    ⚠️ `estado_envio` no se copia: ningun codigo la escribe.
    ⚠️ `idusuariogerentenotificado` no se copia: es identidad de persona.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_notificacion_ventas (
            idnotificacion      Int32,
            fecha               Date,
            fechahora           DateTime,
            idprospecto         Int32,
            empresa             String,
            regla_disparada     String,
            canal_aviso         String,
            hubo_avance         UInt8,
            segundos_a_reaccion Nullable(Int32),
            cargado_en          DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idprospecto, idnotificacion)
        """
    )


# ─────────────────────────────── Hechos ─────────────────────────────────


def ensure_hecho_accidente() -> None:
    """Instantánea acumulada. **Grano: un caso registrado.**

    Los tiempos del proceso son restas de esta misma fila, sin uniones y sin
    ordenar. Un hito no alcanzado va `NULL`.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_accidente (
            idaccidente             String,
            fecha                   Date,
            fechahora_accidente     DateTime,
            franja_horaria          String,

            idcalle                 Nullable(Int32),
            condado                 Nullable(String),
            ciudad                  Nullable(String),
            idseveridad             Nullable(Int32),
            severidad               Nullable(String),
            tipo_reportado          Nullable(String),

            hora_confirmacion       Nullable(DateTime),
            hora_primera_asignacion Nullable(DateTime),
            hora_primera_llegada    Nullable(DateTime),
            hora_cierre             Nullable(DateTime),

            num_vehiculos           Nullable(Int32),
            num_heridos             Nullable(Int32),
            num_victimas            Nullable(Int32),
            num_fallecidos          Nullable(Int32),
            duracion_minutos        Nullable(Int32),
            total_intentos_despacho Nullable(Int32),
            num_evidencias          Nullable(Int32),

            -- §4.bis — métricas de enriquecimiento y cierre (US3).
            --
            -- ⚠️ Todas `Nullable`, y la nulidad significa cosas **opuestas** en
            -- los dos bloques:
            --
            -- Los recuentos van a `0` cuando el caso existe y no tiene ninguno:
            -- cero notas es una medición, no una ausencia. Solo van nulos en las
            -- filas cargadas antes de que la métrica existiera, donde el `0`
            -- afirmaría algo que nadie midió.
            num_notas               Nullable(Int32),
            num_conductores         Nullable(Int32),
            num_implicados          Nullable(Int32),
            num_elementos_clima     Nullable(Int32),
            num_escaladas_severidad Nullable(Int32),

            -- Estos tres van nulos cuando **no se registraron**. Una
            -- calificación de `0` sería la peor nota posible, que es lo
            -- contrario de «sin calificar» — y es la clase de confusión que
            -- convierte un caso sin encuestar en el peor caso del mes.
            severidad_inicial       Nullable(String),
            resultado_atencion      Nullable(String),
            calificacion            Nullable(Int32),

            fue_descartado          UInt8,
            es_duplicado            UInt8,
            duplicado_de            Nullable(String),

            cargado_en              DateTime,
            version                 DateTime
        ) ENGINE = ReplacingMergeTree(version)
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idaccidente)
        """
    )


def ensure_hecho_baja_unidad() -> None:
    """Hecho de **transaccion**. Grano: una baja de unidad (Red Operativa, US1).

    Tiene instante propio, tipo y motivo, y su grano no es la unidad: una unidad
    puede darse de baja mas de una vez si vuelve a la flota. Guardarlo como
    metrica de la dimension perderia el instante, que es justo lo que miden la
    rotacion y las bajas forzadas.

    ⚠️ `con_caso_en_curso` se **deriva** de que la baja traiga un accidente
    asociado. Es lo que distingue una baja ordenada de una que dejo un caso a
    medias, y el origen no lo dice de otra forma: lo unico que hay es
    `idaccidente` poblado o no.

    ⚠️ `motivo` **si entra** al modelo, y es una excepcion razonada. Es un campo
    corto y clasificable del catalogo operativo —«retiro por averia mecanica»—,
    no una nota redactada por quien da la baja. Si algun dia admitiera texto
    libre, sale del modelo: el criterio es si se puede agrupar, no si es corto.

    **`idusuario` no se copia**, aunque el origen lo trae: quien firma la baja es
    identidad de persona.

    `proveedor` es el de la version vigente **al darse de baja**, por atribucion
    historica. Copiar el actual reatribuiria las bajas de un proveedor al que
    heredo sus unidades, que es el defecto que este modelo existe para corregir.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_baja_unidad (
            idbaja             Int32,
            fecha              Date,
            fechahora          DateTime,

            sk_unidad          UInt64,
            idunidademergencia Int32,
            unidad             String,
            proveedor          String,
            idcondado          Nullable(Int32),
            condado            Nullable(String),

            tipo_baja          String,
            motivo             Nullable(String),
            con_caso_en_curso  UInt8,
            idaccidente        Nullable(String),

            dias_en_flota      Nullable(Int32),

            cargado_en         DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idunidademergencia)
        """
    )


def ensure_hecho_validacion_region() -> None:
    """Hecho de **transaccion**. Grano: un intento de validacion de region.

    ⚠️ `numero_intento` es lo que hace calculable la tasa de aprobacion al primer
    intento. Sin el, una region rechazada dos veces y aprobada a la tercera
    contaria como **aprobada**, y el indicador daria el mejor resultado
    justamente en el caso que peor fue. Es el mismo mecanismo que en el hecho de
    despacho, y el mismo motivo.

    ⚠️ **`idusuario` no se copia**, aunque el origen lo trae. El validador es una
    persona, y un informe de validaciones desglosado por quien las firma es un
    registro de decisiones individuales: sobre el se juzgaria a alguien por
    resultados que dependen de las regiones que le tocaron (FR-021).

    Cuesta mas de ver que otras exclusiones porque parece informacion de proceso.
    No lo es.

    `motivo` **si entra**: es la categoria del rechazo, y es lo que hace util el
    informe de motivos. Un motivo ausente en una aprobacion es correcto —no hubo
    nada que justificar— y **no** debe convertirse en una categoria.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_validacion_region (
            idvalidacion      Int32,
            fecha             Date,
            fechahora         DateTime,

            sk_region         UInt64,
            idregionoperativa Int32,
            nombre_region     String,

            resultado         String,
            motivo            Nullable(String),
            numero_intento    UInt8,

            cargado_en        DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idregionoperativa, idvalidacion)
        """
    )


def ensure_hecho_despacho() -> None:
    """Instantánea acumulada. **Grano: un intento de asignación a una unidad.**

    `proveedor` es el de la versión vigente **al despachar**. Copiar el actual
    reintroduciría el defecto que este modelo existe para corregir.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_despacho (
            iddespacho         Int32,
            idaccidente        String,
            fecha              Date,
            fechahora_despacho DateTime,

            sk_unidad          UInt64,
            idunidademergencia Int32,
            unidad             String,
            proveedor          String,
            idorigendespacho   Int32,
            origen_despacho    String,
            idseveridad        Nullable(Int32),
            severidad          Nullable(String),
            condado            Nullable(String),

            hora_confirmacion  Nullable(DateTime),
            hora_rechazo       Nullable(DateTime),
            hora_llegada       Nullable(DateTime),
            hora_retiro        Nullable(DateTime),

            segundos_respuesta Nullable(Int32),
            segundos_transito  Nullable(Int32),
            segundos_atencion  Nullable(Int32),

            numero_intento     UInt8,
            resultado          String,
            motivo_rechazo     Nullable(String),
            retiro_forzado     UInt8,

            cargado_en         DateTime,
            version            DateTime
        ) ENGINE = ReplacingMergeTree(version)
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idaccidente, iddespacho)
        """
    )


def ensure_hecho_ping_unidad() -> None:
    """Hecho de **transacción**. Grano: una posición reportada por una unidad.

    Es el hecho más voluminoso del modelo —59 045 filas hoy y creciendo con cada
    seguimiento— y el que sostiene el informe de pérdida de señal: los huecos se
    detectan comparando instantes consecutivos de la misma unidad.

    ⚠️ **Sin latitud ni longitud.** El origen las trae y **no se copian**: la
    pérdida de señal se calcula con los instantes, no con las posiciones. Es el
    caso que mejor ilustra la exclusión del §5 — la utilidad analítica no
    requiere el dato sensible, así que el dato sensible no entra.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_ping_unidad (
            idping             Int32,
            fecha              Date,
            fechahora          DateTime,

            sk_unidad          UInt64,
            idunidademergencia Int32,
            proveedor          String,
            idaccidente        Nullable(String),

            segundos_desde_anterior Nullable(Int32),

            cargado_en         DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idunidademergencia, fechahora)
        """
    )


def ensure_hecho_estado_unidad() -> None:
    """Hecho de **transacción**. Grano: un cambio de estado registrado.

    Es el tercer hecho del modelo, y el primero que no es una instantánea
    acumulada. Por eso usa `MergeTree` y no el motor con deduplicación: una fila
    de transacción **no se actualiza nunca** —el suceso ya ocurrió— y las
    consultas sobre esta tabla no necesitan forzar versión final. La idempotencia
    la da el descarte de partición, no el motor.

    `idusuario` **no se copia**, aunque el origen lo trae: analizar la
    disponibilidad de la flota no requiere saber quién movió cada estado.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_estado_unidad (
            idhistorial                  Int32,
            fecha                        Date,
            fechahora                    DateTime,

            sk_unidad                    UInt64,
            idunidademergencia           Int32,
            unidad                       String,
            proveedor                    String,

            idestadounidademergencia     Nullable(Int32),
            estado_nuevo                 Nullable(String),
            estado_anterior              Nullable(String),

            es_cambio_efectivo           UInt8,
            segundos_en_estado_anterior  Nullable(Int32),

            cargado_en                   DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idunidademergencia, idhistorial)
        """
    )


# ──────────────────────────── Orquestación ──────────────────────────────

#: Las dimensiones, en el orden en que se crean. **Siempre antes que los hechos.**


def ensure_hecho_evidencia() -> None:
    """Hecho de **transacción**. Grano: una evidencia capturada.

    Por qué un hecho y no unas métricas más del caso: tiene **dos instantes
    propios** —capturada y sincronizada— y su grano no es el caso. Un caso puede
    tener varias evidencias con latencias muy distintas, y contarlas en el caso
    respondería «cuántas hubo» pero nunca «cuánto tardaron».

    **Fotos y notas en la misma tabla** porque comparten grano, dimensiones y
    preguntas. Separarlas obligaría a unir dos hechos para responder «cobertura
    de foto **y** nota», que es justamente el informe #17.

    ⚠️ **Sin `idusuario`**, aunque las dos fuentes lo traen (research D6). El
    informe de volumen se entrega **por unidad**, no por persona: un ranking de
    quién sube menos fotos es una herramienta de vigilancia laboral, y el
    problema que se quiere ver —qué unidades documentan mal— se responde igual
    sin nombrar a nadie.

    ⚠️ **`fechahora_sincronia` ausente significa «aún no sincronizada»**, no
    «sincronizada en la época cero». La latencia de esas evidencias es
    **ausente**: ni cero, que diría que fue instantánea, ni infinita, que diría
    que nunca llegará.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_evidencia (
            idevidencia          Int32,
            tipo                 String,
            fecha                Date,
            fechahora_captura    DateTime,
            fechahora_sincronia  Nullable(DateTime),

            idaccidente          String,
            sk_unidad            UInt64,
            idunidademergencia   Int32,
            proveedor            String,
            idseveridad          Nullable(Int32),
            severidad            Nullable(String),
            condado              Nullable(String),

            segundos_hasta_sincronia Nullable(Int32),
            categoria_nota       Nullable(String),

            cargado_en           DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idunidademergencia, idevidencia)
        """
    )


#: Columnas añadidas a `hecho_accidente` después de su creación (§4.bis).
COLUMNAS_ANADIDAS_HECHO_ACCIDENTE = (
    ("num_notas", "Nullable(Int32)"),
    ("num_conductores", "Nullable(Int32)"),
    ("num_implicados", "Nullable(Int32)"),
    ("num_elementos_clima", "Nullable(Int32)"),
    ("num_escaladas_severidad", "Nullable(Int32)"),
    ("severidad_inicial", "Nullable(String)"),
    ("resultado_atencion", "Nullable(String)"),
    ("calificacion", "Nullable(Int32)"),
    ("distancia_millas", "Nullable(Float64)"),
    ("condicion_clima", "Nullable(String)"),
)


#: Columnas anadidas a dimensiones despues de su creacion (Red Operativa, US1).
#: Cuentas amplia `dim_cliente` aqui: `CREATE TABLE IF NOT EXISTS` no migra.
COLUMNAS_ANADIDAS_DIMENSIONES = (
    ("dim_unidad", "fecha_alta", "Nullable(DateTime)"),
    ("dim_unidad", "tuvo_primer_acceso", "UInt8 DEFAULT 0"),
    ("dim_geografia", "condados_vecinos", "Array(Int32)"),
    ("dim_geografia", "idregionoperativa", "Nullable(Int32)"),
    ("dim_cliente", "cohorte_alta", "Nullable(String)"),
    ("dim_cliente", "fecha_baja", "Nullable(DateTime)"),
    ("dim_cliente", "motivo_baja", "Nullable(String)"),
    ("dim_cliente", "etapa_onboarding_actual", "Nullable(String)"),
    ("dim_cliente", "onboarding_completo", "UInt8 DEFAULT 0"),
    ("dim_cliente", "resultado_solicitud", "Nullable(String)"),
)

COLUMNAS_ANADIDAS_HECHO_FACTURA = (
    ("tipo", "Nullable(String)"),
)


def ensure_columnas_nuevas_dimensiones() -> None:
    """Anade a las dimensiones las columnas que se sumaron despues de crearlas.

    Misma razon que en `hecho_accidente`: `CREATE TABLE IF NOT EXISTS` **no
    migra**. En una instalacion nueva la tabla nace completa; en la que ya existe
    el `CREATE` no hace nada y las columnas no aparecen, sin ningun error hasta
    que una consulta pida una que no esta.
    """
    for tabla, nombre, tipo in COLUMNAS_ANADIDAS_DIMENSIONES:
        execute_clickhouse(
            f"ALTER TABLE {tabla} ADD COLUMN IF NOT EXISTS {nombre} {tipo}"
        )


def ensure_columnas_nuevas_hecho_onboarding() -> None:
    """`completada` se sumo despues de crear la tabla (decision #45).

    ⚠️ Hace falta porque `CREATE TABLE IF NOT EXISTS` **no migra nada**: en un
    entorno con la tabla ya creada, la columna nueva no aparece sola y la carga
    falla al insertar.
    """
    execute_clickhouse(
        "ALTER TABLE hecho_onboarding ADD COLUMN IF NOT EXISTS completada UInt8 DEFAULT 1"
    )


def ensure_columnas_nuevas_hecho_factura() -> None:
    """Partners necesita `tipo` para separar excedente de ingreso base."""
    for nombre, tipo in COLUMNAS_ANADIDAS_HECHO_FACTURA:
        execute_clickhouse(
            f"ALTER TABLE hecho_factura ADD COLUMN IF NOT EXISTS {nombre} {tipo}"
        )


def ensure_columnas_nuevas_hecho_accidente() -> None:
    """Añade a `hecho_accidente` las columnas que se sumaron después de crearla.

    ⚠️ **Hace falta porque `CREATE TABLE IF NOT EXISTS` no migra nada.** En una
    instalación nueva la tabla nace con las ocho columnas y todo cuadra; en la
    que ya existe, el `CREATE` no hace nada —la tabla ya está— y las columnas
    **no aparecen**. El DDL sería correcto y el almacén estaría incompleto, sin
    ningún error por ninguna parte hasta que una consulta pidiera una columna
    inexistente.

    Las filas anteriores quedan con `NULL` en las columnas nuevas, que es lo
    correcto: nadie midió cuántas notas tenía un caso cargado antes de que la
    métrica existiera, y un `0` lo afirmaría.
    """
    for nombre, tipo in COLUMNAS_ANADIDAS_HECHO_ACCIDENTE:
        execute_clickhouse(
            f"ALTER TABLE hecho_accidente ADD COLUMN IF NOT EXISTS {nombre} {tipo}"
        )


DIMENSIONES = (
    ensure_dim_tiempo,
    ensure_dim_geografia,
    ensure_dim_severidad,
    ensure_dim_origen_despacho,
    ensure_dim_unidad,
    ensure_dim_region,
    ensure_dim_prospecto,
    ensure_dim_canal,
    ensure_dim_condado_vecino,
    ensure_dim_plan,
    ensure_dim_cliente,
    ensure_dim_sla_config,
    ensure_dim_servicio,
    ensure_dim_estado_soporte,
    ensure_dim_usuario_organizacion,
    ensure_dim_etapa_onboarding,
    ensure_dim_rol,
    ensure_dim_usuario_rol,
    ensure_dim_partner,
    ensure_dim_credencial_api,
    ensure_dim_version_contrato,
)

HECHOS = (
    ensure_hecho_accidente,
    ensure_hecho_evidencia,
    ensure_hecho_baja_unidad,
    ensure_hecho_validacion_region,
    ensure_hecho_despacho,
    ensure_hecho_estado_unidad,
    ensure_hecho_ping_unidad,
    ensure_hecho_transicion_embudo,
    ensure_hecho_asignacion_prospecto,
    ensure_hecho_interaccion_demo,
    ensure_hecho_notificacion_ventas,
    ensure_hecho_suscripcion,
    ensure_hecho_factura,
    ensure_hecho_solicitud_cambio_plan,
    ensure_hecho_ticket,
    ensure_hecho_accion_ticket,
    ensure_hecho_sesion,
    ensure_hecho_onboarding,
    ensure_hecho_llamada_api,
    ensure_hecho_cambio_acceso,
)


def ensure_modelo_analitico() -> None:
    """Crea el modelo entero. Idempotente: repetirlo no altera nada."""
    for crear in DIMENSIONES + HECHOS:
        crear()
    # Después de los `CREATE`, porque migra una tabla que aquellos dan por hecha.
    ensure_columnas_nuevas_hecho_accidente()
    ensure_columnas_nuevas_hecho_factura()
    ensure_columnas_nuevas_hecho_onboarding()
    ensure_columnas_nuevas_dimensiones()

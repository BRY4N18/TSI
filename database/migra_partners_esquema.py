"""Prepara el esquema Pinot del departamento Partners y API.

Motivo (ver `partner-api-onboarding/backend/spec.md` seccion 15, D2):
Pinot no tiene NULL en este proyecto — ninguna de las 78 tablas habilita
`nullHandlingEnabled`. Todo NULL publicado se materializa como un centinela
elegido por Pinot, y esos centinelas rompen reglas de negocio del departamento:

  planapi            NULL -> 'null'   (string de 4 letras, NO vacio)
                     => la precondicion "planapi IS NOT NULL" de RF-PON-004
                        seria SIEMPRE cierta: un partner sin plan podria
                        emitir credenciales.
  limitellamadasmes  NULL -> 0
                     => cupo 0 es indistinguible de "sin plan"; CU-O54
                        facturaria todo el consumo como excedente.
  sandbox_expiracion NULL -> Long.MIN_VALUE
                     => un partner recien registrado figura como vencido.
  fecha_expiracion   NULL -> Long.MIN_VALUE
                     => un job "expira lo vencido" revocaria TODAS las
                        credenciales de produccion.

La decision (2026-08-08) fue declarar centinelas explicitos por columna,
elegidos para que las consultas de negocio funcionen sin casos especiales,
manteniendo la convencion unica del proyecto (sin habilitar null handling).

Ademas corrige `timeColumnName` de Dim_Partner: apuntaba a `sandbox_activado`,
una columna OPCIONAL que esta vacia hasta la activacion de pruebas. La columna
de tiempo de Pinot se usa para gestion de segmentos y retencion, y debe estar
siempre poblada: pasa a `fecha_actualizacion`, como en todas las demas
dimensiones mutables del esquema (Dim_Servicio, Dim_Plan, Dim_Cliente,
Dim_EstadoIntegracion).

Alcance: solo tablas del departamento Partners y API, todas VACIAS (0 filas)
al momento de esta migracion. No toca Fact_Factura ni Fact_Reclamo, que tienen
datos reales y pertenecen a otros departamentos.

Uso:
    python database/migra_partners_esquema.py --dry-run
    python database/migra_partners_esquema.py
"""
import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
ESQUEMAS = RAIZ / "esquemas.json"
TABLAS = RAIZ / "tablas.json"

# Centinela de "no expira nunca": 9999-12-31T23:59:59Z.
# Elegido en el FUTURO a proposito, para que `fecha_expiracion < now()`
# encuentre solo las credenciales realmente vencidas, sin excluir a mano
# las de produccion (RF-PON-008).
NUNCA_EXPIRA = 253402300799000

# --- Centinelas por columna -------------------------------------------------
# Cada valor se eligio para ser IMPOSIBLE como dato real, de modo que la
# ausencia sea inequivoca y las consultas de negocio no necesiten casos aparte.
DEFAULTS = {
    "Dim_Partner": {
        "planapi": "",                 # "" = sin plan; 'null' era indistinguible de un plan real
        "limitellamadasmes": -1,       # -1 = sin cupo asignado; 0 seria un cupo valido
        "limitellamadasminuto": -1,
        "sandbox_activado": 0,         # epoch 0 = nunca activo pruebas
        "sandbox_expiracion": 0,
        "fecha_suspension": "",        # "" = no suspendido
        "motivo_suspension": "",
    },
    "Dim_CredencialAPI": {
        "nombre_credencial": "",
        "fecha_expiracion": NUNCA_EXPIRA,
    },
    "Fact_HistorialAccesoPartner": {
        "idcredencial": -1,            # -1 = evento del partner, no de una credencial (RF-PON-010)
        "motivo": "",
        "estado_anterior": "",
    },
}

# --- Columnas nuevas --------------------------------------------------------
COLUMNAS_NUEVAS = {
    "Dim_CredencialAPI": {
        "dimensionFieldSpecs": [
            # RF-PON-005 / RF-O49.1: credenciales nombradas por sistema.
            {"name": "nombre_credencial", "dataType": "STRING", "defaultNullValue": ""},
        ],
        "dateTimeFieldSpecs": [
            # RF-PON-006: la vigencia es POR CREDENCIAL, no por partner.
            {"name": "fecha_expiracion", "dataType": "LONG",
             "format": "1:MILLISECONDS:EPOCH", "granularity": "1:MILLISECONDS",
             "defaultNullValue": NUNCA_EXPIRA},
        ],
    },
}

# --- Correccion de timeColumnName / comparisonColumn ------------------------
# Ambas apuntaban a columnas que pueden estar vacias o que no avanzan al
# actualizar. `fecha_actualizacion` siempre se escribe y siempre crece.
TIEMPO = {
    "Dim_Partner": "fecha_actualizacion",        # antes: sandbox_activado (opcional, vacia al registrar)
    "Dim_CredencialAPI": "fecha_actualizacion",  # antes: fecha_creacion (no avanza al actualizar)
}

# --- Tabla nueva: catalogo de versiones del contrato (CU-O50, D1) -----------
ESQUEMA_VERSIONES = {
    "schemaName": "Dim_VersionContratoAPI",
    "primaryKeyColumns": ["idversion"],
    "dimensionFieldSpecs": [
        {"name": "idversion", "dataType": "INT"},
        # FK obligatoria: el versionado es POR SERVICIO. Dim_Servicio tiene hoy
        # tres entradas (API Despacho, API Registro de accidentes, Portal Cliente).
        {"name": "id_servicio", "dataType": "INT"},
        {"name": "version", "dataType": "STRING"},
        {"name": "estado", "dataType": "STRING"},   # vigente | soportada | retirada
        {"name": "spec_url", "dataType": "STRING", "defaultNullValue": ""},
        {"name": "activo", "dataType": "BOOLEAN"},
    ],
    "dateTimeFieldSpecs": [
        {"name": "fecha_publicacion", "dataType": "LONG",
         "format": "1:MILLISECONDS:EPOCH", "granularity": "1:MILLISECONDS"},
        # 0 = sin fecha de retiro planificada. Obligatoria antes de pasar a
        # 'retirada' (RN-PON-012), validado a nivel de aplicacion.
        {"name": "fecha_retiro", "dataType": "LONG",
         "format": "1:MILLISECONDS:EPOCH", "granularity": "1:MILLISECONDS",
         "defaultNullValue": 0},
        {"name": "fecha_actualizacion", "dataType": "LONG",
         "format": "1:MILLISECONDS:EPOCH", "granularity": "1:MILLISECONDS"},
    ],
}


def config_tabla(nombre, columna_tiempo):
    """Config REALTIME identica al patron de Dim_Servicio."""
    return {
        "tableName": nombre,
        "schemaName": nombre,
        "tableType": "REALTIME",
        "segmentsConfig": {
            "timeColumnName": columna_tiempo,
            "replication": "1",
            "replicasPerPartition": "1",
        },
        "tenants": {},
        "tableIndexConfig": {
            "loadMode": "MMAP",
            "streamConfigs": {
                "streamType": "kafka",
                "stream.kafka.topic.name": f"{nombre}_topic",
                "stream.kafka.broker.list": "kafka:29092",
                "stream.kafka.consumer.type": "lowlevel",
                "stream.kafka.consumer.prop.auto.offset.reset": "smallest",
                "stream.kafka.consumer.factory.class.name":
                    "org.apache.pinot.plugin.stream.kafka20.KafkaConsumerFactory",
                "stream.kafka.decoder.class.name":
                    "org.apache.pinot.plugin.stream.kafka.KafkaJSONMessageDecoder",
            },
        },
        "routing": {"instanceSelectorType": "strictReplicaGroup"},
        "upsertConfig": {"mode": "FULL", "comparisonColumn": columna_tiempo},
        "metadata": {"customConfigs": {}},
    }


def campos(esquema):
    for clave in ("dimensionFieldSpecs", "metricFieldSpecs", "dateTimeFieldSpecs"):
        for campo in esquema.get(clave, []):
            yield clave, campo


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    esquemas = json.loads(ESQUEMAS.read_text(encoding="utf-8"))
    tablas = json.loads(TABLAS.read_text(encoding="utf-8"))
    por_nombre = {e["schemaName"]: e for e in esquemas}
    cambios = []

    # 1. Columnas nuevas
    for tabla, grupos in COLUMNAS_NUEVAS.items():
        esquema = por_nombre[tabla]
        existentes = {c["name"] for _, c in campos(esquema)}
        for grupo, nuevas in grupos.items():
            for col in nuevas:
                if col["name"] in existentes:
                    continue
                esquema.setdefault(grupo, []).append(col)
                cambios.append(f"{tabla}: + columna {col['name']} ({col['dataType']})")

    # 2. defaultNullValue explicitos
    for tabla, defaults in DEFAULTS.items():
        esquema = por_nombre[tabla]
        for _, campo in campos(esquema):
            nombre = campo["name"]
            if nombre not in defaults:
                continue
            deseado = defaults[nombre]
            if campo.get("defaultNullValue") == deseado:
                continue
            campo["defaultNullValue"] = deseado
            cambios.append(f"{tabla}.{nombre}: defaultNullValue = {deseado!r}")

    # 3. Tabla nueva Dim_VersionContratoAPI
    if "Dim_VersionContratoAPI" not in por_nombre:
        esquemas.append(ESQUEMA_VERSIONES)
        cambios.append("+ esquema Dim_VersionContratoAPI")
    if not any(t["tableName"] == "Dim_VersionContratoAPI" for t in tablas):
        tablas.append(config_tabla("Dim_VersionContratoAPI", "fecha_actualizacion"))
        cambios.append("+ tabla Dim_VersionContratoAPI (topic Dim_VersionContratoAPI_topic)")

    # 4. timeColumnName y comparisonColumn
    for tabla in tablas:
        nombre = tabla["tableName"]
        if nombre not in TIEMPO:
            continue
        col = TIEMPO[nombre]
        antes_time = tabla["segmentsConfig"].get("timeColumnName")
        if antes_time != col:
            tabla["segmentsConfig"]["timeColumnName"] = col
            cambios.append(f"{nombre}: timeColumnName {antes_time} -> {col}")
        antes_cmp = tabla.get("upsertConfig", {}).get("comparisonColumn")
        if antes_cmp != col:
            tabla.setdefault("upsertConfig", {})["comparisonColumn"] = col
            cambios.append(f"{nombre}: comparisonColumn {antes_cmp} -> {col}")

    if not cambios:
        print("Sin cambios: el esquema ya esta al dia.")
        return 0

    print(f"{len(cambios)} cambios:")
    for c in cambios:
        print(f"  - {c}")

    if args.dry_run:
        print("\n--dry-run: no se escribio nada.")
        return 0

    ESQUEMAS.write_text(json.dumps(esquemas, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    TABLAS.write_text(json.dumps(tablas, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nEscritos {ESQUEMAS.name} y {TABLAS.name}.")
    print("Siguiente paso: python database/despliega_partners.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

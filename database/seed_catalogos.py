"""
Seed de catalogos de referencia (dimensiones fijas) que el codigo asume pobladas.
Publica directamente a los topicos Kafka correspondientes (unico canal de escritura).
"""
import json
import time
import subprocess

NOW_MS = int(time.time() * 1000)

# IDs deben coincidir con ESTADO_IDS en
# backend/core/repositories/accidentes/estado_accidente_repository.py
tipos_estado_accidente = [
    {"idtipoestadoincidente": 1, "tipoestadoincidente": "BORRADOR", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idtipoestadoincidente": 2, "tipoestadoincidente": "REPORTADO", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idtipoestadoincidente": 3, "tipoestadoincidente": "BUSCANDO_UNIDAD", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idtipoestadoincidente": 4, "tipoestadoincidente": "ASIGNADO", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idtipoestadoincidente": 5, "tipoestadoincidente": "EN_ATENCIÓN", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idtipoestadoincidente": 6, "tipoestadoincidente": "CERRADO", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idtipoestadoincidente": 7, "tipoestadoincidente": "DESCARTADO", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idtipoestadoincidente": 8, "tipoestadoincidente": "FUSIONADO", "activo": True, "fecha_actualizacion": NOW_MS},
]


# IDs deben coincidir con ESTADO_ID_MAP en
# backend/core/repositories/despacho/historial_estado_unidad_repository.py
estados_unidad_emergencia = [
    {"idestadounidademergencia": 1, "estadounidademergencia": "Activa", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idestadounidademergencia": 2, "estadounidademergencia": "Ocupada", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idestadounidademergencia": 3, "estadounidademergencia": "Fuera de servicio", "activo": True, "fecha_actualizacion": NOW_MS},
]

# Unidad demo vinculada al usuario idusuario=7 (paola.zambrano.unidad@demo.tsi.com, rol Unidad)
unidades_emergencia = [
    {
        "idunidademergencia": 1,
        "idusuario": 7,
        "idcliente": 0,
        "tipopropiedad": "Propia",
        "placa": "TSI-001",
        "capacidad": "4",
        "zonacobertura": "1",
        "contactoproveedor": "",
        "unidademergencia": "Ambulancia 01",
        "tipounidademergencia": "Ambulancia",
        "activo": True,
        "latitud": 19.4326,
        "longitud": -99.1332,
        "fecha_actualizacion": NOW_MS,
    },
]

historial_estado_unidad = [
    {
        "idhistorialestadosunidadesemergencias": 1,
        "estadoanterior": None,
        "estadonuevo": "Activa",
        "idestadounidademergencia": 1,
        "idunidademergencia": 1,
        "idusuario": 7,
        "fechahora": NOW_MS,
        "fecha_actualizacion": NOW_MS,
    },
]


# Jerarquia geografica Calle -> Ciudad -> Condado -> Estado -> Pais,
# mas la cobertura operativa EstadoRegion -> RegionOperativa (RN-REG-003b).
paises = [
    {"idpais": 1, "pais": "Mexico", "activo": True, "fecha_actualizacion": NOW_MS},
]

estados = [
    {"idestado": 1, "estado": "Ciudad de Mexico", "idpais": 1, "activo": True, "fecha_actualizacion": NOW_MS},
]

condados = [
    {"idcondado": 1, "condado": "Cuauhtemoc", "idestado": 1, "activo": True, "fecha_actualizacion": NOW_MS},
    # Vecino de Cuauhtemoc (Dim_CondadoVecino en seed_vinculos.py). Sin flota propia,
    # todo escalamiento CU-O34 desde Cuauhtemoc terminaba en "sin unidades en
    # condados vecinos" porque el condado vecino no tenia ni geografia ni unidades.
    {"idcondado": 2, "condado": "Benito Juarez", "idestado": 1, "activo": True, "fecha_actualizacion": NOW_MS},
]

ciudades = [
    {"idciudad": 1, "ciudad": "Ciudad de Mexico", "idcondado": 1, "activo": True, "fecha_actualizacion": NOW_MS},
    {"idciudad": 2, "ciudad": "Ciudad de Mexico", "idcondado": 2, "activo": True, "fecha_actualizacion": NOW_MS},
]

calles = [
    {"idcalle": 1, "calle": "Av. Reforma", "idciudad": 1, "activo": True, "fecha_actualizacion": NOW_MS},
    {"idcalle": 2, "calle": "Av. Insurgentes Sur", "idciudad": 2, "activo": True, "fecha_actualizacion": NOW_MS},
]

# idestadoregion comparte ID con idestado (asuncion del codigo: validacion_accidente_service
# usa resolve_estado_from_calle() -> idestado y lo pasa directo a is_estado_en_produccion()).
estados_region = [
    {"idestadoregion": 1, "estadoregion": "Ciudad de Mexico", "activo": True, "fecha_actualizacion": NOW_MS},
]

regiones_operativas = [
    {
        "idregionoperativa": 1,
        "idestado": 1,
        "nombreregion": "Centro",
        "estadoregion": "Producción",
        "activo": True,
        "fecha_actualizacion": NOW_MS,
    },
]

region_operativa_estado_region = [
    {
        "idregionoperativaestadoregion": 1,
        "idregionoperativa": 1,
        "idestadoregion": 1,
        "nombreregion": "Centro",
        "activo": True,
        "fecha_actualizacion": NOW_MS,
    },
]


# IDs deben coincidir con ORIGEN_IDS en
# backend/apps/despacho/services/asignacion_inteligente_service.py
origenes_despacho = [
    {"idorigendespacho": 1, "origendespacho": "Automatico", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idorigendespacho": 2, "origendespacho": "Manual", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idorigendespacho": 3, "origendespacho": "Escalado_zona", "activo": True, "fecha_actualizacion": NOW_MS},
]

# IDs deben coincidir con ESTADO_ID_MAP en
# backend/core/repositories/despacho/historial_despacho_repository.py
estados_despacho = [
    {"idestadodespacho": 1, "estadodespacho": "Pendiente", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idestadodespacho": 2, "estadodespacho": "Confirmado", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idestadodespacho": 3, "estadodespacho": "Rechazado", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idestadodespacho": 4, "estadodespacho": "Timeout", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idestadodespacho": 5, "estadodespacho": "Abortado", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idestadodespacho": 6, "estadodespacho": "En_sitio", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idestadodespacho": 7, "estadodespacho": "Retirado", "activo": True, "fecha_actualizacion": NOW_MS},
    {"idestadodespacho": 8, "estadodespacho": "En_transito", "activo": True, "fecha_actualizacion": NOW_MS},
]


def publish(topic, records):
    payload = "\n".join(json.dumps(r) for r in records)
    proc = subprocess.run(
        [
            "docker", "exec", "-i", "kafka",
            "kafka-console-producer", "--bootstrap-server", "localhost:9092",
            "--topic", topic,
        ],
        input=payload.encode(),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Error publicando en {topic}: {proc.stderr.decode()}")
    print(f"Publicados {len(records)} registros en {topic}")


def main():
    publish("Dim_TipoEstadoAccidente_topic", tipos_estado_accidente)
    publish("Dim_EstadoUnidadEmergencia_topic", estados_unidad_emergencia)
    publish("Dim_UnidadEmergencia_topic", unidades_emergencia)
    publish("Fact_HistorialEstadoUnidad_topic", historial_estado_unidad)
    publish("Dim_Pais_topic", paises)
    publish("Dim_Estado_topic", estados)
    publish("Dim_Condado_topic", condados)
    publish("Dim_Ciudad_topic", ciudades)
    publish("Dim_Calle_topic", calles)
    publish("Dim_EstadoRegion_topic", estados_region)
    publish("Dim_RegionOperativa_topic", regiones_operativas)
    publish("Dim_RegionOperativaEstadoRegion_topic", region_operativa_estado_region)
    publish("Dim_OrigenDespacho_topic", origenes_despacho)
    publish("Dim_EstadoDespacho_topic", estados_despacho)


if __name__ == "__main__":
    main()

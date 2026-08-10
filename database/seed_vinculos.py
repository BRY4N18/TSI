"""
Seed de las tablas puente que el codigo consulta pero que no estaban provisionadas:

  - Dim_Usuario_Cliente : que usuarios pertenecen a que cliente corporativo.
    La consulta el expediente del cliente (apps/seguimiento/views/cliente_expediente_views.py)
    y la resolucion de cliente en soporte (apps/soporte_cliente/services/cliente_lookup_service.py).
    Sin ella, "Mis expedientes" respondia HTTP 500.

  - Dim_CondadoVecino : adyacencia entre condados, simetrica.
    La consulta el escalamiento de zona CU-O34 (apps/despacho/services/escalamiento_zona_service.py)
    cuando no hay unidades disponibles en el condado del accidente.

Publica a Kafka, unico canal de escritura del dominio (ver infrastructure.md).
"""
import json
import subprocess
import time

NOW_MS = int(time.time() * 1000)

# Usuarios del cliente corporativo 1 (Empresa Demo). Ana Torres es la admin local.
USUARIO_CLIENTE = [
    {"idusuario": 1, "idcliente": 1},
]

# Preferencias del cliente corporativo. `zonas_geograficas` define sobre que
# condados puede ver expedientes (RN-SEG-005): sin esta fila el filtro resuelve
# a cero condados y "Mis expedientes" sale vacio aunque existan casos cerrados.
PREFERENCIAS_CLIENTE = [
    {
        "id_preferencia": 1,
        "id_cliente": 1,
        "umbrales_alerta": "{}",
        "canales_notificacion": "email",
        "telefono_sms": None,
        # Condado 1 (Cuauhtemoc) es donde caen las calles del catalogo demo.
        "zonas_geograficas": "[1]",
        "destinatarios_reportes": "reportes@empresa-demo.com",
        "frecuencia_reportes": "semanal",
        "formato_reportes": "PDF",
        "activo": True,
    },
]

# Adyacencia declarada una sola vez; abajo se expande a las dos direcciones.
ADYACENCIAS = [
    (1, 2),
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
    usuario_cliente = [
        {
            "idusuariocliente": idx,
            "idusuario": v["idusuario"],
            "idcliente": v["idcliente"],
            "activo": True,
            "fecha_actualizacion": NOW_MS,
        }
        for idx, v in enumerate(USUARIO_CLIENTE, start=1)
    ]

    # La adyacencia es simetrica: si A limita con B, B limita con A. Se generan
    # ambos sentidos para que la consulta por idcondado funcione desde cualquiera.
    pares = []
    for a, b in ADYACENCIAS:
        pares.extend([(a, b), (b, a)])
    condado_vecino = [
        {
            "idcondadovecinorel": idx,
            "idcondado": a,
            "idcondadovecino": b,
            "activo": True,
            "fecha_actualizacion": NOW_MS,
        }
        for idx, (a, b) in enumerate(pares, start=1)
    ]

    preferencias = [
        {**p, "fecha_actualizacion": NOW_MS} for p in PREFERENCIAS_CLIENTE
    ]

    publish("Dim_Usuario_Cliente_topic", usuario_cliente)
    publish("Dim_CondadoVecino_topic", condado_vecino)
    publish("Dim_Preferencias_Cliente_topic", preferencias)


if __name__ == "__main__":
    main()

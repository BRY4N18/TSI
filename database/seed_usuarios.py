"""
Seed de usuarios ficticios (demo) para Dim_Usuarios, Dim_Rol, Dim_Usuario_Rol y Dim_Credencial.
Publica directamente a los topicos Kafka correspondientes (unico canal de escritura, ver infrastructure.md).
Password de todos los usuarios demo: ver DEMO_PASSWORD en backend/scripts/_demo_seed_common.py
"""
import json
import pathlib
import subprocess
import sys
import time

import bcrypt

# Fuente unica de la contrasena demo, compartida con los seeds que corren dentro
# del contenedor Django. Antes este script sembraba "Demo1234!" mientras los de
# backend/scripts sembraban "password123", asi que la misma cuenta pedia una u
# otra segun cual hubiera corrido ultimo.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "backend" / "scripts"))
from _demo_seed_common import (  # noqa: E402
    DEMO_PASSWORD,
    ESTADO_CREDENCIAL_ACTIVO,
    filas_dim_rol,
)

NOW_MS = int(time.time() * 1000)
PASSWORD_PLAIN = DEMO_PASSWORD
PASSWORD_HASH = bcrypt.hashpw(PASSWORD_PLAIN.encode(), bcrypt.gensalt(rounds=12)).decode()

# Catalogo de roles: se toma del modulo compartido para que este seed y los de
# backend/scripts no publiquen listas divergentes sobre los mismos idrol.
roles = filas_dim_rol(NOW_MS)

usuarios = [
    {"idusuario": 1, "nombres": "Ana", "apellidos": "Torres", "gmail": "ana.torres.cliente@demo.tsi.com", "identificacion": "0102030405", "genero": "F", "telefono": "0991234501", "activo": True, "fechanacimiento": -600000000000, "fecha_actualizacion": NOW_MS, "idrol": 1},
    {"idusuario": 2, "nombres": "Carlos", "apellidos": "Mendoza", "gmail": "carlos.mendoza.admin@demo.tsi.com", "identificacion": "0102030406", "genero": "M", "telefono": "0991234502", "activo": True, "fechanacimiento": -500000000000, "fecha_actualizacion": NOW_MS, "idrol": 2},
    {"idusuario": 3, "nombres": "Lucia", "apellidos": "Vera", "gmail": "lucia.vera.soporte@demo.tsi.com", "identificacion": "0102030407", "genero": "F", "telefono": "0991234503", "activo": True, "fechanacimiento": -450000000000, "fecha_actualizacion": NOW_MS, "idrol": 3},
    {"idusuario": 4, "nombres": "Diego", "apellidos": "Ramirez", "gmail": "diego.ramirez.operador@demo.tsi.com", "identificacion": "0102030408", "genero": "M", "telefono": "0991234504", "activo": True, "fechanacimiento": -400000000000, "fecha_actualizacion": NOW_MS, "idrol": 4},
    {"idusuario": 5, "nombres": "Maria", "apellidos": "Suarez", "gmail": "maria.suarez.dev@demo.tsi.com", "identificacion": "0102030409", "genero": "F", "telefono": "0991234505", "activo": True, "fechanacimiento": -350000000000, "fecha_actualizacion": NOW_MS, "idrol": 5},
    {"idusuario": 6, "nombres": "Roberto", "apellidos": "Paredes", "gmail": "roberto.paredes.director@demo.tsi.com", "identificacion": "0102030410", "genero": "M", "telefono": "0991234506", "activo": True, "fechanacimiento": -300000000000, "fecha_actualizacion": NOW_MS, "idrol": 6},
    {"idusuario": 7, "nombres": "Paola", "apellidos": "Zambrano", "gmail": "paola.zambrano.unidad@demo.tsi.com", "identificacion": "0102030411", "genero": "F", "telefono": "0991234507", "activo": True, "fechanacimiento": -350000000000, "fecha_actualizacion": NOW_MS, "idrol": 7},
    {"idusuario": 8, "nombres": "Julio", "apellidos": "Herrera", "gmail": "julio.herrera.despacho@demo.tsi.com", "identificacion": "0102030412", "genero": "M", "telefono": "0991234508", "activo": True, "fechanacimiento": -400000000000, "fecha_actualizacion": NOW_MS, "idrol": 8},
    {"idusuario": 9, "nombres": "Camila", "apellidos": "Rios", "gmail": "camila.rios.tecnico@demo.tsi.com", "identificacion": "0102030413", "genero": "F", "telefono": "0991234509", "activo": True, "fechanacimiento": -380000000000, "fecha_actualizacion": NOW_MS, "idrol": 9},
    # Segunda unidad de campo: el despacho necesita mas de una unidad para poder
    # demostrar seleccion de candidata y escalamiento de zona (CU-O34).
    {"idusuario": 11, "nombres": "Marco", "apellidos": "Silva", "gmail": "marco.silva.unidad@demo.tsi.com", "identificacion": "0102030415", "genero": "M", "telefono": "0991234511", "activo": True, "fechanacimiento": -360000000000, "fecha_actualizacion": NOW_MS, "idrol": 7},
    # Tercera unidad, en el condado vecino (Benito Juarez). Sin ella, escalar a
    # condados vecinos (CU-O34) siempre resolvia "sin unidades disponibles" aunque
    # el escalamiento en si funcionara — no habia flota para encontrar del otro lado.
    {"idusuario": 14, "nombres": "Valeria", "apellidos": "Cortes", "gmail": "valeria.cortes.unidad@demo.tsi.com", "identificacion": "0102030416", "genero": "F", "telefono": "0991234513", "activo": True, "fechanacimiento": -340000000000, "fecha_actualizacion": NOW_MS, "idrol": 7},
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
    dim_usuarios = [
        {k: v for k, v in u.items() if k != "idrol"} for u in usuarios
    ]
    dim_usuario_rol = [
        {"idusuariorol": u["idusuario"], "idusuario": u["idusuario"], "idrol": u["idrol"], "activo": True, "fecha_actualizacion": NOW_MS}
        for u in usuarios
    ]
    dim_credencial = [
        {"idcredencial": u["idusuario"], "idusuario": u["idusuario"], "contrasena": PASSWORD_HASH, "estadocredencial": ESTADO_CREDENCIAL_ACTIVO, "fecha_actualizacion": NOW_MS}
        for u in usuarios
    ]

    publish("Dim_Rol_topic", roles)
    publish("Dim_Usuarios_topic", dim_usuarios)
    publish("Dim_Usuario_Rol_topic", dim_usuario_rol)
    publish("Dim_Credencial_topic", dim_credencial)

    print("\n=== Credenciales demo (password para todos: %s) ===" % PASSWORD_PLAIN)
    roles_by_id = {r["idrol"]: r["rol"] for r in roles}
    for u in usuarios:
        print(f"- {u['gmail']:40s} rol={roles_by_id.get(u['idrol'], '?')}")


if __name__ == "__main__":
    main()

"""
Regenera todo el sistema salvo el dominio de accidentes (ese viene del CSV).

Tras `reset_total.py` las 79 tablas quedan vacias. Este script las vuelve a
llenar ejecutando los seeds que ya existen **en orden de dependencias**: los
catalogos primero, porque todo lo demas los referencia, y los casos borde al
final, porque necesitan que exista lo normal para contrastar.

**Por que un orquestador y no un seed nuevo.** Cada uno de estos scripts es la
forma canonica de sembrar su dominio y ya conoce sus reglas —ids, centinelas de
Pinot, topics—. Reescribirlos aqui duplicaria esas reglas y las dos copias se
separarian a la primera. Lo que si falta es el ORDEN, que hasta ahora vivia en
la cabeza de quien los ejecutaba.

Algunos corren dentro del contenedor de Django porque importan `config.settings`
(el modulo no resuelve desde el host); esos van marcados con `en_contenedor`.

Uso:
    python database/regenera_todo.py --dry-run
    python database/regenera_todo.py
    python database/regenera_todo.py --desde seed_soporte.py   # reanudar
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# (script, en_contenedor, para que sirve)
PASOS = [
    # --- 1. Catalogos: dimensiones fijas que todo lo demas referencia --------
    ("database/seed_catalogos.py", False, "catalogos de referencia"),
    ("database/seed_severidad.py", False, "Dim_Severidad"),
    ("database/seed_estado_integracion.py", False, "Dim_EstadoIntegracion"),
    ("backend/scripts/seed_catalogos_registro.py", True, "catalogos de registro de accidente"),
    ("backend/scripts/seed_catalogos_soporte.py", True, "catalogos de soporte"),
    ("backend/scripts/seed_catalogos_enriquecimiento.py", True, "catalogos de enriquecimiento"),
    ("backend/scripts/seed_catalogos_red_operativa.py", True, "catalogos de red operativa"),
    ("database/seed_vinculos.py", False, "tablas puente"),

    # --- 2. Comercial: planes y clientes -------------------------------------
    ("backend/scripts/seed_planes_publicos.py", True, "planes publicos"),

    # --- 3. Flota y red operativa --------------------------------------------
    ("database/seed_flota_demo.py", False, "flota de emergencia"),
    ("database/seed_segundo_estado_geografico.py", False, "segundo estado operativo"),

    # --- 4. Soporte -----------------------------------------------------------
    ("database/seed_soporte.py", False, "tickets y SLA"),
    ("database/seed_sla_plan_de_los_tickets.py", False, "SLA del plan real de los tickets"),
    # Necesita un `Dim_Cliente`, y quien lo crea es `seed_soporte.py`: por eso
    # va despues y no junto al resto de la flota.
    ("backend/scripts/seed_demo_proveedor_flota.py", True, "proveedor de flota"),

    # --- 5. Ventas ------------------------------------------------------------
    ("backend/scripts/seed_demo_prospectos.py", True, "prospectos"),
    ("backend/scripts/seed_demo_ventas_tactico.py", True, "pipeline de ventas"),
    ("database/seed_nutricion_ventas.py", False, "interacciones y notificaciones de venta"),

    # --- 6. Partners ----------------------------------------------------------
    ("database/seed_usuario_partner_demo.py", False, "usuario partner"),
    # Recrea sus tablas y aborta si alguna trae filas, asi que va ANTES de
    # `seed_versiones_contrato.py`, que llena `Dim_VersionContratoAPI`.
    ("database/despliega_partners.py", False, "partners y credenciales"),
    ("database/seed_versiones_contrato.py", False, "versiones de contrato de API"),
    ("database/seed_monitoreo_demo.py", False, "monitoreo de consumo de API"),

    # --- 7. Estrategico y casos borde ----------------------------------------
    ("backend/scripts/seed_demo_director_estrategia.py", True, "tablero estrategico"),
    ("database/siembra_roles_tacticos.py", True, "roles y usuarios de la capa tactica"),
    # Va el ultimo a proposito: los casos borde contrastan contra lo normal, asi
    # que necesitan que lo normal ya exista.
    ("database/seed_casos_borde_informes.py", False, "casos borde de informes"),
]


def ejecuta(script: str, en_contenedor: bool) -> tuple[bool, str]:
    if en_contenedor:
        # el contenedor monta el backend en /app
        interno = script.replace("backend/", "")
        cmd = ["docker", "exec", "accidentes-django", "python", interno]
    else:
        cmd = [sys.executable, script]
    p = subprocess.run(cmd, cwd=RAIZ, capture_output=True)
    salida = (p.stdout.decode(errors="replace") + p.stderr.decode(errors="replace")).strip()
    return p.returncode == 0, salida


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--desde", help="reanudar a partir de este script")
    args = ap.parse_args()

    pasos = PASOS
    if args.desde:
        idx = [i for i, (s, _, _) in enumerate(pasos) if s.endswith(args.desde)]
        if not idx:
            print(f"no encuentro '{args.desde}' en la lista")
            return 1
        pasos = pasos[idx[0]:]

    print(f"Pasos: {len(pasos)}")
    if args.dry_run:
        for s, c, d in pasos:
            print(f"   {'[contenedor]' if c else '[host]      '} {s:52} {d}")
        return 0

    fallos = []
    for i, (script, en_contenedor, desc) in enumerate(pasos, 1):
        if not (RAIZ / script).exists():
            print(f"[{i:2}/{len(pasos)}] {desc:42} SALTADO (no existe {script})")
            continue
        t0 = time.time()
        ok, salida = ejecuta(script, en_contenedor)
        marca = "OK  " if ok else "FALLO"
        print(f"[{i:2}/{len(pasos)}] {desc:42} {marca} ({time.time()-t0:,.0f}s)")
        if not ok:
            fallos.append((script, salida[-400:]))
        # Pinot ingiere por Kafka con retardo; el siguiente seed puede depender
        # de lo que acaba de publicar el anterior.
        time.sleep(6)

    if fallos:
        print(f"\n{len(fallos)} fallaron:")
        for s, err in fallos:
            print(f"\n--- {s}\n{err}")
        return 1
    print("\nRegeneracion completa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

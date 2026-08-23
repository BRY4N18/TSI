"""Da de alta los roles tácticos y un usuario por cada uno.

Por qué hace falta
------------------
Los informes tácticos conceden acceso a **ocho autoridades departamentales**
declaradas en `backend/core/auth/roles_tacticos.py`. De esas ocho, en la base
solo existían dos: `DirectorTecnologico` y `DirectorEstrategia`.

Las otras seis —incluido el **Director de Operaciones**, que es la autoridad de
todos los informes compuestos de Emergencias— **no existían como rol ni tenían
ningún usuario**. Los permisos estaban escritos y pasaban sus pruebas porque
esas pruebas acuñan el JWT directamente: comprueban que el permiso decide bien,
no que exista alguien capaz de obtener ese token.

Es una distinción que no falla por ninguna parte. La API responde `403` a quien
no tiene el rol, y a un rol que no existe le responde exactamente igual, así que
«nadie puede entrar» y «el permiso funciona» se ven idénticos desde fuera.

Qué hace
--------
1. Crea los roles tácticos que falten, **sin tocar los que ya están**.
2. Crea un usuario por rol, con contraseña conocida, para poder **entrar por el
   login de verdad** y no solo por un token fabricado.
3. Asigna cada rol a su usuario.

Es **idempotente**: repetirlo no duplica nada. Se apoya en los repositorios del
backend, que publican por Kafka — no escribe en Pinot directamente, porque el
único escritor del sistema operativo es el productor.

Uso
---
    docker exec accidentes-django bash -lc "cd /app && python /app/siembra.py"

⚠️ **Las contraseñas de este fichero son de entorno de pruebas.** No se use en
un despliegue real sin cambiarlas.
"""

from __future__ import annotations

import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.cuentas_clientes.services.user_management_service import (  # noqa: E402
    UserManagementError,
    UserManagementService,
)
from core.auth.roles_tacticos import (  # noqa: E402
    ROL_DIRECTOR_CUENTAS,
    ROL_DIRECTOR_DATOS,
    ROL_DIRECTOR_ESTRATEGIA,
    ROL_DIRECTOR_EXPANSION,
    ROL_DIRECTOR_FINANCIERO,
    ROL_DIRECTOR_MARKETING,
    ROL_DIRECTOR_OPERACIONES,
    ROL_DIRECTOR_TECNOLOGICO,
    ROL_GERENTE_EXITO_CLIENTE,
)

#: Rol → (descripción, correo del usuario que lo llevará, nombre).
#:
#: Un usuario **por rol** y no uno con los ocho: la autoridad de estos informes
#: está repartida —en Red Operativa, Expansión y Tecnológico no ven lo mismo— y
#: un usuario con todos los roles haría imposible comprobar ese reparto entrando
#: de verdad. Con uno por rol, la separación se puede probar por login.
TACTICOS = {
    ROL_DIRECTOR_OPERACIONES: (
        "Autoridad tactica de Emergencias: informes de registro, despacho, "
        "seguimiento, evidencia y cierre",
        "director.operaciones@demo.tsi.com",
        ("Olivia", "Ortega"),
    ),
    ROL_DIRECTOR_EXPANSION: (
        "Autoridad tactica de Red Operativa, materia de crecimiento y flota",
        "director.expansion@demo.tsi.com",
        ("Elena", "Prado"),
    ),
    ROL_DIRECTOR_MARKETING: (
        "Autoridad tactica de Ventas y CRM",
        "director.marketing@demo.tsi.com",
        ("Mateo", "Rivas"),
    ),
    ROL_DIRECTOR_FINANCIERO: (
        "Autoridad tactica de Suscripciones, materia de resultado economico",
        "director.financiero@demo.tsi.com",
        ("Fernanda", "Cano"),
    ),
    ROL_GERENTE_EXITO_CLIENTE: (
        "Autoridad tactica de Soporte al Cliente",
        "gerente.exito@demo.tsi.com",
        ("Gabriel", "Ledesma"),
    ),
    ROL_DIRECTOR_CUENTAS: (
        "Autoridad tactica de Cuentas y Clientes: ciclo de vida e incorporacion",
        "director.cuentas@demo.tsi.com",
        ("Andrea", "Salas"),
    ),
    ROL_DIRECTOR_DATOS: (
        "Autoridad tactica de Analitica e Inteligencia",
        "director.datos@demo.tsi.com",
        ("Daniela", "Nunez"),
    ),
    # Estos dos ya existen como rol. Se listan igual para darles usuario propio:
    # el rol sin nadie que lo lleve no se puede probar por login.
    ROL_DIRECTOR_TECNOLOGICO: (
        "Autoridad tactica de Partners y API, validacion de region y accesos tecnicos",
        "director.tecnologico@demo.tsi.com",
        ("Tomas", "Herrera"),
    ),
    ROL_DIRECTOR_ESTRATEGIA: (
        "Autoridad tactica de Suscripciones, materia de catalogo y precios",
        "director.estrategia@demo.tsi.com",
        ("Sofia", "Alarcon"),
    ),
}

#: ⚠️ Entorno de pruebas. Ver el docstring.
CLAVE = "Tactico2026!"


def main() -> int:
    servicio = UserManagementService()
    roles_repo = servicio.role_repo
    admin = ["Administrador"]

    creados_rol, creados_usuario, ya_estaban = [], [], []

    for rol, (descripcion, gmail, (nombres, apellidos)) in TACTICOS.items():
        existente = roles_repo.find_role_by_name(rol)
        if existente:
            idrol = int(existente["idrol"])
        else:
            idrol = int(roles_repo.create_role({"rol": rol, "descripcion": descripcion})["idrol"])
            creados_rol.append(rol)

        usuario = servicio.user_repo.find_by_gmail(gmail)
        if usuario:
            # El usuario ya existe: solo se asegura el vinculo con su rol, que es
            # idempotente en el repositorio.
            roles_repo.assign_role_to_user(int(usuario["idusuario"]), idrol)
            ya_estaban.append(f"{rol} -> {gmail}")
            continue

        try:
            nuevo = servicio.create_user(
                {
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "gmail": gmail,
                    "password": CLAVE,
                    "role_ids": [idrol],
                },
                admin_roles=admin,
            )
        except UserManagementError as exc:
            print(f"  FALLA {rol}: {exc}")
            continue
        creados_usuario.append(f"{rol} -> {gmail} (id {nuevo['idusuario']})")

    print("\nRoles creados     :", creados_rol or "ninguno (ya estaban todos)")
    print("Usuarios creados  :")
    for linea in creados_usuario or ["  ninguno"]:
        print("   ", linea)
    if ya_estaban:
        print("Ya existian       :")
        for linea in ya_estaban:
            print("   ", linea)
    print(f"\nClave de todos    : {CLAVE}   (entorno de pruebas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Recorre el sistema por la API real, en escenarios felices y de error.

**Por que por la API y no publicando en Kafka.** Sembrar `Fact_Despacho` a mano
produce filas que ningun flujo genero: quedan sin su `Fact_NotificacionDespacho`,
sin su historial de estado y sin haber pasado por las reglas de negocio. Aqui se
llama a los endpoints de verdad, asi que cada fila nace del mismo camino que
recorreria un usuario — y de paso se comprueba que ese camino funciona con los
2 millones de accidentes cargados.

Los casos de ERROR importan tanto como los felices: son los que dejan la
interfaz con algo que mostrar en sus estados no-felices (rechazos, escalados,
403 por rol, validaciones), que de otro modo no se ven nunca.

Uso:
    python database/recorre_escenarios.py
    python database/recorre_escenarios.py --api http://localhost:8000
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request

API = "http://localhost:8000/api/v1"
PASSWORD = "password123"

# Focos donde vive la flota tras `reubica_flota_ee_uu.py`.
MIAMI = (25.8895, -80.2002)
ORLANDO = (28.4471, -81.4013)
# California quedo "Despublicada" y Texas "En_Alerta": registrar ahi da
# "fuera de cobertura" de verdad, sin inventar coordenadas imposibles.
CALIFORNIA = (34.0357, -118.3113)

resultados: list[tuple[str, str, str]] = []


def registra(escenario: str, esperado: str, obtenido: str) -> None:
    ok = "OK " if esperado == obtenido else "REVISAR"
    resultados.append((ok, escenario, f"esperado {esperado}, obtenido {obtenido}"))
    print(f"  [{ok:7}] {escenario:52} {obtenido}")


def peticion(metodo: str, ruta: str, token: str | None = None, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(f"{API}{ruta}", data=datos, method=metodo)
    if datos:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:  # noqa: BLE001
            return e.code, {}
    except Exception as e:  # noqa: BLE001
        return 0, {"error": str(e)}


def entra(gmail: str) -> str | None:
    code, d = peticion("POST", "/auth/login", cuerpo={"gmail": gmail, "password": PASSWORD})
    if code != 200:
        print(f"  !! no pude entrar como {gmail} ({code})")
        return None
    return d["data"]["accessToken"]


def calle_del_condado(idcondado: int) -> int | None:
    """Una calle real del condado donde vive una unidad.

    No se usa el endpoint de calles porque exige ciudad, ni la geocodificacion
    inversa porque el proveedor no cubre estas coordenadas. La consulta directa
    a Pinot es la unica que garantiza una calle del condado correcto — y que sea
    del condado importa: si no, el despacho no encuentra unidad cercana y el
    camino feliz se convierte en un escalado.
    """
    req = urllib.request.Request(
        "http://localhost:8099/query/sql",
        data=json.dumps({"sql":
            "SELECT c.idcalle FROM Dim_Calle c WHERE c.idciudad IN "
            f"(SELECT idciudad FROM Dim_Ciudad WHERE idcondado = {idcondado}) LIMIT 1"}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            filas = json.load(r).get("resultTable", {}).get("rows") or []
        if filas:
            return int(filas[0][0])
    except Exception:  # noqa: BLE001
        pass
    # sin subconsulta: se resuelve en dos pasos
    for sql in (f"SELECT idciudad FROM Dim_Ciudad WHERE idcondado = {idcondado} LIMIT 1",):
        req = urllib.request.Request("http://localhost:8099/query/sql",
                                     data=json.dumps({"sql": sql}).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            filas = json.load(r).get("resultTable", {}).get("rows") or []
        if not filas:
            return None
        idciudad = int(filas[0][0])
        req = urllib.request.Request("http://localhost:8099/query/sql",
                                     data=json.dumps({"sql":
                                         f"SELECT idcalle FROM Dim_Calle WHERE idciudad = {idciudad} LIMIT 1"}).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            filas = json.load(r).get("resultTable", {}).get("rows") or []
        return int(filas[0][0]) if filas else None
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=API)
    args = ap.parse_args()
    globals()["API"] = args.api.rstrip("/") + "/api/v1" if not args.api.endswith("/v1") else args.api

    print("Entrando con cada rol")
    operador = entra("sofia.castro.operador@demo.tsi.com")
    unidad = entra("marco.silva.unidad@demo.tsi.com")
    soporte = entra("lucia.vera.soporte@demo.tsi.com")
    admin = entra("carlos.mendoza.admin@demo.tsi.com")
    cliente = entra("ana.torres.cliente@demo.tsi.com")
    if not all([operador, unidad, soporte, admin]):
        return 1

    ahora = int(time.time() * 1000)
    # El detector de duplicados mira sitio + ventana temporal, asi que sin un
    # desplazamiento propio la segunda corrida del script se detecta a si misma
    # como duplicada de la primera y el camino feliz deja de serlo.
    jitter = (ahora % 900) / 10000.0
    # 29 es el condado de Miami-Dade, donde quedo la unidad 1
    idcalle = calle_del_condado(29)
    print(f"\nCalle de referencia: {idcalle}")

    # ================= ERRORES DE VALIDACION AL REGISTRAR =================
    print("\n--- Registro de accidente: casos de error ---")
    code, _ = peticion("POST", "/accidentes", operador, {})
    registra("registro sin GPS", "400", str(code))

    code, _ = peticion("POST", "/accidentes", operador,
                       {"latitudinicio": 999, "longitudinicio": 999,
                        "descripcion": "x", "idcalle": idcalle})
    registra("registro con GPS fuera de rango", "400", str(code))

    code, _ = peticion("POST", "/accidentes", operador,
                       {"latitudinicio": MIAMI[0], "longitudinicio": MIAMI[1],
                        "descripcion": "x", "idcalle": idcalle,
                        "fechahoraaccidente": ahora + 86_400_000})
    registra("registro con fecha futura", "400", str(code))

    code, _ = peticion("POST", "/accidentes", operador,
                       {"latitudinicio": MIAMI[0], "longitudinicio": MIAMI[1]})
    registra("registro sin descripcion ni calle", "400", str(code))

    # Regresion: omitir la fecha reventaba con TypeError y devolvia un 500.
    code, _ = peticion("POST", "/accidentes", operador,
                       {"latitudinicio": MIAMI[0], "longitudinicio": MIAMI[1],
                        "descripcion": "Sin fecha", "idcalle": idcalle})
    registra("registro sin fecha del accidente", "400", str(code))

    code, _ = peticion("POST", "/accidentes", operador,
                       {"latitudinicio": MIAMI[0], "longitudinicio": MIAMI[1],
                        "descripcion": "Retrospectivo sin justificar", "idcalle": idcalle,
                        "fechahoraaccidente": ahora - 40 * 86_400_000})
    # 422 y no 400: la peticion esta bien formada, lo que falla es la regla
    registra("registro retrospectivo sin justificacion", "422", str(code))

    # ================= PERMISOS =================
    print("\n--- Permisos ---")
    code, _ = peticion("GET", "/accidentes?limit=1")
    registra("listar accidentes sin token", "401", str(code))

    code, _ = peticion("POST", "/accidentes", cliente or "",
                       {"latitudinicio": MIAMI[0], "longitudinicio": MIAMI[1],
                        "descripcion": "y", "idcalle": idcalle})
    registra("cliente intenta registrar accidente", "403", str(code))

    code, _ = peticion("GET", "/soporte/sla-config", unidad)
    registra("unidad accede a configuracion de SLA", "403", str(code))

    # ================= CAMINO FELIZ: REGISTRO Y DESPACHO =================
    print("\n--- Registro y despacho: camino feliz ---")
    creados = []
    for i, (lat, lon, sev, desc) in enumerate([
        (MIAMI[0] + jitter, MIAMI[1] + jitter, 4, "Colision multiple con victimas en I-95"),
        (MIAMI[0] + jitter + 0.01, MIAMI[1] + jitter, 3, "Volcadura en carril central"),
        (ORLANDO[0] + jitter, ORLANDO[1] + jitter, 2, "Alcance entre dos vehiculos"),
        (ORLANDO[0] + jitter + 0.02, ORLANDO[1] + jitter, 1, "Roce lateral sin heridos"),
    ]):
        code, d = peticion("POST", "/accidentes", operador, {
            "latitudinicio": lat, "longitudinicio": lon,
            "idseveridad": sev, "descripcion": desc, "idcalle": idcalle,
            "numvehiculos": 2, "numheridos": 1 if sev >= 3 else 0,
            "fechahoraaccidente": ahora - (i + 1) * 60_000,
        })
        registra(f"registrar accidente severidad {sev}", "201", str(code))
        idacc = ((d.get("data") or {}) or {}).get("idaccidente")
        if idacc:
            creados.append(idacc)

    # Duplicado deliberado: mismo sitio y misma ventana temporal que el anterior.
    # Es el escenario que deja la pantalla de fusion con algo que mostrar.
    if creados:
        code, _ = peticion("POST", "/accidentes", operador, {
            "latitudinicio": ORLANDO[0] + jitter, "longitudinicio": ORLANDO[1] + jitter,
            "idseveridad": 2, "descripcion": "Mismo suceso, reportado dos veces",
            "idcalle": idcalle, "fechahoraaccidente": ahora - 3 * 60_000,
        })
        registra("registrar un duplicado del mismo suceso", "409", str(code))

    print(f"\n  accidentes creados: {creados}")
    if creados:
        print("  esperando al worker de despacho (~20s)")
        time.sleep(20)
        for idacc in creados[:2]:
            code, d = peticion("GET", f"/accidentes/{idacc}/despacho", operador)
            registra(f"despacho de {idacc[:22]}", "200", str(code))

    # ================= ESCALADO: SIN UNIDADES EN ZONA =================
    print("\n--- Escalado: accidente lejos de toda unidad ---")
    code, d = peticion("POST", "/accidentes", operador, {
        "latitudinicio": CALIFORNIA[0], "longitudinicio": CALIFORNIA[1],
        "idseveridad": 3, "descripcion": "Sin cobertura en la zona",
        "idcalle": calle_del_condado(18),  # Los Angeles: region Despublicada
        "fechahoraaccidente": ahora - 30_000,
    })
    registra("accidente en region despublicada", "409", str(code))

    # ================= UNIDAD: DISPONIBILIDAD Y DESPACHOS =================
    print("\n--- Unidad de emergencia ---")
    code, _ = peticion("GET", "/mi-unidad-emergencia/disponibilidad", unidad)
    registra("consultar mi disponibilidad", "200", str(code))

    for estado in ("Activa", "Fuera de servicio", "Activa"):
        code, _ = peticion("POST", "/mi-unidad-emergencia/disponibilidad", unidad,
                           {"estadonuevo": estado})
        # 201 y no 200: cada declaracion crea un registro de historial
        registra(f"declarar disponibilidad '{estado}'", "201", str(code))

    code, _ = peticion("POST", "/mi-unidad-emergencia/disponibilidad", unidad,
                       {"estadonuevo": "EstadoInventado"})
    registra("declarar un estado inexistente", "422", str(code))

    code, d = peticion("GET", "/mi-despacho/pendientes", unidad)
    registra("consultar despachos pendientes", "200", str(code))
    pendientes = (d.get("data") or []) if isinstance(d.get("data"), list) else []
    print(f"  pendientes: {len(pendientes)}")

    # aceptar uno y rechazar otro, para que existan las dos ramas
    for i, p in enumerate(pendientes[:2]):
        idn = p.get("idnotificaciondespacho")
        if not idn:
            continue
        if i == 0:
            code, _ = peticion("PATCH", f"/mi-despacho/{idn}", unidad, {"accion": "aceptar"})
            registra("aceptar un despacho", "200", str(code))
        else:
            code, _ = peticion("PATCH", f"/mi-despacho/{idn}", unidad,
                               {"accion": "rechazar", "motivo": "Unidad en mantenimiento"})
            registra("rechazar un despacho", "200", str(code))

    # ================= SOPORTE =================
    print("\n--- Soporte ---")
    code, d = peticion("GET", "/soporte/tickets", soporte)
    registra("listar tickets", "200", str(code))
    tickets = (d.get("data") or []) if isinstance(d.get("data"), list) else []
    print(f"  tickets: {len(tickets)}")

    if tickets:
        tid = tickets[0].get("id_reclamo")
        code, _ = peticion("POST", f"/soporte/tickets/{tid}/tomar", soporte, {})
        registra(f"tomar ticket {tid}", "200", str(code))
        code, _ = peticion("POST", f"/soporte/tickets/{tid}/tomar", soporte, {})
        registra("tomar un ticket ya tomado", "409", str(code))
        code, _ = peticion("POST", f"/soporte/tickets/{tid}/comentarios", soporte,
                           {"comentario": "Revisado por el agente"})
        registra("comentar un ticket", "201", str(code))
        code, _ = peticion("POST", f"/soporte/tickets/{tid}/resolver", soporte,
                           {"solucion": "Resuelto en primera linea"})
        registra("resolver un ticket", "200", str(code))
        code, _ = peticion("POST", f"/soporte/tickets/{tid}/reabrir", soporte,
                           {"motivo": "El cliente reporta reincidencia"})
        registra("reabrir un ticket resuelto", "200", str(code))
        if len(tickets) > 1:
            t2 = tickets[1].get("id_reclamo")
            code, _ = peticion("POST", f"/soporte/tickets/{t2}/escalar", soporte,
                               {"motivo": "Requiere segundo nivel"})
            registra("escalar un ticket", "200", str(code))

    code, _ = peticion("POST", "/soporte/tickets/999999/tomar", soporte, {})
    registra("tomar un ticket inexistente", "404", str(code))

    # ================= VENTAS =================
    print("\n--- Ventas ---")
    code, d = peticion("GET", "/ventas-crm/prospectos", admin)
    registra("listar prospectos", "200", str(code))

    code, _ = peticion("POST", "/ventas-crm/prospectos", admin, {})
    registra("crear prospecto sin datos", "400", str(code))

    # ================= SUSCRIPCIONES =================
    print("\n--- Suscripciones ---")
    for ruta, esperado in [("/suscripciones/planes", "200"),
                           ("/suscripciones/severidades", "200"),
                           # 403 y no 404: el endpoint esta cerrado por rol antes de mirar el id
                           ("/suscripciones/planes/999999", "403")]:
        code, _ = peticion("GET", ruta, admin)
        registra(f"GET {ruta}", esperado, str(code))

    # ================= RESUMEN =================
    print("\n" + "=" * 70)
    ok = sum(1 for r in resultados if r[0] == "OK ")
    print(f"Escenarios recorridos: {len(resultados)}   como se esperaba: {ok}   a revisar: {len(resultados)-ok}")
    for marca, esc, det in resultados:
        if marca != "OK ":
            print(f"   REVISAR  {esc:52} {det}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

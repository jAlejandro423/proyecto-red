"""Lectura JSON → modelo."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.modelo import Caso, Nodo, Utilidad, UtilidadLog, UtilidadTabla
from src.validacion import ErrorValidacion, como_entero, validar


@dataclass(frozen=True)
class CasoLeido:
    """Resultado de leer un archivo: `caso` es None si hay errores.

    `parametros` trae N, k, B y universo, con None en los que no se pudieron leer.
    """

    nombre: str
    caso: Caso | None
    errores: list[ErrorValidacion]
    parametros: dict = field(default_factory=dict)


def leer_caso(ruta) -> CasoLeido:
    """Lee y valida un archivo de caso sin lanzar excepciones por su contenido."""
    ruta = Path(ruta)
    try:
        # utf-8-sig acepta UTF-8 con o sin BOM. ValueError cubre codificación y JSON inválidos.
        datos = json.loads(ruta.read_text(encoding="utf-8-sig"))
    except (ValueError, RecursionError, OSError) as error:
        return CasoLeido(ruta.stem, None, [ErrorValidacion("E01", f"JSON ilegible: {error}")])

    nombre = _nombre(datos, ruta.stem)
    parametros = _parametros(datos)
    errores = validar(datos)
    if errores:
        return CasoLeido(nombre, None, errores, parametros)
    try:
        return CasoLeido(nombre, _construir_caso(datos, nombre), [], parametros)
    except (OverflowError, MemoryError):
        detalle = f"universo = {datos['universo']} no cabe en la memoria disponible"
        return CasoLeido(nombre, None, [ErrorValidacion("E03", detalle)], parametros)


def _nombre(datos, nombre_archivo: str) -> str:
    nombre = datos.get("nombre") if isinstance(datos, dict) else None
    return nombre if isinstance(nombre, str) and nombre.strip() else nombre_archivo


def _parametros(datos) -> dict:
    if not isinstance(datos, dict):
        return {}
    return {clave: como_entero(datos.get(clave)) for clave in ("N", "k", "B", "universo")}


def _construir_caso(datos: dict, nombre: str) -> Caso:
    universo = como_entero(datos["universo"])
    pesos = datos["pesos_universo"] if "pesos_universo" in datos else [1.0] * universo
    return Caso(
        nombre=nombre,
        N=como_entero(datos["N"]),
        k=como_entero(datos["k"]),
        B=como_entero(datos["B"]),
        universo=universo,
        pesos_universo=tuple(float(peso) for peso in pesos),
        nodos=tuple(_construir_nodo(nodo) for nodo in datos["nodos"]),
    )


def _construir_nodo(nodo: dict) -> Nodo:
    id_nodo = nodo["id"]
    return Nodo(
        id=id_nodo if isinstance(id_nodo, str) else como_entero(id_nodo),
        cubre=tuple(como_entero(elemento) for elemento in nodo["cubre"]),
        utilidad=_construir_utilidad(nodo["utilidad"]),
    )


def _construir_utilidad(utilidad: dict) -> Utilidad:
    if utilidad["tipo"] == "tabla":
        return UtilidadTabla(tuple(float(valor) for valor in utilidad["valores"]))
    return UtilidadLog(float(utilidad["a"]), float(utilidad["b"]))

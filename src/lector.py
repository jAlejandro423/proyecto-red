"""Lectura JSON → modelo."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.conjunta import Influencia
from src.modelo import Caso, Nodo, Utilidad, UtilidadLog, UtilidadTabla
from src.validacion import ErrorValidacion, como_entero, es_formato_docente, validar

NOTA_NO_USADOS = "variantes, entregas posteriores"


@dataclass(frozen=True)
class CasoLeido:
    """Resultado de leer un archivo: `caso` es None si hay errores.

    `parametros` trae N, k, B y universo, con None en los que no se pudieron leer
    (en el formato de la docente, universo siempre es None). `formato` es "propio"
    o "docente"; `campos_no_usados` solo se llena en un caso válido de la docente.
    """

    nombre: str
    caso: Caso | None
    errores: list[ErrorValidacion]
    parametros: dict = field(default_factory=dict)
    formato: str = "propio"
    campos_no_usados: dict | None = None


def leer_caso(ruta) -> CasoLeido:
    """Lee y valida un archivo de caso sin lanzar excepciones por su contenido."""
    ruta = Path(ruta)
    try:
        # utf-8-sig acepta UTF-8 con o sin BOM. ValueError cubre codificación y JSON inválidos.
        datos = json.loads(ruta.read_text(encoding="utf-8-sig"))
    except (ValueError, RecursionError, OSError) as error:
        return CasoLeido(ruta.stem, None, [ErrorValidacion("E01", f"JSON ilegible: {error}")])

    nombre = _nombre(datos, ruta.stem)
    errores = validar(datos)
    if es_formato_docente(datos):
        parametros = _parametros_docente(datos)
        if errores:
            return CasoLeido(nombre, None, errores, parametros, "docente")
        caso = _construir_caso_docente(datos, nombre)
        return CasoLeido(nombre, caso, [], parametros, "docente", _campos_no_usados(datos))

    parametros = _parametros(datos)
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


# --- Formato de la docente (sección 2.7) -----------------------------------------


def _parametros_docente(datos: dict) -> dict:
    parametros = datos.get("parametros")
    if not isinstance(parametros, dict):
        parametros = {}
    return {
        "N": como_entero(parametros.get("numero_nodos")),
        "k": como_entero(parametros.get("cupo_participantes_por_ronda_k")),
        "B": como_entero(parametros.get("presupuesto_ruido_por_ronda_B")),
        "universo": None,
    }


def _construir_caso_docente(datos: dict, nombre: str) -> Caso:
    parametros = _parametros_docente(datos)
    nodos = datos["nodos"]
    posicion = {_texto(nodo["id"]): i for i, nodo in enumerate(nodos)}
    coeficientes = [float(nodo["coeficiente_utilidad"]) for nodo in nodos]
    aristas = [
        (posicion[_texto(arista["u"])], posicion[_texto(arista["v"])], float(arista["peso_influencia"]))
        for arista in datos["grafo"]
    ]
    return Caso(
        nombre=nombre,
        N=parametros["N"],
        k=parametros["k"],
        B=parametros["B"],
        universo=0,
        pesos_universo=(),
        nodos=tuple(
            Nodo(
                id=nodo["id"] if isinstance(nodo["id"], str) else como_entero(nodo["id"]),
                cubre=(),
                utilidad=UtilidadLog(c, 1.0, tope=como_entero(nodo["presupuesto_total_nodo"])),
            )
            for nodo, c in zip(nodos, coeficientes)
        ),
        conjunta=Influencia.desde_aristas(coeficientes, aristas),
    )


def _texto(valor) -> str:
    return valor if isinstance(valor, str) else str(como_entero(valor))


def _campos_no_usados(datos: dict) -> dict:
    """Copia tal cual los campos de las variantes que trae la entrada; omite los ausentes."""
    no_usados: dict = {"nota": NOTA_NO_USADOS}
    parametros = datos["parametros"]
    for campo in ("numero_rondas", "presupuesto_costos_participacion_por_ronda"):
        if campo in parametros:
            no_usados[campo] = parametros[campo]
    costos = {_texto(nodo["id"]): nodo["costo_participacion"] for nodo in datos["nodos"] if "costo_participacion" in nodo}
    if costos:
        no_usados["costo_participacion"] = costos
    return no_usados

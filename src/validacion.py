"""E01–E10 (formato propio) y E11–E17 (formato de la docente), devuelve lista de errores."""

import math
from dataclasses import dataclass

TOLERANCIA = 1e-9
TIPOS_UTILIDAD = ("tabla", "log")


@dataclass(frozen=True)
class ErrorValidacion:
    codigo: str
    detalle: str


def es_numero(valor) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def es_finito(valor) -> bool:
    try:
        return math.isfinite(valor)
    except OverflowError:  # entero demasiado grande para un real
        return False


def como_entero(valor) -> int | None:
    """Devuelve el entero que representa `valor`, o None si no representa ninguno."""
    if not es_numero(valor):
        return None
    if isinstance(valor, int):
        return valor
    return int(valor) if math.isfinite(valor) and valor.is_integer() else None


def es_formato_docente(datos) -> bool:
    """El formato de la docente se reconoce por `parametros` o `grafo` en la raíz (sección 2)."""
    return isinstance(datos, dict) and ("parametros" in datos or "grafo" in datos)


def validar(datos) -> list[ErrorValidacion]:
    """Comprueba un caso decodificado, en cualquiera de los dos formatos, y devuelve todos sus errores."""
    if not isinstance(datos, dict):
        return [ErrorValidacion("E01", "la raíz del JSON debe ser un objeto")]
    if es_formato_docente(datos):
        return _validar_docente(datos)

    errores: list[ErrorValidacion] = []
    if "nombre" in datos and not isinstance(datos["nombre"], str):
        errores.append(ErrorValidacion("E02", "nombre debe ser un string"))

    N = _campo_entero(datos, "N", errores)
    k = _campo_entero(datos, "k", errores)
    B = _campo_entero(datos, "B", errores)
    universo = _campo_entero(datos, "universo", errores)

    # Un campo fuera de rango pasa a None para omitir lo que depende de él.
    if N is not None and N < 1:
        errores.append(ErrorValidacion("E03", f"N debe ser ≥ 1 (vale {N})"))
        N = None
    if k is not None and (k < 1 or (N is not None and k >= N)):
        errores.append(ErrorValidacion("E03", f"k debe cumplir 1 ≤ k < N (k = {k}, N = {N})"))
    if B is not None and B < 0:
        errores.append(ErrorValidacion("E03", f"B debe ser ≥ 0 (vale {B})"))
        B = None
    if universo is not None and universo < 0:
        errores.append(ErrorValidacion("E03", f"universo debe ser ≥ 0 (vale {universo})"))
        universo = None

    _validar_pesos(datos, universo, errores)
    _validar_nodos(datos, N, B, universo, errores)
    return errores


def _campo_entero(datos, campo, errores) -> int | None:
    if campo not in datos:
        errores.append(ErrorValidacion("E01", f"falta el campo obligatorio {campo}"))
        return None
    return _entero(datos[campo], campo, errores)


def _entero(valor, ubicacion, errores) -> int | None:
    entero = como_entero(valor)
    if entero is None:
        if es_numero(valor) and not es_finito(valor):
            errores.append(ErrorValidacion("E09", f"{ubicacion} no es un número finito"))
        else:
            errores.append(ErrorValidacion("E02", f"{ubicacion} debe ser un entero"))
    return entero


def _real(valor, ubicacion, errores) -> float | None:
    if not es_numero(valor):
        errores.append(ErrorValidacion("E02", f"{ubicacion} debe ser un número"))
        return None
    if not es_finito(valor):
        errores.append(ErrorValidacion("E09", f"{ubicacion} no es un número finito"))
        return None
    return float(valor)


def _validar_pesos(datos, universo, errores) -> None:
    if "pesos_universo" not in datos:
        return
    pesos = datos["pesos_universo"]
    if not isinstance(pesos, list):
        errores.append(ErrorValidacion("E02", "pesos_universo debe ser una lista"))
        return
    if universo is not None and len(pesos) != universo:
        errores.append(
            ErrorValidacion("E06", f"pesos_universo tiene {len(pesos)} valores y |U| = {universo}")
        )
    for i, peso in enumerate(pesos):
        real = _real(peso, f"pesos_universo[{i}]", errores)
        if real is not None and real < 0:
            errores.append(ErrorValidacion("E06", f"pesos_universo[{i}] es negativo ({real})"))


def _validar_nodos(datos, N, B, universo, errores) -> None:
    if "nodos" not in datos:
        errores.append(ErrorValidacion("E01", "falta el campo obligatorio nodos"))
        return
    nodos = datos["nodos"]
    if not isinstance(nodos, list):
        errores.append(ErrorValidacion("E02", "nodos debe ser una lista"))
        return
    if N is not None and len(nodos) != N:
        errores.append(ErrorValidacion("E04", f"nodos tiene {len(nodos)} elementos y N = {N}"))

    posiciones_por_id: dict[str, list[int]] = {}
    for i, nodo in enumerate(nodos):
        ubicacion = f"nodos[{i}]"
        if not isinstance(nodo, dict):
            errores.append(ErrorValidacion("E02", f"{ubicacion} debe ser un objeto"))
            continue
        id_nodo = _validar_id(nodo, ubicacion, errores)
        if id_nodo is not None:
            posiciones_por_id.setdefault(str(id_nodo), []).append(i)
        _validar_cubre(nodo, ubicacion, universo, errores)
        _validar_utilidad(nodo, ubicacion, B, errores)

    for texto, posiciones in posiciones_por_id.items():
        if len(posiciones) > 1:
            errores.append(
                ErrorValidacion("E04", f"id {texto!r} repetido en las posiciones {posiciones}")
            )


def _validar_id(nodo, ubicacion, errores) -> int | str | None:
    if "id" not in nodo:
        errores.append(ErrorValidacion("E01", f"{ubicacion}: falta el campo obligatorio id"))
        return None
    valor = nodo["id"]
    if isinstance(valor, str):
        return valor
    if es_numero(valor) and not es_finito(valor) and not isinstance(valor, int):
        errores.append(ErrorValidacion("E09", f"{ubicacion}.id no es un número finito"))
        return None
    entero = como_entero(valor)
    if entero is None:
        errores.append(ErrorValidacion("E02", f"{ubicacion}.id debe ser un entero o un string"))
    return entero


def _validar_cubre(nodo, ubicacion, universo, errores) -> None:
    if "cubre" not in nodo:
        errores.append(ErrorValidacion("E01", f"{ubicacion}: falta el campo obligatorio cubre"))
        return
    cubre = nodo["cubre"]
    if not isinstance(cubre, list):
        errores.append(ErrorValidacion("E02", f"{ubicacion}.cubre debe ser una lista"))
        return

    vistos: set[int] = set()
    fuera_de_rango: list[int] = []
    repetidos: list[int] = []
    for j, valor in enumerate(cubre):
        elemento = _entero(valor, f"{ubicacion}.cubre[{j}]", errores)
        if elemento is None:
            continue
        if universo is not None and not 0 <= elemento < universo:
            fuera_de_rango.append(elemento)
        if elemento in vistos:
            repetidos.append(elemento)
        vistos.add(elemento)

    if fuera_de_rango:
        errores.append(
            ErrorValidacion(
                "E05", f"{ubicacion}.cubre tiene valores fuera de [0, {universo}): {fuera_de_rango}"
            )
        )
    if repetidos:
        errores.append(ErrorValidacion("E05", f"{ubicacion}.cubre repite valores: {repetidos}"))


def _validar_utilidad(nodo, ubicacion, B, errores) -> None:
    if "utilidad" not in nodo:
        errores.append(ErrorValidacion("E01", f"{ubicacion}: falta el campo obligatorio utilidad"))
        return
    utilidad = nodo["utilidad"]
    ubicacion = f"{ubicacion}.utilidad"
    if not isinstance(utilidad, dict):
        errores.append(ErrorValidacion("E02", f"{ubicacion} debe ser un objeto"))
        return
    if "tipo" not in utilidad:
        errores.append(ErrorValidacion("E01", f"{ubicacion}: falta el campo obligatorio tipo"))
        return
    tipo = utilidad["tipo"]
    if tipo not in TIPOS_UTILIDAD:
        errores.append(ErrorValidacion("E10", f"{ubicacion}: tipo desconocido {tipo!r}"))
    elif tipo == "tabla":
        _validar_tabla(utilidad, ubicacion, errores)
    else:
        _validar_log(utilidad, ubicacion, B, errores)


def _validar_tabla(utilidad, ubicacion, errores) -> None:
    if "valores" not in utilidad:
        errores.append(ErrorValidacion("E01", f"{ubicacion}: falta el campo obligatorio valores"))
        return
    valores = utilidad["valores"]
    if not isinstance(valores, list) or not valores:
        errores.append(ErrorValidacion("E02", f"{ubicacion}.valores debe ser una lista no vacía"))
        return
    reales = [_real(v, f"{ubicacion}.valores[{j}]", errores) for j, v in enumerate(valores)]
    if None in reales:
        return

    ganancias = [siguiente - actual for actual, siguiente in zip(reales, reales[1:])]
    decrecientes = [x for x, g in enumerate(ganancias) if g < -TOLERANCIA]
    no_concavos = [
        x + 1
        for x, (g, g_siguiente) in enumerate(zip(ganancias, ganancias[1:]))
        if g_siguiente > g + TOLERANCIA
    ]
    # Se informa un error por nodo y condición: una tabla larga no debe inundar la salida.
    if decrecientes:
        x = decrecientes[0]
        errores.append(
            ErrorValidacion(
                "E07",
                f"{ubicacion} no es creciente: g({x}) = {ganancias[x]} < 0 "
                f"({len(decrecientes)} en total)",
            )
        )
    if no_concavos:
        x = no_concavos[0]
        errores.append(
            ErrorValidacion(
                "E08",
                f"{ubicacion} no es cóncava: g({x}) = {ganancias[x]} > "
                f"g({x - 1}) = {ganancias[x - 1]} ({len(no_concavos)} en total)",
            )
        )


def _validar_log(utilidad, ubicacion, B, errores) -> None:
    faltantes = [campo for campo in ("a", "b") if campo not in utilidad]
    for campo in faltantes:
        errores.append(ErrorValidacion("E01", f"{ubicacion}: falta el campo obligatorio {campo}"))

    a = _real(utilidad["a"], f"{ubicacion}.a", errores) if "a" not in faltantes else None
    b = _real(utilidad["b"], f"{ubicacion}.b", errores) if "b" not in faltantes else None
    if a is not None and a < 0:
        errores.append(ErrorValidacion("E09", f"{ubicacion}.a debe ser ≥ 0 (vale {a})"))
        a = None
    if b is not None and b <= 0:
        errores.append(ErrorValidacion("E09", f"{ubicacion}.b debe ser > 0 (vale {b})"))
        b = None
    if a is not None and b is not None and B is not None and not _log_evaluable(a, b, B):
        errores.append(ErrorValidacion("E09", f"{ubicacion} desborda al evaluar u(B + 1)"))


def _log_evaluable(a, b, B) -> bool:
    try:
        return math.isfinite(a * math.log1p(b * (B + 1)))
    except OverflowError:
        return False


# --- Formato de la docente (sección 2.7) -----------------------------------------


def _validar_docente(datos: dict) -> list[ErrorValidacion]:
    errores: list[ErrorValidacion] = []
    if "nombre" in datos and not isinstance(datos["nombre"], str):
        errores.append(ErrorValidacion("E02", "nombre debe ser un string"))

    N, k, B = _validar_parametros_docente(datos, errores)
    ids = _validar_nodos_docente(datos, N, B, errores)
    _validar_grafo(datos, ids, errores)
    return errores


def _obligatorio(objeto: dict, campo: str, ubicacion: str, errores) -> bool:
    if campo in objeto:
        return True
    donde = f"{ubicacion}: " if ubicacion else ""
    errores.append(ErrorValidacion("E11", f"{donde}falta el campo obligatorio {campo}"))
    return False


def _validar_parametros_docente(datos, errores) -> tuple[int | None, int | None, int | None]:
    if not _obligatorio(datos, "parametros", "", errores):
        return None, None, None
    parametros = datos["parametros"]
    if not isinstance(parametros, dict):
        errores.append(ErrorValidacion("E02", "parametros debe ser un objeto"))
        return None, None, None

    def leer(campo):
        if not _obligatorio(parametros, campo, "parametros", errores):
            return None
        return _entero(parametros[campo], f"parametros.{campo}", errores)

    N = leer("numero_nodos")
    k = leer("cupo_participantes_por_ronda_k")
    B = leer("presupuesto_ruido_por_ronda_B")

    # Como en el formato propio, un valor fuera de rango pasa a None para omitir lo que depende de él.
    if N is not None and N < 1:
        errores.append(ErrorValidacion("E12", f"numero_nodos debe ser ≥ 1 (vale {N})"))
        N = None
    if k is not None and (k < 1 or (N is not None and k > N)):
        errores.append(
            ErrorValidacion("E12", f"cupo_participantes_por_ronda_k debe cumplir 1 ≤ k ≤ N (k = {k}, N = {N})")
        )
    if B is not None and B < 0:
        errores.append(ErrorValidacion("E12", f"presupuesto_ruido_por_ronda_B debe ser ≥ 0 (vale {B})"))
        B = None
    return N, k, B


def _validar_nodos_docente(datos, N, B, errores) -> set[str] | None:
    """Valida los nodos y devuelve sus ids como texto, o None si no se pueden conocer todos."""
    if not _obligatorio(datos, "nodos", "", errores):
        return None
    nodos = datos["nodos"]
    if not isinstance(nodos, list):
        errores.append(ErrorValidacion("E02", "nodos debe ser una lista"))
        return None
    if N is not None and len(nodos) != N:
        errores.append(ErrorValidacion("E04", f"nodos tiene {len(nodos)} elementos y numero_nodos = {N}"))

    posiciones_por_id: dict[str, list[int]] = {}
    ids_completos = True
    for i, nodo in enumerate(nodos):
        ubicacion = f"nodos[{i}]"
        if not isinstance(nodo, dict):
            errores.append(ErrorValidacion("E02", f"{ubicacion} debe ser un objeto"))
            ids_completos = False
            continue
        id_nodo = _validar_id(nodo, ubicacion, errores) if _obligatorio(nodo, "id", ubicacion, errores) else None
        if id_nodo is None:
            ids_completos = False
        else:
            posiciones_por_id.setdefault(str(id_nodo), []).append(i)

        coeficiente = None
        if _obligatorio(nodo, "coeficiente_utilidad", ubicacion, errores):
            coeficiente = _real(nodo["coeficiente_utilidad"], f"{ubicacion}.coeficiente_utilidad", errores)
            if coeficiente is not None and coeficiente < 0:
                errores.append(
                    ErrorValidacion("E16", f"{ubicacion}.coeficiente_utilidad debe ser ≥ 0 (vale {coeficiente})")
                )
                coeficiente = None
        if _obligatorio(nodo, "presupuesto_total_nodo", ubicacion, errores):
            tope = _entero(nodo["presupuesto_total_nodo"], f"{ubicacion}.presupuesto_total_nodo", errores)
            if tope is not None and tope < 0:
                errores.append(
                    ErrorValidacion("E17", f"{ubicacion}.presupuesto_total_nodo debe ser ≥ 0 (vale {tope})")
                )
        # Misma comprobación que la utilidad log (a = c, b = 1), sin truncar en el tope.
        if coeficiente is not None and B is not None and not _log_evaluable(coeficiente, 1.0, B):
            errores.append(ErrorValidacion("E09", f"{ubicacion}.coeficiente_utilidad desborda al evaluar u(B + 1)"))

    for texto, posiciones in posiciones_por_id.items():
        if len(posiciones) > 1:
            errores.append(ErrorValidacion("E04", f"id {texto!r} repetido en las posiciones {posiciones}"))
    return set(posiciones_por_id) if ids_completos else None


def _validar_grafo(datos, ids, errores) -> None:
    if not _obligatorio(datos, "grafo", "", errores):
        return
    grafo = datos["grafo"]
    if not isinstance(grafo, list):
        errores.append(ErrorValidacion("E02", "grafo debe ser una lista"))
        return

    vistas: dict[frozenset, int] = {}
    for j, arista in enumerate(grafo):
        ubicacion = f"grafo[{j}]"
        if not isinstance(arista, dict):
            errores.append(ErrorValidacion("E02", f"{ubicacion} debe ser un objeto"))
            continue
        u = _extremo(arista, "u", ubicacion, ids, errores)
        v = _extremo(arista, "v", ubicacion, ids, errores)
        if _obligatorio(arista, "peso_influencia", ubicacion, errores):
            peso = _real(arista["peso_influencia"], f"{ubicacion}.peso_influencia", errores)
            if peso is not None and not 0 <= peso <= 1:
                errores.append(
                    ErrorValidacion("E15", f"{ubicacion}.peso_influencia debe estar en [0, 1] (vale {peso})")
                )
        if u is None or v is None:
            continue
        if u == v:
            errores.append(ErrorValidacion("E14", f"{ubicacion} es un lazo: u = v = {u!r}"))
            continue
        clave = frozenset((u, v))
        if clave in vistas:
            errores.append(
                ErrorValidacion("E14", f"{ubicacion} repite la arista {u!r}–{v!r} de grafo[{vistas[clave]}]")
            )
        else:
            vistas[clave] = j


def _extremo(arista, campo, ubicacion, ids, errores) -> str | None:
    """Devuelve el extremo como texto, o None si falta o es inválido."""
    if not _obligatorio(arista, campo, ubicacion, errores):
        return None
    valor = arista[campo]
    if isinstance(valor, str):
        texto = valor
    else:
        entero = como_entero(valor)
        if entero is None:
            codigo = "E09" if es_numero(valor) and not es_finito(valor) else "E02"
            errores.append(ErrorValidacion(codigo, f"{ubicacion}.{campo} debe ser un entero o un string"))
            return None
        texto = str(entero)
    if ids is not None and texto not in ids:
        errores.append(ErrorValidacion("E13", f"{ubicacion}.{campo} = {texto!r} no es el id de ningún nodo"))
    return texto

"""Parte 2: voraz submodular (+ traza opcional)."""

from dataclasses import dataclass

from src.modelo import Caso


@dataclass(frozen=True)
class ResultadoSeleccion:
    """`indices` son posiciones en `caso.nodos`, en el orden en que se eligieron."""

    indices: tuple[int, ...]
    utilidad_conjunta: float


def seleccionar(caso: Caso, traza: list | None = None, resumen: bool = False) -> ResultadoSeleccion:
    """Elige `k` nodos con el voraz directo, en O(N · k · τ).

    Si se pasa `traza`, añade un registro por paso; con `resumen` omite las
    ganancias de los candidatos.
    """
    cubierto = [False] * caso.universo
    seleccionado = [False] * caso.N
    indices: list[int] = []
    utilidad = 0.0

    for paso in range(1, caso.k + 1):
        ganancias: dict[str, float] = {}
        mejor = -1
        mejor_ganancia = 0.0
        mejor_clave = -1.0

        for i, nodo in enumerate(caso.nodos):
            if seleccionado[i]:
                continue
            ganancia = sum((caso.pesos_universo[e] for e in nodo.cubre if not cubierto[e]), 0.0)
            if traza is not None and not resumen:
                ganancias[str(nodo.id)] = ganancia
            # Comparación estricta: si empatan, se queda el primero de la lista.
            clave = round(ganancia, 9)
            if clave > mejor_clave:
                mejor, mejor_ganancia, mejor_clave = i, ganancia, clave

        seleccionado[mejor] = True
        indices.append(mejor)
        for e in caso.nodos[mejor].cubre:
            cubierto[e] = True
        utilidad += mejor_ganancia

        if traza is not None:
            registro = {"paso": paso}
            if not resumen:
                registro["ganancias"] = ganancias
            registro["elegido"] = caso.nodos[mejor].id
            registro["ganancia"] = mejor_ganancia
            registro["utilidad_acumulada"] = utilidad
            traza.append(registro)

    return ResultadoSeleccion(tuple(indices), utilidad)

"""Parte 1: voraz con heapq (+ traza opcional)."""

import heapq
from dataclasses import dataclass

from src.modelo import Caso, Utilidad

TOLERANCIA = 1e-9


@dataclass(frozen=True)
class ResultadoReparto:
    """`asignacion` va de posición en `caso.nodos` a unidades, en orden de selección."""

    asignacion: dict[int, int]
    utilidad_total: float
    presupuesto_usado: int
    presupuesto_sin_usar: int


def _entrada(utilidad: Utilidad, x: int, indice: int) -> tuple[float, int, float]:
    """Entrada del montículo: la mayor ganancia queda en la cima y, si empatan, el primer nodo."""
    ganancia = utilidad.ganancia(x)
    return (-round(ganancia, 9), indice, ganancia)


def repartir(caso: Caso, indices, traza: list | None = None) -> ResultadoReparto:
    """Reparte `B` entre los `N = len(indices)` nodos por ganancia marginal, en O(N + B log N).

    Si se pasa `traza`, añade un registro por unidad asignada; registrar los
    candidatos cuesta O(N) por unidad, así que el tiempo se mide sin traza.
    """
    asignacion = {i: 0 for i in indices}
    utilidad = sum((caso.nodos[i].utilidad.valor(0) for i in indices), 0.0)
    monticulo = [_entrada(caso.nodos[i].utilidad, 0, i) for i in indices]
    heapq.heapify(monticulo)
    usado = 0

    for unidad in range(1, caso.B + 1):
        if not monticulo or monticulo[0][2] <= TOLERANCIA:
            break
        if traza is not None:
            candidatos = {
                str(caso.nodos[i].id): caso.nodos[i].utilidad.ganancia(x)
                for i, x in asignacion.items()
            }

        _, i, ganancia = heapq.heappop(monticulo)
        asignacion[i] += 1
        utilidad += ganancia
        usado += 1
        heapq.heappush(monticulo, _entrada(caso.nodos[i].utilidad, asignacion[i], i))

        if traza is not None:
            traza.append(
                {
                    "unidad": unidad,
                    "candidatos": candidatos,
                    "asignada_a": caso.nodos[i].id,
                    "ganancia": ganancia,
                    "x_nuevo": asignacion[i],
                    "utilidad_acumulada": utilidad,
                }
            )

    return ResultadoReparto(asignacion, utilidad, usado, caso.B - usado)

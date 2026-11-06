"""Utilidad conjunta f(A) intercambiable (Parte 2): cobertura e influencia.

Cada estrategia ofrece la misma interfaz, que usan el voraz y la fuerza bruta:

- `estado_inicial(caso)`: estado del voraz con A vacío.
- `ganancia(caso, estado, i)`: f(A ∪ {i}) − f(A), con A descrito por `estado`.
- `agregar(caso, estado, i)`: actualiza `estado` para A ∪ {i}.
- `valor(caso, indices)`: f(A) calculada desde cero, para la fuerza bruta.

Los índices son posiciones en `caso.nodos`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modelo import Caso


@dataclass(frozen=True)
class Cobertura:
    """f(A) = Σ w_e para e ∈ ⋃_{i∈A} cubre_i. El estado es el arreglo `cubierto`."""

    nombre = "cobertura"

    def estado_inicial(self, caso: Caso) -> list[bool]:
        return [False] * caso.universo

    def ganancia(self, caso: Caso, cubierto: list[bool], i: int) -> float:
        """Cuesta τ = O(|cubre_i|)."""
        return sum((caso.pesos_universo[e] for e in caso.nodos[i].cubre if not cubierto[e]), 0.0)

    def agregar(self, caso: Caso, cubierto: list[bool], i: int) -> None:
        for e in caso.nodos[i].cubre:
            cubierto[e] = True

    def valor(self, caso: Caso, indices) -> float:
        cubiertos = set().union(*(caso.nodos[i].cubre for i in indices))
        return math.fsum(caso.pesos_universo[e] for e in cubiertos)


@dataclass(frozen=True)
class Influencia:
    """f(A) = Σ_v c_v · [1 − Π_{u∈A} (1 − p_uv)], con p_vv = 1 y p_uv = 0 sin arista.

    `vecinos[u]` lista los pares (v, p_uv) de las aristas no dirigidas de u.
    El estado es q[v] = Π_{u∈A} (1 − p_uv).
    """

    coeficientes: tuple[float, ...]
    vecinos: tuple[tuple[tuple[int, float], ...], ...]

    nombre = "influencia"

    @classmethod
    def desde_aristas(cls, coeficientes, aristas) -> Influencia:
        """Construye las listas de adyacencia a partir de tuplas (u, v, p) por posición."""
        vecinos: list[list[tuple[int, float]]] = [[] for _ in coeficientes]
        for u, v, p in aristas:
            vecinos[u].append((v, float(p)))
            vecinos[v].append((u, float(p)))
        return cls(tuple(float(c) for c in coeficientes), tuple(tuple(lista) for lista in vecinos))

    def estado_inicial(self, caso: Caso) -> list[float]:
        return [1.0] * caso.N

    def ganancia(self, caso: Caso, q: list[float], u: int) -> float:
        """Σ_v c_v · q[v] · p_uv, recorriendo la adyacencia de u: τ = O(1 + grado(u)) ≤ O(N)."""
        c = self.coeficientes
        ganancia = c[u] * q[u]
        for v, p in self.vecinos[u]:
            ganancia += c[v] * q[v] * p
        return ganancia

    def agregar(self, caso: Caso, q: list[float], u: int) -> None:
        q[u] = 0.0
        for v, p in self.vecinos[u]:
            q[v] *= 1 - p

    def valor(self, caso: Caso, indices) -> float:
        q = self.estado_inicial(caso)
        for u in indices:
            self.agregar(caso, q, u)
        return math.fsum(c * (1 - qv) for c, qv in zip(self.coeficientes, q))

"""Clases Caso, Nodo, Utilidad (tabla y log, con tope opcional)."""

import math
from dataclasses import dataclass, field

from src.conjunta import Cobertura, Influencia


class Utilidad:
    """Función u_i(x) sobre enteros no negativos, creciente y cóncava."""

    def valor(self, x: int) -> float:
        raise NotImplementedError

    def ganancia(self, x: int) -> float:
        """Ganancia marginal g(x) = u(x+1) − u(x)."""
        return self.valor(x + 1) - self.valor(x)


@dataclass(frozen=True)
class UtilidadTabla(Utilidad):
    """u(x) = valores[x]; para x mayor que el último índice vale el último valor."""

    valores: tuple[float, ...]

    def valor(self, x: int) -> float:
        return self.valores[min(x, len(self.valores) - 1)]


@dataclass(frozen=True)
class UtilidadLog(Utilidad):
    """u(x) = a · ln(1 + b·x); con `tope`, u(x) = u(tope) para x > tope."""

    a: float
    b: float
    tope: int | None = None

    def valor(self, x: int) -> float:
        if self.tope is not None:
            x = min(x, self.tope)
        return self.a * math.log1p(self.b * x)


@dataclass(frozen=True)
class Nodo:
    id: int | str
    cubre: tuple[int, ...]
    utilidad: Utilidad


@dataclass(frozen=True)
class Caso:
    nombre: str
    N: int
    k: int
    B: int
    universo: int
    pesos_universo: tuple[float, ...]
    nodos: tuple[Nodo, ...]
    # Utilidad conjunta f(S) de la Parte 2: cobertura (formato propio) o influencia (docente).
    conjunta: Cobertura | Influencia = field(default_factory=Cobertura)

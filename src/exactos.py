"""Fuerza bruta Parte 2 y DP Parte 1 (verificación)."""

import itertools
import math

from src.modelo import Caso

LIMITE_FUERZA_BRUTA = 10**6
LIMITE_DP = 10**7
COTA_SELECCION = 1 - 1 / math.e

# Por el redondeo y la parada, cada unidad puede perder hasta 1.5e-9 frente al óptimo.
TOLERANCIA_POR_UNIDAD = 2e-9
# Margen para el error acumulado de coma flotante, proporcional a la utilidad.
TOLERANCIA_RELATIVA = 1e-12


def cabe_fuerza_bruta(caso: Caso) -> bool:
    return math.comb(caso.N, caso.k) <= LIMITE_FUERZA_BRUTA


def cabe_dp(caso: Caso) -> bool:
    return caso.k * caso.B**2 <= LIMITE_DP


def seleccion_optima(caso: Caso) -> float:
    """Devuelve `f_optimo` probando los C(N, k) subconjuntos con la utilidad conjunta del caso."""
    mejor = 0.0
    for subconjunto in itertools.combinations(range(caso.N), caso.k):
        mejor = max(mejor, caso.conjunta.valor(caso, subconjunto))
    return mejor


def razon_seleccion(f_voraz: float, f_optimo: float) -> float:
    """Razón `f(S) / f_optimo`; vale 1 si `f_optimo` es 0."""
    return 1.0 if f_optimo == 0 else f_voraz / f_optimo


def reparto_optimo(caso: Caso, indices) -> float:
    """Devuelve la mayor `Σ u_i(x_i)` con `Σ x_i ≤ B`, por DP en O(k · B²)."""
    mejor = [0.0] * (caso.B + 1)
    for i in indices:
        utilidad = caso.nodos[i].utilidad
        valores = [utilidad.valor(x) for x in range(caso.B + 1)]
        mejor = [
            max(mejor[b - x] + valores[x] for x in range(b + 1))
            for b in range(caso.B + 1)
        ]
    return mejor[caso.B]


def voraz_coincide(voraz: float, optimo: float, B: int) -> bool:
    """Indica si la diferencia con el óptimo se explica solo por el redondeo de las comparaciones."""
    return abs(voraz - optimo) <= TOLERANCIA_POR_UNIDAD * B + TOLERANCIA_RELATIVA * abs(optimo)

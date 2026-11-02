"""Pruebas del voraz contra los algoritmos exactos."""

import math
import random
from pathlib import Path

import pytest

from src.exactos import (
    COTA_SELECCION,
    cabe_dp,
    cabe_fuerza_bruta,
    razon_seleccion,
    reparto_optimo,
    seleccion_optima,
    voraz_coincide,
)
from src.lector import leer_caso
from src.modelo import Caso, Nodo, UtilidadLog, UtilidadTabla
from src.reparto import repartir
from src.seleccion import seleccionar

CASOS_EJEMPLO = Path(__file__).resolve().parent.parent / "casos_ejemplo"
INSTANCIAS = 200


def tabla(*valores):
    return UtilidadTabla(tuple(float(valor) for valor in valores))


def tabla_por_ganancias(*ganancias):
    valores = [0.0]
    for ganancia in ganancias:
        valores.append(valores[-1] + ganancia)
    return UtilidadTabla(tuple(valores))


def crear_caso(coberturas=None, utilidades=None, k=1, B=0, universo=0, pesos=None):
    if utilidades is None:
        utilidades = [tabla(0)] * len(coberturas)
    if coberturas is None:
        coberturas = [()] * len(utilidades)
    return Caso(
        nombre="prueba",
        N=len(coberturas),
        k=k,
        B=B,
        universo=universo,
        pesos_universo=tuple(pesos) if pesos is not None else (1.0,) * universo,
        nodos=tuple(
            Nodo(i, tuple(cubre), utilidad)
            for i, (cubre, utilidad) in enumerate(zip(coberturas, utilidades))
        ),
    )


def utilidad_aleatoria(azar, B):
    if azar.random() < 0.5:
        ganancias = sorted((azar.uniform(0, 10) for _ in range(azar.randint(0, B + 1))), reverse=True)
        valores = [azar.uniform(0, 5)]
        for ganancia in ganancias:
            valores.append(valores[-1] + ganancia)
        return UtilidadTabla(tuple(valores))
    return UtilidadLog(azar.uniform(0.1, 10), azar.uniform(0.1, 5))


def instancia_aleatoria(semilla):
    azar = random.Random(semilla)
    N = azar.randint(2, 10)
    universo = azar.randint(0, 14)
    B = azar.randint(0, 25)
    return Caso(
        nombre=f"azar_{semilla}",
        N=N,
        k=azar.randint(1, N - 1),
        B=B,
        universo=universo,
        pesos_universo=tuple(azar.uniform(0.1, 5) for _ in range(universo)),
        nodos=tuple(
            Nodo(
                i,
                # Coberturas pequeñas: si cubren casi todo, el voraz acierta siempre.
                tuple(azar.sample(range(universo), azar.randint(0, universo // 2))),
                utilidad_aleatoria(azar, B),
            )
            for i in range(N)
        ),
    )


@pytest.fixture
def ejemplo_01():
    return leer_caso(CASOS_EJEMPLO / "ejemplo_01.json").caso


# Fuerza bruta de la Parte 2


def test_fuerza_bruta_en_ejemplo_01(ejemplo_01):
    assert seleccion_optima(ejemplo_01) == 6.0


def test_fuerza_bruta_supera_al_voraz_donde_este_se_equivoca():
    caso = crear_caso([[0, 1, 2, 3], [0, 1, 4], [2, 3, 5]], k=2, universo=6)
    assert seleccionar(caso).utilidad_conjunta == 5.0
    assert seleccion_optima(caso) == 6.0


def test_fuerza_bruta_no_cuenta_dos_veces_lo_cubierto():
    caso = crear_caso([[0, 1], [0, 1]], k=1, universo=2, pesos=[2.0, 3.0])
    assert seleccion_optima(caso) == 5.0


def test_fuerza_bruta_usa_los_pesos():
    caso = crear_caso([[0, 1], [2]], k=1, universo=3, pesos=[1.0, 1.0, 5.0])
    assert seleccion_optima(caso) == 5.0


def test_fuerza_bruta_con_universo_vacio_da_cero_real():
    optimo = seleccion_optima(crear_caso([[], []], k=1, universo=0))
    assert optimo == 0.0
    assert isinstance(optimo, float)


def test_razon_divide_entre_el_optimo():
    assert razon_seleccion(5.0, 6.0) == 5.0 / 6.0


def test_razon_vale_uno_si_el_optimo_es_cero():
    assert razon_seleccion(0.0, 0.0) == 1.0


def test_limite_de_la_fuerza_bruta_es_inclusivo():
    # C(10^6, 1) = 10^6 subconjuntos.
    def caso_con(N, k):
        return Caso("prueba", N, k, 0, 0, (), ())

    assert cabe_fuerza_bruta(caso_con(10**6, 1))
    assert not cabe_fuerza_bruta(caso_con(10**6 + 1, 1))


# Programación dinámica de la Parte 1


def test_dp_en_ejemplo_01(ejemplo_01):
    assert reparto_optimo(ejemplo_01, (0, 2)) == pytest.approx(10 + 6 * math.log(3))


def test_dp_prueba_todas_las_divisiones():
    # El mejor reparto da las 2 unidades al nodo 1, no 1 y 1.
    caso = crear_caso(utilidades=[tabla(0, 3, 3), tabla(0, 3, 6)], k=1, B=2)
    assert reparto_optimo(caso, (0, 1)) == 6.0


def test_dp_solo_usa_los_nodos_indicados():
    caso = crear_caso(utilidades=[tabla(0, 100), tabla(0, 1), tabla(0, 2)], k=2, B=1)
    assert reparto_optimo(caso, (1, 2)) == 2.0


def test_dp_incluye_u_de_cero_de_quien_no_recibe():
    caso = crear_caso(utilidades=[tabla(2, 7), tabla(4, 5)], k=1, B=1)
    assert reparto_optimo(caso, (0, 1)) == 11.0


def test_dp_con_presupuesto_cero():
    caso = crear_caso(utilidades=[tabla(2, 7), tabla(4, 5)], k=1, B=0)
    assert reparto_optimo(caso, (0, 1)) == 6.0


def test_dp_con_tabla_mas_corta_que_b():
    caso = crear_caso(utilidades=[tabla(0, 5, 8), tabla(0, 3)], k=1, B=10)
    assert reparto_optimo(caso, (0, 1)) == 11.0


def test_limite_de_la_dp_es_inclusivo():
    def caso_con(k, B):
        return Caso("prueba", k + 1, k, B, 0, (), ())

    assert cabe_dp(caso_con(10, 1000))
    assert not cabe_dp(caso_con(11, 1000))


# Voraz contra exactos en instancias aleatorias


@pytest.fixture(scope="module")
def instancias():
    return [instancia_aleatoria(semilla) for semilla in range(INSTANCIAS)]


def test_parte_1_el_voraz_coincide_con_la_dp(instancias):
    for caso in instancias:
        indices = seleccionar(caso).indices
        voraz = repartir(caso, indices).utilidad_total
        optimo = reparto_optimo(caso, indices)
        assert abs(voraz - optimo) <= 1e-9, caso.nombre
        assert voraz_coincide(voraz, optimo, caso.B), caso.nombre


def test_parte_2_el_voraz_cumple_la_cota(instancias):
    for caso in instancias:
        razon = razon_seleccion(seleccionar(caso).utilidad_conjunta, seleccion_optima(caso))
        assert razon >= COTA_SELECCION, caso.nombre
        assert razon <= 1 + 1e-9, caso.nombre


def test_las_instancias_de_la_parte_2_no_son_triviales(instancias):
    """Si el voraz siempre acertara, la prueba de la cota no demostraría nada."""
    razones = [
        razon_seleccion(seleccionar(caso).utilidad_conjunta, seleccion_optima(caso))
        for caso in instancias
    ]
    assert min(razones) < 1 - 1e-9


# Riesgo del redondeo: round(g, 9) acumula más de 1e-9 frente a la DP


def test_el_empate_por_redondeo_puede_acumular_mas_de_1e_9():
    # Ambas ganancias redondean a 1.0: el empate favorece al nodo 0 en cada unidad.
    caso = crear_caso(
        utilidades=[
            tabla_por_ganancias(*[1.0] * 10),
            tabla_por_ganancias(*[1.0 + 4e-10] * 10),
        ],
        k=1,
        B=10,
    )
    voraz = repartir(caso, (0, 1))
    optimo = reparto_optimo(caso, (0, 1))
    assert voraz.asignacion == {0: 10, 1: 0}
    assert optimo - voraz.utilidad_total > 1e-9
    assert voraz_coincide(voraz.utilidad_total, optimo, caso.B)


def test_la_parada_puede_dejar_mas_de_1e_9_sin_gastar():
    caso = crear_caso(utilidades=[tabla_por_ganancias(*[1e-9] * 10)], k=1, B=10)
    voraz = repartir(caso, (0,))
    optimo = reparto_optimo(caso, (0,))
    assert voraz.presupuesto_sin_usar == 10
    assert optimo - voraz.utilidad_total > 1e-9
    assert voraz_coincide(voraz.utilidad_total, optimo, caso.B)


def test_el_peor_caso_de_la_parada_cabe_en_la_tolerancia():
    # La cima vale 1e-9 y detrás hay 1.4e-9 por unidad, que redondea igual.
    caso = crear_caso(
        utilidades=[tabla_por_ganancias(1e-9), tabla_por_ganancias(*[1.4e-9] * 10)],
        k=1,
        B=10,
    )
    voraz = repartir(caso, (0, 1))
    optimo = reparto_optimo(caso, (0, 1))
    assert voraz.presupuesto_sin_usar == 10
    assert optimo - voraz.utilidad_total == pytest.approx(1.4e-8)
    assert voraz_coincide(voraz.utilidad_total, optimo, caso.B)


def test_una_diferencia_real_no_se_da_por_coincidencia():
    assert not voraz_coincide(10.0, 10.1, B=10)
    assert not voraz_coincide(10.0, 10.0 + 3e-8, B=10)


def test_con_presupuesto_cero_la_tolerancia_es_solo_de_coma_flotante():
    assert voraz_coincide(6.0, 6.0, B=0)
    assert not voraz_coincide(6.0, 6.0 + 1e-9, B=0)


def test_la_tolerancia_absorbe_el_error_de_coma_flotante_con_valores_grandes():
    assert voraz_coincide(1e9, 1e9 + 1e-4, B=1)


def test_el_voraz_coincide_en_instancias_con_ganancias_casi_iguales():
    """Busca violar la cota: muchas ganancias dentro de un mismo grupo de redondeo."""
    azar = random.Random(4)
    peor = 0.0
    for _ in range(INSTANCIAS):
        B = azar.randint(1, 30)
        base = azar.choice([1.0, 1e-9, 2e-9, 5e-10])
        utilidades = [
            tabla_por_ganancias(
                *sorted(
                    (max(base + azar.uniform(-1e-9, 1e-9), 0.0) for _ in range(azar.randint(1, B))),
                    reverse=True,
                )
            )
            for _ in range(azar.randint(1, 5))
        ]
        caso = crear_caso(utilidades=utilidades, k=1, B=B)
        indices = tuple(range(len(utilidades)))
        voraz = repartir(caso, indices).utilidad_total
        optimo = reparto_optimo(caso, indices)
        peor = max(peor, optimo - voraz)
        assert voraz_coincide(voraz, optimo, B)
    assert peor > 1e-9

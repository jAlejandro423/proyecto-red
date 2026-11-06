"""Pruebas de la utilidad conjunta intercambiable: cobertura e influencia."""

import itertools
import math
import random

import pytest

from src.conjunta import Cobertura, Influencia
from src.exactos import COTA_SELECCION, seleccion_optima
from src.modelo import Caso, Nodo, UtilidadLog, UtilidadTabla
from src.seleccion import seleccionar

INSTANCIAS = 200
TOLERANCIA = 1e-9


def caso_influencia(coeficientes, aristas, k=1, B=0):
    """Caso con utilidad conjunta de influencia; `aristas` son tuplas (u, v, p) por posición."""
    N = len(coeficientes)
    return Caso(
        nombre="prueba",
        N=N,
        k=k,
        B=B,
        universo=0,
        pesos_universo=(),
        nodos=tuple(Nodo(i, (), UtilidadLog(c, 1.0)) for i, c in enumerate(coeficientes)),
        conjunta=Influencia.desde_aristas(coeficientes, aristas),
    )


def influencia_aleatoria(semilla):
    azar = random.Random(semilla)
    N = azar.randint(2, 9)
    coeficientes = [azar.uniform(0, 10) for _ in range(N)]
    aristas = [
        (u, v, azar.choice((0.0, 1.0, azar.random())))
        for u, v in itertools.combinations(range(N), 2)
        if azar.random() < 0.6
    ]
    return caso_influencia(coeficientes, aristas, k=azar.randint(1, N))


def influencia_dirigida(semilla):
    """Mezcla pares en una dirección (simétricos) y en las dos (con pesos distintos)."""
    azar = random.Random(semilla + 5000)
    N = azar.randint(2, 9)
    coeficientes = [azar.uniform(0, 10) for _ in range(N)]
    aristas = []
    for u, v in itertools.combinations(range(N), 2):
        sorteo = azar.random()
        if sorteo < 0.5:
            aristas.append((u, v, azar.random()))
            aristas.append((v, u, azar.random()))
        elif sorteo < 0.8:
            aristas.append((v, u, azar.random()) if azar.random() < 0.5 else (u, v, azar.random()))
    azar.shuffle(aristas)
    return caso_influencia(coeficientes, aristas, k=azar.randint(1, N))


def f_directa(caso, indices):
    """f(A) = Σ_v c_v · [1 − Π_{u∈A} (1 − p_uv)], escrita tal cual la definición."""
    conjunta = caso.conjunta
    p = [[0.0] * caso.N for _ in range(caso.N)]
    for u in range(caso.N):
        p[u][u] = 1.0
        for v, peso in conjunta.vecinos[u]:
            p[u][v] = peso
    total = 0.0
    for v in range(caso.N):
        producto = 1.0
        for u in indices:
            producto *= 1 - p[u][v]
        total += conjunta.coeficientes[v] * (1 - producto)
    return total


# --- Interfaz común -------------------------------------------------------------


def test_el_caso_usa_cobertura_por_defecto():
    caso = Caso("prueba", 2, 1, 0, 0, (), ())
    assert isinstance(caso.conjunta, Cobertura)


def test_cobertura_valor_es_el_peso_de_la_union():
    caso = Caso(
        "prueba", 3, 2, 0, 4, (1.0, 2.0, 3.0, 4.0),
        (Nodo(0, (0, 1), UtilidadTabla((0.0,))), Nodo(1, (1, 2), UtilidadTabla((0.0,))),
         Nodo(2, (3,), UtilidadTabla((0.0,)))),
    )
    assert caso.conjunta.valor(caso, (0, 1)) == 6.0
    assert caso.conjunta.valor(caso, ()) == 0.0


@pytest.mark.parametrize("fabrica", ["cobertura", "influencia", "dirigida"])
def test_la_ganancia_es_la_diferencia_de_valores(fabrica):
    azar = random.Random(7)
    for semilla in range(50):
        if fabrica == "influencia":
            caso = influencia_aleatoria(semilla)
        elif fabrica == "dirigida":
            caso = influencia_dirigida(semilla)
        else:
            universo = azar.randint(0, 8)
            N = azar.randint(2, 6)
            caso = Caso(
                "prueba", N, 1, 0, universo, tuple(azar.uniform(0, 3) for _ in range(universo)),
                tuple(Nodo(i, tuple(e for e in range(universo) if azar.random() < 0.4), UtilidadTabla((0.0,)))
                      for i in range(N)),
            )
        conjunta = caso.conjunta
        estado = conjunta.estado_inicial(caso)
        elegidos = []
        for u in azar.sample(range(caso.N), caso.N):
            esperado = conjunta.valor(caso, elegidos + [u]) - conjunta.valor(caso, elegidos)
            assert conjunta.ganancia(caso, estado, u) == pytest.approx(esperado, abs=1e-9)
            conjunta.agregar(caso, estado, u)
            elegidos.append(u)


# --- Influencia: definición, monotonía y submodularidad -------------------------


def test_influencia_vale_lo_mismo_que_la_definicion():
    for semilla in range(INSTANCIAS):
        caso = influencia_aleatoria(semilla)
        azar = random.Random(semilla)
        A = azar.sample(range(caso.N), azar.randint(0, caso.N))
        assert caso.conjunta.valor(caso, A) == pytest.approx(f_directa(caso, A), abs=1e-9)


def test_influencia_de_un_nodo_aislado_es_su_coeficiente():
    caso = caso_influencia([3.0, 5.0], [])
    assert caso.conjunta.valor(caso, [1]) == 5.0
    assert caso.conjunta.valor(caso, []) == 0.0


def test_influencia_con_peso_uno_cubre_al_vecino_del_todo():
    caso = caso_influencia([3.0, 5.0], [(0, 1, 1.0)])
    assert caso.conjunta.valor(caso, [0]) == 8.0
    assert caso.conjunta.valor(caso, [0, 1]) == 8.0


def test_las_aristas_son_no_dirigidas():
    caso = caso_influencia([2.0, 4.0], [(0, 1, 0.5)])
    assert caso.conjunta.valor(caso, [0]) == pytest.approx(2.0 + 4.0 * 0.5)
    assert caso.conjunta.valor(caso, [1]) == pytest.approx(4.0 + 2.0 * 0.5)


def test_un_par_en_las_dos_direcciones_conserva_cada_peso():
    caso = caso_influencia([2.0, 4.0], [(0, 1, 0.5), (1, 0, 0.1)])
    assert caso.conjunta.vecinos == (((1, 0.5),), ((0, 0.1),))
    assert caso.conjunta.valor(caso, [0]) == pytest.approx(2.0 + 4.0 * 0.5)
    assert caso.conjunta.valor(caso, [1]) == pytest.approx(4.0 + 2.0 * 0.1)


def test_la_direccion_inversa_puede_venir_antes():
    caso = caso_influencia([2.0, 4.0], [(1, 0, 0.1), (0, 1, 0.5)])
    assert caso.conjunta.vecinos == (((1, 0.5),), ((0, 0.1),))


def test_dirigida_vale_lo_mismo_que_la_definicion():
    for semilla in range(INSTANCIAS):
        caso = influencia_dirigida(semilla)
        azar = random.Random(semilla)
        A = azar.sample(range(caso.N), azar.randint(0, caso.N))
        assert caso.conjunta.valor(caso, A) == pytest.approx(f_directa(caso, A), abs=1e-9)


@pytest.mark.parametrize("generador", [influencia_aleatoria, influencia_dirigida])
def test_influencia_es_monotona(generador):
    for semilla in range(INSTANCIAS):
        caso = generador(semilla)
        azar = random.Random(semilla + 1000)
        orden = azar.sample(range(caso.N), caso.N)
        anterior = 0.0
        for i in range(1, caso.N + 1):
            actual = caso.conjunta.valor(caso, orden[:i])
            assert actual >= anterior - TOLERANCIA
            anterior = actual


@pytest.mark.parametrize("generador", [influencia_aleatoria, influencia_dirigida])
def test_influencia_es_submodular(generador):
    """f(A ∪ {x}) − f(A) ≥ f(B ∪ {x}) − f(B) para A ⊆ B y x ∉ B."""
    for semilla in range(INSTANCIAS):
        caso = generador(semilla)
        azar = random.Random(semilla + 2000)
        if caso.N < 2:
            continue
        orden = azar.sample(range(caso.N), caso.N)
        x, resto = orden[0], orden[1:]
        B = resto[: azar.randint(0, len(resto))]
        A = B[: azar.randint(0, len(B))]
        f = caso.conjunta.valor
        assert f(caso, A + [x]) - f(caso, A) >= f(caso, B + [x]) - f(caso, B) - TOLERANCIA


# --- Voraz y fuerza bruta con influencia ---------------------------------------


@pytest.mark.parametrize("generador", [influencia_aleatoria, influencia_dirigida])
def test_el_voraz_con_influencia_reporta_el_valor_de_lo_que_elige(generador):
    for semilla in range(INSTANCIAS):
        caso = generador(semilla)
        resultado = seleccionar(caso)
        assert len(resultado.indices) == caso.k
        assert len(set(resultado.indices)) == caso.k
        assert resultado.utilidad_conjunta == pytest.approx(
            caso.conjunta.valor(caso, resultado.indices), abs=1e-9
        )


@pytest.mark.parametrize("generador", [influencia_aleatoria, influencia_dirigida])
def test_la_fuerza_bruta_con_influencia_es_el_maximo_de_la_definicion(generador):
    for semilla in range(50):
        caso = generador(semilla)
        esperado = max(f_directa(caso, A) for A in itertools.combinations(range(caso.N), caso.k))
        assert seleccion_optima(caso) == pytest.approx(esperado, abs=1e-9)


@pytest.mark.parametrize("generador", [influencia_aleatoria, influencia_dirigida])
def test_el_voraz_con_influencia_cumple_la_cota(generador):
    for semilla in range(INSTANCIAS):
        caso = generador(semilla)
        voraz = seleccionar(caso).utilidad_conjunta
        optimo = seleccion_optima(caso)
        assert voraz <= optimo + 1e-9
        assert voraz >= COTA_SELECCION * optimo - 1e-9


def test_el_voraz_con_influencia_desempata_por_orden_de_la_lista():
    caso = caso_influencia([4.0, 4.0, 1.0], [], k=1)
    traza = []
    assert seleccionar(caso, traza).indices == (0,)
    assert traza[0]["ganancias"] == {"0": 4.0, "1": 4.0, "2": 1.0}


def test_el_voraz_con_influencia_descuenta_lo_ya_cubierto():
    # Elegir 0 cubre la mitad de 1; después 2 (aislado, c = 3) vale más que 1 (queda 4 · 0.5 = 2).
    caso = caso_influencia([6.0, 4.0, 3.0], [(0, 1, 0.5)], k=2)
    traza = []
    resultado = seleccionar(caso, traza)
    assert resultado.indices == (0, 2)
    assert resultado.utilidad_conjunta == pytest.approx(6.0 + 2.0 + 3.0)
    assert traza[1]["ganancias"] == {"1": pytest.approx(2.0), "2": 3.0}


# --- Utilidad log con tope ------------------------------------------------------


def test_log_con_tope_se_trunca():
    utilidad = UtilidadLog(2.0, 1.0, tope=3)
    assert utilidad.valor(3) == pytest.approx(2.0 * math.log(4))
    assert utilidad.valor(10) == utilidad.valor(3)
    assert utilidad.ganancia(3) == 0.0
    assert utilidad.ganancia(2) == pytest.approx(2.0 * (math.log(4) - math.log(3)))


def test_log_con_tope_cero_no_gana_nada():
    utilidad = UtilidadLog(5.0, 1.0, tope=0)
    assert utilidad.valor(0) == 0.0
    assert utilidad.ganancia(0) == 0.0


def test_log_sin_tope_conserva_su_comportamiento():
    assert UtilidadLog(6.0, 1.0).valor(2) == pytest.approx(6 * math.log(3))
    assert UtilidadLog(6.0, 1.0) == UtilidadLog(6.0, 1.0, tope=None)

"""Pruebas de la Parte 2."""

from pathlib import Path

import pytest

from src.lector import leer_caso
from src.modelo import Caso, Nodo, UtilidadTabla
from src.seleccion import seleccionar

CASOS_EJEMPLO = Path(__file__).resolve().parent.parent / "casos_ejemplo"


def crear_caso(coberturas, k, universo, pesos=None, ids=None):
    ids = ids if ids is not None else range(len(coberturas))
    return Caso(
        nombre="prueba",
        N=len(coberturas),
        k=k,
        B=0,
        universo=universo,
        pesos_universo=tuple(pesos) if pesos is not None else (1.0,) * universo,
        nodos=tuple(
            Nodo(id_nodo, tuple(cubre), UtilidadTabla((0.0,)))
            for id_nodo, cubre in zip(ids, coberturas)
        ),
    )


@pytest.fixture
def ejemplo_01():
    return leer_caso(CASOS_EJEMPLO / "ejemplo_01.json").caso


def test_ejemplo_01_selecciona_0_y_2_con_f_6(ejemplo_01):
    resultado = seleccionar(ejemplo_01)
    assert resultado.indices == (0, 2)
    assert resultado.utilidad_conjunta == 6.0


def test_ejemplo_01_produce_la_traza_de_la_especificacion(ejemplo_01):
    traza = []
    seleccionar(ejemplo_01, traza)
    assert traza == [
        {
            "paso": 1,
            "ganancias": {"0": 3.0, "1": 2.0, "2": 3.0, "3": 2.0},
            "elegido": 0,
            "ganancia": 3.0,
            "utilidad_acumulada": 3.0,
        },
        {
            "paso": 2,
            "ganancias": {"1": 1.0, "2": 3.0, "3": 1.0},
            "elegido": 2,
            "ganancia": 3.0,
            "utilidad_acumulada": 6.0,
        },
    ]


def test_traza_resumen_omite_las_ganancias_de_los_candidatos(ejemplo_01):
    traza = []
    seleccionar(ejemplo_01, traza, resumen=True)
    assert traza == [
        {"paso": 1, "elegido": 0, "ganancia": 3.0, "utilidad_acumulada": 3.0},
        {"paso": 2, "elegido": 2, "ganancia": 3.0, "utilidad_acumulada": 6.0},
    ]


def test_la_traza_no_cambia_el_resultado(ejemplo_01):
    assert seleccionar(ejemplo_01, []) == seleccionar(ejemplo_01)


def test_elige_la_mayor_ganancia_aunque_no_sea_el_primero():
    caso = crear_caso([[0], [1, 2, 3], [0, 1]], k=1, universo=4)
    assert seleccionar(caso).indices == (1,)


def test_el_orden_de_indices_es_el_de_seleccion():
    caso = crear_caso([[0], [1, 2, 3]], k=1, universo=4)
    caso_tres = crear_caso([[0], [1, 2, 3], [4]], k=2, universo=5)
    assert seleccionar(caso).indices == (1,)
    assert seleccionar(caso_tres).indices == (1, 0)


def test_la_ganancia_marginal_descuenta_lo_ya_cubierto():
    caso = crear_caso([[0, 1, 2], [0, 1], [3]], k=2, universo=4)
    resultado = seleccionar(caso)
    assert resultado.indices == (0, 2)
    assert resultado.utilidad_conjunta == 4.0


def test_usa_los_pesos_del_universo():
    caso = crear_caso([[0, 1], [2]], k=1, universo=3, pesos=[1.0, 1.0, 5.0])
    resultado = seleccionar(caso)
    assert resultado.indices == (1,)
    assert resultado.utilidad_conjunta == 5.0


def test_empate_tras_redondear_a_9_decimales_gana_el_primero():
    caso = crear_caso([[0], [1, 2]], k=1, universo=3, pesos=[0.3, 0.1, 0.2])
    assert 0.1 + 0.2 > 0.3
    assert seleccionar(caso).indices == (0,)


def test_diferencia_mayor_que_el_redondeo_no_es_empate():
    caso = crear_caso([[0], [1]], k=1, universo=2, pesos=[1.0, 1.0 + 1e-8])
    assert seleccionar(caso).indices == (1,)


def test_la_utilidad_acumulada_no_se_redondea():
    pesos = [1.0000000004, 2.0000000004]
    caso = crear_caso([[0], [1]], k=2, universo=2, pesos=pesos)
    assert seleccionar(caso).utilidad_conjunta == pesos[1] + pesos[0]


def test_elige_exactamente_k_aunque_las_ganancias_sean_cero():
    caso = crear_caso([[0], [0], [], [0]], k=3, universo=1)
    resultado = seleccionar(caso)
    assert resultado.indices == (0, 1, 2)
    assert resultado.utilidad_conjunta == 1.0


def test_universo_vacio_da_utilidad_cero():
    caso = crear_caso([[], [], []], k=2, universo=0)
    resultado = seleccionar(caso)
    assert resultado.indices == (0, 1)
    assert resultado.utilidad_conjunta == 0.0


def test_cada_paso_evalua_todos_los_no_seleccionados():
    caso = crear_caso([[0], [1], [2], [3], [4]], k=3, universo=5)
    traza = []
    seleccionar(caso, traza)
    assert [len(paso["ganancias"]) for paso in traza] == [5, 4, 3]


def test_las_ganancias_de_la_traza_son_reales_con_cubre_vacio():
    caso = crear_caso([[], []], k=1, universo=0)
    traza = []
    seleccionar(caso, traza)
    assert isinstance(traza[0]["ganancias"]["0"], float)
    assert isinstance(traza[0]["ganancia"], float)


def test_ids_de_texto_en_la_traza():
    caso = crear_caso([[0], [1, 2]], k=1, universo=3, ids=["a", 7])
    traza = []
    seleccionar(caso, traza)
    assert traza[0]["ganancias"] == {"a": 1.0, "7": 2.0}
    assert traza[0]["elegido"] == 7

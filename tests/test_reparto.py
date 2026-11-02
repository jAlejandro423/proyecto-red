"""Pruebas de la Parte 1."""

import math
from pathlib import Path

import pytest

from src.lector import leer_caso
from src.modelo import Caso, Nodo, UtilidadLog, UtilidadTabla
from src.reparto import repartir
from src.seleccion import seleccionar

CASOS_EJEMPLO = Path(__file__).resolve().parent.parent / "casos_ejemplo"


def tabla(*valores):
    return UtilidadTabla(tuple(float(valor) for valor in valores))


def crear_caso(utilidades, B, ids=None):
    ids = ids if ids is not None else range(len(utilidades))
    return Caso(
        nombre="prueba",
        N=len(utilidades),
        k=max(len(utilidades) - 1, 1),
        B=B,
        universo=0,
        pesos_universo=(),
        nodos=tuple(Nodo(id_nodo, (), u) for id_nodo, u in zip(ids, utilidades)),
    )


@pytest.fixture
def ejemplo_01():
    return leer_caso(CASOS_EJEMPLO / "ejemplo_01.json").caso


def test_ejemplo_01_reparte_3_y_2_con_utilidad_esperada(ejemplo_01):
    resultado = repartir(ejemplo_01, seleccionar(ejemplo_01).indices)
    assert resultado.asignacion == {0: 3, 2: 2}
    assert resultado.utilidad_total == pytest.approx(10 + 6 * math.log(3))
    assert round(resultado.utilidad_total, 4) == 16.5917
    assert resultado.presupuesto_usado == 5
    assert resultado.presupuesto_sin_usar == 0


def test_ejemplo_01_sigue_la_tabla_de_la_especificacion(ejemplo_01):
    traza = []
    repartir(ejemplo_01, (0, 2), traza)
    assert [paso["unidad"] for paso in traza] == [1, 2, 3, 4, 5]
    assert [paso["asignada_a"] for paso in traza] == [0, 2, 0, 2, 0]
    assert [paso["x_nuevo"] for paso in traza] == [1, 1, 2, 2, 3]
    assert [round(paso["ganancia"], 4) for paso in traza] == [5.0, 4.1589, 3.0, 2.4328, 2.0]
    primero = traza[0]
    assert primero["candidatos"] == {"0": 5.0, "2": pytest.approx(6 * math.log(2))}
    assert primero["utilidad_acumulada"] == 5.0
    assert traza[-1]["candidatos"]["2"] == pytest.approx(6 * (math.log(4) - math.log(3)))
    assert traza[-1]["utilidad_acumulada"] == pytest.approx(10 + 6 * math.log(3))


def test_la_traza_no_cambia_el_resultado(ejemplo_01):
    assert repartir(ejemplo_01, (0, 2), []) == repartir(ejemplo_01, (0, 2))


def test_solo_reparte_entre_los_seleccionados():
    caso = crear_caso([tabla(0, 100), tabla(0, 1), tabla(0, 2)], B=1)
    assert repartir(caso, (1, 2)).asignacion == {1: 0, 2: 1}


def test_la_asignacion_incluye_a_quien_recibe_cero():
    caso = crear_caso([tabla(0, 5, 9, 12), tabla(0, 1)], B=2)
    assert repartir(caso, (0, 1)).asignacion == {0: 2, 1: 0}


def test_la_asignacion_sigue_el_orden_de_seleccion():
    caso = crear_caso([tabla(0, 1), tabla(0, 2)], B=2)
    assert list(repartir(caso, (1, 0)).asignacion) == [1, 0]


def test_empate_gana_el_primero_de_la_lista_aunque_se_eligiera_despues():
    caso = crear_caso([tabla(0, 3), tabla(0, 3)], B=1)
    assert repartir(caso, (1, 0)).asignacion == {0: 1, 1: 0}


def test_empate_tras_redondear_a_9_decimales_gana_el_primero():
    caso = crear_caso([tabla(0, 0.3), tabla(0, 0.1 + 0.2)], B=1)
    assert repartir(caso, (0, 1)).asignacion == {0: 1, 1: 0}


def test_diferencia_mayor_que_el_redondeo_no_es_empate():
    caso = crear_caso([tabla(0, 1), tabla(0, 1 + 1e-8)], B=1)
    assert repartir(caso, (0, 1)).asignacion == {0: 0, 1: 1}


def test_presupuesto_cero():
    caso = crear_caso([tabla(0, 5), tabla(0, 3)], B=0)
    resultado = repartir(caso, (0, 1))
    assert resultado.asignacion == {0: 0, 1: 0}
    assert resultado.utilidad_total == 0.0
    assert resultado.presupuesto_usado == 0
    assert resultado.presupuesto_sin_usar == 0


def test_tabla_mas_corta_que_b_deja_presupuesto_sin_usar():
    caso = crear_caso([tabla(0, 5, 8), tabla(0, 3)], B=10)
    resultado = repartir(caso, (0, 1))
    assert resultado.asignacion == {0: 2, 1: 1}
    assert resultado.utilidad_total == 11.0
    assert resultado.presupuesto_usado == 3
    assert resultado.presupuesto_sin_usar == 7


def test_para_con_ganancia_igual_a_la_tolerancia():
    caso = crear_caso([tabla(0, 1e-9), tabla(0, 5e-10)], B=2)
    resultado = repartir(caso, (0, 1))
    assert resultado.asignacion == {0: 0, 1: 0}
    assert resultado.presupuesto_sin_usar == 2


def test_no_para_con_ganancia_mayor_que_la_tolerancia():
    caso = crear_caso([tabla(0, 3e-9), tabla(0, 1)], B=2)
    resultado = repartir(caso, (0, 1))
    assert resultado.asignacion == {0: 1, 1: 1}
    assert resultado.presupuesto_sin_usar == 0


def test_la_utilidad_incluye_u_de_cero_de_todos_los_seleccionados():
    caso = crear_caso([tabla(2, 7), tabla(4, 5), tabla(100, 200)], B=1)
    resultado = repartir(caso, (0, 1))
    assert resultado.asignacion == {0: 1, 1: 0}
    assert resultado.utilidad_total == 11.0


def test_la_traza_acumula_desde_u_de_cero():
    caso = crear_caso([tabla(2, 7), tabla(4, 5)], B=1)
    traza = []
    repartir(caso, (0, 1), traza)
    assert traza[0]["utilidad_acumulada"] == 11.0


def test_la_utilidad_acumulada_no_se_redondea():
    caso = crear_caso([tabla(0, 1.0000000004)], B=1)
    assert repartir(caso, (0,)).utilidad_total == 1.0000000004


def test_utilidad_logaritmica_gasta_todo_el_presupuesto():
    caso = crear_caso([UtilidadLog(1.0, 1.0), UtilidadLog(1.0, 1.0)], B=4)
    resultado = repartir(caso, (0, 1))
    assert resultado.asignacion == {0: 2, 1: 2}
    assert resultado.presupuesto_usado == 4


def test_ids_de_texto_en_la_traza():
    caso = crear_caso([tabla(0, 1), tabla(0, 2)], B=1, ids=["a", 7])
    traza = []
    repartir(caso, (0, 1), traza)
    assert traza[0]["candidatos"] == {"a": 1.0, "7": 2.0}
    assert traza[0]["asignada_a"] == 7


def test_la_traza_no_registra_la_parada():
    caso = crear_caso([tabla(0, 5)], B=3)
    traza = []
    repartir(caso, (0,), traza)
    assert len(traza) == 1

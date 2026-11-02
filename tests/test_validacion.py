"""Pruebas de la entrada: modelo, lectura y validaciones E01–E10."""

import json
import math
from pathlib import Path

import pytest

from src.lector import leer_caso
from src.modelo import UtilidadLog, UtilidadTabla
from src.validacion import validar

CASOS_EJEMPLO = Path(__file__).resolve().parent.parent / "casos_ejemplo"
NAN = float("nan")
INF = float("inf")


def caso_valido():
    return {
        "N": 3,
        "k": 2,
        "B": 5,
        "universo": 4,
        "nodos": [
            {"id": 0, "cubre": [0, 1], "utilidad": {"tipo": "tabla", "valores": [0, 5, 8]}},
            {"id": 1, "cubre": [1, 2], "utilidad": {"tipo": "log", "a": 6.0, "b": 1.0}},
            {"id": 2, "cubre": [], "utilidad": {"tipo": "tabla", "valores": [0, 3]}},
        ],
    }


def _padre(datos, ruta):
    actual = datos
    for clave in ruta[:-1]:
        actual = actual[clave]
    return actual


def con(ruta, valor):
    """Caso válido con el campo de `ruta` reemplazado o añadido."""
    datos = caso_valido()
    _padre(datos, ruta)[ruta[-1]] = valor
    return datos


def sin(ruta):
    """Caso válido sin el campo de `ruta`."""
    datos = caso_valido()
    del _padre(datos, ruta)[ruta[-1]]
    return datos


def codigos(datos):
    return [error.codigo for error in validar(datos)]


TABLA = ("nodos", 0, "utilidad")
LOG = ("nodos", 1, "utilidad")


def test_caso_valido_no_tiene_errores():
    assert codigos(caso_valido()) == []


@pytest.mark.parametrize(
    "ruta",
    [
        ("N",),
        ("k",),
        ("B",),
        ("universo",),
        ("nodos",),
        ("nodos", 0, "id"),
        ("nodos", 0, "cubre"),
        ("nodos", 0, "utilidad"),
        TABLA + ("tipo",),
        TABLA + ("valores",),
        LOG + ("a",),
        LOG + ("b",),
    ],
)
def test_e01_campo_obligatorio_faltante(ruta):
    assert codigos(sin(ruta)) == ["E01"]


def test_e01_raiz_que_no_es_objeto():
    assert codigos([1, 2, 3]) == ["E01"]


@pytest.mark.parametrize(
    "ruta, valor",
    [
        (("N",), 10.5),
        (("N",), "3"),
        (("N",), True),
        (("k",), None),
        (("B",), 5.5),
        (("universo",), False),
        (("nombre",), 5),
        (("nodos",), "nodos"),
        (("nodos", 0), 3),
        (("nodos", 0, "id"), True),
        (("nodos", 0, "id"), 1.5),
        (("nodos", 0, "id"), None),
        (("nodos", 0, "cubre"), "0"),
        (("nodos", 0, "cubre", 0), 1.5),
        (("nodos", 0, "cubre", 0), True),
        (("nodos", 0, "utilidad"), 3),
        (TABLA + ("valores",), "0,5,8"),
        (TABLA + ("valores",), []),
        (TABLA + ("valores", 1), True),
        (TABLA + ("valores", 1), "5"),
        (LOG + ("a",), "6"),
        (LOG + ("b",), None),
        (("pesos_universo",), "1"),
        (("pesos_universo",), [1, True, 1, 1]),
    ],
)
def test_e02_tipo_incorrecto(ruta, valor):
    assert codigos(con(ruta, valor)) == ["E02"]


@pytest.mark.parametrize("ruta", [("N",), ("k",), ("B",), ("universo",)])
def test_real_con_valor_entero_se_acepta(ruta):
    valor = float(_padre(caso_valido(), ruta)[ruta[-1]])
    assert codigos(con(ruta, valor)) == []


@pytest.mark.parametrize(
    "ruta, valor",
    [
        (("N",), 0),
        (("k",), 0),
        (("k",), 3),
        (("k",), 4),
        (("B",), -1),
        (("universo",), -1),
    ],
)
def test_e03_rango_invalido(ruta, valor):
    assert codigos(con(ruta, valor)) == ["E03"]


def test_e03_un_solo_nodo_no_admite_k_valido():
    datos = con(("N",), 1)
    datos["k"] = 1
    datos["nodos"] = datos["nodos"][:1]
    assert codigos(datos) == ["E03"]


def test_e04_longitud_distinta_de_n():
    datos = con(("N",), 2)
    datos["k"] = 1
    assert codigos(datos) == ["E04"]


@pytest.mark.parametrize("primero, segundo", [(1, 1), (1, "1"), (1, 1.0), ("a", "a")])
def test_e04_ids_duplicados_al_comparar_como_texto(primero, segundo):
    datos = caso_valido()
    datos["nodos"][0]["id"] = primero
    datos["nodos"][1]["id"] = segundo
    assert codigos(datos) == ["E04"]


@pytest.mark.parametrize("cubre", [[4], [-1], [0, 0], [0, 0.0]])
def test_e05_cubre_invalido(cubre):
    assert codigos(con(("nodos", 0, "cubre"), cubre)) == ["E05"]


@pytest.mark.parametrize("pesos", [[1, 1, 1], [1, 1, 1, 1, 1], [1, -0.5, 1, 1]])
def test_e06_pesos_invalidos(pesos):
    assert codigos(con(("pesos_universo",), pesos)) == ["E06"]


def test_pesos_validos_se_aceptan():
    assert codigos(con(("pesos_universo",), [1, 0, 2.5, 1])) == []


def test_e07_utilidad_decreciente():
    assert codigos(con(TABLA + ("valores",), [0, 5, 3])) == ["E07"]


def test_e08_utilidad_no_concava():
    assert codigos(con(TABLA + ("valores",), [0, 1, 3])) == ["E08"]


def test_e07_y_e08_en_la_misma_tabla_se_reportan_ambos():
    assert codigos(con(TABLA + ("valores",), [5, 0, 10])) == ["E07", "E08"]


@pytest.mark.parametrize(
    "valores",
    [
        [7],
        [2, 5, 7],
        [0, 1, 1 - 1e-10],
        [0, 1, 2 + 1e-10],
    ],
)
def test_tablas_validas_incluida_la_tolerancia(valores):
    assert codigos(con(TABLA + ("valores",), valores)) == []


@pytest.mark.parametrize(
    "ruta, valor",
    [
        (("N",), NAN),
        (("B",), INF),
        (("nodos", 0, "id"), NAN),
        (("nodos", 0, "cubre", 0), INF),
        (TABLA + ("valores", 1), INF),
        (TABLA + ("valores", 1), 10**400),
        (("pesos_universo",), [1, NAN, 1, 1]),
        (LOG + ("a",), NAN),
        (LOG + ("b",), INF),
        (LOG + ("a",), -1),
        (LOG + ("b",), 0),
        (LOG + ("b",), -1),
    ],
)
def test_e09_numeros_no_finitos_y_parametros_log(ruta, valor):
    assert codigos(con(ruta, valor)) == ["E09"]


def test_e09_utilidad_log_que_desborda_al_evaluarse():
    datos = con(LOG + ("a",), 1e308)
    datos["nodos"][1]["utilidad"]["b"] = 1e308
    assert codigos(datos) == ["E09"]


@pytest.mark.parametrize("tipo", ["cuadratica", "TABLA", 5, None])
def test_e10_tipo_desconocido(tipo):
    assert codigos(con(TABLA + ("tipo",), tipo)) == ["E10"]


def test_se_reportan_todos_los_errores_sin_cascada():
    datos = caso_valido()
    datos["B"] = -1
    datos["nodos"][0]["cubre"] = [9]
    datos["nodos"][1]["utilidad"]["tipo"] = "otro"
    datos["nodos"][2]["utilidad"]["valores"] = [0, 1, 3]
    assert codigos(datos) == ["E03", "E05", "E10", "E08"]


def test_el_detalle_ubica_el_error():
    errores = validar(con(("nodos", 1, "cubre"), [9]))
    assert "nodos[1]" in errores[0].detalle


def test_campos_adicionales_se_ignoran():
    assert codigos(con(("extra",), NAN)) == []


def escribir(tmp_path, datos, nombre="caso.json"):
    ruta = tmp_path / nombre
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    return ruta


def test_lectura_json_mal_formado_da_e01(tmp_path):
    ruta = tmp_path / "roto.json"
    ruta.write_text("{ esto no es json", encoding="utf-8")
    leido = leer_caso(ruta)
    assert [e.codigo for e in leido.errores] == ["E01"]
    assert leido.caso is None
    assert leido.nombre == "roto"


def test_lectura_que_no_es_utf8_da_e01(tmp_path):
    ruta = tmp_path / "latin.json"
    ruta.write_bytes('{"nombre": "año"}'.encode("latin-1"))
    assert [e.codigo for e in leer_caso(ruta).errores] == ["E01"]


def test_lectura_acepta_utf8_con_bom(tmp_path):
    ruta = tmp_path / "bom.json"
    ruta.write_text(json.dumps(caso_valido()), encoding="utf-8-sig")
    assert leer_caso(ruta).errores == []


def test_lectura_detecta_nan_literal_como_e09(tmp_path):
    ruta = tmp_path / "nan.json"
    ruta.write_text(
        json.dumps(caso_valido()).replace('"a": 6.0', '"a": NaN'), encoding="utf-8"
    )
    assert [e.codigo for e in leer_caso(ruta).errores] == ["E09"]


def test_lectura_normaliza_enteros_e_ids(tmp_path):
    datos = caso_valido()
    datos["B"] = 5.0
    datos["nodos"][0]["id"] = 7.0
    datos["nodos"][1]["id"] = "b"
    datos["nodos"][0]["cubre"] = [0.0, 1]
    caso = leer_caso(escribir(tmp_path, datos)).caso
    assert caso.B == 5 and isinstance(caso.B, int)
    assert caso.nodos[0].id == 7 and isinstance(caso.nodos[0].id, int)
    assert caso.nodos[1].id == "b"
    assert caso.nodos[0].cubre == (0, 1)
    assert all(isinstance(e, int) for e in caso.nodos[0].cubre)


def test_pesos_por_defecto_valen_uno(tmp_path):
    caso = leer_caso(escribir(tmp_path, caso_valido())).caso
    assert caso.pesos_universo == (1.0, 1.0, 1.0, 1.0)


@pytest.mark.parametrize("universo", [10**12, 10**30, 1e308])
def test_universo_que_no_cabe_en_memoria_da_e03(tmp_path, universo):
    leido = leer_caso(escribir(tmp_path, con(("universo",), universo)))
    assert [e.codigo for e in leido.errores] == ["E03"]
    assert leido.caso is None


def test_pesos_dados_se_conservan_como_reales(tmp_path):
    datos = con(("pesos_universo",), [1, 0, 2.5, 1])
    caso = leer_caso(escribir(tmp_path, datos)).caso
    assert caso.pesos_universo == (1.0, 0.0, 2.5, 1.0)


@pytest.mark.parametrize(
    "nombre, esperado",
    [("Mi caso", "Mi caso"), (None, "archivo"), (5, "archivo"), ("", "archivo"), ("  ", "archivo")],
)
def test_nombre_cae_al_nombre_del_archivo(tmp_path, nombre, esperado):
    datos = caso_valido()
    if nombre is not None:
        datos["nombre"] = nombre
    assert leer_caso(escribir(tmp_path, datos, "archivo.json")).nombre == esperado


def test_utilidad_tabla_se_extiende_con_el_ultimo_valor():
    u = UtilidadTabla((0.0, 5.0, 8.0))
    assert u.valor(2) == 8.0
    assert u.valor(10) == 8.0
    assert u.ganancia(1) == 3.0
    assert u.ganancia(2) == 0.0
    assert u.ganancia(10) == 0.0


def test_utilidad_log_sigue_la_formula():
    u = UtilidadLog(6.0, 1.0)
    assert u.valor(0) == 0.0
    assert u.valor(2) == pytest.approx(6 * math.log(3))
    assert u.ganancia(2) == pytest.approx(6 * (math.log(4) - math.log(3)))


def test_ejemplo_01_se_lee_como_en_la_especificacion():
    leido = leer_caso(CASOS_EJEMPLO / "ejemplo_01.json")
    assert leido.errores == []
    assert leido.nombre == "ejemplo_01"
    caso = leido.caso
    assert (caso.N, caso.k, caso.B, caso.universo) == (4, 2, 5, 6)
    assert [nodo.id for nodo in caso.nodos] == [0, 1, 2, 3]
    assert caso.nodos[0].cubre == (0, 1, 2)
    log = caso.nodos[2].utilidad
    assert [round(log.ganancia(x), 4) for x in range(3)] == [4.1589, 2.4328, 1.7261]
    assert caso.nodos[0].utilidad.valor(3) + log.valor(2) == pytest.approx(16.5917, abs=5e-5)


def test_invalido_01_reporta_utilidad_no_concava():
    leido = leer_caso(CASOS_EJEMPLO / "invalido_01.json")
    assert [e.codigo for e in leido.errores] == ["E08"]
    assert leido.caso is None

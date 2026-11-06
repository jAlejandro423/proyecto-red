"""Pruebas del formato de entrada de la docente: detección, caso de referencia, validaciones y salida."""

import copy
import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

from src.conjunta import Cobertura, Influencia
from src.exactos import razon_seleccion, reparto_optimo, seleccion_optima, voraz_coincide
from src.lector import leer_caso
from src.modelo import UtilidadLog
from src.reparto import repartir
from src.seleccion import seleccionar
from src.validacion import es_formato_docente, validar

RAIZ = Path(__file__).resolve().parent.parent
CASO_DOCENTE = RAIZ / "casos_ejemplo" / "entrada_G2_red_15_nodos.json"


def docente_valido():
    return {
        "parametros": {
            "numero_nodos": 3,
            "numero_rondas": 2,
            "cupo_participantes_por_ronda_k": 2,
            "presupuesto_ruido_por_ronda_B": 6,
            "presupuesto_costos_participacion_por_ronda": 10,
        },
        "grafo": [
            {"u": "A", "v": "B", "peso_influencia": 0.5},
            {"u": "B", "v": "C", "peso_influencia": 0.25},
        ],
        "nodos": [
            {"id": "A", "coeficiente_utilidad": 4.0, "presupuesto_total_nodo": 2, "costo_participacion": 1},
            {"id": "B", "coeficiente_utilidad": 2.0, "presupuesto_total_nodo": 5, "costo_participacion": 2},
            {"id": "C", "coeficiente_utilidad": 3.0, "presupuesto_total_nodo": 0, "costo_participacion": 3},
        ],
    }


def codigos(datos):
    return [error.codigo for error in validar(datos)]


def escribir(tmp_path, datos, nombre="caso.json"):
    ruta = tmp_path / nombre
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    return ruta


# --- Detección ------------------------------------------------------------------


def test_detecta_el_formato_de_la_docente():
    assert es_formato_docente(docente_valido())
    assert es_formato_docente({"parametros": {}})
    assert es_formato_docente({"grafo": []})


def test_el_formato_propio_no_se_confunde():
    assert not es_formato_docente({"N": 2, "k": 1, "B": 0, "universo": 0, "nodos": []})
    assert not es_formato_docente([1, 2])


def test_el_caso_de_la_docente_es_valido():
    assert validar(json.loads(CASO_DOCENTE.read_text(encoding="utf-8"))) == []


def test_la_lectura_mapea_los_parametros():
    leido = leer_caso(CASO_DOCENTE)
    assert leido.errores == []
    assert leido.formato == "docente"
    caso = leido.caso
    assert (caso.N, caso.k, caso.B) == (15, 5, 30)
    assert leido.parametros == {"N": 15, "k": 5, "B": 30, "universo": None}
    assert isinstance(caso.conjunta, Influencia)
    assert caso.nodos[0].id == "N01"
    assert caso.nodos[0].utilidad == UtilidadLog(8.5, 1.0, tope=18)


def test_la_lectura_del_formato_propio_no_cambia():
    leido = leer_caso(RAIZ / "casos_ejemplo" / "ejemplo_01.json")
    assert leido.formato == "propio"
    assert leido.campos_no_usados is None
    assert isinstance(leido.caso.conjunta, Cobertura)


def test_el_nombre_es_el_del_archivo_si_no_viene(tmp_path):
    assert leer_caso(escribir(tmp_path, docente_valido(), "ronda.json")).nombre == "ronda"
    datos = docente_valido() | {"nombre": "mi ronda"}
    assert leer_caso(escribir(tmp_path, datos)).nombre == "mi ronda"


def test_los_campos_no_usados_se_reportan():
    leido = leer_caso(CASO_DOCENTE)
    no_usados = leido.campos_no_usados
    assert no_usados["nota"] == "variantes, entregas posteriores"
    assert no_usados["numero_rondas"] == 3
    assert no_usados["presupuesto_costos_participacion_por_ronda"] == 24
    assert no_usados["costo_participacion"]["N01"] == 3
    assert no_usados["costo_participacion"]["N15"] == 6
    assert len(no_usados["costo_participacion"]) == 15


def test_los_campos_no_usados_ausentes_se_omiten(tmp_path):
    datos = docente_valido()
    del datos["parametros"]["numero_rondas"]
    for nodo in datos["nodos"]:
        del nodo["costo_participacion"]
    no_usados = leer_caso(escribir(tmp_path, datos)).campos_no_usados
    assert no_usados == {
        "nota": "variantes, entregas posteriores",
        "presupuesto_costos_participacion_por_ronda": 10,
    }


def test_un_grafo_vacio_deja_solo_los_coeficientes(tmp_path):
    datos = docente_valido()
    datos["grafo"] = []
    caso = leer_caso(escribir(tmp_path, datos)).caso
    assert caso.conjunta.valor(caso, (0, 2)) == 7.0


# --- Caso de referencia de la docente -------------------------------------------


@pytest.fixture(scope="module")
def caso_docente():
    return leer_caso(CASO_DOCENTE).caso


def ids(caso, indices):
    return [caso.nodos[i].id for i in indices]


def test_seleccion_voraz_del_caso_docente(caso_docente):
    resultado = seleccionar(caso_docente)
    assert ids(caso_docente, resultado.indices) == ["N11", "N14", "N09", "N15", "N13"]
    assert resultado.utilidad_conjunta == pytest.approx(145.5795, abs=1e-4)


def test_optimo_por_fuerza_bruta_del_caso_docente(caso_docente):
    optimo = seleccion_optima(caso_docente)
    assert optimo == pytest.approx(145.9072, abs=1e-4)
    indices = [i for i, nodo in enumerate(caso_docente.nodos) if nodo.id in {"N09", "N11", "N12", "N13", "N15"}]
    assert caso_docente.conjunta.valor(caso_docente, indices) == pytest.approx(optimo)
    razon = razon_seleccion(seleccionar(caso_docente).utilidad_conjunta, optimo)
    assert razon == pytest.approx(0.99775, abs=1e-5)


def test_reparto_del_caso_docente(caso_docente):
    seleccion = seleccionar(caso_docente)
    reparto = repartir(caso_docente, seleccion.indices)
    asignacion = {caso_docente.nodos[i].id: x for i, x in reparto.asignacion.items()}
    assert asignacion == {"N11": 5, "N14": 7, "N09": 7, "N15": 6, "N13": 5}
    assert reparto.utilidad_total == pytest.approx(88.564, abs=1e-3)
    assert reparto.presupuesto_usado == 30
    optimo = reparto_optimo(caso_docente, seleccion.indices)
    assert voraz_coincide(reparto.utilidad_total, optimo, caso_docente.B)


def test_el_reparto_respeta_el_tope(tmp_path):
    # A tiene tope 2 y C tope 0: con B = 6 el voraz no puede pasar de esos topes.
    datos = docente_valido()
    datos["parametros"]["cupo_participantes_por_ronda_k"] = 3
    caso = leer_caso(escribir(tmp_path, datos)).caso
    reparto = repartir(caso, (0, 1, 2))
    assert reparto.asignacion == {0: 2, 1: 4, 2: 0}
    assert reparto.utilidad_total == pytest.approx(4 * math.log(3) + 2 * math.log(5))
    assert reparto.utilidad_total == pytest.approx(reparto_optimo(caso, (0, 1, 2)))


def test_el_tope_puede_dejar_presupuesto_sin_usar(tmp_path):
    datos = docente_valido()
    datos["parametros"]["presupuesto_ruido_por_ronda_B"] = 20
    datos["parametros"]["cupo_participantes_por_ronda_k"] = 3
    reparto = repartir(leer_caso(escribir(tmp_path, datos)).caso, (0, 1, 2))
    assert reparto.presupuesto_usado == 7
    assert reparto.presupuesto_sin_usar == 13


def test_k_igual_a_N_es_valido_en_el_formato_docente(tmp_path):
    datos = docente_valido()
    datos["parametros"]["cupo_participantes_por_ronda_k"] = 3
    leido = leer_caso(escribir(tmp_path, datos))
    assert leido.errores == []
    assert sorted(seleccionar(leido.caso).indices) == [0, 1, 2]


# --- Validaciones ---------------------------------------------------------------


def sin(datos, *ruta):
    actual = datos
    for clave in ruta[:-1]:
        actual = actual[clave]
    del actual[ruta[-1]]
    return datos


def con(datos, valor, *ruta):
    actual = datos
    for clave in ruta[:-1]:
        actual = actual[clave]
    actual[ruta[-1]] = valor
    return datos


def test_el_caso_minimo_es_valido():
    assert codigos(docente_valido()) == []


@pytest.mark.parametrize(
    "ruta",
    [
        ("parametros",),
        ("grafo",),
        ("nodos",),
        ("parametros", "numero_nodos"),
        ("parametros", "cupo_participantes_por_ronda_k"),
        ("parametros", "presupuesto_ruido_por_ronda_B"),
        ("grafo", 0, "u"),
        ("grafo", 0, "v"),
        ("grafo", 0, "peso_influencia"),
        ("nodos", 1, "id"),
        ("nodos", 1, "coeficiente_utilidad"),
        ("nodos", 1, "presupuesto_total_nodo"),
    ],
)
def test_E11_campo_obligatorio_faltante(ruta):
    datos = sin(docente_valido(), *ruta)
    assert "E11" in codigos(datos)


def test_E11_menciona_el_campo():
    errores = validar(sin(docente_valido(), "nodos", 1, "coeficiente_utilidad"))
    assert any("nodos[1]" in e.detalle and "coeficiente_utilidad" in e.detalle for e in errores)


def test_los_campos_no_usados_no_son_obligatorios():
    datos = docente_valido()
    del datos["parametros"]["numero_rondas"]
    del datos["parametros"]["presupuesto_costos_participacion_por_ronda"]
    for nodo in datos["nodos"]:
        del nodo["costo_participacion"]
    assert codigos(datos) == []


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("numero_nodos", 0),
        ("cupo_participantes_por_ronda_k", 0),
        ("cupo_participantes_por_ronda_k", 4),
        ("presupuesto_ruido_por_ronda_B", -1),
    ],
)
def test_E12_parametros_fuera_de_rango(campo, valor):
    assert "E12" in codigos(con(docente_valido(), valor, "parametros", campo))


@pytest.mark.parametrize("extremo", ["u", "v"])
def test_E13_arista_con_id_inexistente(extremo):
    errores = validar(con(docente_valido(), "Z", "grafo", 1, extremo))
    assert [e.codigo for e in errores] == ["E13"]
    assert "'Z'" in errores[0].detalle


def test_E13_compara_los_ids_como_texto():
    datos = docente_valido()
    datos["nodos"][0]["id"] = 1
    datos["grafo"][0]["u"] = "1"
    assert codigos(datos) == []


def test_E14_lazo():
    assert codigos(con(docente_valido(), "B", "grafo", 1, "v")) == ["E14"]


@pytest.mark.parametrize("u, v", [("A", "B"), ("B", "A")])
def test_E14_arista_repetida_en_cualquier_orden(u, v):
    datos = docente_valido()
    datos["grafo"].append({"u": u, "v": v, "peso_influencia": 0.1})
    assert codigos(datos) == ["E14"]


@pytest.mark.parametrize("peso", [-0.1, 1.5])
def test_E15_peso_fuera_de_rango(peso):
    assert codigos(con(docente_valido(), peso, "grafo", 0, "peso_influencia")) == ["E15"]


@pytest.mark.parametrize("peso", [0, 1, 0.0, 1.0])
def test_pesos_en_los_bordes_son_validos(peso):
    assert codigos(con(docente_valido(), peso, "grafo", 0, "peso_influencia")) == []


def test_E16_coeficiente_negativo():
    assert codigos(con(docente_valido(), -1.0, "nodos", 0, "coeficiente_utilidad")) == ["E16"]


def test_E17_tope_negativo():
    assert codigos(con(docente_valido(), -2, "nodos", 0, "presupuesto_total_nodo")) == ["E17"]


@pytest.mark.parametrize(
    "ruta, valor",
    [
        (("parametros",), [1, 2]),
        (("grafo",), {"u": "A"}),
        (("nodos",), "A"),
        (("grafo", 0), "A-B"),
        (("nodos", 0), 7),
        (("parametros", "numero_nodos"), "3"),
        (("parametros", "presupuesto_ruido_por_ronda_B"), 6.5),
        (("parametros", "cupo_participantes_por_ronda_k"), True),
        (("grafo", 0, "u"), ["A"]),
        (("grafo", 0, "peso_influencia"), "0.5"),
        (("nodos", 0, "coeficiente_utilidad"), None),
        (("nodos", 0, "presupuesto_total_nodo"), 2.5),
        (("nodos", 0, "id"), True),
    ],
)
def test_E02_tipos_incorrectos(ruta, valor):
    assert "E02" in codigos(con(docente_valido(), valor, *ruta))


def test_los_reales_con_valor_entero_se_aceptan():
    datos = docente_valido()
    datos["parametros"]["presupuesto_ruido_por_ronda_B"] = 6.0
    datos["nodos"][0]["presupuesto_total_nodo"] = 2.0
    assert codigos(datos) == []


def test_E04_cantidad_de_nodos_distinta_de_N():
    assert "E04" in codigos(con(docente_valido(), 4, "parametros", "numero_nodos"))


def test_E04_ids_repetidos():
    assert "E04" in codigos(con(docente_valido(), "A", "nodos", 2, "id"))


@pytest.mark.parametrize(
    "ruta",
    [("grafo", 0, "peso_influencia"), ("nodos", 0, "coeficiente_utilidad")],
)
def test_E09_numero_no_finito(ruta):
    assert codigos(con(docente_valido(), float("nan"), *ruta)) == ["E09"]


def test_E09_coeficiente_que_desborda():
    assert codigos(con(docente_valido(), 1e308, "nodos", 1, "coeficiente_utilidad")) == ["E09"]


def test_E01_raiz_que_no_es_objeto_sigue_igual():
    assert codigos([docente_valido()]) == ["E01"]


def test_reporta_todos_los_errores_a_la_vez():
    datos = docente_valido()
    datos["grafo"][0]["peso_influencia"] = 2
    datos["grafo"][1]["v"] = "Z"
    datos["nodos"][2]["presupuesto_total_nodo"] = -1
    assert sorted(codigos(datos)) == ["E13", "E15", "E17"]


def test_sin_errores_en_cascada_si_nodos_es_invalido():
    # Sin una lista de nodos válida no se puede saber qué ids existen: no se reporta E13.
    assert codigos(con(docente_valido(), "x", "nodos")) == ["E02"]


def test_un_caso_invalido_no_se_construye(tmp_path):
    leido = leer_caso(escribir(tmp_path, con(docente_valido(), 3, "grafo", 0, "peso_influencia")))
    assert leido.caso is None
    assert [e.codigo for e in leido.errores] == ["E15"]
    assert leido.parametros == {"N": 3, "k": 2, "B": 6, "universo": None}


# --- Salida por la CLI ----------------------------------------------------------


def ejecutar(*argumentos):
    return subprocess.run(
        [sys.executable, str(RAIZ / "main.py"), *map(str, argumentos)],
        capture_output=True,
        cwd=RAIZ,
        encoding="utf-8",
        errors="replace",
    )


@pytest.fixture(scope="module")
def salida_docente(tmp_path_factory):
    salida = tmp_path_factory.mktemp("salida")
    proceso = ejecutar("--input", CASO_DOCENTE, "--output", salida, "--verificar")
    assert proceso.returncode == 0, proceso.stderr
    carpeta = salida / "entrada_G2_red_15_nodos"
    resultado = json.loads((carpeta / "resultado.json").read_text(encoding="utf-8"))
    traza = json.loads((carpeta / "traza.json").read_text(encoding="utf-8"))
    with open(salida / "resumen.csv", encoding="utf-8", newline="") as archivo:
        resumen = list(csv.DictReader(archivo))
    return resultado, traza, resumen


def test_resultado_del_caso_docente(salida_docente):
    resultado, _, _ = salida_docente
    assert resultado["caso"] == "entrada_G2_red_15_nodos"
    assert resultado["estado"] == "ok"
    assert resultado["formato"] == "docente"
    assert list(resultado)[:3] == ["caso", "estado", "formato"]
    assert resultado["parametros"] == {"N": 15, "k": 5, "B": 30, "universo": None}
    assert resultado["seleccion"] == {
        "nodos": ["N11", "N14", "N09", "N15", "N13"],
        "utilidad_conjunta": 145.5795,
    }
    assert resultado["reparto"]["asignacion"] == {"N11": 5, "N14": 7, "N09": 7, "N15": 6, "N13": 5}
    assert resultado["reparto"]["utilidad_total"] == 88.564
    assert resultado["verificacion_optimo"] == {
        "parte2": {"f_optimo": 145.9072, "razon": 0.9978, "cumple_cota_1_menos_1_e": True},
        "parte1": {"utilidad_optima": 88.564, "voraz_es_optimo": True},
    }


def test_restricciones_del_caso_docente(salida_docente):
    resultado, _, _ = salida_docente
    restricciones = resultado["verificacion_restricciones"]
    assert restricciones["asignacion_respeta_topes"] is True
    assert all(restricciones.values())


def test_campos_no_usados_en_la_salida(salida_docente):
    resultado, _, _ = salida_docente
    assert list(resultado)[-2:] == ["campos_no_usados", "tiempos_ms"]
    no_usados = resultado["campos_no_usados"]
    assert no_usados["nota"] == "variantes, entregas posteriores"
    assert no_usados["numero_rondas"] == 3
    assert no_usados["costo_participacion"]["N13"] == 7


def test_traza_del_caso_docente(salida_docente):
    _, traza, _ = salida_docente
    assert [paso["elegido"] for paso in traza["seleccion"]] == ["N11", "N14", "N09", "N15", "N13"]
    assert len(traza["seleccion"][0]["ganancias"]) == 15
    assert len(traza["seleccion"][4]["ganancias"]) == 11
    assert set(traza["reparto"][0]) == {
        "unidad", "candidatos", "asignada_a", "ganancia", "x_nuevo", "utilidad_acumulada",
    }
    assert len(traza["reparto"]) == 30


def test_resumen_del_caso_docente(salida_docente):
    _, _, resumen = salida_docente
    assert len(resumen) == 1
    fila = resumen[0]
    assert (fila["N"], fila["k"], fila["B"], fila["universo"]) == ("15", "5", "30", "")
    assert fila["f_S"] == "145.5795"
    assert fila["razon_optimo"] == "0.9978"


def test_el_formato_propio_no_lleva_campos_nuevos(tmp_path):
    proceso = ejecutar("--input", RAIZ / "casos_ejemplo" / "ejemplo_01.json", "--output", tmp_path)
    assert proceso.returncode == 0
    resultado = json.loads((tmp_path / "ejemplo_01" / "resultado.json").read_text(encoding="utf-8"))
    assert "formato" not in resultado
    assert "campos_no_usados" not in resultado
    assert "asignacion_respeta_topes" not in resultado["verificacion_restricciones"]


def test_una_carpeta_mezcla_los_dos_formatos(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    (entrada / "docente.json").write_text(json.dumps(docente_valido()), encoding="utf-8")
    (entrada / "propio.json").write_bytes((RAIZ / "casos_ejemplo" / "ejemplo_01.json").read_bytes())
    malo = con(docente_valido(), "Z", "grafo", 0, "u")
    (entrada / "roto.json").write_text(json.dumps(malo), encoding="utf-8")
    proceso = ejecutar("--input", entrada, "--output", tmp_path / "salida")
    assert proceso.returncode == 1
    assert "docente: ok" in proceso.stdout
    assert "propio: ok" in proceso.stdout
    assert "roto: invalido" in proceso.stdout
    assert "E13" in proceso.stdout

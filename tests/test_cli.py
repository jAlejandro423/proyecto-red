"""Pruebas de la salida y de la CLI."""

import csv
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from src.salida import nombres_carpetas, redondear, sanitizar

RAIZ = Path(__file__).resolve().parent.parent
CASOS_EJEMPLO = RAIZ / "casos_ejemplo"


def ejecutar(*argumentos, cwd=RAIZ):
    return subprocess.run(
        [sys.executable, str(RAIZ / "main.py"), *map(str, argumentos)],
        capture_output=True,
        cwd=cwd,
        encoding="utf-8",
        errors="replace",
    )


def leer_json(ruta):
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def leer_resumen(salida):
    with open(Path(salida) / "resumen.csv", encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def caso_valido(**cambios):
    caso = {
        "N": 2,
        "k": 1,
        "B": 2,
        "universo": 2,
        "nodos": [
            {"id": 0, "cubre": [0], "utilidad": {"tipo": "tabla", "valores": [0, 2, 3]}},
            {"id": 1, "cubre": [1], "utilidad": {"tipo": "tabla", "valores": [0, 1, 2]}},
        ],
    }
    caso.update(cambios)
    return caso


def escribir_caso(carpeta, nombre, datos=None):
    ruta = Path(carpeta) / nombre
    ruta.write_text(json.dumps(datos if datos is not None else caso_valido()), encoding="utf-8")
    return ruta


@pytest.fixture
def entrada(tmp_path):
    carpeta = tmp_path / "entrada"
    carpeta.mkdir()
    return carpeta


@pytest.fixture
def salida(tmp_path):
    return tmp_path / "salida"


# Nombres de carpeta


@pytest.mark.parametrize(
    "nombre, esperado",
    [
        ("normal", "normal"),
        ('a<b>c:d"e/f\\g|h?i*j', "a_b_c_d_e_f_g_h_i_j"),
        ("con\x01control", "con_control"),
        ("fin. . ", "fin"),
        ("...", "caso"),
        ("", "caso"),
        ("CON", "_CON"),
        ("nul", "_nul"),
        ("COM1", "_COM1"),
        ("lpt9", "_lpt9"),
        ("CON.datos", "_CON.datos"),
        ("COM10", "COM10"),
        ("consola", "consola"),
    ],
)
def test_sanitizar(nombre, esperado):
    assert sanitizar(nombre) == esperado


def test_las_colisiones_sin_distinguir_mayusculas_reciben_sufijo():
    assert nombres_carpetas(["a", "A", "a"]) == ["a", "A_2", "a_3"]


def test_un_sufijo_no_choca_con_otro_nombre_existente():
    assert nombres_carpetas(["a", "A", "a_2"]) == ["a", "A_2", "a_2_2"]


def test_la_carpeta_de_un_caso_no_choca_con_el_resumen():
    assert nombres_carpetas(["RESUMEN.csv"]) == ["RESUMEN.csv_2"]


# Redondeo


def test_redondear_recorre_listas_y_diccionarios():
    assert redondear({"a": [1.23456, {"b": 2.00001}]}) == {"a": [1.2346, {"b": 2.0}]}


def test_redondear_conserva_enteros_textos_y_booleanos():
    assert redondear({"a": 3, "b": "x", "c": True, "d": None}) == {"a": 3, "b": "x", "c": True, "d": None}
    assert isinstance(redondear(3), int)


def test_redondear_no_deja_cero_negativo():
    assert math.copysign(1.0, redondear(-1e-9)) == 1.0


# Caso válido


def test_ejemplo_01_produce_el_resultado_de_la_especificacion(salida):
    proceso = ejecutar("--input", CASOS_EJEMPLO / "ejemplo_01.json", "--output", salida, "--verificar")
    assert proceso.returncode == 0, proceso.stderr
    resultado = leer_json(salida / "ejemplo_01" / "resultado.json")
    tiempos = resultado.pop("tiempos_ms")
    assert resultado == {
        "caso": "ejemplo_01",
        "estado": "ok",
        "parametros": {"N": 4, "k": 2, "B": 5, "universo": 6},
        "seleccion": {"nodos": [0, 2], "utilidad_conjunta": 6.0},
        "reparto": {
            "asignacion": {"0": 3, "2": 2},
            "utilidad_total": 16.5917,
            "presupuesto_usado": 5,
            "presupuesto_sin_usar": 0,
        },
        "verificacion_restricciones": {
            "seleccion_tiene_k_nodos": True,
            "seleccion_sin_repetidos": True,
            "suma_asignacion_menor_igual_B": True,
            "asignacion_solo_a_seleccionados": True,
            "asignaciones_no_negativas": True,
        },
        "verificacion_optimo": {
            "parte2": {"f_optimo": 6.0, "razon": 1.0, "cumple_cota_1_menos_1_e": True},
            "parte1": {"utilidad_optima": 16.5917, "voraz_es_optimo": True},
        },
    }
    assert list(tiempos) == ["seleccion", "reparto", "total", "repeticiones", "estadistico"]
    assert tiempos["repeticiones"] == 5
    assert tiempos["estadistico"] == "mediana"
    assert all(tiempos[clave] > 0 for clave in ("seleccion", "reparto", "total"))


def test_ejemplo_01_produce_la_traza_de_la_especificacion(salida):
    ejecutar("--input", CASOS_EJEMPLO / "ejemplo_01.json", "--output", salida)
    traza = leer_json(salida / "ejemplo_01" / "traza.json")
    assert traza["seleccion"][0] == {
        "paso": 1,
        "ganancias": {"0": 3.0, "1": 2.0, "2": 3.0, "3": 2.0},
        "elegido": 0,
        "ganancia": 3.0,
        "utilidad_acumulada": 3.0,
    }
    assert traza["reparto"][0] == {
        "unidad": 1,
        "candidatos": {"0": 5.0, "2": 4.1589},
        "asignada_a": 0,
        "ganancia": 5.0,
        "x_nuevo": 1,
        "utilidad_acumulada": 5.0,
    }
    assert len(traza["reparto"]) == 5


def test_los_reales_se_escriben_como_reales(entrada, salida):
    escribir_caso(entrada, "c.json")
    ejecutar("--input", entrada, "--output", salida)
    texto = (salida / "c" / "resultado.json").read_text(encoding="utf-8")
    assert '"utilidad_conjunta": 1.0' in texto
    assert '"utilidad_total": 3.0' in texto
    assert leer_resumen(salida)[0]["f_S"] == "1.0"


def test_los_tiempos_tienen_a_lo_sumo_6_decimales(salida):
    ejecutar("--input", CASOS_EJEMPLO / "ejemplo_01.json", "--output", salida)
    tiempos = leer_json(salida / "ejemplo_01" / "resultado.json")["tiempos_ms"]
    for clave in ("seleccion", "reparto", "total"):
        assert tiempos[clave] == round(tiempos[clave], 6)


def test_conserva_el_tipo_del_id_y_usa_texto_en_las_claves(entrada, salida):
    datos = caso_valido()
    datos["nodos"][0]["id"] = "a"
    datos["nodos"][1]["id"] = 7
    escribir_caso(entrada, "c.json", datos)
    ejecutar("--input", entrada, "--output", salida)
    resultado = leer_json(salida / "c" / "resultado.json")
    assert resultado["seleccion"]["nodos"] == ["a"]
    assert resultado["reparto"]["asignacion"] == {"a": 2}
    traza = leer_json(salida / "c" / "traza.json")
    assert traza["seleccion"][0]["ganancias"] == {"a": 1.0, "7": 1.0}
    assert traza["seleccion"][0]["elegido"] == "a"


def test_el_campo_caso_usa_el_nombre_y_el_csv_la_carpeta(entrada, salida):
    escribir_caso(entrada, "archivo.json", caso_valido(nombre="Mi caso"))
    ejecutar("--input", entrada, "--output", salida)
    assert leer_json(salida / "archivo" / "resultado.json")["caso"] == "Mi caso"
    assert leer_resumen(salida)[0]["caso"] == "archivo"


# Opciones


def test_sin_verificar_la_verificacion_es_null_y_la_razon_queda_vacia(entrada, salida):
    escribir_caso(entrada, "c.json")
    ejecutar("--input", entrada, "--output", salida)
    assert leer_json(salida / "c" / "resultado.json")["verificacion_optimo"] is None
    assert leer_resumen(salida)[0]["razon_optimo"] == ""


def test_con_verificar_la_razon_llega_al_resumen(entrada, salida):
    escribir_caso(entrada, "c.json")
    ejecutar("--input", entrada, "--output", salida, "--verificar")
    assert leer_resumen(salida)[0]["razon_optimo"] == "1.0"


def test_la_razon_es_real_y_refleja_al_voraz_suboptimo(entrada, salida):
    tabla = {"tipo": "tabla", "valores": [0, 1]}
    datos = {
        "N": 3,
        "k": 2,
        "B": 1,
        "universo": 6,
        "nodos": [
            {"id": 0, "cubre": [0, 1, 2, 3], "utilidad": tabla},
            {"id": 1, "cubre": [0, 1, 4], "utilidad": tabla},
            {"id": 2, "cubre": [2, 3, 5], "utilidad": tabla},
        ],
    }
    escribir_caso(entrada, "c.json", datos)
    ejecutar("--input", entrada, "--output", salida, "--verificar")
    parte2 = leer_json(salida / "c" / "resultado.json")["verificacion_optimo"]["parte2"]
    assert parte2 == {"f_optimo": 6.0, "razon": 0.8333, "cumple_cota_1_menos_1_e": True}


def test_parte_2_omitida_por_tamano(entrada, salida):
    nodos = [
        {"id": i, "cubre": [], "utilidad": {"tipo": "tabla", "valores": [0, 1]}} for i in range(25)
    ]
    escribir_caso(entrada, "c.json", {"N": 25, "k": 12, "B": 1, "universo": 0, "nodos": nodos})
    proceso = ejecutar("--input", entrada, "--output", salida, "--verificar")
    assert proceso.returncode == 0, proceso.stderr
    verificacion = leer_json(salida / "c" / "resultado.json")["verificacion_optimo"]
    assert verificacion["parte2"]["omitida"] is True
    assert verificacion["parte2"]["motivo"]
    assert verificacion["parte1"]["voraz_es_optimo"] is True
    assert leer_resumen(salida)[0]["razon_optimo"] == ""


def test_parte_1_omitida_por_tamano(entrada, salida):
    escribir_caso(entrada, "c.json", caso_valido(B=3163))
    proceso = ejecutar("--input", entrada, "--output", salida, "--verificar")
    assert proceso.returncode == 0, proceso.stderr
    verificacion = leer_json(salida / "c" / "resultado.json")["verificacion_optimo"]
    assert verificacion["parte1"]["omitida"] is True
    assert verificacion["parte1"]["motivo"]
    assert verificacion["parte2"]["razon"] == 1.0
    assert leer_resumen(salida)[0]["razon_optimo"] == "1.0"


def test_traza_resumen_omite_ganancias_de_la_parte_2_y_no_toca_la_parte_1(entrada, salida):
    escribir_caso(entrada, "c.json")
    ejecutar("--input", entrada, "--output", salida, "--traza", "resumen")
    traza = leer_json(salida / "c" / "traza.json")
    assert "ganancias" not in traza["seleccion"][0]
    assert "candidatos" in traza["reparto"][0]


def test_traza_ninguna_no_genera_el_archivo(entrada, salida):
    escribir_caso(entrada, "c.json")
    ejecutar("--input", entrada, "--output", salida, "--traza", "ninguna")
    assert (salida / "c" / "resultado.json").exists()
    assert not (salida / "c" / "traza.json").exists()


def test_una_traza_anterior_no_sobrevive_a_traza_ninguna(entrada, salida):
    escribir_caso(entrada, "c.json")
    ejecutar("--input", entrada, "--output", salida)
    ejecutar("--input", entrada, "--output", salida, "--traza", "ninguna")
    assert not (salida / "c" / "traza.json").exists()


def test_repeticiones_se_reporta(entrada, salida):
    escribir_caso(entrada, "c.json")
    ejecutar("--input", entrada, "--output", salida, "--repeticiones", 3)
    assert leer_json(salida / "c" / "resultado.json")["tiempos_ms"]["repeticiones"] == 3


@pytest.mark.parametrize("valor", ["0", "-1", "dos"])
def test_repeticiones_invalidas_dan_codigo_2(entrada, salida, valor):
    escribir_caso(entrada, "c.json")
    proceso = ejecutar("--input", entrada, "--output", salida, "--repeticiones", valor)
    assert proceso.returncode == 2
    assert not salida.exists()


# Casos inválidos y lote


def test_caso_invalido_reporta_errores_sin_traza(salida):
    proceso = ejecutar("--input", CASOS_EJEMPLO / "invalido_01.json", "--output", salida)
    assert proceso.returncode == 1
    resultado = leer_json(salida / "invalido_01" / "resultado.json")
    assert list(resultado) == ["caso", "estado", "errores"]
    assert resultado["caso"] == "invalido_01"
    assert resultado["estado"] == "invalido"
    assert {error["codigo"] for error in resultado["errores"]} == {"E08"}
    assert not (salida / "invalido_01" / "traza.json").exists()
    assert "E08" in proceso.stdout


def test_el_resumen_de_un_invalido_conserva_los_datos_que_se_pudieron_leer(salida):
    ejecutar("--input", CASOS_EJEMPLO / "invalido_01.json", "--output", salida)
    fila = leer_resumen(salida)[0]
    assert (fila["caso"], fila["estado"]) == ("invalido_01", "invalido")
    assert (fila["N"], fila["k"], fila["B"], fila["universo"]) == ("3", "2", "4", "4")
    assert fila["f_S"] == fila["utilidad_total"] == fila["t_total_ms"] == fila["razon_optimo"] == ""


def test_el_resumen_deja_vacios_los_parametros_que_no_se_pudieron_leer(entrada, salida):
    escribir_caso(entrada, "c.json", {"N": "x", "k": 1})
    (entrada / "roto.json").write_text("{no es json", encoding="utf-8")
    ejecutar("--input", entrada, "--output", salida)
    c, roto = leer_resumen(salida)
    assert (c["N"], c["k"], c["B"]) == ("", "1", "")
    assert roto["N"] == ""
    assert leer_json(salida / "roto" / "resultado.json")["errores"][0]["codigo"] == "E01"


def test_un_lote_mixto_no_se_cae_y_procesa_todo_en_orden_alfabetico(entrada, salida):
    escribir_caso(entrada, "b_valido.json")
    (entrada / "a_roto.json").write_text("{", encoding="utf-8")
    escribir_caso(entrada, "c_invalido.json", caso_valido(k=5))
    escribir_caso(entrada, "D_valido.json")
    proceso = ejecutar("--input", entrada, "--output", salida)
    assert proceso.returncode == 1
    assert [(fila["caso"], fila["estado"]) for fila in leer_resumen(salida)] == [
        ("a_roto", "invalido"),
        ("b_valido", "ok"),
        ("c_invalido", "invalido"),
        ("D_valido", "ok"),
    ]


def test_el_encabezado_del_resumen_es_el_de_la_especificacion(entrada, salida):
    escribir_caso(entrada, "c.json")
    ejecutar("--input", entrada, "--output", salida)
    primera = (salida / "resumen.csv").read_text(encoding="utf-8").splitlines()[0]
    assert primera == (
        "caso,estado,N,k,B,universo,f_S,utilidad_total,presupuesto_usado,"
        "t_seleccion_ms,t_reparto_ms,t_total_ms,razon_optimo"
    )


def test_un_error_inesperado_no_tumba_el_lote(entrada, salida):
    # Pasa la validación, pero el valor desborda y no se puede escribir como JSON.
    datos = caso_valido()
    datos["nodos"][0]["utilidad"] = {"tipo": "tabla", "valores": [-1.7e308, 1.7e308]}
    escribir_caso(entrada, "a_desborda.json", datos)
    escribir_caso(entrada, "b_valido.json")
    proceso = ejecutar("--input", entrada, "--output", salida)
    assert proceso.returncode == 1
    assert "Traceback" not in proceso.stderr
    resultado = leer_json(salida / "a_desborda" / "resultado.json")
    assert resultado["estado"] == "error"
    assert resultado["errores"][0]["codigo"] == "INTERNO"
    assert not (salida / "a_desborda" / "traza.json").exists()
    assert [fila["estado"] for fila in leer_resumen(salida)] == ["error", "ok"]


def test_nombres_que_la_consola_no_puede_mostrar_no_tumban_el_lote(entrada, salida):
    escribir_caso(entrada, "caso_\U0001f600.json", {"N": 1})
    escribir_caso(entrada, "z.json")
    proceso = ejecutar("--input", entrada, "--output", salida)
    assert proceso.returncode == 1
    assert "Traceback" not in proceso.stderr
    assert len(leer_resumen(salida)) == 2


# Entrada y códigos de salida


def test_entrada_inexistente_da_codigo_2(tmp_path, salida):
    proceso = ejecutar("--input", tmp_path / "no_existe", "--output", salida)
    assert proceso.returncode == 2
    assert "no_existe" in proceso.stderr
    assert not salida.exists()


def test_carpeta_sin_json_da_codigo_2(entrada, salida):
    (entrada / "notas.txt").write_text("x", encoding="utf-8")
    proceso = ejecutar("--input", entrada, "--output", salida)
    assert proceso.returncode == 2
    assert proceso.stderr
    assert not salida.exists()


def test_salida_no_escribible_da_codigo_2(entrada, tmp_path):
    escribir_caso(entrada, "c.json")
    archivo = tmp_path / "soy_un_archivo"
    archivo.write_text("x", encoding="utf-8")
    proceso = ejecutar("--input", entrada, "--output", archivo)
    assert proceso.returncode == 2
    assert "Traceback" not in proceso.stderr


@pytest.mark.parametrize("argumentos", [["--input", "x"], ["--output", "x"], []])
def test_input_y_output_son_obligatorios(argumentos):
    assert ejecutar(*argumentos).returncode == 2


def test_las_subcarpetas_y_otros_archivos_se_ignoran(entrada, salida):
    escribir_caso(entrada, "c.json")
    (entrada / "notas.txt").write_text("x", encoding="utf-8")
    subcarpeta = entrada / "sub"
    subcarpeta.mkdir()
    escribir_caso(subcarpeta, "oculto.json")
    (entrada / "carpeta.json").mkdir()
    proceso = ejecutar("--input", entrada, "--output", salida)
    assert proceso.returncode == 0, proceso.stderr
    assert [fila["caso"] for fila in leer_resumen(salida)] == ["c"]


def test_la_carpeta_de_salida_usa_el_nombre_sanitizado_con_sufijo(entrada, salida):
    escribir_caso(entrada, "a b. .json")
    escribir_caso(entrada, "CON.json")
    proceso = ejecutar("--input", entrada, "--output", salida)
    assert proceso.returncode == 0, proceso.stderr
    assert (salida / "a b" / "resultado.json").exists()
    assert (salida / "_CON" / "resultado.json").exists()


def test_funciona_desde_otra_carpeta_con_rutas_relativas(tmp_path):
    shutil.copy(CASOS_EJEMPLO / "ejemplo_01.json", tmp_path / "ejemplo_01.json")
    proceso = ejecutar("--input", "ejemplo_01.json", "--output", "res", cwd=tmp_path)
    assert proceso.returncode == 0, proceso.stderr
    assert (tmp_path / "res" / "ejemplo_01" / "resultado.json").exists()
    assert (tmp_path / "res" / "resumen.csv").exists()


def test_dos_ejecuciones_producen_archivos_identicos_salvo_tiempos(tmp_path):
    def sin_tiempos(salida):
        resultado = leer_json(salida / "ejemplo_01" / "resultado.json")
        resultado.pop("tiempos_ms")
        return resultado

    primera, segunda = tmp_path / "1", tmp_path / "2"
    for salida in (primera, segunda):
        ejecutar("--input", CASOS_EJEMPLO, "--output", salida, "--verificar")
    assert sin_tiempos(primera) == sin_tiempos(segunda)
    for caso, archivo in (("ejemplo_01", "traza.json"), ("invalido_01", "resultado.json")):
        assert (primera / caso / archivo).read_bytes() == (segunda / caso / archivo).read_bytes()

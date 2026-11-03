"""Pruebas del generador de instancias."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from generar import generar_caso
from src.exactos import COTA_SELECCION, razon_seleccion, reparto_optimo, seleccion_optima, voraz_coincide
from src.lector import leer_caso
from src.reparto import repartir
from src.seleccion import seleccionar
from src.validacion import validar

RAIZ = Path(__file__).resolve().parent.parent
LIMITE_TABLA = 50


def ejecutar(script, *argumentos):
    return subprocess.run(
        [sys.executable, str(RAIZ / script), *map(str, argumentos)],
        capture_output=True,
        cwd=RAIZ,
        encoding="utf-8",
        errors="replace",
    )


def generar(salida, N=6, k=2, B=10, universo=8, semilla=1):
    return ejecutar(
        "generar.py", "--N", N, "--k", k, "--B", B, "--universo", universo, "--semilla", semilla, "--salida", salida
    )


# Contenido


@pytest.mark.parametrize(
    "N, k, B, universo",
    [(2, 1, 0, 0), (2, 1, 1, 1), (5, 4, 3, 2), (50, 10, 200, 100), (10, 3, 10**6, 20)],
)
@pytest.mark.parametrize("semilla", range(5))
def test_lo_generado_pasa_la_validacion(N, k, B, universo, semilla):
    assert validar(generar_caso(N, k, B, universo, semilla)) == []


def test_respeta_los_parametros():
    caso = generar_caso(N=6, k=2, B=10, universo=8, semilla=1)
    assert (caso["N"], caso["k"], caso["B"], caso["universo"]) == (6, 2, 10, 8)
    assert [nodo["id"] for nodo in caso["nodos"]] == list(range(6))
    assert len(caso["pesos_universo"]) == 8


def test_el_nombre_identifica_los_parametros():
    assert generar_caso(6, 2, 10, 8, 1)["nombre"] == "gen_N6_k2_B10_U8_s1"


def test_cubre_a_lo_sumo_la_mitad_del_universo_en_orden():
    for semilla in range(20):
        for nodo in generar_caso(10, 3, 5, 9, semilla)["nodos"]:
            assert len(nodo["cubre"]) <= 4
            assert nodo["cubre"] == sorted(nodo["cubre"])


def test_las_tablas_no_crecen_con_b():
    nodos = generar_caso(40, 3, 10**9, 4, 1)["nodos"]
    tablas = [nodo["utilidad"] for nodo in nodos if nodo["utilidad"]["tipo"] == "tabla"]
    assert tablas
    assert all(len(tabla["valores"]) <= LIMITE_TABLA + 1 for tabla in tablas)


def test_produce_los_dos_tipos_y_tablas_mas_cortas_que_b():
    nodos = generar_caso(40, 3, 10, 4, 1)["nodos"]
    utilidades = [nodo["utilidad"] for nodo in nodos]
    assert {utilidad["tipo"] for utilidad in utilidades} == {"tabla", "log"}
    assert any(len(u["valores"]) <= 10 for u in utilidades if u["tipo"] == "tabla")


def test_la_misma_semilla_da_el_mismo_caso():
    assert generar_caso(10, 3, 20, 15, 7) == generar_caso(10, 3, 20, 15, 7)


def test_otra_semilla_da_otro_caso():
    assert generar_caso(10, 3, 20, 15, 7)["nodos"] != generar_caso(10, 3, 20, 15, 8)["nodos"]


def test_el_voraz_cumple_sobre_lo_generado(tmp_path):
    ruta = tmp_path / "caso.json"
    for semilla in range(50):
        ruta.write_text(json.dumps(generar_caso(8, 3, 15, 12, semilla)), encoding="utf-8")
        caso = leer_caso(ruta).caso
        seleccion = seleccionar(caso)
        razon = razon_seleccion(seleccion.utilidad_conjunta, seleccion_optima(caso))
        assert razon >= COTA_SELECCION
        reparto = repartir(caso, seleccion.indices)
        assert voraz_coincide(reparto.utilidad_total, reparto_optimo(caso, seleccion.indices), caso.B)


# CLI


def test_escribe_el_archivo_con_el_nombre_de_la_especificacion(tmp_path):
    salida = tmp_path / "a" / "casos"
    proceso = generar(salida, N=50, k=10, B=200, universo=100, semilla=42)
    assert proceso.returncode == 0, proceso.stderr
    ruta = salida / "gen_N50_k10_B200_U100_s42.json"
    assert ruta.exists()
    assert str(ruta.name) in proceso.stdout


def test_el_archivo_es_lo_que_devuelve_generar_caso(tmp_path):
    generar(tmp_path)
    ruta = tmp_path / "gen_N6_k2_B10_U8_s1.json"
    assert json.loads(ruta.read_text(encoding="utf-8")) == generar_caso(6, 2, 10, 8, 1)


def test_el_archivo_tiene_un_nodo_por_linea(tmp_path):
    generar(tmp_path)
    texto = (tmp_path / "gen_N6_k2_B10_U8_s1.json").read_text(encoding="utf-8")
    assert [linea.count('"id"') for linea in texto.splitlines()].count(1) == 6
    assert texto.count('"id"') == 6
    assert texto.endswith("\n")


def test_dos_ejecuciones_dan_archivos_identicos(tmp_path):
    generar(tmp_path / "1")
    generar(tmp_path / "2")
    nombre = "gen_N6_k2_B10_U8_s1.json"
    assert (tmp_path / "1" / nombre).read_bytes() == (tmp_path / "2" / nombre).read_bytes()


@pytest.mark.parametrize(
    "cambio",
    [{"N": 0}, {"k": 0}, {"k": 6}, {"k": 7}, {"B": -1}, {"universo": -1}, {"N": "x"}, {"semilla": "x"}],
)
def test_argumentos_invalidos_dan_codigo_2(tmp_path, cambio):
    salida = tmp_path / "casos"
    proceso = generar(salida, **cambio)
    assert proceso.returncode == 2
    assert proceso.stderr
    assert not salida.exists()


@pytest.mark.parametrize("falta", ["--N", "--k", "--B", "--universo", "--semilla", "--salida"])
def test_todos_los_argumentos_son_obligatorios(tmp_path, falta):
    valores = {"--N": 6, "--k": 2, "--B": 10, "--universo": 8, "--semilla": 1, "--salida": tmp_path / "x"}
    del valores[falta]
    argumentos = [parte for par in valores.items() for parte in par]
    assert ejecutar("generar.py", *argumentos).returncode == 2


def test_salida_no_escribible_da_codigo_2(tmp_path):
    archivo = tmp_path / "soy_un_archivo"
    archivo.write_text("x", encoding="utf-8")
    proceso = generar(archivo)
    assert proceso.returncode == 2
    assert "Traceback" not in proceso.stderr


# Integración con la CLI principal


def test_main_resuelve_lo_generado(tmp_path):
    generar(tmp_path / "casos")
    salida = tmp_path / "res"
    proceso = ejecutar("main.py", "--input", tmp_path / "casos", "--output", salida, "--verificar")
    assert proceso.returncode == 0, proceso.stdout + proceso.stderr
    resultado = json.loads((salida / "gen_N6_k2_B10_U8_s1" / "resultado.json").read_text(encoding="utf-8"))
    assert resultado["caso"] == "gen_N6_k2_B10_U8_s1"
    assert all(resultado["verificacion_restricciones"].values())
    assert resultado["verificacion_optimo"]["parte2"]["cumple_cota_1_menos_1_e"] is True
    assert resultado["verificacion_optimo"]["parte1"]["voraz_es_optimo"] is True


def test_el_lector_acepta_el_archivo_generado(tmp_path):
    generar(tmp_path)
    assert leer_caso(tmp_path / "gen_N6_k2_B10_U8_s1.json").errores == []


def test_main_con_una_instancia_grande_omite_la_verificacion(tmp_path):
    generar(tmp_path / "casos", N=60, k=20, B=5000, universo=100, semilla=3)
    salida = tmp_path / "res"
    proceso = ejecutar("main.py", "--input", tmp_path / "casos", "--output", salida, "--verificar", "--traza", "resumen")
    assert proceso.returncode == 0, proceso.stdout + proceso.stderr
    resultado = json.loads((salida / "gen_N60_k20_B5000_U100_s3" / "resultado.json").read_text(encoding="utf-8"))
    assert resultado["verificacion_optimo"]["parte2"]["omitida"] is True
    assert resultado["verificacion_optimo"]["parte1"]["omitida"] is True

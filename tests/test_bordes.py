"""Pruebas de punta a punta de bordes, tipos y determinismo (sección 7 de la especificación)."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


def ejecutar(script, *argumentos, semilla_hash=None):
    entorno = dict(os.environ)
    if semilla_hash is not None:
        entorno["PYTHONHASHSEED"] = str(semilla_hash)
    return subprocess.run(
        [sys.executable, str(RAIZ / script), *map(str, argumentos)],
        capture_output=True,
        cwd=RAIZ,
        encoding="utf-8",
        errors="replace",
        env=entorno,
    )


def nodo(id_nodo, cubre, *valores):
    return {"id": id_nodo, "cubre": cubre, "utilidad": {"tipo": "tabla", "valores": list(valores)}}


def caso(nodos, k=1, B=2, universo=2, **otros):
    return {"N": len(nodos), "k": k, "B": B, "universo": universo, "nodos": nodos, **otros}


@pytest.fixture
def resolver(tmp_path):
    """Escribe un caso, lo ejecuta con --verificar y devuelve su resultado y su traza."""

    def _resolver(datos):
        entrada = tmp_path / "c.json"
        entrada.write_text(json.dumps(datos), encoding="utf-8")
        salida = tmp_path / "res"
        proceso = ejecutar("main.py", "--input", entrada, "--output", salida, "--verificar")
        carpeta = salida / "c"
        resultado = json.loads((carpeta / "resultado.json").read_text(encoding="utf-8"))
        traza = carpeta / "traza.json"
        return (
            proceso.returncode,
            resultado,
            json.loads(traza.read_text(encoding="utf-8")) if traza.exists() else None,
        )

    return _resolver


# Bordes


def test_presupuesto_cero(resolver):
    codigo, resultado, traza = resolver(caso([nodo(0, [0], 2, 5), nodo(1, [1], 4, 5)], B=0))
    assert codigo == 0
    assert resultado["reparto"] == {
        "asignacion": {"0": 0},
        "utilidad_total": 2.0,
        "presupuesto_usado": 0,
        "presupuesto_sin_usar": 0,
    }
    assert traza["reparto"] == []
    assert resultado["verificacion_optimo"]["parte1"] == {"utilidad_optima": 2.0, "voraz_es_optimo": True}


def test_universo_vacio(resolver):
    codigo, resultado, traza = resolver(caso([nodo(0, [], 0, 1), nodo(1, [], 0, 9)], universo=0))
    assert codigo == 0
    assert resultado["seleccion"] == {"nodos": [0], "utilidad_conjunta": 0.0}
    assert traza["seleccion"][0]["ganancias"] == {"0": 0.0, "1": 0.0}


def test_f_optimo_cero_da_razon_uno(resolver):
    codigo, resultado, _ = resolver(caso([nodo(0, [], 0, 1), nodo(1, [], 0, 9)], universo=0))
    assert codigo == 0
    assert resultado["verificacion_optimo"]["parte2"] == {
        "f_optimo": 0.0,
        "razon": 1.0,
        "cumple_cota_1_menos_1_e": True,
    }


def test_pesos_cero_dan_f_optimo_cero(resolver):
    datos = caso([nodo(0, [0], 0, 1), nodo(1, [1], 0, 1)], pesos_universo=[0, 0])
    _, resultado, _ = resolver(datos)
    assert resultado["verificacion_optimo"]["parte2"]["razon"] == 1.0


def test_nodo_con_cubre_vacio_no_se_elige_si_hay_ganancia(resolver):
    _, resultado, _ = resolver(caso([nodo(0, [], 0, 9), nodo(1, [0], 0, 1)]))
    assert resultado["seleccion"]["nodos"] == [1]


def test_nodo_con_cubre_vacio_se_elige_para_completar_k(resolver):
    _, resultado, _ = resolver(caso([nodo(0, [0, 1], 0, 1), nodo(1, [], 0, 1), nodo(2, [], 0, 1)], k=2))
    assert resultado["seleccion"]["nodos"] == [0, 1]
    assert resultado["seleccion"]["utilidad_conjunta"] == 2.0


def test_tabla_mas_corta_que_b_deja_presupuesto_sin_usar(resolver):
    codigo, resultado, traza = resolver(caso([nodo(0, [0], 0, 5, 8), nodo(1, [], 0, 1)], B=10))
    assert codigo == 0
    assert resultado["reparto"] == {
        "asignacion": {"0": 2},
        "utilidad_total": 8.0,
        "presupuesto_usado": 2,
        "presupuesto_sin_usar": 8,
    }
    assert len(traza["reparto"]) == 2
    assert all(resultado["verificacion_restricciones"].values())
    assert resultado["verificacion_optimo"]["parte1"]["voraz_es_optimo"] is True


def test_tabla_de_un_solo_valor(resolver):
    _, resultado, _ = resolver(caso([nodo(0, [0], 7), nodo(1, [], 1)], B=3))
    assert resultado["reparto"]["utilidad_total"] == 7.0
    assert resultado["reparto"]["presupuesto_sin_usar"] == 3


def test_nodo_seleccionado_con_cero_unidades(resolver):
    datos = caso([nodo(0, [0], 0, 9, 18), nodo(1, [1], 0, 1, 2), nodo(2, [], 0, 1)], k=2)
    codigo, resultado, _ = resolver(datos)
    assert codigo == 0
    assert resultado["reparto"]["asignacion"] == {"0": 2, "1": 0}
    assert all(resultado["verificacion_restricciones"].values())


# Tipos


def test_real_con_valor_entero_se_normaliza(resolver):
    datos = caso([nodo(1.0, [0.0], 0, 5, 8), nodo("b", [1], 0, 1)], k=1.0, B=2.0, universo=2.0)
    codigo, resultado, _ = resolver(datos)
    assert codigo == 0
    assert resultado["parametros"] == {"N": 2, "k": 1, "B": 2, "universo": 2}
    assert resultado["seleccion"]["nodos"] == [1]
    assert resultado["reparto"]["asignacion"] == {"1": 2}


@pytest.mark.parametrize("valor", [10.5, True])
def test_real_con_decimales_y_booleano_dan_e02(resolver, valor):
    codigo, resultado, traza = resolver(caso([nodo(0, [0], 0, 1), nodo(1, [1], 0, 1)], B=valor))
    assert codigo == 1
    assert [error["codigo"] for error in resultado["errores"]] == ["E02"]
    assert traza is None


def test_id_entero_y_texto_iguales_dan_e04(resolver):
    codigo, resultado, _ = resolver(caso([nodo(1, [0], 0, 1), nodo("1", [1], 0, 1)]))
    assert codigo == 1
    assert [error["codigo"] for error in resultado["errores"]] == ["E04"]


# Determinismo


@pytest.fixture
def lote(tmp_path):
    """Carpeta con empates, ids de texto, un caso generado y un inválido."""
    carpeta = tmp_path / "lote"
    carpeta.mkdir()
    empates = caso(
        [nodo(f"n{i}", [i % 3], 0, 2, 3) for i in range(8)],
        k=3,
        B=7,
        universo=3,
    )
    (carpeta / "empates.json").write_text(json.dumps(empates), encoding="utf-8")
    (carpeta / "malo.json").write_text(json.dumps(caso([nodo(0, [0], 0, 1, 3)])), encoding="utf-8")
    ejecutar("generar.py", "--N", 12, "--k", 4, "--B", 30, "--universo", 20, "--semilla", 5, "--salida", carpeta)
    return carpeta


def sin_tiempos(salida):
    """Contenido de una salida sin los campos de tiempo."""
    contenido = {}
    for ruta in sorted(Path(salida).rglob("*")):
        if ruta.is_dir():
            continue
        relativa = ruta.relative_to(salida).as_posix()
        if ruta.name == "resultado.json":
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            datos.pop("tiempos_ms", None)
            contenido[relativa] = datos
        elif ruta.name == "resumen.csv":
            filas = ruta.read_text(encoding="utf-8").splitlines()
            contenido[relativa] = [fila.split(",")[:9] + fila.split(",")[12:] for fila in filas]
        else:
            contenido[relativa] = ruta.read_bytes()
    return contenido


def test_dos_ejecuciones_producen_lo_mismo_salvo_tiempos(lote, tmp_path):
    uno, dos = tmp_path / "1", tmp_path / "2"
    ejecutar("main.py", "--input", lote, "--output", uno, "--verificar")
    ejecutar("main.py", "--input", lote, "--output", dos, "--verificar")
    contenido = sin_tiempos(uno)
    assert contenido == sin_tiempos(dos)
    assert "empates/traza.json" in contenido
    assert "malo/resultado.json" in contenido
    assert "resumen.csv" in contenido


def test_el_resultado_no_depende_de_la_semilla_de_hash(lote, tmp_path):
    uno, dos = tmp_path / "1", tmp_path / "2"
    ejecutar("main.py", "--input", lote, "--output", uno, "--verificar", semilla_hash=1)
    ejecutar("main.py", "--input", lote, "--output", dos, "--verificar", semilla_hash=2)
    assert sin_tiempos(uno) == sin_tiempos(dos)


def test_los_empates_se_resuelven_por_el_orden_en_nodos(lote, tmp_path):
    salida = tmp_path / "res"
    ejecutar("main.py", "--input", lote, "--output", salida)
    resultado = json.loads((salida / "empates" / "resultado.json").read_text(encoding="utf-8"))
    assert resultado["seleccion"]["nodos"] == ["n0", "n1", "n2"]
    assert resultado["reparto"]["asignacion"] == {"n0": 2, "n1": 2, "n2": 2}
    assert resultado["reparto"]["presupuesto_sin_usar"] == 1

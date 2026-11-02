"""CLI: recorre casos, ejecuta, escribe salidas."""

import argparse
import statistics
import sys
import time
from pathlib import Path

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
from src.reparto import repartir
from src.salida import escribir_caso, escribir_resumen, fila_resumen, nombres_carpetas, redondear
from src.seleccion import seleccionar

SALIDA_OK = 0
SALIDA_CASOS_CON_FALLOS = 1
SALIDA_ERROR_DE_USO = 2


def _entero_positivo(texto: str) -> int:
    valor = int(texto)
    if valor < 1:
        raise argparse.ArgumentTypeError("debe ser un entero positivo")
    return valor


def _leer_argumentos(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Proyecto Red: selección de nodos y reparto de presupuesto.")
    parser.add_argument("--input", required=True, type=Path, help="archivo .json o carpeta con casos")
    parser.add_argument("--output", required=True, type=Path, help="carpeta de resultados")
    parser.add_argument("--verificar", action="store_true", help="compara contra los algoritmos exactos")
    parser.add_argument("--traza", choices=("completa", "resumen", "ninguna"), default="completa")
    parser.add_argument("--repeticiones", type=_entero_positivo, default=5)
    return parser.parse_args(argv)


def _listar_casos(entrada: Path) -> list[Path]:
    if entrada.is_file():
        return [entrada]
    # Solo el primer nivel: las subcarpetas de la entrada se ignoran.
    archivos = [ruta for ruta in entrada.iterdir() if ruta.is_file() and ruta.suffix.lower() == ".json"]
    return sorted(archivos, key=lambda ruta: (ruta.name.casefold(), ruta.name))


def _medir(caso, repeticiones: int):
    """Ejecuta sin traza `repeticiones` veces; devuelve los resultados y las medianas en ms."""
    seleccion_ms, reparto_ms, total_ms = [], [], []
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        seleccion = seleccionar(caso)
        intermedio = time.perf_counter()
        reparto = repartir(caso, seleccion.indices)
        fin = time.perf_counter()
        seleccion_ms.append((intermedio - inicio) * 1000)
        reparto_ms.append((fin - intermedio) * 1000)
        total_ms.append((fin - inicio) * 1000)
    tiempos = {
        "seleccion": round(statistics.median(seleccion_ms), 6),
        "reparto": round(statistics.median(reparto_ms), 6),
        "total": round(statistics.median(total_ms), 6),
        "repeticiones": repeticiones,
        "estadistico": "mediana",
    }
    return seleccion, reparto, tiempos


def _generar_traza(caso, modo: str) -> dict | None:
    if modo == "ninguna":
        return None
    traza_seleccion: list = []
    traza_reparto: list = []
    seleccion = seleccionar(caso, traza_seleccion, resumen=modo == "resumen")
    repartir(caso, seleccion.indices, traza_reparto)
    return {"seleccion": traza_seleccion, "reparto": traza_reparto}


def _verificar_optimo(caso, seleccion, reparto) -> dict:
    return {"parte2": _verificar_seleccion(caso, seleccion), "parte1": _verificar_reparto(caso, seleccion, reparto)}


def _verificar_seleccion(caso, seleccion) -> dict:
    if not cabe_fuerza_bruta(caso):
        return {"omitida": True, "motivo": "C(N, k) supera 10^6 subconjuntos"}
    f_optimo = seleccion_optima(caso)
    razon = razon_seleccion(seleccion.utilidad_conjunta, f_optimo)
    return {"f_optimo": f_optimo, "razon": razon, "cumple_cota_1_menos_1_e": razon >= COTA_SELECCION}


def _verificar_reparto(caso, seleccion, reparto) -> dict:
    if not cabe_dp(caso):
        return {"omitida": True, "motivo": "k·B² supera 10^7"}
    optimo = reparto_optimo(caso, seleccion.indices)
    return {"utilidad_optima": optimo, "voraz_es_optimo": voraz_coincide(reparto.utilidad_total, optimo, caso.B)}


def _verificar_restricciones(caso, seleccion, reparto) -> dict:
    indices = seleccion.indices
    return {
        "seleccion_tiene_k_nodos": len(indices) == caso.k,
        "seleccion_sin_repetidos": len(set(indices)) == len(indices),
        "suma_asignacion_menor_igual_B": sum(reparto.asignacion.values()) <= caso.B,
        "asignacion_solo_a_seleccionados": set(reparto.asignacion) <= set(indices),
        "asignaciones_no_negativas": all(x >= 0 for x in reparto.asignacion.values()),
    }


def _resolver(nombre: str, caso, opciones) -> tuple[dict, dict | None]:
    """Resuelve un caso válido y devuelve el contenido de `resultado.json` y de `traza.json`."""
    seleccion, reparto, tiempos = _medir(caso, opciones.repeticiones)
    traza = _generar_traza(caso, opciones.traza)
    verificacion = _verificar_optimo(caso, seleccion, reparto) if opciones.verificar else None
    resultado = redondear(
        {
            "caso": nombre,
            "estado": "ok",
            "parametros": {"N": caso.N, "k": caso.k, "B": caso.B, "universo": caso.universo},
            "seleccion": {
                "nodos": [caso.nodos[i].id for i in seleccion.indices],
                "utilidad_conjunta": seleccion.utilidad_conjunta,
            },
            "reparto": {
                "asignacion": {str(caso.nodos[i].id): x for i, x in reparto.asignacion.items()},
                "utilidad_total": reparto.utilidad_total,
                "presupuesto_usado": reparto.presupuesto_usado,
                "presupuesto_sin_usar": reparto.presupuesto_sin_usar,
            },
            "verificacion_restricciones": _verificar_restricciones(caso, seleccion, reparto),
            "verificacion_optimo": verificacion,
        }
    )
    resultado["tiempos_ms"] = tiempos
    return resultado, redondear(traza)


def _procesar(ruta: Path, salida: Path, carpeta: str, opciones) -> dict:
    """Procesa un caso sin dejar escapar sus errores y devuelve su fila de `resumen.csv`."""
    nombre, parametros = ruta.stem, {}
    try:
        leido = leer_caso(ruta)
        nombre, parametros = leido.nombre, leido.parametros
        if leido.errores:
            errores = [{"codigo": e.codigo, "detalle": e.detalle} for e in leido.errores]
            escribir_caso(salida / carpeta, {"caso": nombre, "estado": "invalido", "errores": errores})
            _informar(carpeta, "invalido", errores)
            return {"caso": carpeta, "estado": "invalido", **parametros}

        resultado, traza = _resolver(nombre, leido.caso, opciones)
        escribir_caso(salida / carpeta, resultado, traza)
        _informar(carpeta, "ok")
        return fila_resumen(carpeta, resultado)
    except Exception as error:
        errores = [{"codigo": "INTERNO", "detalle": f"{type(error).__name__}: {error}"}]
        _informar(carpeta, "error", errores)
        try:
            escribir_caso(salida / carpeta, {"caso": nombre, "estado": "error", "errores": errores})
        except OSError as error_escritura:
            print(f"  No se pudo escribir el resultado: {error_escritura}", file=sys.stderr)
        return {"caso": carpeta, "estado": "error", **parametros}


def _informar(carpeta: str, estado: str, errores=()) -> None:
    print(f"{carpeta}: {estado}")
    for error in errores:
        print(f"  {error['codigo']}: {error['detalle']}")


def main(argv=None) -> int:
    # Un nombre que la consola no puede mostrar no debe tumbar el lote.
    sys.stdout.reconfigure(errors="backslashreplace")
    sys.stderr.reconfigure(errors="backslashreplace")
    opciones = _leer_argumentos(argv)

    try:
        rutas = _listar_casos(opciones.input)
    except OSError as error:
        print(f"No se puede leer la entrada {opciones.input}: {error}", file=sys.stderr)
        return SALIDA_ERROR_DE_USO
    if not rutas:
        print(f"La carpeta {opciones.input} no contiene archivos .json", file=sys.stderr)
        return SALIDA_ERROR_DE_USO

    try:
        opciones.output.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        print(f"No se puede escribir en {opciones.output}: {error}", file=sys.stderr)
        return SALIDA_ERROR_DE_USO

    carpetas = nombres_carpetas(ruta.stem for ruta in rutas)
    filas = [_procesar(ruta, opciones.output, carpeta, opciones) for ruta, carpeta in zip(rutas, carpetas)]

    try:
        escribir_resumen(opciones.output, filas)
    except OSError as error:
        print(f"No se puede escribir el resumen en {opciones.output}: {error}", file=sys.stderr)
        return SALIDA_ERROR_DE_USO

    resueltos = sum(fila["estado"] == "ok" for fila in filas)
    print(f"{len(filas)} casos, {resueltos} resueltos. Resultados en {opciones.output}")
    return SALIDA_OK if resueltos == len(filas) else SALIDA_CASOS_CON_FALLOS


if __name__ == "__main__":
    sys.exit(main())

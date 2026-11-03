"""Generador de instancias con semilla."""

import argparse
import json
import random
import sys
from pathlib import Path

SALIDA_OK = 0
SALIDA_ERROR_DE_USO = 2
MAX_GANANCIAS_TABLA = 50


def _utilidad(azar: random.Random, B: int) -> dict:
    if azar.random() < 0.5:
        return {"tipo": "log", "a": azar.uniform(0.1, 10), "b": azar.uniform(0.1, 5)}
    cantidad = azar.randint(0, min(B + 1, MAX_GANANCIAS_TABLA))
    valores = [azar.uniform(0, 5)]
    for ganancia in sorted((azar.uniform(0, 10) for _ in range(cantidad)), reverse=True):
        valores.append(valores[-1] + ganancia)
    return {"tipo": "tabla", "valores": valores}


def generar_caso(N: int, k: int, B: int, universo: int, semilla: int) -> dict:
    """Crea un caso válido; los mismos argumentos producen siempre el mismo caso."""
    azar = random.Random(semilla)
    return {
        "nombre": f"gen_N{N}_k{k}_B{B}_U{universo}_s{semilla}",
        "N": N,
        "k": k,
        "B": B,
        "universo": universo,
        "pesos_universo": [azar.uniform(0.1, 5) for _ in range(universo)],
        "nodos": [
            {
                "id": i,
                "cubre": sorted(azar.sample(range(universo), azar.randint(0, universo // 2))),
                "utilidad": _utilidad(azar, B),
            }
            for i in range(N)
        ],
    }


def _a_json(caso: dict) -> str:
    """Serializa con un nodo por línea, para poder revisar el archivo a simple vista."""
    cabecera = {clave: valor for clave, valor in caso.items() if clave != "nodos"}
    nodos = ",\n".join(f"  {json.dumps(nodo)}" for nodo in caso["nodos"])
    return f'{json.dumps(cabecera)[:-1]}, "nodos": [\n{nodos}\n]}}\n'


def _leer_argumentos(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera una instancia sintética reproducible.")
    parser.add_argument("--N", required=True, type=int, help="número de nodos")
    parser.add_argument("--k", required=True, type=int, help="nodos a seleccionar")
    parser.add_argument("--B", required=True, type=int, help="presupuesto")
    parser.add_argument("--universo", required=True, type=int, help="tamaño del universo")
    parser.add_argument("--semilla", required=True, type=int)
    parser.add_argument("--salida", required=True, type=Path, help="carpeta de destino")
    argumentos = parser.parse_args(argv)
    if argumentos.N < 1 or not 1 <= argumentos.k < argumentos.N or argumentos.B < 0 or argumentos.universo < 0:
        parser.error("se requiere N ≥ 1, 1 ≤ k < N, B ≥ 0 y universo ≥ 0")
    return argumentos


def main(argv=None) -> int:
    sys.stdout.reconfigure(errors="backslashreplace")
    sys.stderr.reconfigure(errors="backslashreplace")
    argumentos = _leer_argumentos(argv)
    caso = generar_caso(argumentos.N, argumentos.k, argumentos.B, argumentos.universo, argumentos.semilla)
    ruta = argumentos.salida / f"{caso['nombre']}.json"
    try:
        argumentos.salida.mkdir(parents=True, exist_ok=True)
        ruta.write_text(_a_json(caso), encoding="utf-8", newline="\n")
    except OSError as error:
        print(f"No se puede escribir en {argumentos.salida}: {error}", file=sys.stderr)
        return SALIDA_ERROR_DE_USO
    print(f"Caso escrito en {ruta}")
    return SALIDA_OK


if __name__ == "__main__":
    sys.exit(main())

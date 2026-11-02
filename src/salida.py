"""Escritura de resultado.json, traza.json, resumen.csv."""

import csv
import json
from pathlib import Path

ARCHIVO_RESUMEN = "resumen.csv"
COLUMNAS_RESUMEN = (
    "caso",
    "estado",
    "N",
    "k",
    "B",
    "universo",
    "f_S",
    "utilidad_total",
    "presupuesto_usado",
    "t_seleccion_ms",
    "t_reparto_ms",
    "t_total_ms",
    "razon_optimo",
)
CARACTERES_PROHIBIDOS = set('<>:"/\\|?*')
NOMBRES_RESERVADOS = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitizar(nombre: str) -> str:
    """Convierte el nombre de un archivo en un nombre de carpeta válido en cualquier sistema."""
    limpio = "".join(
        "_" if c in CARACTERES_PROHIBIDOS or ord(c) < 32 or ord(c) == 127 else c for c in nombre
    ).rstrip(" .")
    if not limpio:
        return "caso"
    if limpio.split(".")[0].rstrip(" ").upper() in NOMBRES_RESERVADOS:
        return f"_{limpio}"
    return limpio


def nombres_carpetas(nombres) -> list[str]:
    """Asigna una carpeta a cada caso; las colisiones, sin distinguir mayúsculas, llevan sufijo."""
    usados = {ARCHIVO_RESUMEN}
    carpetas = []
    for nombre in nombres:
        base = sanitizar(nombre)
        carpeta = base
        sufijo = 2
        while carpeta.casefold() in usados:
            carpeta = f"{base}_{sufijo}"
            sufijo += 1
        usados.add(carpeta.casefold())
        carpetas.append(carpeta)
    return carpetas


def redondear(valor, decimales: int = 4):
    """Redondea los reales de una estructura; sumar 0.0 convierte -0.0 en 0.0."""
    if isinstance(valor, float):
        return round(valor, decimales) + 0.0
    if isinstance(valor, dict):
        return {clave: redondear(v, decimales) for clave, v in valor.items()}
    if isinstance(valor, list):
        return [redondear(v, decimales) for v in valor]
    return valor


def _a_json(contenido) -> str:
    # allow_nan=False: un valor infinito no es JSON válido y debe reportarse como error.
    return json.dumps(contenido, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def _escribir_texto(ruta: Path, texto: str) -> None:
    # backslashreplace: un nombre con surrogados sueltos no debe impedir la escritura.
    ruta.write_text(texto, encoding="utf-8", errors="backslashreplace", newline="\n")


def escribir_caso(carpeta, resultado: dict, traza: dict | None = None) -> None:
    """Escribe los archivos de un caso; sin `traza` borra la de una ejecución anterior."""
    carpeta = Path(carpeta)
    # Se serializa todo antes de escribir para no dejar un caso a medias si algo falla.
    texto_resultado = _a_json(resultado)
    texto_traza = None if traza is None else _a_json(traza)

    carpeta.mkdir(parents=True, exist_ok=True)
    _escribir_texto(carpeta / "resultado.json", texto_resultado)
    if texto_traza is None:
        (carpeta / "traza.json").unlink(missing_ok=True)
    else:
        _escribir_texto(carpeta / "traza.json", texto_traza)


def fila_resumen(carpeta: str, resultado: dict) -> dict:
    """Fila de `resumen.csv` de un caso resuelto."""
    verificacion = resultado["verificacion_optimo"] or {}
    return {
        "caso": carpeta,
        "estado": resultado["estado"],
        **resultado["parametros"],
        "f_S": resultado["seleccion"]["utilidad_conjunta"],
        "utilidad_total": resultado["reparto"]["utilidad_total"],
        "presupuesto_usado": resultado["reparto"]["presupuesto_usado"],
        "t_seleccion_ms": resultado["tiempos_ms"]["seleccion"],
        "t_reparto_ms": resultado["tiempos_ms"]["reparto"],
        "t_total_ms": resultado["tiempos_ms"]["total"],
        "razon_optimo": verificacion.get("parte2", {}).get("razon"),
    }


def escribir_resumen(salida, filas) -> None:
    ruta = Path(salida) / ARCHIVO_RESUMEN
    with open(ruta, "w", encoding="utf-8", errors="backslashreplace", newline="") as archivo:
        escritor = csv.DictWriter(archivo, COLUMNAS_RESUMEN, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)

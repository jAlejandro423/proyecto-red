# Proyecto Red

**Grupo 2 · Análisis y Diseño de Algoritmos (ADAG) 2026-B · Universidad de Caldas**

Reparto de presupuesto y selección de participantes en una red de nodos. Cada caso se resuelve en este orden:

1. **Parte 2, selección:** elige `k` de `N` nodos maximizando una utilidad conjunta monótona y submodular (cobertura ponderada). El problema es NP-difícil; se usa un voraz con garantía `≥ (1 − 1/e)` del óptimo. Complejidad: `O(N·k·τ)`, donde `τ` es el costo de calcular la ganancia de un nodo.
2. **Parte 1, reparto:** reparte el presupuesto entero `B` entre los nodos seleccionados, con utilidades cóncavas y crecientes. Se usa un voraz por ganancia marginal con montículo, que da el óptimo salvo la tolerancia descrita en la sección 3.4 de la especificación. Complejidad: `O(N + B log N)`, pseudo-polinomial, donde `N` es la cantidad de nodos que reciben el reparto.

La fuente de verdad de formatos y reglas es [ESPECIFICACION.md](ESPECIFICACION.md).

## Requisitos

- Python 3.10 o superior.
- El núcleo usa solo la librería estándar. `pytest` solo hace falta para las pruebas.

## Instalación

```bash
git clone https://github.com/jAlejandro423/proyecto-red.git
cd proyecto-red
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

**En Windows:** usa `py -m venv .venv` si `python` no funciona, y activa el entorno con `.venv\Scripts\activate`. Con el entorno activo, `python` ya funciona en todos los comandos de este documento.

**En Linux o Mac:** usa `python3 -m venv .venv` si `python` no existe.

## Uso rápido

Desde la carpeta del repositorio:

```bash
python main.py --input casos_ejemplo/ --output resultados/ --verificar
```

Para tus propios casos, cambia `--input` por tu archivo o carpeta. La verificación contra el óptimo se omite sola en los casos grandes e indica el motivo en `resultado.json`.

## Opciones de `main.py`

| Opción | Obligatoria | Por defecto | Descripción |
|---|---|---|---|
| `--input RUTA` | Sí | — | Archivo `.json` o carpeta con casos. En una carpeta se leen solo los `.json` directos; las subcarpetas se ignoran. |
| `--output CARPETA` | Sí | — | Carpeta de resultados; se crea si no existe. |
| `--verificar` | No | Desactivada | Compara contra los algoritmos exactos: fuerza bruta en la Parte 2 si `C(N, k) ≤ 10⁶` y programación dinámica en la Parte 1 si `k·B² ≤ 10⁷`. |
| `--traza {completa,resumen,ninguna}` | No | `completa` | `resumen` guarda en la Parte 2 solo el elegido por paso; `ninguna` no genera `traza.json`. |
| `--repeticiones R` | No | `5` | Veces que se mide cada caso, entero positivo. Se reporta la mediana. |

## Formato de entrada

Cada caso es un archivo JSON en UTF-8. Este es `casos_ejemplo/ejemplo_01.json`:

```json
{
  "nombre": "ejemplo_01",
  "N": 4, "k": 2, "B": 5,
  "universo": 6,
  "nodos": [
    { "id": 0, "cubre": [0, 1, 2], "utilidad": { "tipo": "tabla", "valores": [0, 5, 8, 10, 11, 11] } },
    { "id": 1, "cubre": [2, 3],    "utilidad": { "tipo": "tabla", "valores": [0, 4, 7, 9, 10, 10] } },
    { "id": 2, "cubre": [3, 4, 5], "utilidad": { "tipo": "log", "a": 6.0, "b": 1.0 } },
    { "id": 3, "cubre": [0, 5],    "utilidad": { "tipo": "tabla", "valores": [0, 3, 5, 6] } }
  ]
}
```

| Campo | Tipo | Obligatorio | Restricción | Significado |
|---|---|---|---|---|
| `nombre` | string | No | — | Nombre del caso; si falta, se usa el del archivo. |
| `N` | entero | Sí | `N ≥ 1` | Número de nodos candidatos. |
| `k` | entero | Sí | `1 ≤ k < N` | Nodos a seleccionar. |
| `B` | entero | Sí | `B ≥ 0` | Presupuesto total. |
| `universo` | entero | Sí | `≥ 0` | Tamaño `\|U\|`; los elementos son `0, …, \|U\|−1`. |
| `pesos_universo` | lista de números | No | Longitud `\|U\|`, valores `≥ 0` | Peso de cada elemento; si falta, todos valen 1. |
| `nodos` | lista de objetos | Sí | Longitud `N` | Nodos candidatos. |
| `nodos[].id` | entero o string | Sí | Único al compararlo como texto | Identificador del nodo. |
| `nodos[].cubre` | lista de enteros | Sí | En `[0, \|U\|)`, sin repetidos | Elementos que aporta el nodo (Parte 2). |
| `nodos[].utilidad` | objeto | Sí | Creciente y cóncava | Función `u(x)` del nodo (Parte 1). |

La utilidad tiene una de estas dos formas:

- **Tabla:** `{ "tipo": "tabla", "valores": [u(0), u(1), ..., u(L)] }`. Si `L < B`, para `x > L` se asume `u(x) = u(L)`.
- **Logarítmica:** `{ "tipo": "log", "a": 6.0, "b": 1.0 }`, es decir, `u(x) = a · ln(1 + b·x)`, con `a ≥ 0` y `b > 0`.

### Códigos de error

Un caso inválido no se ejecuta: se reportan todos sus errores y el lote sigue con el siguiente caso.

| Código | Qué indica |
|---|---|
| `E01` | JSON ilegible o que no está en UTF-8, raíz que no es un objeto, o falta un campo obligatorio. |
| `E02` | Tipo incorrecto en un campo. Por ejemplo, `10.5` o `true` donde va un entero (`10.0` sí se acepta). |
| `E03` | No se cumple `N ≥ 1`, `1 ≤ k < N`, `B ≥ 0` o `universo ≥ 0`. |
| `E04` | `nodos` no tiene `N` elementos, o hay `id` repetidos (`1` y `"1"` cuentan como repetidos). |
| `E05` | Un valor de `cubre` está fuera de `[0, \|U\|)` o se repite dentro del nodo. |
| `E06` | `pesos_universo` no tiene longitud `\|U\|` o tiene valores negativos. |
| `E07` | La utilidad no es creciente. |
| `E08` | La utilidad no es cóncava. |
| `E09` | Utilidad `log` con `a < 0` o `b ≤ 0`, o algún número no finito (`NaN`, `Infinity`). |
| `E10` | Tipo de utilidad desconocido: no es `tabla` ni `log`. |
| `INTERNO` | Error inesperado al procesar un caso válido, como falta de memoria o un valor que desborda. No es de validación: el caso queda con estado `error`. |

Las reglas completas de tipos y validación están en la [sección 2 de la especificación](ESPECIFICACION.md#2-formato-de-entrada).

## Salidas

Por cada caso se crea `<output>/<carpeta>/`, y en `<output>/` queda el resumen del lote:

| Archivo | Contenido |
|---|---|
| `resultado.json` | Parámetros, nodos seleccionados, utilidad conjunta, reparto, verificación de restricciones, verificación contra el óptimo (`null` sin `--verificar`) y tiempos en milisegundos. |
| `traza.json` | Paso a paso de ambos algoritmos: ganancias y nodo elegido en la selección; candidatos y destino de cada unidad en el reparto. |
| `resumen.csv` | Una fila por caso: `caso,estado,N,k,B,universo,f_S,utilidad_total,presupuesto_usado,t_seleccion_ms,t_reparto_ms,t_total_ms,razon_optimo`. Los valores no disponibles quedan vacíos. |

**Estados de un caso:**

| Estado | Significado | `resultado.json` | `traza.json` |
|---|---|---|---|
| `ok` | Se resolvió. | Completo | Sí, salvo con `--traza ninguna` |
| `invalido` | No pasó la validación. | `caso`, `estado` y `errores` | No |
| `error` | Falló de forma inesperada (`INTERNO`). | `caso`, `estado` y `errores` | No |

**Nombre de la carpeta de cada caso:** es el nombre del archivo de entrada sin `.json`, con estos ajustes para que sea válido en cualquier sistema:

- Los caracteres `< > : " / \ | ? *` y los de control se reemplazan por `_`.
- Se eliminan los espacios y puntos finales.
- Los nombres reservados de Windows (`CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`, `LPT1`–`LPT9`) llevan el prefijo `_`.
- Si el nombre queda vacío, se usa `caso`.
- Si dos carpetas coinciden sin distinguir mayúsculas, se añade `_2`, `_3`, etc., en orden alfabético de los archivos.

## Salida esperada

El comando de [Uso rápido](#uso-rápido) muestra esto en consola:

```text
ejemplo_01: ok
invalido_01: invalido
  E08: nodos[1].utilidad no es cóncava: g(1) = 3.0 > g(0) = 1.0 (2 en total)
2 casos, 1 resueltos. Resultados en resultados
```

Termina con **código de salida 1, y eso es lo esperado:** `invalido_01` está en la carpeta a propósito para mostrar que un caso inválido se rechaza sin detener el lote.

Extracto de `resultados/ejemplo_01/resultado.json`:

```json
{
  "caso": "ejemplo_01",
  "estado": "ok",
  "seleccion": {
    "nodos": [
      0,
      2
    ],
    "utilidad_conjunta": 6.0
  },
  "reparto": {
    "asignacion": {
      "0": 3,
      "2": 2
    },
    "utilidad_total": 16.5917,
    "presupuesto_usado": 5,
    "presupuesto_sin_usar": 0
  },
  "verificacion_optimo": {
    "parte2": {
      "f_optimo": 6.0,
      "razon": 1.0,
      "cumple_cota_1_menos_1_e": true
    },
    "parte1": {
      "utilidad_optima": 16.5917,
      "voraz_es_optimo": true
    }
  },
  "tiempos_ms": {
    "seleccion": 0.0165,
    "reparto": 0.0211,
    "total": 0.0376,
    "repeticiones": 5,
    "estadistico": "mediana"
  }
}
```

Es decir: selecciona `{0, 2}` con `f = 6`, reparte `x0 = 3` y `x2 = 2`, obtiene una utilidad de `16.5917` y la razón contra el óptimo es `1.0`. **Los tiempos dependen de la máquina;** todo lo demás debe coincidir.

`resultados/invalido_01/resultado.json` contiene un único error, `E08`, porque las ganancias del nodo 1 aumentan en lugar de disminuir:

```json
{
  "caso": "invalido_01",
  "estado": "invalido",
  "errores": [
    {
      "codigo": "E08",
      "detalle": "nodos[1].utilidad no es cóncava: g(1) = 3.0 > g(0) = 1.0 (2 en total)"
    }
  ]
}
```

## Códigos de salida

### `main.py`

| Código | Significado |
|---|---|
| `0` | Todos los casos se resolvieron. |
| `1` | Hubo algún caso inválido o con error; igual se procesaron todos. |
| `2` | Argumentos de la línea de comandos inválidos; `--input` no existe o es una carpeta sin archivos `.json`; o no se puede escribir en `--output`. Se muestra un mensaje que lo explica. |

### `generar.py`

| Código | Significado |
|---|---|
| `0` | Escribió el archivo. |
| `2` | Argumentos inválidos o no se puede escribir en `--salida`. Se muestra un mensaje que lo explica. |

## Generador de instancias

`generar.py` crea casos sintéticos válidos. Todos sus argumentos son obligatorios, y los mismos argumentos producen siempre el mismo archivo:

```bash
python generar.py --N 50 --k 10 --B 200 --universo 100 --semilla 42 --salida casos/
python main.py --input casos/ --output resultados/gen/ --verificar
```

Salida real en Windows (en Linux y Mac, las rutas se muestran con `/`):

```text
Caso escrito en casos\gen_N50_k10_B200_U100_s42.json
gen_N50_k10_B200_U100_s42: ok
1 casos, 1 resueltos. Resultados en resultados\gen
```

El caso se resuelve con `f = 244.9889` y utilidad `713.196`, usando las 200 unidades. También muestra la omisión por tamaño: la Parte 2 no se compara contra el óptimo porque `C(50, 10)` es demasiado grande, y `resultado.json` lo indica así:

```json
"verificacion_optimo": {
  "parte2": {
    "omitida": true,
    "motivo": "C(N, k) supera 10^6 subconjuntos"
  },
  "parte1": {
    "utilidad_optima": 713.196,
    "voraz_es_optimo": true
  }
}
```

## Pruebas

Con el entorno activo, desde la carpeta del repositorio:

```bash
python -m pytest
```

También funciona `pytest` a secas. Hay **293 pruebas** en esta versión y tardan alrededor de un minuto.

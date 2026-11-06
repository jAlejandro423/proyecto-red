# Proyecto Red

**Grupo 2 · Análisis y Diseño de Algoritmos (ADAG) 2026-B · Universidad de Caldas**

**Autor:** Juan Alejandro Betancourth · Código 40960 · Docente: Luz Enith Guerrero Mendieta

Reparto de presupuesto y selección de participantes en una red de nodos. Cada caso se resuelve en este orden:

1. **Parte 2, selección:** elige `k` de `N` nodos maximizando una utilidad conjunta monótona y submodular: cobertura ponderada (formato propio) o influencia en un grafo (formato de la docente). El problema es NP-difícil; se usa un voraz con garantía `≥ (1 − 1/e)` del óptimo. Complejidad: `O(N·k·τ)`, donde `τ` es el costo de calcular la ganancia de un nodo.
2. **Parte 1, reparto:** reparte el presupuesto entero `B` entre los nodos seleccionados, con utilidades cóncavas y crecientes. Se usa un voraz por ganancia marginal con montículo, que da el óptimo salvo la tolerancia descrita en la sección 3.4 de la especificación. Complejidad: `O(N + B log N)`, pseudo-polinomial, donde `N` es la cantidad de nodos que reciben el reparto.

La fuente de verdad de formatos y reglas es [ESPECIFICACION.md](ESPECIFICACION.md).

## Requisitos

- Python 3.10 o superior.
- El núcleo usa solo la librería estándar. `pytest` solo hace falta para las pruebas.
- Probado en Windows con Python 3.12.6 y pytest 9.2.0. El núcleo solo usa la librería estándar, así que debería funcionar igual en Linux y macOS con Python 3.10 o superior.

## Instalación

La versión entregada es la etiqueta `entrega-1` de la rama `main`. Para obtener exactamente esa versión: `git checkout entrega-1` después de clonar.

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

Cada caso es un archivo JSON en UTF-8. El programa acepta dos formatos y **detecta solo cuál es**: si la raíz trae `parametros` o `grafo`, es el [formato de la docente](#formato-de-la-docente); si no, el formato propio. Una misma carpeta puede mezclar casos de los dos.

### Formato propio

Este es `casos_ejemplo/ejemplo_01.json`:

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

### Formato de la docente

Es el formato de los casos de prueba de la docente. Este es un extracto de `casos_ejemplo/entrada_G2_red_15_nodos.json` (15 nodos, grafo completo de 105 aristas):

```json
{
  "parametros": {
    "numero_nodos": 15,
    "numero_rondas": 3,
    "cupo_participantes_por_ronda_k": 5,
    "presupuesto_ruido_por_ronda_B": 30,
    "presupuesto_costos_participacion_por_ronda": 24
  },
  "grafo": [
    { "u": "N01", "v": "N02", "peso_influencia": 0.25 },
    ...
  ],
  "nodos": [
    { "id": "N01", "coeficiente_utilidad": 8.5, "presupuesto_total_nodo": 18, "costo_participacion": 3 },
    ...
  ]
}
```

| Campo | Tipo | Obligatorio | Restricción | Uso |
|---|---|---|---|---|
| `nombre` | string | No | — | Nombre del caso; si falta, se usa el del archivo. |
| `parametros.numero_nodos` | entero | Sí | `≥ 1` | `N`. |
| `parametros.cupo_participantes_por_ronda_k` | entero | Sí | `1 ≤ k ≤ N` | `k` (aquí sí se permite `k = N`). |
| `parametros.presupuesto_ruido_por_ronda_B` | entero | Sí | `≥ 0` | `B`. |
| `grafo` | lista de objetos | Sí | Puede ser vacía | Aristas de influencia. |
| `grafo[].u`, `grafo[].v` | entero o string | Sí | `id` existentes, sin lazos ni el mismo par `(u, v)` repetido | `u` influye sobre `v`. |
| `grafo[].peso_influencia` | número | Sí | En `[0, 1]` | `p_uv`; también `p_vu` si el par viene en una sola dirección. |
| `nodos` | lista de objetos | Sí | Longitud `N` | Nodos candidatos. |
| `nodos[].id` | entero o string | Sí | Único al compararlo como texto | Identificador. |
| `nodos[].coeficiente_utilidad` | número | Sí | `≥ 0` | `c_i`. |
| `nodos[].presupuesto_total_nodo` | entero | Sí | `≥ 0` | Tope `T_i` de unidades útiles del nodo. |
| `numero_rondas`, `presupuesto_costos_participacion_por_ronda`, `costo_participacion` | cualquiera | No | — | Se leen pero no se usan en esta entrega (variantes). |

Cómo se interpreta:

- **Reparto (Parte 1):** cada nodo usa `u_i(x) = c_i · ln(1 + min(x, T_i))`, la utilidad logarítmica con `b = 1` truncada en su tope. Ningún nodo recibe más de `T_i` unidades; si todos los topes se llenan, sobra presupuesto.
- **Aristas:** un par escrito en una sola dirección es no dirigido (`p_uv = p_vu`). Si vienen `(u, v)` y `(v, u)`, cada dirección conserva su peso (influencia dirigida). Repetir la misma dirección es `E14`.
- **Selección (Parte 2):** la utilidad conjunta es la influencia `f(A) = Σ_v c_v · [1 − Π_{u∈A} (1 − p_uv)]`, con `p_vv = 1` y `p = 0` sin arista. Es monótona y submodular, así que el voraz conserva la garantía `≥ (1 − 1/e)`. Cada ganancia cuesta `O(N)`, y la selección queda en `O(N²·k)`.
- **Campos no usados:** se copian a `resultado.json` bajo `campos_no_usados`, con la nota `"variantes, entregas posteriores"`.

El detalle completo está en la [sección 2.7 de la especificación](ESPECIFICACION.md#27-formato-de-la-docente).

### Códigos de error

Un caso inválido no se ejecuta: se reportan todos sus errores y el lote sigue con el siguiente caso.

| Código | Qué indica |
|---|---|
| `E01` | JSON ilegible o que no está en UTF-8, raíz que no es un objeto, o falta un campo obligatorio (formato propio). |
| `E02` | Tipo incorrecto en un campo. Por ejemplo, `10.5` o `true` donde va un entero (`10.0` sí se acepta). |
| `E03` | No se cumple `N ≥ 1`, `1 ≤ k < N`, `B ≥ 0` o `universo ≥ 0`. |
| `E04` | `nodos` no tiene `N` elementos, o hay `id` repetidos (`1` y `"1"` cuentan como repetidos). |
| `E05` | Un valor de `cubre` está fuera de `[0, \|U\|)` o se repite dentro del nodo. |
| `E06` | `pesos_universo` no tiene longitud `\|U\|` o tiene valores negativos. |
| `E07` | La utilidad no es creciente. |
| `E08` | La utilidad no es cóncava. |
| `E09` | Utilidad `log` con `a < 0` o `b ≤ 0`, algún número no finito (`NaN`, `Infinity`), o una utilidad que desborda al evaluarla. |
| `E10` | Tipo de utilidad desconocido: no es `tabla` ni `log`. |
| `E11` | Formato de la docente: falta un campo obligatorio. |
| `E12` | Formato de la docente: no se cumple `numero_nodos ≥ 1`, `1 ≤ k ≤ N` o `B ≥ 0`. |
| `E13` | Formato de la docente: un extremo de arista no es el `id` de ningún nodo. |
| `E14` | Formato de la docente: lazo (`u = v`) o la misma arista `(u, v)` repetida en la misma dirección (`(u, v)` y `(v, u)` juntas sí se aceptan). |
| `E15` | Formato de la docente: `peso_influencia` fuera de `[0, 1]`. |
| `E16` | Formato de la docente: `coeficiente_utilidad` negativo. |
| `E17` | Formato de la docente: `presupuesto_total_nodo` negativo. |
| `INTERNO` | Error inesperado al procesar un caso válido, como falta de memoria o un valor que desborda. No es de validación: el caso queda con estado `error`. |

En el formato de la docente, `E02` (tipos), `E04` (cantidad de nodos o `id` repetidos) y `E09` (números no finitos o desborde) significan lo mismo que en el propio.

Las reglas completas de tipos y validación están en la [sección 2 de la especificación](ESPECIFICACION.md#2-formato-de-entrada).

## Salidas

Por cada caso se crea `<output>/<carpeta>/`, y en `<output>/` queda el resumen del lote:

| Archivo | Contenido |
|---|---|
| `resultado.json` | Parámetros, nodos seleccionados, utilidad conjunta, reparto, verificación de restricciones, verificación contra el óptimo (`null` sin `--verificar`) y tiempos en milisegundos. En los casos de la docente agrega `"formato": "docente"`, la restricción `asignacion_respeta_topes` y `campos_no_usados`; `universo` vale `null`. |
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
entrada_G2_red_15_nodos: ok
invalido_01: invalido
  E08: nodos[1].utilidad no es cóncava: g(1) = 3.0 > g(0) = 1.0 (2 en total)
3 casos, 2 resueltos. Resultados en resultados
```

Y `resultados/resumen.csv` queda así (los tiempos varían):

```text
caso,estado,N,k,B,universo,f_S,utilidad_total,presupuesto_usado,t_seleccion_ms,t_reparto_ms,t_total_ms,razon_optimo
ejemplo_01,ok,4,2,5,6,6.0,16.5917,5,0.0181,0.0206,0.0387,1.0
entrada_G2_red_15_nodos,ok,15,5,30,,145.5795,88.564,30,0.1752,0.0976,0.2781,0.9978
invalido_01,invalido,3,2,4,4,,,,,,,
```

Termina con **código de salida 1, y eso es lo esperado:** `invalido_01` está en la carpeta a propósito para mostrar que un caso inválido se rechaza sin detener el lote.

### Caso propio

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

### Caso de la docente

Extracto de `resultados/entrada_G2_red_15_nodos/resultado.json` (se omiten 13 de los 15 costos):

```json
{
  "caso": "entrada_G2_red_15_nodos",
  "estado": "ok",
  "formato": "docente",
  "parametros": { "N": 15, "k": 5, "B": 30, "universo": null },
  "seleccion": {
    "nodos": ["N11", "N14", "N09", "N15", "N13"],
    "utilidad_conjunta": 145.5795
  },
  "reparto": {
    "asignacion": { "N11": 5, "N14": 7, "N09": 7, "N15": 6, "N13": 5 },
    "utilidad_total": 88.564,
    "presupuesto_usado": 30,
    "presupuesto_sin_usar": 0
  },
  "verificacion_restricciones": {
    "seleccion_tiene_k_nodos": true,
    "seleccion_sin_repetidos": true,
    "suma_asignacion_menor_igual_B": true,
    "asignacion_solo_a_seleccionados": true,
    "asignaciones_no_negativas": true,
    "asignacion_respeta_topes": true
  },
  "verificacion_optimo": {
    "parte2": { "f_optimo": 145.9072, "razon": 0.9978, "cumple_cota_1_menos_1_e": true },
    "parte1": { "utilidad_optima": 88.564, "voraz_es_optimo": true }
  },
  "campos_no_usados": {
    "nota": "variantes, entregas posteriores",
    "numero_rondas": 3,
    "presupuesto_costos_participacion_por_ronda": 24,
    "costo_participacion": { "N01": 3, "N02": 5, "...": "..." }
  },
  "tiempos_ms": { "seleccion": 0.1759, "reparto": 0.0997, "total": 0.2779, "repeticiones": 5, "estadistico": "mediana" }
}
```

Es decir: el voraz elige `N11, N14, N09, N15, N13` con `f ≈ 145.5795`; el óptimo por fuerza bruta (`{N09, N11, N12, N13, N15}`) vale `145.9072`, así que la razón es `0.9978`, por encima de `1 − 1/e ≈ 0.632`. El reparto da `N11 = 5, N14 = 7, N09 = 7, N15 = 6, N13 = 5`, con utilidad `88.564`, igual a la de la programación dinámica. En `traza.json`, el primer paso de la selección lista las ganancias de los 15 nodos (la mayor es la de `N11`, `103.49`) y el reparto tiene 30 registros, uno por unidad.

### Caso inválido

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

También funciona `pytest` a secas. Hay **402 pruebas** en esta versión y tardan alrededor de un minuto.

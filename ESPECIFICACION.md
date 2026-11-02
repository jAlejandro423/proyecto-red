# Especificación de entrada, salida y ejecución
**Proyecto Red — ADAG 2026-B — Grupo 2**
Reparto de presupuesto y selección de participantes · Primera entrega

> Este documento es la fuente de verdad para el código, el README y el manual técnico. Si algo cambia en el código, se cambia primero aquí.

---

## 1. Flujo general

Cada caso se resuelve como una ronda del sistema, en este orden:

1. **Parte 2 — Selección:** de los `N` nodos candidatos se eligen `k` con el voraz submodular, maximizando la utilidad conjunta `f(S)`.
2. **Parte 1 — Reparto:** el presupuesto `B` se reparte entre los `k` nodos seleccionados con el voraz por ganancia marginal (montículo), maximizando `Σ u_i(x_i)`.
3. **Verificación:** se comprueban las restricciones y, si se pide, se compara contra el óptimo exacto en casos pequeños.

```
caso.json → validar → Parte 2 (selección) → Parte 1 (reparto) → verificar → resultado.json + traza.json
```

---

## 2. Formato de entrada

Un caso = un archivo JSON (UTF-8). Se puede pasar un archivo o una carpeta con varios `.json`. En una carpeta se procesan solo los `.json` directos; las subcarpetas se ignoran. Se acepta UTF-8 con o sin BOM.

### 2.1 Campos globales

| Campo | Tipo | Obligatorio | Restricción | Significado |
|---|---|---|---|---|
| `nombre` | string | No | — | Nombre descriptivo del caso. Solo aparece en el campo `caso` de `resultado.json`. Si falta, se usa el nombre del archivo sin `.json`. |
| `N` | entero | Sí | `N ≥ 1` | Número de nodos candidatos. |
| `k` | entero | Sí | `1 ≤ k < N` | Nodos a seleccionar en la ronda. |
| `B` | entero | Sí | `B ≥ 0` | Presupuesto total en unidades enteras. |
| `universo` | entero | Sí | `≥ 0` | Tamaño `|U|`; los elementos son `0, 1, …, |U|−1`. |
| `pesos_universo` | lista de números | No | longitud `|U|`, valores `≥ 0` | Peso de cada elemento. Si falta, todos valen 1. |
| `nodos` | lista de objetos | Sí | longitud exactamente `N` | Descripción de cada nodo (ver 2.2). |

### 2.2 Campos de cada nodo

| Campo | Tipo | Obligatorio | Restricción | Significado |
|---|---|---|---|---|
| `id` | entero o string | Sí | único, comparado como texto | Identificador del nodo. |
| `cubre` | lista de enteros | Sí | valores en `[0, |U|)`, sin repetidos | Elementos del universo que aporta el nodo (Parte 2). |
| `utilidad` | objeto | Sí | ver 2.3 | Función `u_i(x)` del nodo (Parte 1). |

### 2.3 Representación de la utilidad `u_i(x)`

La Definición 3.2.1 exige `u_i` definida sobre enteros no negativos, **creciente y cóncava**. Se aceptan dos formas:

**a) Tabla (forma canónica)**
```json
{ "tipo": "tabla", "valores": [u(0), u(1), ..., u(L)] }
```
- Si `L < B`, para `x > L` se asume `u(x) = u(L)` (ganancia marginal 0). Esto conserva la monotonía y la concavidad.
- Ganancia marginal: `g(x) = u(x+1) − u(x)`.

**b) Logarítmica (para instancias grandes)**
```json
{ "tipo": "log", "a": 6.0, "b": 1.0 }
```
- `u(x) = a · ln(1 + b·x)`, con `a ≥ 0` y `b > 0`. Es creciente y cóncava por construcción.

En ambas formas se permite `u(0) ≠ 0`, porque la Definición 3.2.1 no lo restringe. Cualquier otro valor de `tipo` es un error `E10`.

### 2.4 Utilidad conjunta `f(S)` (Parte 2)

Cobertura ponderada:

```
f(S) = Σ  w_e      para todo e ∈ ⋃_{i∈S} cubre_i
```

Con pesos unitarios es exactamente `|⋃_{i∈S} cubre_i|`, la función de la reducción desde Cobertura Máxima. Es monótona y submodular por construcción.

### 2.5 Validaciones (antes de ejecutar cualquier algoritmo)

| Código | Condición que se verifica |
|---|---|
| `E01` | El archivo es JSON válido en UTF-8 y tiene todos los campos obligatorios, incluidos `tipo` y sus parámetros (`valores`, o `a` y `b`) dentro de `utilidad`. |
| `E02` | Tipos correctos en todos los campos (ver reglas de tipos abajo). |
| `E03` | `N ≥ 1`, `1 ≤ k < N`, `B ≥ 0`, `universo ≥ 0`. |
| `E04` | `len(nodos) == N` y los `id` son únicos al compararlos como texto: `1` y `"1"` son duplicados. |
| `E05` | Cada elemento de `cubre` está en `[0, |U|)` y no se repite dentro del nodo. |
| `E06` | `pesos_universo`, si existe, tiene longitud `|U|` y valores `≥ 0`. |
| `E07` | Utilidad creciente: `g(x) ≥ 0` para todo `x` (tolerancia `1e−9`). |
| `E08` | Utilidad cóncava: `g(x+1) ≤ g(x)` para todo `x` (tolerancia `1e−9`). |
| `E09` | Utilidad `log` con `a ≥ 0` y `b > 0`; todos los números de cualquier campo son finitos (sin `NaN` ni `Infinity`). |
| `E10` | El `tipo` de la utilidad es `tabla` o `log`; cualquier otro valor es un tipo desconocido. |

**Reglas de tipos (`E02`):**
- **Enteros:** `N`, `k`, `B`, `universo` y los elementos de `cubre`. `id` es entero o string.
- **Reales con valor entero exacto:** se aceptan como enteros y se normalizan (`10.0` → `10`). Si tienen parte decimal (`10.5`), dan `E02`.
- **Booleanos:** se rechazan en cualquier campo numérico o `id`.
- **Estructura:** `nombre` es string; `nodos`, `cubre`, `pesos_universo` y `valores` son listas; `valores` no puede estar vacía; `utilidad` y cada nodo son objetos; `valores`, `pesos_universo`, `a` y `b` contienen números.
- **Números no finitos:** se reportan solo como `E09`, no además como `E02`.
- **`id` real:** `1.0` se normaliza a `1`, así que es duplicado de `1` y de `"1"`.
- **Raíz:** un JSON cuya raíz no es un objeto da `E01`.
- **`nombre`:** un string vacío o solo con espacios no da error, pero se usa el nombre del archivo.
- **Campos adicionales:** los campos no definidos en esta especificación se ignoran y no se validan.
- **Utilidad `log` evaluable:** si `u(B+1)` desborda el rango de los reales, da `E09`.
- **`universo` enorme:** si los pesos por defecto de `|U|` elementos no caben en memoria, da `E03`.

Las comprobaciones que dependen de un campo ya inválido se omiten para no reportar errores en cascada.

Si un caso es inválido, **no se ejecuta**, se reportan todos los errores encontrados (no solo el primero) y el programa **continúa con el siguiente caso**.

### 2.6 Ejemplo completo (`casos_ejemplo/ejemplo_01.json`)

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

**Resultado esperado (calculado a mano; sirve como prueba):**

*Selección:*
- Paso 1: ganancias `{0: 3, 1: 2, 2: 3, 3: 2}` → empate 0 y 2 → se elige **0** (desempate por índice).
- Paso 2: ganancias `{1: 1, 2: 3, 3: 1}` → se elige **2**. `f(S) = 6`.

*Reparto entre {0, 2}* (ganancias del nodo 2: 4.1589, 2.4328, 1.7261, …):

| Unidad | Ganancia nodo 0 | Ganancia nodo 2 | Asignada a |
|---|---|---|---|
| 1 | 5 | 4.1589 | 0 |
| 2 | 3 | 4.1589 | 2 |
| 3 | 3 | 2.4328 | 0 |
| 4 | 2 | 2.4328 | 2 |
| 5 | 2 | 1.7261 | 0 |

Reparto final `x_0 = 3, x_2 = 2`. Utilidad total `u_0(3) + u_2(2) = 10 + 6·ln 3 ≈ 16.5917`.

---

## 3. Reglas de los algoritmos

### 3.1 Parte 2 — Voraz submodular
- En cada uno de los `k` pasos se calcula la ganancia marginal de **todos** los nodos no seleccionados y se elige la mayor.
- Se implementa la versión directa (sin *lazy greedy*) para que el código coincida con el análisis `T(N, k) = O(N · k · τ)`.
- Se mantiene un arreglo booleano `cubierto[0..|U|−1]`, así la ganancia de un nodo cuesta `τ = O(|cubre_i|) ≤ O(|U|)`.
- Se eligen siempre exactamente `k` nodos, aunque las ganancias restantes sean 0.

### 3.2 Parte 1 — Voraz por ganancia marginal con montículo
- Montículo con clave `(−round(ganancia_siguiente, 9), índice)`: en la cima queda la mayor ganancia y, si empatan, el primer nodo de la lista (sección 3.3). Construcción con `heapify` en `O(N)`.
- Cada unidad: extraer el máximo, asignar, recalcular su siguiente ganancia, reinsertar → `O(log N)`.
- **Parada:** se detiene al agotar `B` o cuando la ganancia del nodo en la cima cumple `g ≤ 1e−9`. Lo no gastado se reporta como `presupuesto_sin_usar` (gastar presupuesto sin ganancia solo agrega ruido).
- **Utilidad total:** `Σ u_i(x_i)` sobre los `k` seleccionados, incluido `u_i(0)` en los que reciben 0 unidades.
- Complejidad: `T(N, B) = O(N + B log N)`.

### 3.3 Desempates y tolerancia
- Las ganancias se comparan redondeadas a 9 decimales con `round(g, 9)`, tanto en la selección como en el reparto. Si empatan, gana el nodo que aparece primero en la lista `nodos`.
- El redondeo agrupa valores: dos ganancias a menos de `1e−9` pueden caer en grupos distintos y no empatar. Se acepta porque la regla es determinista y conserva `O(log N)` en el montículo.
- El redondeo solo se usa para comparar. La utilidad se acumula con las ganancias sin redondear.
- Esto hace la salida **determinista**: la misma entrada siempre produce la misma salida y la misma traza.

### 3.4 Verificación contra el óptimo (`--verificar`)
- **Parte 2:** fuerza bruta sobre los `C(N, k)` subconjuntos si `C(N, k) ≤ 10⁶`; se reporta `f_optimo`, la razón `f(S) / f_optimo` y si cumple `≥ 1 − 1/e ≈ 0.6321`. Si `f_optimo = 0`, la razón vale 1 y la cota se da por cumplida. Si el caso es demasiado grande, se omite y se indica el motivo.
- **Parte 1:** programación dinámica exacta `O(k · B²)` si `k · B² ≤ 10⁷`; se reporta si el voraz coincide con el óptimo: diferencia `≤ 2e−9 · B + 1e−12 · |óptimo|`.
- Esa tolerancia cubre lo que el voraz puede perder por la sección 3.3 y la parada, hasta `1.5e−9` por unidad, más el error de coma flotante. Un valor fijo de `1e−9` daría falsos negativos: 10 unidades con ganancias de `1.0` y `1.0 + 4e−10` empatan al redondear y acumulan `4e−9`. La cota supone concavidad exacta; una tabla aceptada gracias a la tolerancia de `E08` puede superarla, y entonces se reporta `voraz_es_optimo: false`.
- Las comprobaciones se hacen con precisión completa, antes de redondear la salida.
- Sin `--verificar`, `verificacion_optimo` es `null`. La sección `verificacion_restricciones` se calcula siempre. Si `parte1` o `parte2` se omite por tamaño, esa parte contiene `{"omitida": true, "motivo": "..."}`.

---

## 4. Formato de salida

Por cada caso se crea `<salida>/<carpeta>/`, donde `<salida>` es el argumento `--output` y `<carpeta>` es el nombre del archivo de entrada sin `.json`, sanitizado:

- Los caracteres `< > : " / \ | ? *` y los de control se reemplazan por `_`.
- Se eliminan los espacios y puntos finales.
- Los nombres reservados de Windows (`CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`, `LPT1`–`LPT9`) llevan el prefijo `_`.
- Si el resultado queda vacío, se usa `caso`.
- Si dos carpetas coinciden sin distinguir mayúsculas, se añade `_2`, `_3`, etc. Los archivos se procesan en orden alfabético, así que el sufijo es determinista.

**Reglas numéricas de toda la salida (JSON y CSV):**

- Se calcula con precisión completa y se escribe redondeado.
- Utilidades, ganancias y razones: 4 decimales, escritas siempre como número real (`3.0`, no `3`).
- Tiempos en milisegundos: 6 decimales.

Los `id` de nodo conservan su tipo como valores y se escriben como texto cuando son claves de un objeto JSON.

### 4.1 `resultado.json`
```json
{
  "caso": "ejemplo_01",
  "estado": "ok",
  "parametros": { "N": 4, "k": 2, "B": 5, "universo": 6 },
  "seleccion": { "nodos": [0, 2], "utilidad_conjunta": 6.0 },
  "reparto": {
    "asignacion": { "0": 3, "2": 2 },
    "utilidad_total": 16.5917,
    "presupuesto_usado": 5,
    "presupuesto_sin_usar": 0
  },
  "verificacion_restricciones": {
    "seleccion_tiene_k_nodos": true,
    "seleccion_sin_repetidos": true,
    "suma_asignacion_menor_igual_B": true,
    "asignacion_solo_a_seleccionados": true,
    "asignaciones_no_negativas": true
  },
  "verificacion_optimo": {
    "parte2": { "f_optimo": 6.0, "razon": 1.0, "cumple_cota_1_menos_1_e": true },
    "parte1": { "utilidad_optima": 16.5917, "voraz_es_optimo": true }
  },
  "tiempos_ms": { "seleccion": 0.012, "reparto": 0.008, "total": 0.020, "repeticiones": 5, "estadistico": "mediana" }
}
```
- `caso` contiene el campo `nombre` de la entrada o, si falta o no es un string válido, el nombre del archivo sin `.json`.
- `asignacion` incluye a los `k` seleccionados, también a los que reciben 0 unidades.
- `tiempos_ms.total` es la mediana de los totales por repetición, así que puede diferir de la suma de las medianas de `seleccion` y `reparto`.
- Si el caso es inválido, `resultado.json` contiene solo `caso`, `"estado": "invalido"` y `"errores": [{"codigo": "E08", "detalle": "..."}]`, y no se genera `traza.json`.
- Si ocurre un error inesperado al procesar un caso (por ejemplo, falta de memoria o un valor que desborda), `resultado.json` tiene la misma forma con `"estado": "error"` y `"codigo": "INTERNO"`, tampoco se genera `traza.json` y el lote continúa.

### 4.2 `traza.json`
```json
{
  "seleccion": [
    { "paso": 1,
      "ganancias": { "0": 3.0, "1": 2.0, "2": 3.0, "3": 2.0 },
      "elegido": 0, "ganancia": 3.0, "utilidad_acumulada": 3.0 }
  ],
  "reparto": [
    { "unidad": 1,
      "candidatos": { "0": 5.0, "2": 4.1589 },
      "asignada_a": 0, "ganancia": 5.0, "x_nuevo": 1, "utilidad_acumulada": 5.0 }
  ]
}
```

### 4.3 `<salida>/resumen.csv` (todos los casos)
```
caso,estado,N,k,B,universo,f_S,utilidad_total,presupuesto_usado,t_seleccion_ms,t_reparto_ms,t_total_ms,razon_optimo
```
- `caso` es el nombre de `<carpeta>`, para que cada fila identifique su caso sin ambigüedad.
- Los valores no disponibles quedan vacíos: `razon_optimo` sin `--verificar` o si se omitió la Parte 2 por tamaño, y los datos que no se pudieron obtener de un caso inválido.

### 4.4 Medición de tiempos
- `time.perf_counter()`, sin incluir lectura de archivos ni escritura de resultados.
- Los tiempos se miden **con la traza desactivada**, para no contaminar la medición. Se repite `r` veces (por defecto 5) y se reporta la mediana. Después se hace una ejecución adicional con traza para generar `traza.json`.

---

## 5. Ejecución

```bash
# Resolver un caso o una carpeta de casos
python main.py --input casos/ --output resultados/ [--verificar] [--traza completa|resumen|ninguna] [--repeticiones 5]

# Generar instancias sintéticas reproducibles
python generar.py --N 50 --k 10 --B 200 --universo 100 --semilla 42 --salida casos/
```

- **Obligatorios:** `--input` y `--output`.
- **Valores por defecto:** sin `--verificar` (no se compara contra el óptimo), `--traza completa`, `--repeticiones 5`.
- `--traza resumen`: en la Parte 2 guarda solo el elegido por paso (sin las ganancias de todos los candidatos); útil para casos grandes.
- `--traza ninguna`: no se genera `traza.json`.
- Código de salida: `0` si todos los casos válidos terminaron, `1` si hubo algún caso inválido o con error (igual se procesan todos), `2` si el argumento de entrada no existe, es una carpeta sin archivos `.json` o no se puede escribir en `--output` (con un mensaje que lo explica).

---

## 6. Estructura del repositorio

```
proyecto-red/
├── README.md
├── ESPECIFICACION.md
├── requirements.txt          # núcleo: solo librería estándar; pytest para pruebas
├── pytest.ini                # permite ejecutar pytest desde la raíz
├── main.py                   # CLI: recorre casos, ejecuta, escribe salidas
├── generar.py                # generador de instancias con semilla
├── src/
│   ├── modelo.py             # clases Caso, Nodo, Utilidad (tabla y log)
│   ├── lector.py             # lectura JSON → modelo
│   ├── validacion.py         # E01–E10, devuelve lista de errores
│   ├── seleccion.py          # Parte 2: voraz submodular (+ traza opcional)
│   ├── reparto.py            # Parte 1: voraz con heapq (+ traza opcional)
│   ├── exactos.py            # fuerza bruta Parte 2 y DP Parte 1 (verificación)
│   └── salida.py             # escritura de resultado.json, traza.json, resumen.csv
├── casos_ejemplo/
│   ├── ejemplo_01.json       # el caso de la sección 2.6
│   └── invalido_01.json      # utilidad no cóncava, para mostrar validación
└── tests/
    ├── test_validacion.py
    ├── test_seleccion.py
    ├── test_reparto.py
    ├── test_contra_exactos.py
    └── test_cli.py
```

Python 3.10+. El núcleo usa solo la librería estándar (`json`, `heapq`, `math`, `itertools`, `time`, `argparse`, `csv`). `pytest` se instala en un `.venv/` local dentro del repositorio, que no se versiona.

---

## 7. Pruebas mínimas

1. `ejemplo_01.json` produce exactamente el resultado de la sección 2.6.
2. Cada error `E01–E10` tiene al menos un caso que lo dispara.
3. **Parte 1:** en 200 instancias aleatorias pequeñas, el voraz coincide con la DP exacta (diferencia `≤ 1e−9`); con ganancias casi iguales, dentro de la tolerancia de la sección 3.4.
4. **Parte 2:** en 200 instancias aleatorias pequeñas, `f(S_voraz) ≥ (1 − 1/e) · f_optimo`.
5. Determinismo: ejecutar dos veces el mismo caso produce archivos idénticos (excepto tiempos).
6. Bordes: `B = 0`, `universo = 0`, nodos con `cubre` vacío, tabla de utilidad más corta que `B`, `f_optimo = 0`, nodo seleccionado con 0 unidades.
7. Tipos: `10.0` se acepta como entero, `10.5` da `E02` y los booleanos se rechazan; `1` y `"1"` como `id` dan `E04`.
8. Salida: la carpeta usa el nombre sanitizado del archivo y las colisiones reciben sufijo; las subcarpetas de `--input` se ignoran; una parte omitida por tamaño reporta `omitida` y `motivo`; los valores por defecto de la CLI y los códigos de salida se cumplen.

---

## 8. Limitaciones conocidas (para el manual)

- La verificación contra el óptimo solo es posible en casos pequeños (`C(N, k) ≤ 10⁶`, `k·B² ≤ 10⁷`).
- `T(N, B) = O(N + B log N)` es pseudo-polinomial: depende del valor de `B`, no de su tamaño en bits.
- La utilidad conjunta implementada es cobertura ponderada; otras funciones submodulares requieren una nueva implementación de `f`.
- Las variantes del proyecto (costos de participación, rondas con fallas, nodos vecinos) no hacen parte de esta entrega; la estructura modular permite agregarlas.

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

Se aceptan dos formatos, y en una misma carpeta pueden mezclarse:

- **Formato propio** (secciones 2.1–2.6): utilidad conjunta por cobertura ponderada.
- **Formato de la docente** (sección 2.7): utilidad conjunta por influencia en un grafo.

**Detección automática:** si la raíz es un objeto con el campo `parametros` o el campo `grafo`, el caso se lee en el formato de la docente; en otro caso, en el formato propio. Un archivo completo de la docente trae `parametros`, `grafo` y `nodos` con `coeficiente_utilidad`. Basta uno de los dos primeros campos para que un archivo incompleto de la docente reporte sus propios errores (`E11`, falta un campo) y no los del formato propio.

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

En el formato propio, cobertura ponderada (la del formato de la docente está en la sección 2.7):

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

### 2.7 Formato de la docente

Es el formato de los casos de prueba de la docente (`casos_ejemplo/entrada_G2_red_15_nodos.json`):

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

**Campos y mapeo al modelo:**

| Campo | Tipo | Obligatorio | Restricción | Uso |
|---|---|---|---|---|
| `nombre` | string | No | — | Igual que en el formato propio. |
| `parametros` | objeto | Sí | — | Parámetros de la ronda. |
| `parametros.numero_nodos` | entero | Sí | `≥ 1` | `N`. |
| `parametros.cupo_participantes_por_ronda_k` | entero | Sí | `1 ≤ k ≤ N` | `k`. |
| `parametros.presupuesto_ruido_por_ronda_B` | entero | Sí | `≥ 0` | `B`. |
| `parametros.numero_rondas` | cualquiera | No | — | Se lee pero no se usa (ver abajo). |
| `parametros.presupuesto_costos_participacion_por_ronda` | cualquiera | No | — | Se lee pero no se usa. |
| `grafo` | lista de objetos | Sí | puede ser vacía | Aristas de influencia (ver abajo cuándo son dirigidas). |
| `grafo[j].u`, `grafo[j].v` | entero o string | Sí | `id` existentes, `u ≠ v`, sin repetir el mismo par ordenado | Extremos de la arista: `u` influye sobre `v`. |
| `grafo[j].peso_influencia` | número | Sí | en `[0, 1]` | `p_uv`; también `p_vu` si el par aparece en una sola dirección. |
| `nodos` | lista de objetos | Sí | longitud exactamente `N` | Nodos candidatos. |
| `nodos[i].id` | entero o string | Sí | único, comparado como texto | Identificador. |
| `nodos[i].coeficiente_utilidad` | número | Sí | `≥ 0` | `c_i`. |
| `nodos[i].presupuesto_total_nodo` | entero | Sí | `≥ 0` | Tope `T_i` de unidades útiles del nodo. |
| `nodos[i].costo_participacion` | cualquiera | No | — | Se lee pero no se usa. |

En este formato se permite `k = N` (todos los nodos participan): un caso de la docente con `k = N` es legítimo y los algoritmos lo resuelven sin cambios. En el formato propio se mantiene `k < N`.

**Sentido de las aristas.** `{"u": u, "v": v, "peso_influencia": p}` significa "`u` influye sobre `v` con probabilidad `p`", es decir, `p_uv = p`.

- Si el par aparece en **una sola dirección**, la arista es no dirigida: `p_uv = p_vu = p`.
- Si aparece en **las dos direcciones**, `(u, v)` y `(v, u)`, cada una conserva su peso: `p_uv` y `p_vu` pueden ser distintos (influencia dirigida).
- Repetir la **misma dirección** (`(u, v)` dos veces) o un lazo (`u = v`) es `E14`.

Con pesos iguales en las dos direcciones el resultado es el mismo que con la arista escrita una sola vez.

**Utilidad de cada nodo (Parte 1):** la utilidad `log` existente con `a = c_i`, `b = 1`, truncada en el tope:

```
u_i(x) = c_i · ln(1 + min(x, T_i))
```

Para `x > T_i` vale `u_i(T_i)` (ganancia marginal 0), así que sigue siendo creciente y cóncava, igual que una tabla más corta que `B` (sección 2.3). Como el voraz se detiene en cada nodo cuando su ganancia es 0, ningún nodo recibe más de `T_i` unidades.

**Utilidad conjunta (Parte 2), influencia:**

```
f(A) = Σ_v c_v · [1 − Π_{u∈A} (1 − p_uv)]
```

con `p_vv = 1` y `p_uv = 0` si no hay arista de `u` hacia `v`. Es una cobertura probabilística ponderada: el nodo `v` queda cubierto por `A` con probabilidad `1 − Π (1 − p_uv)`, y estar en `A` lo cubre del todo. Es monótona y submodular porque cada término es `c_v ≥ 0` por una función de cobertura probabilística con `p_uv ∈ [0, 1]`; el argumento no usa la simetría, así que vale igual con `p_uv ≠ p_vu`. Con `p_uv ∈ {0, 1}` y `c_v = 1` se reduce a la cobertura de vecindarios, un caso de Cobertura Máxima.

**Campos no usados:** `numero_rondas`, `presupuesto_costos_participacion_por_ronda` y `costo_participacion` pertenecen a las variantes (rondas, costos de participación), que no hacen parte de esta entrega. Se copian tal cual a `resultado.json` bajo `campos_no_usados` (sección 4.1); los que no vienen en la entrada se omiten.

**Validaciones propias de este formato:**

| Código | Condición que se verifica |
|---|---|
| `E11` | Están todos los campos obligatorios de la tabla anterior. |
| `E12` | `numero_nodos ≥ 1`, `1 ≤ k ≤ N` y `B ≥ 0`. |
| `E13` | Los extremos `u` y `v` de cada arista son `id` de nodos existentes (comparados como texto). |
| `E14` | No hay lazos (`u = v`) ni aristas repetidas en la misma dirección (`(u, v)` dos veces). `(u, v)` y `(v, u)` juntas sí se permiten. |
| `E15` | `peso_influencia` está en `[0, 1]`. |
| `E16` | `coeficiente_utilidad ≥ 0`. |
| `E17` | `presupuesto_total_nodo ≥ 0`. |

Las condiciones que también existen en el formato propio conservan su código: `E01` (JSON ilegible o raíz que no es objeto), `E02` (tipos, con las mismas reglas de la sección 2.5), `E04` (`len(nodos) ≠ numero_nodos` o `id` repetidos) y `E09` (números no finitos, o `c_i · ln(1 + (B+1))` que desborda: la misma comprobación de la utilidad `log`, sin truncar en el tope). Las comprobaciones que dependen de un campo inválido se omiten, como en el formato propio.

**Resultado esperado de `entrada_G2_red_15_nodos.json`** (sirve como prueba):

- Selección voraz: `N11, N14, N09, N15, N13`, con `f ≈ 145.5795`.
- Óptimo por fuerza bruta: `{N09, N11, N12, N13, N15}`, con `f ≈ 145.9072`; razón `≈ 0.99775`.
- Reparto: `N11 = 5, N14 = 7, N09 = 7, N15 = 6, N13 = 5`, utilidad `≈ 88.564`, igual a la DP.

---

## 3. Reglas de los algoritmos

### 3.1 Parte 2 — Voraz submodular
- En cada uno de los `k` pasos se calcula la ganancia marginal de **todos** los nodos no seleccionados y se elige la mayor.
- Se implementa la versión directa (sin *lazy greedy*) para que el código coincida con el análisis `T(N, k) = O(N · k · τ)`.
- La utilidad conjunta es una **estrategia intercambiable** (`src/conjunta.py`): cobertura (formato propio) o influencia (formato de la docente). El voraz y la fuerza bruta usan la misma interfaz: estado inicial, ganancia marginal de un candidato, agregar un nodo, y valor `f(A)` de un subconjunto.
- **Cobertura:** se mantiene un arreglo booleano `cubierto[0..|U|−1]`, así la ganancia de un nodo cuesta `τ = O(|cubre_i|) ≤ O(|U|)`.
- **Influencia:** se mantiene `q[v] = Π_{u∈A} (1 − p_uv)` para cada nodo `v` (al inicio vale 1). La ganancia de un candidato `u` es `Σ_v c_v · q[v] · p_uv = c_u · q[u] + Σ_{(u,v)∈E} c_v · q[v] · p_uv`, recorriendo la lista de adyacencia de `u`, que guarda sus aristas **salientes** `(v, p_uv)` (una arista no dirigida aparece en las listas de sus dos extremos): `τ = O(1 + grado(u)) ≤ O(N)`. Al agregar `u`: `q[u] = 0` y `q[v] ← q[v] · (1 − p_uv)` para sus vecinos. Así `T(N, k) = O(N · k · N) = O(N² · k)` en el peor caso (grafo completo, como el de la docente).
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
- **Parte 2:** fuerza bruta sobre los `C(N, k)` subconjuntos si `C(N, k) ≤ 10⁶`, con la misma utilidad conjunta del caso (cobertura o influencia); se reporta `f_optimo`, la razón `f(S) / f_optimo` y si cumple `≥ 1 − 1/e ≈ 0.6321`. Si `f_optimo = 0`, la razón vale 1 y la cota se da por cumplida. Si el caso es demasiado grande, se omite y se indica el motivo.
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
- **Formato de la docente:** `resultado.json` agrega `"formato": "docente"` después de `estado`; `parametros.universo` vale `null` (no hay universo); `verificacion_restricciones` agrega `"asignacion_respeta_topes"` (`x_i ≤ presupuesto_total_nodo` para cada seleccionado), y antes de `tiempos_ms` va:
  ```json
  "campos_no_usados": {
    "nota": "variantes, entregas posteriores",
    "numero_rondas": 3,
    "presupuesto_costos_participacion_por_ronda": 24,
    "costo_participacion": { "N01": 3, "N02": 5, "...": "..." }
  }
  ```
  En el formato propio la salida no cambia. En `resumen.csv` la columna `universo` queda vacía para los casos de la docente.
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
- Código de salida: `0` si todos los casos válidos terminaron, `1` si hubo algún caso inválido o con error (igual se procesan todos), `2` si los argumentos de la línea de comandos son inválidos, si el argumento de entrada no existe o es una carpeta sin archivos `.json`, o si no se puede escribir en `--output` (con un mensaje que lo explica).

**Generador (`generar.py`):**
- **Obligatorios:** todos sus argumentos (`--N`, `--k`, `--B`, `--universo`, `--semilla`, `--salida`). Los valores deben cumplir `E03`.
- **Archivo:** crea la carpeta `--salida` si hace falta y escribe `gen_N<N>_k<k>_B<B>_U<universo>_s<semilla>.json`, con ese mismo texto en `nombre`. Los mismos argumentos producen un archivo idéntico.
- **Contenido:** pesos reales aleatorios; cada nodo cubre entre 0 y `⌊universo/2⌋` elementos, y su utilidad es tabla (con a lo sumo 50 ganancias, y que puede ser más corta que `B`) o `log`, con la misma probabilidad.
- **Código de salida:** `0` si escribe el archivo; `2` si los argumentos son inválidos o no se puede escribir en `--salida` (con un mensaje que lo explica).

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
│   ├── modelo.py             # clases Caso, Nodo, Utilidad (tabla y log, con tope opcional)
│   ├── conjunta.py           # utilidad conjunta intercambiable: cobertura e influencia
│   ├── lector.py             # lectura JSON → modelo, detecta el formato
│   ├── validacion.py         # E01–E10 (propio) y E11–E17 (docente), devuelve lista de errores
│   ├── seleccion.py          # Parte 2: voraz submodular (+ traza opcional)
│   ├── reparto.py            # Parte 1: voraz con heapq (+ traza opcional)
│   ├── exactos.py            # fuerza bruta Parte 2 y DP Parte 1 (verificación)
│   └── salida.py             # escritura de resultado.json, traza.json, resumen.csv
├── casos_ejemplo/
│   ├── ejemplo_01.json       # el caso de la sección 2.6
│   ├── invalido_01.json      # utilidad no cóncava, para mostrar validación
│   └── entrada_G2_red_15_nodos.json  # caso de la docente (sección 2.7)
└── tests/
    ├── test_validacion.py
    ├── test_conjunta.py
    ├── test_formato_docente.py
    ├── test_seleccion.py
    ├── test_reparto.py
    ├── test_contra_exactos.py
    ├── test_cli.py
    ├── test_generar.py
    └── test_bordes.py
```

Python 3.10+. El núcleo usa solo la librería estándar (`json`, `heapq`, `math`, `itertools`, `time`, `statistics`, `random`, `argparse`, `csv`). `pytest` se instala en un `.venv/` local dentro del repositorio, que no se versiona.

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
9. **Formato de la docente:** se detecta solo; `entrada_G2_red_15_nodos.json` produce los valores de la sección 2.7; la `f` de influencia es monótona y submodular en instancias aleatorias, simétricas y dirigidas; un par en las dos direcciones se acepta con pesos distintos; el voraz y la fuerza bruta funcionan con las dos estrategias; cada error `E11–E17` tiene al menos un caso que lo dispara.

---

## 8. Limitaciones conocidas (para el manual)

- La verificación contra el óptimo solo es posible en casos pequeños (`C(N, k) ≤ 10⁶`, `k·B² ≤ 10⁷`).
- `T(N, B) = O(N + B log N)` es pseudo-polinomial: depende del valor de `B`, no de su tamaño en bits.
- Hay dos utilidades conjuntas: cobertura ponderada e influencia. Otra función submodular requiere una nueva estrategia en `src/conjunta.py`, sin tocar el voraz ni la fuerza bruta.
- Con influencia, el voraz cuesta `O(N² · k)` en un grafo completo; la DP de verificación no cambia.
- El grafo de la docente se lee con un **modelo mixto**: un par escrito una vez es simétrico y un par escrito en las dos direcciones es dirigido. Si la docente quisiera un grafo totalmente dirigido escribiendo cada arista una sola vez, este programa la estaría simetrizando. Conviene confirmar con ella cómo escribe las aristas su generador.
- Las variantes del proyecto (costos de participación, rondas con fallas, nodos vecinos) no hacen parte de esta entrega; la estructura modular permite agregarlas. Del formato de la docente, `numero_rondas`, `presupuesto_costos_participacion_por_ronda` y `costo_participacion` se reportan sin usarse.

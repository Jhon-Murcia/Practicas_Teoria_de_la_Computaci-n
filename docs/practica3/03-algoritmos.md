# Ejercicio 3. Documentación de los algoritmos

Todos los algoritmos están en Python puro, en [`src/algoritmos/`](../../src/algoritmos/), sin
bibliotecas de autómatas, y se ejecutan y prueban sin abrir la interfaz. Cada uno devuelve, además de
su resultado, la lista de pasos (`algoritmos.pasos.Paso`) que la interfaz reproduce: los pasos se
registran durante la ejecución real, no son una animación aparte.

Notación del coste: n = |Q|, k = |Σ|, m = número de transiciones.

Referencia principal: Hopcroft, J. E., Motwani, R., y Ullman, J. D. (2007), *Introduction to Automata
Theory, Languages, and Computation* (3.ª ed.). Las secciones citadas son de esa edición; verifique la
numeración si usa otra edición o el libro de texto oficial del curso.

> Los ejemplos que siguen son **propios** (no de las listas). Para cada uno se muestra el desarrollo
> a mano y la salida obtenida con el software; los resultados de ambos coinciden. Para documentar
> ejemplos de las listas, cargue sus `.jff` en el software y repita la comparación.

---

## 1. λ-clausura

**Problema.** Dado q, encontrar los estados alcanzables desde q usando sólo transiciones λ.

**Respaldo teórico.** Definición recursiva de ECLOSE(q) (sec. 2.5.3): q ∈ ECLOSE(q), y si p ∈ ECLOSE(q)
y r ∈ δ(p, λ), entonces r ∈ ECLOSE(q).

**Pseudocódigo** ↔ `algoritmos/cerradura.py`

```
cerradura(q):                          # cerradura_con_pasos(a, q)
    C := {q};  pila := [q]
    mientras pila ≠ ∅:
        p := pila.sacar()
        para cada r ∈ δ(p, λ):
            si r ∉ C:  C := C ∪ {r};  pila.meter(r)
    devolver C
```

`cerradura(a, estados)` es la misma idea para un conjunto; `tabla_cerraduras(a)` la aplica a cada estado.

**Ejemplo** (AFND-λ *a\*b\*c\**: p –λ→ q –λ→ r, con bucles a, b, c).

| A mano | Software |
|---|---|
| λ-cl(p): {p}; δ(p,λ) = {q} → {p,q}; δ(q,λ) = {r} → {p,q,r}; δ(r,λ) = ∅. | `{p, q, r}` |
| λ-cl(q): {q} → {q, r}. | `{q, r}` |
| λ-cl(r): {r}. | `{r}` |

**Coste.** Cada estado entra a la pila una vez y cada arista λ se revisa una vez: O(n + m_λ) por
estado y O(n·(n + m_λ)) para la tabla.

**Papel en el reconocimiento.** La simulación directa ([`core/simulacion.py`](../../src/core/simulacion.py))
parte de λ-cl(q0) y, tras leer cada símbolo, vuelve a aplicar la clausura. La pantalla de simulación
muestra el conjunto antes y después de la clausura en cada paso.

---

## 2. Eliminación de transiciones λ

**Problema.** Dado un AFN-λ, obtener un AFN sin λ con el mismo lenguaje.

**Respaldo teórico.** Equivalencia de AFN-λ y AFN (sec. 2.5.5). Se conserva Q y se define
δ'(q, a) = λ-cl(δ(λ-cl(q), a)), F' = {q : λ-cl(q) ∩ F ≠ ∅}.

**Pseudocódigo** ↔ `algoritmos/eliminacion_lambda.py::eliminar_lambda`

```
C := tabla_cerraduras(M)
para cada q ∈ Q, a ∈ Σ:
    δ'(q, a) := ∪_{d ∈ ∪_{p ∈ C[q]} δ(p, a)} C[d]
F' := { q : C[q] ∩ F ≠ ∅ }
```

**Ejemplo** (AFND-λ del Anexo 3: δ(q0,a) = q1, δ(q0,b) = q0, δ(q0,λ) = q1, F = {q1}).

| A mano | Software |
|---|---|
| λ-cl(q0) = {q0,q1}, λ-cl(q1) = {q1}. | igual |
| δ'(q0,a) = λ-cl(δ({q0,q1},a)) = λ-cl({q1}) = {q1}. | `δ'(q0,a) = {q1}` |
| δ'(q0,b) = λ-cl({q0}) = {q0,q1} → se **agrega** q0 –b→ q1. | agregada `(q0, b, q1)` |
| q0 pasa a F' porque λ-cl(q0) ∋ q1. | nuevos de aceptación: `q0` |

**Coste.** O(n · k · n²) = O(n³k) en el peor caso, con las clausuras precalculadas.

---

## 3. Construcción de subconjuntos

**Problema.** Dado un AFN, obtener un AFD equivalente generando sólo los subconjuntos alcanzables.

**Respaldo teórico.** Teorema de equivalencia entre AFD y AFN (Rabin y Scott, 1959; sec. 2.3.5,
teorema 2.11), con la evaluación «perezosa» de los subconjuntos alcanzables descrita en la misma sección.

**Pseudocódigo** ↔ `algoritmos/subconjuntos.py::construir_afd`

```
D0 := λ-cl({q0}); cola := [D0]; vistos := {D0}
mientras cola ≠ ∅:
    S := cola.sacar()
    para cada a ∈ Σ:
        T := λ-cl(∪_{q ∈ S} δ(q, a))
        δ_D(S, a) := T
        si T ∉ vistos: vistos ∪= {T}; cola.meter(T)
F_D := { S ∈ vistos : S ∩ F ≠ ∅ }
```

**Ejemplo** (AFND *termina en ab*: δ(q0,a) = {q0,q1}, δ(q0,b) = {q0}, δ(q1,b) = {q2}, F = {q2}).

| Subconjunto | a | b | ¿Acepta? |
|---|---|---|---|
| {q0} | {q0,q1} | {q0} | no |
| {q0,q1} | {q0,q1} | {q0,q2} | no |
| {q0,q2} | {q0,q1} | {q0} | sí: contiene q2 |

La tabla a mano y la del software (mismos tres subconjuntos, misma tabla) coinciden. Se generan 3 de los
2³ = 8 posibles subconjuntos. En cambio, con *tercero desde el final es 1* (4 estados) se generan los
8 = 2³ subconjuntos que contienen a q0: la familia «el n-ésimo símbolo desde el final es 1» alcanza la
cota (sec. 2.3.6).

**Coste.** Hasta 2ⁿ subconjuntos; por cada uno y cada símbolo se unen hasta n conjuntos de destinos:
O(2ⁿ · k · n²).

---

## 4. Minimización de AFD

**Problema.** Dado un AFD, obtener el AFD con el menor número de estados que reconoce el mismo lenguaje,
y decidir con él si dos AFD son equivalentes.

**Respaldo teórico.** Equivalencia de estados y minimización (sec. 4.4.1-4.4.3); unicidad del AFD
mínimo salvo isomorfismo (sec. 4.4.4, teorema de Myhill-Nerode).

**Pseudocódigo** ↔ `algoritmos/minimizacion.py`

```
M := eliminar_inaccesibles(M)                 # eliminar_inaccesibles
M := completar(M)                             # completar: sumidero ⊥ si δ es parcial
P := {F, Q − F}                               # refinar
repetir:
    P' := para cada bloque B ∈ P, agrupar q ∈ B por (bloque de δ(q,a))_{a ∈ Σ}
    si |P'| = |P|: terminar
    P := P'
AFD mínimo: un estado por bloque              # minimizar
```

`tabla_distinguibles` implementa además el método de la tabla de pares. `equivalencia.comparar`
minimiza ambos autómatas (completos) y busca el isomorfismo recorriéndolos en paralelo; si falla,
encuentra el contraejemplo más corto con un recorrido en anchura del autómata producto.

**Ejemplo** (AFD de paridad de aes duplicado: p0, i0, p1, i1 y un estado x inaccesible; F = {p0, p1}).

| Paso | A mano | Software |
|---|---|---|
| Inaccesibles | x no se alcanza desde p0. | `inaccesibles: ['x']` |
| Completar | δ ya es total. | sin sumidero |
| P0 | {p0,p1}, {i0,i1} | `B0 = {p0, p1}  B1 = {i0, i1}` |
| Ronda 1 | p0 y p1 van con a a B1 y con b a B0: no se separan; igual i0 e i1. P1 = P0, estable. | la partición no cambia |
| Resultado | 2 estados: [p0,p1] (inicial, aceptación) y [i0,i1]. | `['[p0,p1]', '[i0,i1]']` |
| Tabla de pares | Se marcan los 4 pares con un estado de F y otro no; {p0,p1} e {i0,i1} quedan sin marcar. | igual |

**Coste.** Cada ronda revisa n·k transiciones y hay a lo sumo n rondas: O(n²k). (El algoritmo de
Hopcroft baja a O(n·k·log n) procesando siempre el bloque más pequeño; no se implementó porque el
refinamiento de Moore muestra con más claridad cada ronda.) La equivalencia agrega el isomorfismo, O(n·k).

---

## 5. De autómata a expresión regular (eliminación de estados)

**Problema.** Dado un autómata, obtener una expresión regular de su lenguaje.

**Respaldo teórico.** Teorema de Kleene, dirección AF → ER; método de eliminación de estados (sec. 3.2.2;
Brzozowski y McCluskey, 1963).

**Pseudocódigo** ↔ `algoritmos/eliminacion_estados.py::eliminar_estados`

```
agregar I –λ→ q0 y f –λ→ F para cada f ∈ F; unir aristas paralelas con +
mientras queden estados de Q:
    q := el de menos (entradas × salidas)            # o el orden indicado
    para cada p → q y q → r:
        R(p,r) := R(p,r) + R(p,q) R(q,q)* R(q,r)
    quitar q
devolver R(I, F)
```

Las expresiones se construyen con `core/expresion_regular.py`, cuyos constructores aplican las leyes
algebraicas (∅ + r = r, λr = r, ∅r = ∅, (r*)* = r*, λ + rr* = r*, …; sec. 3.4).

**Ejemplo** (*termina en ab*, orden q0, q1, q2).

| Estado eliminado | A mano | Software |
|---|---|---|
| q0 (bucle a+b) | R(I,q1) = λ(a+b)*a = (a+b)*a | `R(I,q1) = ∅ + (λ)(a+b)*(a) = (a+b)*a` |
| q1 (sin bucle) | R(I,q2) = (a+b)*a·∅*·b = (a+b)*ab | `(a+b)*ab` |
| q2 (sin bucle) | R(I,F) = (a+b)*ab·λ = (a+b)*ab | `(a+b)*ab` |

Con *binarios múltiplos de 3* el software obtiene `(0+1(01*0)*1)*`.

**Coste.** Eliminar un estado con e entradas y s salidas crea e·s expresiones: O(n³) operaciones en total;
el tamaño de la expresión puede crecer exponencialmente en el peor caso.

---

## 6. Validación de varias cadenas

`core/simulacion.py`: `leer_lineas` (una cadena por línea, `λ` es la vacía), `validar_lote` (simulación
directa de cada una) e `informe_lote` (texto con el resultado de cada cadena). Coste: la suma de las
simulaciones, O(Σ|w|·n²).

---

## Pruebas (2.6)

[`tests/test_algoritmos.py`](../../tests/test_algoritmos.py) comprueba, para cada caso, que el original,
el AFN sin λ, el AFD de subconjuntos y el AFD mínimo aceptan **exactamente las mismas cadenas** de Σ* de
longitud ≤ 8 (longitud 4 o 3 para alfabetos grandes) y que el mínimo **no tiene más estados** que el AFD
del que procede. Justificación de la longitud: los casos tienen a lo sumo 6 estados, de modo que las
cadenas de longitud ≤ 8 alcanzan todos los estados y recorren cada ciclo; como una exploración finita no
es una demostración, cada caso se confirma además con la equivalencia exacta (isomorfismo de mínimos).

Casos: los 8 ejemplos integrados, 12 AFND-λ aleatorios con semilla fija y **todos los `.jff` de
[`automatas/practica3/casos-de-prueba/`](../../automatas/practica3/casos-de-prueba/)**: si se agregan ahí
los autómatas de la Lista 3 (ejercicios 151-157, 191-194, 196-200 y 260-263), las pruebas los incluyen
sin modificar el código. [`tests/test_eliminacion_estados.py`](../../tests/test_eliminacion_estados.py)
verifica cada expresión obtenida con derivadas de Brzozowski y con `re.fullmatch`.

## Referencias

* Brzozowski, J. A., y McCluskey, E. J. (1963). Signal flow graph techniques for sequential circuit state
  diagrams. *IEEE Transactions on Electronic Computers, EC-12*(2), 67-76. https://doi.org/10.1109/PGEC.1963.263416
* Hopcroft, J. E., Motwani, R., y Ullman, J. D. (2007). *Introduction to automata theory, languages, and
  computation* (3.ª ed.). Pearson/Addison-Wesley. ISBN 978-0-321-45536-9.
* Rabin, M. O., y Scott, D. (1959). Finite automata and their decision problems. *IBM Journal of Research
  and Development, 3*(2), 114-125. https://doi.org/10.1147/rd.32.0114

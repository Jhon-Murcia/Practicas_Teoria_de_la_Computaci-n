# Ejercicio 3. Simulador de autómatas con interfaz gráfica

## Arquitectura: núcleo separado de la interfaz

```
src/
  core/
    lenguajes.py      operaciones de la Práctica 1 (sin cambios)
    automata.py       la quíntupla M = (Q, Σ, δ, q0, F) para AFD, AFND y AFND-λ
    simulacion.py     simulación directa, λ-clausura y árbol de computaciones
    disposicion.py    posiciones automáticas por capas (BFS desde q0)
    ejemplos.py       autómatas de ejemplo propios y el de aplicación (TCP)
    proyecto.py       varios autómatas en un archivo .alab.json
  formatos/
    jff.py  json_fmt.py  xml_fmt.py   lectura y escritura de los tres formatos
  ui/
    geometria.py      flechas, curvas y bucles (funciones puras, probadas)
    componentes/lienzo.py             lienzo interactivo con flet.canvas
    paginas/editor.py simulacion.py archivos.py ...
```

`core/` y `formatos/` no importan Flet: todo lo que se evalúa (modelo, simulación, formatos) se
prueba con pytest sin abrir la interfaz. `ui/geometria.py` tampoco depende de Flet.

## 3.1 Definición interactiva

**Editor visual** (pantalla *Editor*):

| Acción | Cómo |
|---|---|
| Crear estado | Herramienta *Estado* y clic en el lienzo |
| Crear transición | Herramienta *Transición*, clic en origen y en destino; se piden los símbolos (botón «Insertar λ») |
| Estado inicial / de aceptación | Interruptores del panel *Propiedades*, o la pestaña *Definición* |
| Renombrar, editar símbolos, eliminar | Panel *Propiedades* del elemento seleccionado; herramienta *Eliminar* (con confirmación para estados) |
| Mover, desplazar, zoom | Arrastre de estados y del fondo; rueda del ratón; *Ajustar vista*; *Ordenar automáticamente* |
| Deshacer / rehacer | Botones o Ctrl+Z / Ctrl+Y |

**Definición formal** (pestaña *Definición*): Σ editable, Q, q0 en una lista, F con fichas que se
activan con un clic y la quíntupla completa. **Tabla δ** (pestaña *Tabla δ*): una fila por estado
(→ inicial, * aceptación) y una columna por símbolo más λ; cada celda se edita escribiendo los
destinos separados por comas.

El tipo se **deduce** de δ y se muestra siempre junto al nombre. El diagnóstico lista cada
conflicto de determinismo con su estado y su símbolo (por ejemplo `δ(q0, a) tiene 2 destinos:
{q0, q1}`), avisa si δ es parcial y señala los estados inaccesibles.

## 3.2 Importación y 3.4 exportación

| Formato | λ | Particularidades |
|---|---|---|
| `.jff` | `<read/>` vacío | Σ se deduce de los símbolos usados; se toleran las coordenadas, el JFLAP antiguo sin `<automaton>`, nombres repetidos y transiciones de varios caracteres (se expanden con estados intermedios y se avisa). Se rechazan con mensaje claro los archivos que no son `<type>fa</type>`, sin estados, sin estado inicial o con ids inexistentes. |
| `.json` | `"lee": ""` | Esquema del Anexo 3, más `nombre`, `descripcion` y `posiciones` opcionales. `hacia` es una lista. |
| `.xml` | `lee=""` | Esquema del Anexo 3; un `<transicion>` por destino; `x` e `y` opcionales. |

Al importar, la pantalla *Archivos* muestra las **cinco componentes** interpretadas para verificarlas.
La convención para λ (cadena vacía como símbolo leído) se documenta también en el README.

**Exportar e importar son operaciones inversas.** La prueba `test_ida_y_vuelta` exporta los ocho
ejemplos en los tres formatos, los vuelve a leer, comprueba que la quíntupla es la misma y que
exportar lo leído produce *exactamente el mismo archivo*. Para lograrlo, las transiciones se
escriben en un orden canónico (estado, símbolo, destino) que no depende del orden de Σ, porque
`.jff` no guarda Σ. En la aplicación servida desde el navegador se comprobó además que el `.jff`
descargado es idéntico byte a byte al importado.

## 3.3 Simulación y la decisión de diseño para el no determinismo

**Decisión: simular el no determinismo directamente, siguiendo todos los caminos a la vez.**
En cada paso se mantiene el conjunto de estados activos *S*:

```
S0 := λ-clausura({q0})
para cada símbolo a de w:
    M := ∪_{q ∈ S} δ(q, a)          # mover
    S := λ-clausura(M)              # cerrar
aceptar  ⇔  S ∩ F ≠ ∅
```

| Alternativa | Preprocesamiento | Validar una cadena | Memoria |
|---|---|---|---|
| Simulación directa (elegida) | ninguno | O(\|w\| · \|Q\|²) en el peor caso (\|Q\| activos, cada uno con hasta \|Q\| destinos, más la clausura) | O(\|Q\|) |
| Convertir a AFD y simular | construcción de subconjuntos: hasta 2^\|Q\| estados y 2^\|Q\|·\|Σ\| transiciones | O(\|w\|) | O(2^\|Q\| · \|Σ\|) |

Se eligió la simulación directa porque (1) no paga el coste exponencial de la conversión, que en la
familia «el n-ésimo símbolo desde el final es 1» se alcanza; (2) permite mostrar, en cada paso, el
conjunto activo antes y después de la λ-clausura y las transiciones tomadas, que es lo que se quiere
enseñar; y (3) el AFD resulta un caso particular (|S| ≤ 1). La conversión sólo conviene si un mismo
autómata valida una enorme cantidad de cadenas y el AFD resultante es pequeño.

**Paso a paso.** La pantalla *Simulación* muestra la cinta con el símbolo actual, el conjunto activo
antes, las transiciones aplicadas, el resultado de leer el símbolo, las transiciones λ usadas y el
conjunto después, con el diagrama resaltado (verde si acepta, rojo si rechaza). Se avanza, retrocede
o reproduce automáticamente. La **traza completa** lista todos los pasos.

**Caminos múltiples.** Para mostrar las bifurcaciones, `arbol_computacion` explora todas las
computaciones (un nodo por estado y número de símbolos leídos, siguiendo también las transiciones λ)
y marca cada hoja como *acepta*, *no es de aceptación*, *sin transición* o *ciclo λ* (un ciclo de
transiciones λ se corta para no repetir indefinidamente). El árbol se acota a 300 nodos en la
interfaz porque su tamaño puede crecer exponencialmente.

Un símbolo que no pertenece a Σ se rechaza indicando la posición exacta. Si Σ tiene símbolos de
varios caracteres, la entrada puede separarse con espacios o comas.

## 3.4 Operaciones de la Práctica 1

Siguen disponibles en la misma interfaz (*Cadenas* y *Lenguajes*): subcadenas, prefijos, sufijos,
cerradura de Kleene y cerradura positiva.

## 3.5 Pruebas

| Archivo | Qué comprueba |
|---|---|
| [`test_formatos.py`](../../tests/test_formatos.py) | Los tres archivos del Anexo 3 dan la misma quíntupla; ida y vuelta en los tres formatos para los ocho ejemplos (operaciones inversas); conservación del lenguaje; tolerancia y rechazo de archivos inválidos; lectura de los ejemplos versionados en `automatas/`. |
| [`test_automata.py`](../../tests/test_automata.py) | Clasificación; conflictos de determinismo; edición; **aceptación y rechazo en un AFD** (comparado con la aritmética para todas las cadenas binarias de longitud ≤ 10); AFND contra la definición del lenguaje; **aceptación en un AFND-λ que requiere la λ-clausura** (`test_afnd_lambda_acepta_la_vacia_solo_por_la_clausura`: q0 ∉ F, pero λ se acepta porque q1 ∈ λ-clausura(q0)); árbol de caminos y ciclos λ; autómata TCP. |
| [`test_proyecto.py`](../../tests/test_proyecto.py) | Proyectos con varios autómatas. |
| [`test_geometria.py`](../../tests/test_geometria.py) | Geometría del diagrama. |

Total en esta práctica: **160 pruebas**, aprobadas localmente; en los contenedores y en GitHub
Actions, ver [evidencias](../../evidencias/practica2/).

## Capturas

Las capturas de la aplicación servida desde el contenedor están en
[`evidencias/practica2/app/`](../../evidencias/practica2/app/).

# Ejercicio 2. AFND y AFND-λ en JFLAP

> **Sección a cargo del alumno.** La resolución de las Listas 2 y 3, su clasificación en AFD,
> AFND y AFND-λ, las λ-clausuras y las conversiones en JFLAP corresponden al alumno. Organice los
> archivos en `automatas/lista2-afd/`, `automatas/lista3-afnd/`, `automatas/lista3-afnd-lambda/` y
> `automatas/conversiones/`.

El software ayuda en esta tarea:

* **Clasificación automática.** Al importar un `.jff`, el editor indica si es AFD, AFND o AFND-λ y,
  si no es determinista, qué estado y qué símbolo lo impiden. Sirve para comprobar la clasificación.
* **Formatos.** Cada autómata se puede exportar a `.json` y `.xml` desde la pantalla *Archivos*, como
  pide la entrega («cada autómata en .jff y adicionalmente en .json y .xml»). La herramienta
  [`herramientas/exportar_ejemplos.py`](../../herramientas/exportar_ejemplos.py) muestra cómo hacerlo
  en lote con `formatos.leer_archivo` y `formatos.guardar_archivo`.
* **Recorridos.** La simulación muestra cada paso y el *árbol de caminos* con las bifurcaciones, que
  es lo que pide documentar el apartado 2.2 para los casos no deterministas.

Para la tabla de la cota 2ⁿ, el ejemplo integrado *Tercero desde el final es 1* pertenece a la familia
Lₙ = {w : el n-ésimo símbolo desde el final es 1}, cuyo AFD mínimo necesita 2ⁿ estados
(Hopcroft, Motwani y Ullman, 2007, sec. 2.3.6).

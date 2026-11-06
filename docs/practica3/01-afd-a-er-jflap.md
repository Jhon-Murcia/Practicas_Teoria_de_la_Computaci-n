# Ejercicio 1. Conversión de AFD a expresiones regulares (JFLAP)

> **Sección a cargo del alumno.** Elegir cinco AFD de las Listas 2 y 3, convertirlos con
> *Convert FA to RE* de JFLAP, verificar con *Convert to NFA* y *Compare Equivalence*, simplificar con
> leyes algebraicas y comparar a mano los tres métodos (eliminación de estados, R_ij^(k) y lema de
> Arden). Guarde los `.jff` y sus expresiones en
> [`automatas/practica3/afd-a-er/`](../../automatas/practica3/afd-a-er/).

## Cómo ayuda el software

* **Autómata → ER** (pantalla *Conversiones*) aplica el mismo método que JFLAP, eliminación de estados,
  y muestra el autómata generalizado después de cada estado eliminado con la fórmula
  R(p,r) := R(p,r) + R(p,q)R(q,q)*R(q,r). Sirve para documentar «cada estado eliminado».
* Se puede fijar el **orden de eliminación** (el de Q) o dejar la heurística de menos combinaciones;
  comparar ambos muestra cómo el orden cambia la escritura de la expresión, no su lenguaje.
* La expresión se muestra también en la sintaxis de `re` de Python.
* Las leyes algebraicas que aplica automáticamente se listan en
  [03-algoritmos.md](03-algoritmos.md#5-de-autómata-a-expresión-regular-eliminación-de-estados).
* En la Práctica 4 se agrega el analizador de expresiones, con el que la expresión de JFLAP y la del
  software se convierten en AFD mínimos y se comparan con la prueba de equivalencia.

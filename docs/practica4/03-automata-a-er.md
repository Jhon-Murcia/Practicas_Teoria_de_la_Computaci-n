# Ejercicio 3. De autómata a expresión regular

Pantalla *Expresiones regulares → Autómata → ER*:

1. **Importar y verificar.** Se elige un autómata de la sesión o se importa un `.jff`. Si no es
   determinista se lista cada conflicto con su **estado y su símbolo** (por ejemplo «estado q0, símbolo
   a: δ(q0, a) tiene 2 destinos: {q0, q1}» o «estado p, símbolo λ: un AFD no admite transiciones λ»)
   y no se continúa.
2. **Eliminación de estados paso a paso.**
   [`algoritmos/eliminacion_estados.py`](../../src/algoritmos/eliminacion_estados.py), implementado en
   la Práctica 3 y documentado en
   [03-algoritmos.md](../practica3/03-algoritmos.md#5-de-autómata-a-expresión-regular-eliminación-de-estados).
   Cada paso muestra el autómata generalizado después de eliminar un estado, las fórmulas
   R(p,r) := R(p,r) + R(p,q)R(q,q)*R(q,r) aplicadas y la tabla de expresiones de las aristas.
3. **Comparar con JFLAP.** Se escribe la expresión que dio JFLAP en la notación del curso; las dos se
   convierten en AFD mínimos con el Ejercicio 2 y se comparan con la prueba de equivalencia de la
   Práctica 3 (isomorfismo de mínimos). Si difieren se muestra el contraejemplo más corto.

La pestaña *Comparar expresiones* hace lo mismo con dos expresiones cualesquiera; por ejemplo,
`(a+b)*ab` y `(a*b*)*ab` resultan equivalentes aunque se escriben distinto.

**Pruebas.** `test_ida_y_vuelta_er_automata_er` hace ER → AFD mínimo → ER con las 19 expresiones de
prueba y comprueba con derivadas que la expresión obtenida describe el mismo lenguaje;
`test_equivalencia_de_expresiones` cubre la comparación, incluido el contraejemplo, y
`test_determinismo_indica_estado_y_simbolo` la verificación. Los casos de la Lista 3 (254-258), de la
Lista 4 (276-277) y los cinco autómatas de la Práctica 3 corresponden al alumno: impórtelos en esta
pantalla.

# Ejercicio 4. Investigación y estado del arte

> **Sección a cargo del alumno** (3 a 5 cuartillas, sólo con las fuentes admitidas y en APA 7).
> El enunciado prohíbe el texto generado por modelos de lenguaje.

Temas de 4.1: no determinismo (AFN y AFN-λ, aceptación), λ-clausura, construcción de subconjuntos
(teorema y esbozo de demostración), cota 2ⁿ, teorema de Kleene, minimización (Myhill-Nerode y
Hopcroft) y el significado práctico de que el no determinismo no aumente el poder de los AF.

4.2: Rabin y Scott (1959), https://doi.org/10.1147/rd.32.0114 — punto en que se prueba la
equivalencia, diferencias de notación y la mención del Premio Turing 1976.

4.3: dos artículos con DOI (preferentemente desde 2018), al menos uno con implementación medida,
con la ficha de seis puntos de la Práctica 1.

La implementación del simulador (documentada en [03-simulador.md](03-simulador.md)) sigue
exactamente la idea de la construcción de subconjuntos: el conjunto de estados activos tras leer *w*
es δ̂(q0, w) del AFD de subconjuntos.

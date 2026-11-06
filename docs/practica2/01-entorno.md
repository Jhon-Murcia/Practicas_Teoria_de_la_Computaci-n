# Ejercicio 1. Entorno de trabajo y flujo de ramas

## Reutilización

* El entorno de la Práctica 1 se reutiliza sin cambios: [`entorno/Dockerfile`](../../entorno/Dockerfile),
  [`entorno/compose.yml`](../../entorno/compose.yml), [`requirements.txt`](../../requirements.txt) y
  [`pytest.ini`](../../pytest.ini). Se trabaja en el mismo repositorio (opción que admite el enunciado),
  de modo que el historial de la Práctica 1 sigue disponible en la rama `practica1`.
* El módulo [`src/core/lenguajes.py`](../../src/core/lenguajes.py) y sus pruebas
  [`tests/test_lenguajes.py`](../../tests/test_lenguajes.py) **proceden de la Práctica 1** y no se
  reescriben; la pantalla de Lenguajes sigue integrada en la misma aplicación.

## Flujo de ramas

Cada práctica tiene su rama (`practica1`, `practica2`, …), creada desde la versión actualizada de
`main`, con varias confirmaciones por funcionalidad. Ninguna confirmación de desarrollo se hace en
`main`: cada práctica ingresa mediante un Pull Request descrito y fusionado con *merge commit*, de
modo que las fusiones se aprecian en `git log --oneline --graph --all`. Las ramas no se borran tras
fusionarlas, para conservar el estado acumulado de cada práctica.

Se recomienda activar la protección de `main` en *Settings → Branches* para que GitHub rechace las
confirmaciones directas.

## Integración continua

[`.github/workflows/pruebas.yml`](../../.github/workflows/pruebas.yml) ejecuta `pytest -q` con Python
3.11, 3.12 y 3.13 (`strategy.matrix`) en cada *push* y Pull Request; `fail-fast: false` evita que el
fallo de una versión cancele las otras. Es el equivalente en la nube de los tres contenedores locales.

## Evidencias que debe capturar el alumno

En [`evidencias/practica2/`](../../evidencias/practica2/): `git log --oneline --graph --all` con las
fusiones (`git/`), la lista de Pull Requests cerrados (`git/`) y la ejecución de las pruebas en GitHub
Actions con las tres versiones aprobadas (`ci/`).

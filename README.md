# AutómataLab — Software interactivo de Teoría de la Computación

![pruebas](https://github.com/Jhon-Murcia/Practicas_Teoria_de_la_Computaci-n/actions/workflows/pruebas.yml/badge.svg)

| | |
|---|---|
| **Institución** | Instituto Politécnico Nacional — Escuela Superior de Cómputo |
| **Unidad de aprendizaje** | Teoría de la Computación |
| **Carrera** | Ingeniería en Sistemas Computacionales (Plan 2020) |
| **Nombre completo** | _(escriba su nombre)_ |
| **Número de boleta** | _(escriba su boleta)_ |
| **Grupo** | _(escriba su grupo)_ |
| **Profesor** | _(escriba el nombre del profesor)_ |
| **Fechas de entrega** | Práctica 1: martes 22 de septiembre de 2026 · Práctica 2: martes 6 de octubre de 2026 · Práctica 3: miércoles 4 de noviembre de 2026 (etiqueta `practica3`) |

Un único software, construido de forma acumulativa a lo largo de las prácticas, para estudiar
cadenas, lenguajes y autómatas finitos con una interfaz gráfica en **Python + Flet**.

![Editor de autómatas](evidencias/practica2/app/01-editor-tcp.png)

## Índice

### Práctica 1 — Operaciones básicas sobre lenguajes

| Documento | Contenido |
|---|---|
| [01-entorno.md](docs/practica1/01-entorno.md) | Repositorio, Docker, tres versiones de Python |
| [02-investigacion.md](docs/practica1/02-investigacion.md) | Investigación (a cargo del alumno) |
| [03-estado-del-arte.md](docs/practica1/03-estado-del-arte.md) | Cinco artículos (a cargo del alumno) |
| [04-jflap.md](docs/practica1/04-jflap.md) | Autómatas en JFLAP |
| [05-aplicacion.md](docs/practica1/05-aplicacion.md) | Aplicación, convenciones, pruebas y resultados |
| [conclusiones.md](docs/practica1/conclusiones.md) | Conclusiones |
| [bibliografia.md](docs/practica1/bibliografia.md) | Bibliografía |

### Práctica 2 — AFND, simulación e importación/exportación

| Documento | Contenido |
|---|---|
| [01-entorno.md](docs/practica2/01-entorno.md) | Reutilización del entorno, flujo de ramas e integración continua |
| [02-jflap.md](docs/practica2/02-jflap.md) | AFND y AFND-λ en JFLAP (a cargo del alumno) |
| [03-simulador.md](docs/practica2/03-simulador.md) | Simulador: arquitectura, formatos, decisión de diseño, pruebas |
| [04-investigacion.md](docs/practica2/04-investigacion.md) | Investigación y estado del arte (a cargo del alumno) |
| [05-del-articulo-al-automata.md](docs/practica2/05-del-articulo-al-automata.md) | Autómata de aplicación: conexión TCP |
| [propuesta.md](docs/practica2/propuesta.md) | Propuesta de trabajo (opcional) |
| [bibliografia.md](docs/practica2/bibliografia.md) | Bibliografía |

> `src/core/lenguajes.py` y sus pruebas **proceden de la Práctica 1** (rama
> [`practica1`](https://github.com/Jhon-Murcia/Practicas_Teoria_de_la_Computaci-n/tree/practica1)) y se reutilizan sin reescribirse.

### Práctica 3 — Conversiones, λ-clausura y minimización (etiqueta `practica3`)

| Documento | Contenido |
|---|---|
| [01-afd-a-er-jflap.md](docs/practica3/01-afd-a-er-jflap.md) | AFD → ER con JFLAP (a cargo del alumno) y apoyo del software |
| [02-software.md](docs/practica3/02-software.md) | Extensión del software, pruebas y capturas |
| [03-algoritmos.md](docs/practica3/03-algoritmos.md) | Cada algoritmo: teoría, pseudocódigo, ejemplo a mano vs. software, coste |

Uso de las funciones nuevas: *Conversiones* (λ-clausura, eliminar λ, subconjuntos, autómata → ER,
cadena completa), *Minimización* (AFD mínimo, tabla de pares, equivalencia) y *Simulación → Varias
cadenas* (cargar un `.txt` y guardar el informe). Todos los algoritmos se ven paso a paso.

## Funcionalidades

| Módulo | Práctica | Qué hace |
|---|---|---|
| Inicio | 1 | Panel con indicadores, accesos rápidos y actividad reciente |
| Cadenas | 1 | Prefijos, sufijos y subcadenas; conteos y exportación a `.txt` |
| Lenguajes | 1 | Σ*, Σ⁺ y Σⁿ con límite de 200 000 cadenas; operaciones entre lenguajes finitos |
| Editor | 2 | Editor visual (estados, transiciones, λ, zoom, arrastre), definición formal, tabla δ editable, deshacer/rehacer, diagnóstico de determinismo |
| Simulación | 2-3 | Validación paso a paso con cinta, λ-clausura, traza, árbol de caminos y validación de un `.txt` con informe |
| Archivos | 2 | Importar/exportar `.jff`, `.json`, `.xml`; proyectos con varios autómatas |
| Conversiones | 3 | λ-clausura, eliminación de λ, subconjuntos (sólo alcanzables), autómata → ER, cadena completa, paso a paso |
| Minimización | 3 | Inaccesibles, refinamiento de particiones, tabla de pares, equivalencia con contraejemplo |
| Ayuda | 1-3 | Convenciones matemáticas y guía de uso |

Tema oscuro (predeterminado) y claro; el menú lateral se compacta en pantallas estrechas.

## Estructura del repositorio

```
README.md  .gitignore  .gitattributes  requirements.txt  pytest.ini
.github/workflows/pruebas.yml   integración continua (3.11, 3.12, 3.13)
entorno/Dockerfile  entorno/compose.yml
src/
  app.py                 punto de entrada
  core/                  núcleo sin Flet: lenguajes, autómata, simulación, ejemplos
  formatos/              lectura y escritura de .jff, .json y .xml
  algoritmos/            λ-clausura, eliminación de λ, subconjuntos, minimización, equivalencia, AFD → ER
  ui/                    interfaz (tema, estado, componentes, páginas)
  assets/fonts/          tipografías incluidas (SIL OFL)
tests/                   pruebas con pytest
docs/practicaN/          reporte de cada práctica
automatas/               ejemplos/, aplicacion/ y practica3/ (casos de prueba)
herramientas/            utilidades (exportar los ejemplos)
evidencias/practicaN/    git/ ci/ docker/ jflap/ app/
```

## Cómo ejecutar

### Con contenedores (Docker Desktop)

Desde la carpeta `entorno/`:

```bash
docker compose build                              # construye las tres imágenes
docker compose run --rm py311 python --version    # Python 3.11.x
docker compose run --rm py312 python --version    # Python 3.12.x
docker compose run --rm py313 python --version    # Python 3.13.x
docker compose run --rm py311 pytest -q           # pruebas en cada versión
docker compose run --rm py312 pytest -q
docker compose run --rm py313 pytest -q
docker compose up py312                           # interfaz en http://localhost:8550
docker compose down                               # apaga y limpia
```

Si usa Podman, los comandos son los mismos sustituyendo `docker` por `podman`.

### En su equipo

```bash
py -3.12 -m venv venv            # Windows   (macOS/Linux: python3 -m venv venv)
venv\Scripts\activate            # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
python src/app.py                # abre la aplicación de escritorio
pytest -q                        # ejecuta las pruebas
```

## Versiones

* **Flet 0.86.5** (`flet[web]`), **pytest 8.3.4**.
* **FastAPI fijada en 0.144.0**: `flet-web 0.86.5` usa un argumento que FastAPI eliminó en
  0.145.0; con una versión posterior el servidor web no arranca (detalle en
  [01-entorno.md](docs/practica1/01-entorno.md)).

## Convenciones

* **λ en los archivos**: en los tres formatos la transición λ es el símbolo leído vacío:
  `<read/>` en `.jff`, `"lee": ""` en `.json` y `lee=""` en `.xml`. Al leer `.json` y `.xml` también
  se aceptan `λ`, `lambda` y `ε`. JFLAP no guarda Σ: al importar un `.jff` se deduce de las transiciones.
* **No determinismo**: el simulador sigue todos los caminos a la vez (conjunto de estados activos con
  λ-clausura); la justificación y el coste están en [03-simulador.md](docs/practica2/03-simulador.md).

* **λ** es la cadena vacía. Se escribe `λ`, `lambda` o se deja el campo vacío.
* λ y la propia *w* se cuentan entre los prefijos y sufijos de *w*: hay *n + 1* de cada uno.

# Ejercicio 1. Entorno de trabajo: control de versiones y contenedores

## Parte A. Investigación

> **Sección a cargo del alumno.** La investigación (control de versiones, Git y GitHub,
> definiciones de repositorio, *commit*, rama, *merge*, conflicto, Pull Request,
> `.gitignore`, `README`, contenedores frente a máquinas virtuales, imagen, contenedor,
> volumen, puerto publicado, entorno virtual de Python y la conveniencia de fijar la
> versión de la imagen) debe redactarse con sus propias palabras y con fuentes
> admitidas. Este documento contiene sólo la parte técnica del entorno que se construyó.

## Parte B. Repositorio

| Elemento | Dónde está |
|---|---|
| Portada e índice | [`README.md`](../../README.md) |
| Exclusiones | [`.gitignore`](../../.gitignore): `venv/`, `__pycache__/`, `*.pyc`, cachés de pytest y las salidas regenerables (`salidas/`, `resultados/`, `informe_*.txt`). Los `.jff` **no** se excluyen. |
| Normalización de fin de línea | [`.gitattributes`](../../.gitattributes): LF en todo el repositorio, para que los mismos archivos funcionen en Windows y en los contenedores Linux. |
| Flujo de ramas | Una rama por práctica (`practica1` … `practica5`), integrada en `main` mediante Pull Request. |

Evidencias que debe capturar el alumno: `git log --oneline --graph --all` y el Pull Request
fusionado, en [`evidencias/practica1/git/`](../../evidencias/practica1/git/).

## Parte C. Los tres entornos de Python

### Archivos

* [`entorno/Dockerfile`](../../entorno/Dockerfile): un único Dockerfile parametrizado.
* [`entorno/compose.yml`](../../entorno/compose.yml): los servicios `py311`, `py312` y `py313`.
* [`requirements.txt`](../../requirements.txt): dependencias con versión fijada.
* [`pytest.ini`](../../pytest.ini): `pythonpath = src` y `testpaths = tests`.

### El Dockerfile, línea por línea

| Línea | Función |
|---|---|
| `ARG PYTHON_VERSION=3.12` | Declara un argumento de construcción con valor por omisión. Compose lo sustituye por `3.11`, `3.12` o `3.13`. |
| `FROM python:${PYTHON_VERSION}-slim` | Imagen base oficial, variante *slim* (Debian mínimo). La versión queda **fijada** por el argumento; no se usa `latest`. |
| `ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1` | No escribe `.pyc` dentro del volumen montado y muestra la salida al instante en `docker compose logs`. |
| `RUN python -m venv /opt/venv` | Crea el entorno virtual con el intérprete de la imagen. Está **fuera de `/app`** porque el volumen de compose sustituye `/app`. |
| `ENV PATH="/opt/venv/bin:$PATH"` | Antepone el `bin` del entorno virtual: equivale a activarlo para todos los comandos. |
| `WORKDIR /app` | Carpeta de trabajo; ahí se monta el repositorio. |
| `COPY requirements.txt .` | Copia sólo las dependencias, para que la capa de `pip install` se reutilice mientras ese archivo no cambie. |
| `RUN pip install … -r requirements.txt` | Actualiza pip e instala las versiones fijadas sin guardar caché (imagen más pequeña). |
| `COPY . .` | Copia el código (necesario si se ejecuta la imagen sin volumen). [`.dockerignore`](../../.dockerignore) excluye `venv/`, `.git/` y las evidencias. |
| `ENV FLET_FORCE_WEB_SERVER=true FLET_SERVER_IP=0.0.0.0 FLET_SERVER_PORT=8550` | Flet arranca como servidor web (no hay escritorio en el contenedor), escucha en todas las interfaces —sin esto el puerto publicado no llega a la aplicación— y usa el puerto 8550. |
| `EXPOSE 8550` | Documenta el puerto que usa el contenedor. |
| `CMD ["python", "src/app.py"]` | Orden por omisión: servir la interfaz. |

### compose.yml

* `name: tc-automatalab` fija el nombre del proyecto. Sin él, Compose usa el nombre de la
  carpeta (`entorno`) y mezcla estos contenedores con los de cualquier otro proyecto cuya
  carpeta se llame igual (durante el desarrollo apareció justo ese aviso de *orphan containers*).
* `build.context: ..` construye desde la raíz del repositorio; `dockerfile: entorno/Dockerfile`.
* `args.PYTHON_VERSION` elige la versión de cada servicio.
* `volumes: - ..:/app` monta el repositorio: los cambios en el código se ven sin reconstruir.
* `py311` y `py313` tienen `command: pytest -q`; `py312` publica `8550:8550` (equipo : contenedor)
  y conserva el `CMD` que sirve la interfaz.
* No se usa la clave `version:`: Compose V2 la considera obsoleta.

### requirements.txt y una incompatibilidad encontrada

El archivo se generó con `pip freeze` después de instalar `flet[web]==0.86.5` y `pytest==8.3.4`.
Al hacerlo con la FastAPI más reciente (0.162.0), **el servidor web de Flet no arrancaba**:

```
TypeError: FastAPI.__init__() got an unexpected keyword argument 'openapi_prefix'
```

`flet-web 0.86.5` declara `fastapi>=0.115.12` sin cota superior, y FastAPI eliminó ese
argumento a partir de 0.145.0. Se probó cada versión y la última compatible es **0.144.0**,
que quedó fijada. Es un ejemplo concreto de por qué se fijan las versiones: el mismo
`pip install flet[web]==0.86.5` funcionaba o fallaba según el día en que se ejecutara.

Además se fijó `uvloop` (dependencia de `uvicorn[standard]` sólo en Linux) con un marcador
de plataforma, y `colorama` (sólo Windows) con el marcador inverso, de modo que el mismo
archivo es reproducible en Windows, en los contenedores y en GitHub Actions.

### Comandos (desde `entorno/`)

```bash
docker compose build                              # construye las tres imágenes
docker compose run --rm py311 python --version    # 3.11.x
docker compose run --rm py312 python --version    # 3.12.x
docker compose run --rm py313 python --version    # 3.13.x
docker compose run --rm py311 pytest -q
docker compose run --rm py312 pytest -q
docker compose run --rm py313 pytest -q
docker compose up py312                           # y abrir http://localhost:8550
docker compose down                               # apaga y limpia
```

### Resultados obtenidos

Salida real guardada en [`evidencias/practica1/docker/python-version.txt`](../../evidencias/practica1/docker/python-version.txt):

| Servicio | `python --version` |
|---|---|
| py311 | Python 3.11.18 |
| py312 | Python 3.12.16 |
| py313 | Python 3.13.18 |

Se usó Docker Desktop 29.8.0 con Docker Compose v5.5.1.

### Justificación de las tres versiones

* **Requisito de Flet.** Los metadatos del paquete `flet 0.86.5` publicados en PyPI declaran
  `Requires-Python: >=3.10` (Flet, 2026).
* **Calendario de soporte.** Según el calendario oficial de versiones de Python (Python
  Software Foundation, s. f.), cada versión recibe cinco años de soporte. Python 3.10 llegó
  al fin de su soporte en octubre de 2026, por lo que **3.11** es la versión más antigua que
  sigue con mantenimiento y además satisface el requisito de Flet.
* **3.12** es la versión de referencia del curso y la que sirve la interfaz.
* **3.13** es una versión reciente: si el programa dependiera de un comportamiento que
  cambió, las pruebas de este contenedor lo detectarían.

> Verifique las fechas en la fuente antes de entregar y capture la página consultada.

### Referencias

* Flet. (2026). *flet 0.86.5* [Paquete de software]. PyPI. https://pypi.org/project/flet/0.86.5/
* Python Software Foundation. (s. f.). *Status of Python versions*. Python Developer's Guide.
  Recuperado el 6 de noviembre de 2026, de https://devguide.python.org/versions/

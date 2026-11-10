

# AutómataLab

Escuela: Escuela Superior de Cómputo IPN

Estudiante: Jhon Sebastian Murcia Romero

Docente: Gabriel Hurtado áviles

Asignatura: Teoría de la Computación

10/11/2026


![pruebas](https://github.com/Jhon-Murcia/Practicas_Teoria_de_la_Computaci-n/actions/workflows/pruebas.yml/badge.svg)

AutómataLab es una aplicación para estudiar los temas de Teoría de la Computación: cadenas,
lenguajes, autómatas finitos y expresiones regulares. Está hecha en **Python con Flet** y se fue
construyendo práctica por práctica sobre el mismo programa. Se puede usar como aplicación de
escritorio, en el navegador desde un contenedor de Docker o desplegada en Render.

Este README es la documentación del proyecto.

## Contenido

1. [Cómo ejecutarlo](#cómo-ejecutarlo)
2. [Qué hace el programa](#qué-hace-el-programa)
3. [Práctica 1: cadenas y lenguajes](#práctica-1-cadenas-y-lenguajes)
4. [Práctica 2: autómatas, simulación y archivos](#práctica-2-autómatas-simulación-y-archivos)
5. [Práctica 3: conversiones y minimización](#práctica-3-conversiones-y-minimización)
6. [Práctica 4: expresiones regulares y validadores](#práctica-4-expresiones-regulares-y-validadores)
7. [Asistente de IA y sección de práctica](#asistente-de-ia-y-sección-de-práctica)
8. [Despliegue en Render](#despliegue-en-render)
9. [Entorno: Docker y tres versiones de Python](#entorno-docker-y-tres-versiones-de-python)
10. [Pruebas](#pruebas)
11. [Estructura del proyecto](#estructura-del-proyecto)
12. [Referencias](#referencias)

---

## Cómo ejecutarlo

### En la computadora

Desde la carpeta del proyecto (la que tiene `src/`):

```powershell
py -3.12 -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python src/app.py
```

En macOS o Linux se usa `python3 -m venv venv` y `source venv/bin/activate`.

Si se quiere abrir en el navegador en vez de una ventana:

```powershell
$env:FLET_FORCE_WEB_SERVER = "true"
$env:FLET_SERVER_PORT = "8550"
python src/app.py
```

y luego se abre http://localhost:8550.

### Con Docker

Desde la carpeta `entorno/`:

```bash
docker compose build
docker compose up py312        # la aplicación queda en http://localhost:8550
docker compose down            # para apagarla
```

### Para usar el asistente de IA

El asistente usa **Groq**, que es gratis. Hay que crear una cuenta en https://console.groq.com (no pide
tarjeta), ir a *API Keys*, crear una clave y ponerla en una variable de entorno antes de arrancar el
programa:

```powershell
$env:IA_API_KEY = "gsk_..."
```

Sin la clave todo el programa funciona igual, sólo que el asistente aparece desactivado.

---

## Qué hace el programa

El menú de la izquierda tiene estas secciones:

| Sección | Para qué sirve |
|---|---|
| Inicio | Resumen de la sesión y accesos rápidos |
| Cadenas | Prefijos, sufijos y subcadenas de una cadena |
| Lenguajes | Σ*, Σ⁺ y Σⁿ, y operaciones entre lenguajes finitos |
| Editor | Dibujar y editar autómatas (AFD, AFND y AFND-λ) |
| Simulación | Probar cadenas paso a paso |
| Archivos | Abrir y guardar autómatas en `.jff`, `.json` y `.xml` |
| Conversiones | λ-clausura, quitar transiciones λ, construcción de subconjuntos y autómata → expresión regular |
| Minimización | AFD mínimo y comparar si dos autómatas son equivalentes |
| Expresiones regulares | De expresión regular a autómata y al revés |
| Validadores | Correo, teléfono, fecha y URL validados con autómatas |
| Práctica | Ejercicios que el sistema califica, con pistas de la IA |
| Ayuda | Guía rápida y convenciones |

En todas las secciones está el botón **Asistente IA** arriba a la derecha. Hay tema oscuro y claro.

---

## Práctica 1: cadenas y lenguajes

**Cadenas.** Para una cadena *w* se calculan todos sus prefijos, sufijos y subcadenas, y se pueden
guardar en un archivo de texto. La cadena vacía se escribe λ.

Se tomó la convención de que λ y la propia *w* sí cuentan como prefijo y como sufijo, porque
*w* = λ*w* = *w*λ. Por eso una cadena de longitud *n* tiene **n + 1 prefijos** y **n + 1 sufijos**.
Las subcadenas distintas son como máximo **n(n + 1)/2 + 1** (contando λ): hay *n − k + 1* posiciones
para cada longitud *k*. Ese máximo sólo se alcanza cuando todos los símbolos son diferentes; por
ejemplo `abcd` tiene 11 y `abba` sólo 9.

**Lenguajes.** Se generan Σ*, Σ⁺ y Σⁿ hasta una longitud que elige el usuario. Σ⁰ = {λ}, porque la
única cadena de longitud 0 es la vacía, y por eso Σ* − Σ⁺ = {λ}. Como Σ* es infinito, el programa sólo
muestra las cadenas hasta la longitud máxima. El número de cadenas es 1 + |Σ| + |Σ|² + … + |Σ|ⁿ y crece
muy rápido; antes de generarlas el programa hace la cuenta con esa fórmula y **rechaza** cualquier caso
de más de 200 000 cadenas. Por ejemplo, con Σ = {0, 1} y longitud 16 salen 131 071 (se acepta), pero
con longitud 17 saldrían 262 143 (se rechaza).

También hay concatenación, unión, intersección, diferencia, potencia y reflexión de lenguajes finitos.

---

## Práctica 2: autómatas, simulación y archivos

**Editor.** Los estados y transiciones se dibujan con el mouse: herramienta *Estado* para crear,
*Transición* para unir dos estados (se escriben los símbolos y hay un botón para insertar λ),
*Eliminar* y *Mover*. La rueda del mouse hace zoom. A la derecha hay tres pestañas: propiedades del
elemento seleccionado, la definición formal (Q, Σ, q0, F) y la tabla δ, que también se puede editar.

El programa decide solo el tipo: es **AFD** si cada pareja (estado, símbolo) tiene a lo mucho un
destino y no hay λ; **AFND** si alguna tiene varios destinos; **AFND-λ** si hay transiciones λ. Si no es
determinista, dice qué estado y qué símbolo lo impiden.

**Simulación.** Para los no deterministas se simulan **todos los caminos a la vez**: en cada paso se
guarda el conjunto de estados activos y se le aplica la λ-clausura. Se eligió así en lugar de convertir
primero a AFD porque la conversión puede producir hasta 2ⁿ estados, mientras que simular directo cuesta
del orden de |w|·|Q|² y deja ver en cada paso qué pasa con la λ-clausura. Un AFD es el caso en el que
ese conjunto tiene un solo estado. La pantalla muestra la cinta, el paso actual, la traza completa y un
**árbol de caminos** con todas las ramas de un AFND.

**Archivos.** Se leen y escriben `.jff` (JFLAP), `.json` y `.xml`. En los tres formatos la transición λ
se escribe con el símbolo vacío: `<read/>` en JFLAP, `"lee": ""` en JSON y `lee=""` en XML. JFLAP no
guarda el alfabeto, así que al abrir un `.jff` se deduce de las transiciones. Exportar e importar dan
exactamente el mismo archivo. También se puede guardar un proyecto con todos los autómatas de la sesión.

**Autómata de aplicación: una conexión TCP.** Se modeló el ciclo de vida de una conexión TCP según el
diagrama de estados del RFC 793. Cada símbolo es un evento y una cadena se acepta si la conexión vuelve
a quedar cerrada.

| Símbolo | Evento | Símbolo | Evento |
|---|---|---|---|
| P | abrir en modo pasivo | K | llega ACK |
| A | abrir en modo activo (se manda SYN) | F | llega FIN |
| E | enviar datos desde LISTEN | X | llega FIN+ACK |
| S | llega SYN | R | llega RST |
| Y | llega SYN+ACK | C | la aplicación cierra |
| T | se vence el temporizador 2·MSL | | |

Q = {CLOSED, LISTEN, SYN_SENT, SYN_RCVD, ESTABLISHED, FIN_WAIT_1, FIN_WAIT_2, CLOSING, TIME_WAIT,
CLOSE_WAIT, LAST_ACK}, q0 = CLOSED y F = {CLOSED}. Es un AFD con δ parcial: un evento sin transición hace
que la secuencia se rechace. Algunas pruebas:

| Cadena | Resultado | Recorrido |
|---|---|---|
| `PSKFCK` | acepta | CLOSED → LISTEN → SYN_RCVD → ESTABLISHED → CLOSE_WAIT → LAST_ACK → CLOSED |
| `AYCKFT` | acepta | CLOSED → SYN_SENT → ESTABLISHED → FIN_WAIT_1 → FIN_WAIT_2 → TIME_WAIT → CLOSED |
| `AYCXT` | acepta | … → FIN_WAIT_1 → TIME_WAIT → CLOSED |
| `PSK` | rechaza | se queda en ESTABLISHED |
| `K` | rechaza | no hay transición desde CLOSED |

El autómata está en `automatas/aplicacion/` y en *Editor → Ejemplos*.

---

## Práctica 3: conversiones y minimización

Todos los algoritmos están programados en Python sin bibliotecas de autómatas, y se ven **paso a paso**
sobre el diagrama: se puede avanzar, regresar o reproducir los pasos.

| Algoritmo | Idea | Costo aproximado |
|---|---|---|
| λ-clausura | Estados a los que se llega desde q usando sólo λ (recorrido con una pila) | O(\|Q\| + transiciones λ) por estado |
| Quitar λ | δ'(q, a) = λ-clausura(δ(λ-clausura(q), a)); pasan a ser finales los estados cuya clausura toca F | O(\|Q\|³·\|Σ\|) |
| Subconjuntos | Cada estado del AFD es un conjunto de estados del AFN; **sólo se generan los alcanzables** desde λ-clausura(q0). ∅ es el estado de error | hasta 2^\|Q\| subconjuntos |
| Minimización | Se quitan los inaccesibles, se completa δ con un estado sumidero si falta y se refina la partición {F, Q − F} hasta que ya no cambia. También está la tabla de pares distinguibles | O(\|Q\|²·\|Σ\|) |
| Equivalencia | Dos AFD son equivalentes si sus AFD mínimos son iguales salvo el nombre de los estados; si no, se muestra la cadena más corta en la que difieren | |
| Autómata → ER | Eliminación de estados: se agregan un inicio I y un final F, y al quitar q se hace R(p,r) = R(p,r) + R(p,q)R(q,q)*R(q,r) | O(\|Q\|³) operaciones |

Ejemplo: con el AFND que acepta las cadenas que terminan en `ab`, la construcción de subconjuntos genera
sólo 3 de los 8 posibles ({q0}, {q0,q1} y {q0,q2}) y la eliminación de estados da `(a+b)*ab`. En cambio,
con «el tercer símbolo desde el final es 1» se generan los 8: esa familia sí llega a la cota 2ⁿ.

En *Simulación → Varias cadenas* se puede cargar un `.txt` con una cadena por línea, validarlas todas y
guardar un informe.

---

## Práctica 4: expresiones regulares y validadores

**Notación que acepta el analizador.**

| Qué | Cómo se escribe |
|---|---|
| Unión | `+` |
| Concatenación | poner una cosa junto a la otra: `ab` |
| Cerradura de Kleene | `*` |
| Palabra vacía / lenguaje vacío | `λ` / `∅` |
| Agrupar | `( )` |
| Usar un operador como símbolo | `\+`, `\*`, `\(`, `\)`, `\ ` (espacio) |
| Clase de símbolos | se declara `D = [0-9]` y se usa como `{D}` |

La precedencia es `*`, luego la concatenación y al final `+`. Si la expresión está mal escrita, el
programa dice en qué posición está el error y la marca con una flecha. Ojo: en el módulo `re` de Python
el `+` significa «una o más veces» y la unión es `|`; no hay que confundir las dos notaciones.

**De expresión a autómata.** Se muestra el árbol sintáctico y luego la construcción de Thompson paso a
paso (casos básicos, unión, concatenación y cerradura). Después se reutilizan los algoritmos de la
Práctica 3 hasta llegar al AFD mínimo, y cada etapa se puede exportar a `.jff`. Por ejemplo, `(a+b)*abb`
da un AFN-λ de 14 estados, un AFD de 5 y un AFD mínimo de 4.

**De autómata a expresión.** Se abre un `.jff`, el programa revisa si es determinista (si no, dice el
estado y el símbolo que fallan) y aplica la eliminación de estados. La expresión que dio JFLAP se puede
escribir para compararla: las dos se convierten en AFD mínimos y se revisa si son equivalentes.

**Validadores.** Cada uno está escrito en la notación del curso y se valida con su AFD mínimo:

| Validador | AFD antes de minimizar | AFD mínimo | Norma consultada |
|---|---|---|---|
| Correo electrónico | 19 | 9 | RFC 5322 (dot-atom) |
| Teléfono de México (10 dígitos) | 54 | 26 | marcación nacional del IFT |
| Fecha (DD/MM/AAAA y AAAA-MM-DD) | 74 | 26 | ISO 8601 |
| URL (http y https) | 22 | 15 | RFC 3986 |

Ninguna expresión cubre toda la norma. Por ejemplo, el correo no acepta partes locales entre comillas,
la fecha acepta 31/02/2026 porque no revisa los días de cada mes y la URL no acepta la consulta `?…`.
La pantalla muestra todos los límites de cada uno, la expresión en la notación del curso y su versión
en `re` de Python.

Para comprobar que el autómata y `re.fullmatch` coinciden, las pruebas generan **600 cadenas por
validador**: 40 % sacadas al azar del lenguaje, 40 % que son esas mismas cadenas con un cambio pequeño
(insertar, borrar, cambiar o duplicar un carácter) y 20 % aleatorias. En todas coinciden.

---

## Asistente de IA y sección de práctica

### Asistente

Se abre con el botón **Asistente IA**. Cada sección le pasa al asistente lo que hay en la pantalla (el
autómata abierto, el paso del algoritmo, la cadena que se simuló, etc.), así que se le puede preguntar
cosas como «¿por qué se rechazó esta cadena?» o «explícame este paso». Además hay botones
**Explicar este paso** en los algoritmos y **¿Por qué?** en la simulación y en los validadores.

El asistente **explica, pero no resuelve ejercicios**: no da el autómata completo ni la expresión final
de un ejercicio; da pistas y preguntas que ayuden a pensarlo. Esa regla está en sus instrucciones. Como
todo modelo de lenguaje, se puede equivocar, por eso los resultados del programa (simulación,
equivalencia, evaluación) siempre los calculan los algoritmos y no la IA.

Para que no tenga ningún costo, usa el modelo abierto **gpt-oss-120b** (publicado por OpenAI) a través de
**Groq**, que tiene un plan gratuito sin tarjeta. Groq funciona igual que la API de OpenAI, así que el
programa se conecta con la librería `openai` cambiando la dirección. La clave se lee del servidor y nunca
llega al navegador. Se configura con variables de entorno:

| Variable | Para qué | Valor por omisión |
|---|---|---|
| `IA_API_KEY` | Clave de la API (de Groq) | (ninguno: sin ella la IA queda apagada) |
| `IA_URL` | Dirección de la API | `https://api.groq.com/openai/v1` |
| `IA_MODELO` | Modelo que se usa | `openai/gpt-oss-120b` |
| `IA_LIMITE_SESION` | Consultas por sesión del navegador | `40` |

El plan gratuito tiene límites por minuto y por día (se ven en la consola de Groq, en *Settings → Limits*).
Si se pasan, el asistente avisa que hay que esperar; no cobra nada. El límite por sesión existe para que,
si la página queda pública, una sola persona no se gaste toda la cuota del día.

Como la conexión es la estándar de OpenAI, se puede cambiar de servicio sin tocar el código. Por ejemplo,
Gemini de Google también tiene plan gratuito: se crea una clave en https://aistudio.google.com y se pone
`IA_URL=https://generativelanguage.googleapis.com/v1beta/openai/` y en `IA_MODELO` un modelo Flash de los
que la página de Google marque como gratuitos.

### Práctica

- **Ejercicios.** Hay 13 ejercicios propios (construir un AFD, un AFND o un AFND-λ, o escribir una
  expresión regular). La respuesta la califica **el sistema, no la IA**: se compara con una respuesta de
  referencia oculta usando la prueba de equivalencia de AFD mínimos. Si está mal, se muestra una cadena
  concreta en la que falla. Para los autómatas, se dibujan en el Editor y se eligen en Práctica.
- **Pistas.** Si la respuesta está mal se puede pedir una pista a la IA. A la IA se le manda el
  enunciado, el intento y la cadena que falla, pero nunca la respuesta de referencia.
- **Ejercicios nuevos con IA.** La IA propone un enunciado y una expresión de referencia. Antes de
  usarlo, el sistema revisa que la expresión esté bien escrita, use sólo el alfabeto y no describa el
  lenguaje vacío. Se avisa que el enunciado lo escribió la IA y podría no coincidir del todo.
- **Preguntas rápidas.** Se muestra un autómata y una cadena y hay que decir si la acepta.

---

## Despliegue en Render

El repositorio ya tiene todo lo necesario: `render.yaml` y el Dockerfile de `entorno/`. La aplicación
lee el puerto de la variable `PORT` que pone Render.

1. Entrar a https://render.com con la cuenta de GitHub.
2. **New → Blueprint** y elegir este repositorio. Render lee `render.yaml` y crea el servicio web.
3. Cuando lo pida, escribir el valor de `IA_API_KEY`, la clave gratuita de Groq (también se puede
   cambiar después en *Environment*).
4. Esperar a que termine el build y abrir la dirección `https://….onrender.com` que da Render.

Cosas a tener en cuenta:

- En el plan gratuito el servicio se apaga si nadie lo usa un rato y la primera visita tarda en cargar.
- Los autómatas de cada persona viven en su sesión del navegador; si se recarga la página se pierden,
  así que conviene usar *Archivos → Guardar proyecto*.
- La IA no cuesta nada, pero la cuota gratuita de Groq se comparte entre todos los que usen la página.
  Si mucha gente la usa a la vez, el asistente puede pedir que se espere un minuto.

---

## Entorno: Docker y tres versiones de Python

Hay un solo `entorno/Dockerfile` que recibe la versión de Python como argumento (`ARG PYTHON_VERSION`) y
crea un entorno virtual en `/opt/venv`, fuera de `/app`, porque el volumen de Compose reemplaza `/app`.
`entorno/compose.yml` define tres servicios:

| Servicio | Imagen | Por qué |
|---|---|---|
| py311 | python:3.11-slim | La versión más antigua que sigue con soporte y que acepta Flet 0.86.5 (pide Python ≥ 3.10) |
| py312 | python:3.12-slim | La versión del curso; es la que sirve la interfaz en el puerto 8550 |
| py313 | python:3.13-slim | Una versión reciente, para ver que nada dependa de algo que haya cambiado |

```bash
docker compose run --rm py311 pytest -q
docker compose run --rm py312 pytest -q
docker compose run --rm py313 pytest -q
```

Dos cosas que pasaron y vale la pena anotar:

- **FastAPI fijada en 0.144.0.** Con la última versión de FastAPI el servidor web de `flet-web 0.86.5` no
  arrancaba, porque FastAPI quitó el argumento `openapi_prefix` desde la 0.145.0. Por eso
  `requirements.txt` tiene todas las versiones fijas.
- **Una diferencia entre versiones de Python.** Una secuencia de escape inválida en el código pasaba sin
  aviso en 3.11, pero en 3.12 y 3.13 salía un `SyntaxWarning`. Se corrigió y ahora una prueba compila
  todo el código tratando esos avisos como error.

También hay integración continua con GitHub Actions (`.github/workflows/pruebas.yml`), que corre las
pruebas con las tres versiones en cada push y Pull Request.

Cada práctica se trabajó en su propia rama (`practica1` a `practica4`) y entró a `main` por Pull
Request. Las Prácticas 3 y 4 tienen las etiquetas `practica3` y `practica4`. Como las ramas se llaman
igual que las etiquetas, para subir una etiqueta hay que usar el nombre completo:
`git push origin refs/tags/practica4`.

---

## Pruebas

Se usan pruebas con pytest (más de 500). Algunas de las más importantes:

- Cadenas y lenguajes: cadena vacía, alfabeto de un símbolo, Σ* contra Σ⁺ en longitud 0 y el límite de
  200 000 cadenas.
- Archivos: guardar y volver a abrir cada ejemplo en los tres formatos da el mismo autómata y el mismo
  archivo.
- Conversiones: el autómata original, el AFN sin λ, el AFD y el AFD mínimo aceptan **exactamente las
  mismas cadenas** (todas las de longitud hasta 8, o menos si el alfabeto es grande), y además se revisa
  con la prueba de equivalencia exacta.
- Expresiones: cada expresión obtenida se revisa con derivadas de Brzozowski y con `re.fullmatch`.
- Práctica: cada respuesta de referencia se compara con una definición independiente del lenguaje.
- IA: se prueba con un cliente simulado, sin conectarse a internet.

```bash
pytest -q
```

---

## Estructura del proyecto

```
src/
  app.py            arranque de la aplicación
  core/             cadenas, lenguajes, autómata, simulación, expresiones regulares, ejemplos
  formatos/         .jff, .json y .xml
  algoritmos/       λ-clausura, quitar λ, subconjuntos, minimización, equivalencia,
                    eliminación de estados, Thompson y validadores
  practica/         ejercicios y su calificación automática
  ia/               conexión con el modelo (Groq), instrucciones del asistente y contexto de pantalla
  ui/               interfaz (menú, editor, simulación, etc.)
tests/              pruebas con pytest
automatas/          ejemplos en .jff, .json y .xml, y el autómata TCP
entorno/            Dockerfile y compose.yml
render.yaml         despliegue en Render
```

La lógica (`core`, `formatos`, `algoritmos`, `practica`) no depende de Flet, así que todo se puede probar
sin abrir la interfaz.

---

## Referencias

- Berners-Lee, T., Fielding, R., y Masinter, L. (2005). *Uniform Resource Identifier (URI): Generic Syntax*
  (RFC 3986). https://doi.org/10.17487/RFC3986
- Brzozowski, J. A., y McCluskey, E. J. (1963). Signal flow graph techniques for sequential circuit state
  diagrams. *IEEE Transactions on Electronic Computers, EC-12*(2), 67-76. https://doi.org/10.1109/PGEC.1963.263416
- Flet. (2026). *Flet 0.86.5*. https://pypi.org/project/flet/0.86.5/
- Groq. (2026). *GroqCloud documentation*. https://console.groq.com/docs
- Hopcroft, J. E., Motwani, R., y Ullman, J. D. (2007). *Introduction to automata theory, languages, and
  computation* (3.ª ed.). Pearson/Addison-Wesley.
- International Organization for Standardization. (2019). *ISO 8601-1:2019 Date and time —
  Representations for information interchange — Part 1: Basic rules*.
- Postel, J. (1981). *Transmission Control Protocol* (RFC 793). https://doi.org/10.17487/RFC0793
- Python Software Foundation. (s. f.). *Status of Python versions*. https://devguide.python.org/versions/
- Rabin, M. O., y Scott, D. (1959). Finite automata and their decision problems. *IBM Journal of Research
  and Development, 3*(2), 114-125. https://doi.org/10.1147/rd.32.0114
- Resnick, P. (Ed.). (2008). *Internet Message Format* (RFC 5322). https://doi.org/10.17487/RFC5322
- Thompson, K. (1968). Programming techniques: Regular expression search algorithm. *Communications of the
  ACM, 11*(6), 419-422. https://doi.org/10.1145/363347.363387

# Ejercicio 5. Del artículo al autómata: la conexión TCP

Opción elegida: el diagrama de estados del protocolo TCP (Gribkoff, 2013, fig. 4), definido
formalmente a partir de la especificación del protocolo (Postel, 1981, fig. 6).

Archivos: [`automatas/aplicacion/conexion-tcp-aplicacion-afd.jff`](../../automatas/aplicacion/conexion-tcp-aplicacion-afd.jff)
(y `.json`, `.xml`). En el software: *Editor → Ejemplos → Conexión TCP — aplicación (AFD)*.

## El alfabeto, antes de dibujar

Cada símbolo es un **evento** que recibe la máquina de estados de una conexión: una orden de la
aplicación, un segmento recibido o un temporizador.

| Símbolo | Evento |
|---|---|
| P | la aplicación abre en modo pasivo (el servidor escucha) |
| A | la aplicación abre en modo activo (se envía SYN) |
| E | la aplicación envía datos desde LISTEN (se envía SYN) |
| S | se recibe SYN |
| Y | se recibe SYN+ACK |
| K | se recibe ACK |
| F | se recibe FIN |
| X | se recibe FIN+ACK |
| R | se recibe RST |
| C | la aplicación cierra (close) |
| T | vence el temporizador 2·MSL |

Una cadena es una secuencia de eventos. El lenguaje aceptado es el de las **secuencias que describen
un ciclo de vida completo**: la conexión parte de CLOSED y termina de nuevo en CLOSED.

## Definición formal

M = (Q, Σ, δ, q0, F) con

* Q = {CLOSED, LISTEN, SYN_SENT, SYN_RCVD, ESTABLISHED, FIN_WAIT_1, FIN_WAIT_2, CLOSING, TIME_WAIT, CLOSE_WAIT, LAST_ACK}
* Σ = {P, A, E, S, Y, K, F, X, R, C, T}
* q0 = CLOSED
* F = {CLOSED}
* δ (parcial; un evento sin transición rechaza la secuencia):

| δ | Evento → destino |
|---|---|
| CLOSED | P → LISTEN, A → SYN_SENT |
| LISTEN | S → SYN_RCVD, E → SYN_SENT, C → CLOSED |
| SYN_SENT | S → SYN_RCVD, Y → ESTABLISHED, C → CLOSED |
| SYN_RCVD | K → ESTABLISHED, C → FIN_WAIT_1, R → LISTEN |
| ESTABLISHED | C → FIN_WAIT_1, F → CLOSE_WAIT |
| FIN_WAIT_1 | K → FIN_WAIT_2, F → CLOSING, X → TIME_WAIT |
| FIN_WAIT_2 | F → TIME_WAIT |
| CLOSING | K → TIME_WAIT |
| TIME_WAIT | T → CLOSED |
| CLOSE_WAIT | C → LAST_ACK |
| LAST_ACK | K → CLOSED |

Qué representa cada estado: CLOSED, sin conexión; LISTEN, esperando una solicitud; SYN_SENT y
SYN_RCVD, establecimiento en curso (*three-way handshake*); ESTABLISHED, conexión abierta;
FIN_WAIT_1, FIN_WAIT_2, CLOSING y TIME_WAIT, cierre iniciado localmente; CLOSE_WAIT y LAST_ACK,
cierre iniciado por el otro extremo.

Es un **AFD**: ningún par (estado, evento) tiene más de un destino y no hay transiciones λ.

## Cadenas de prueba

Resultados obtenidos al cargar el `.jff` en el simulador (los mismos casos están automatizados en
`tests/test_automata.py::test_conexion_tcp`):

| Cadena | Esperado | Obtenido | Recorrido |
|---|---|---|---|
| `λ` | acepta | acepta | CLOSED |
| `PC` | acepta | acepta | CLOSED → LISTEN → CLOSED |
| `PSKFCK` | acepta | acepta | CLOSED → LISTEN → SYN_RCVD → ESTABLISHED → CLOSE_WAIT → LAST_ACK → CLOSED |
| `AYCKFT` | acepta | acepta | CLOSED → SYN_SENT → ESTABLISHED → FIN_WAIT_1 → FIN_WAIT_2 → TIME_WAIT → CLOSED |
| `AYCXT` | acepta | acepta | CLOSED → SYN_SENT → ESTABLISHED → FIN_WAIT_1 → TIME_WAIT → CLOSED |
| `AYCFKT` | acepta | acepta | CLOSED → SYN_SENT → ESTABLISHED → FIN_WAIT_1 → CLOSING → TIME_WAIT → CLOSED |
| `PSRSKCKFT` | acepta | acepta | CLOSED → LISTEN → SYN_RCVD → LISTEN → SYN_RCVD → ESTABLISHED → FIN_WAIT_1 → FIN_WAIT_2 → TIME_WAIT → CLOSED |
| `PSKCKFT` | acepta | acepta | CLOSED → LISTEN → SYN_RCVD → ESTABLISHED → FIN_WAIT_1 → FIN_WAIT_2 → TIME_WAIT → CLOSED |
| `PSK` | rechaza | rechaza | CLOSED → LISTEN → SYN_RCVD → ESTABLISHED |
| `AYCKF` | rechaza | rechaza | CLOSED → SYN_SENT → ESTABLISHED → FIN_WAIT_1 → FIN_WAIT_2 → TIME_WAIT |
| `K` | rechaza | rechaza | CLOSED → ∅ (no hay transición) |
| `PZ` | rechaza | rechaza | «Z» (posición 2) no pertenece a Σ |
| `AYF` | rechaza | rechaza | CLOSED → SYN_SENT → ESTABLISHED → CLOSE_WAIT |

## La abstracción

> **Sección a cargo del alumno** (media cuartilla, la parte central del ejercicio). Puntos de partida:
> el modelo captura el orden válido de los eventos, pero deja fuera los números de secuencia, la
> retransmisión, el contenido de los datos, la ventana de flujo y el tiempo (el temporizador es un
> símbolo, no una duración); ¿qué consecuencias tiene eso para lo que el autómata puede verificar?

## Referencias

* Gribkoff, E. (2013). *Applications of deterministic finite automata* [Documento de curso, ECS 120].
  University of California, Davis. https://www.cs.ucdavis.edu/~rogaway/classes/120/spring13/eric-dfa.pdf
* Postel, J. (1981). *Transmission Control Protocol* (RFC 793). Internet Engineering Task Force.
  https://doi.org/10.17487/RFC0793

"""Validadores construidos a partir de expresiones regulares (Práctica 4).

Cada validador se define en la notación del curso, con clases de símbolos
declaradas, y se convierte en un AFD mínimo con la cadena
ER → AFN-λ → AFN → AFD → mínimo. Se acompaña de una versión escrita a mano en
la sintaxis de ``re`` de Python, con la que se comparan las pruebas.

Todos son **aproximaciones** de las normas que citan; sus límites se
documentan en ``LIMITES``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from core.automata import Automata
from core.expresion_regular import ER, a_python, analizar, analizar_clases
from core.simulacion import acepta
from algoritmos.tuberia import Resultado, desde_expresion


@dataclass(frozen=True)
class Validador:
    clave: str
    nombre: str
    descripcion: str
    clases: str                 # declaraciones, una por línea
    expresion: str              # notación del curso
    python: str                 # traducción escrita a mano para re.fullmatch
    norma: str                  # referencia consultada
    limites: tuple = field(default=())
    validos: tuple = field(default=())
    invalidos: tuple = field(default=())

    def arbol(self) -> ER:
        return analizar(self.expresion, analizar_clases(self.clases))

    def python_automatico(self) -> str:
        return a_python(self.arbol())


CORREO = Validador(
    "correo", "Correo electrónico",
    "Parte local de uno o más caracteres permitidos, separados por puntos; @; uno o más dominios que "
    "empiezan y terminan en letra o dígito; dominio de nivel superior de dos o más letras.",
    "L = [a-zA-Z]\nA = [a-zA-Z0-9]\nH = [a-zA-Z0-9\\-]\nP = [a-zA-Z0-9_%+\\-]",
    "{P}{P}*(.{P}{P}*)*@{A}({H}*{A}+λ).({A}({H}*{A}+λ).)*{L}{L}{L}*",
    r"[A-Za-z0-9_%+-]+(?:\.[A-Za-z0-9_%+-]+)*@(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}",
    "Resnick, P. (Ed.). (2008). Internet Message Format (RFC 5322), sec. 3.4.1 (addr-spec, dot-atom). "
    "https://doi.org/10.17487/RFC5322",
    ("Excluye las partes locales entre comillas y los caracteres ! # $ & ' * / = ? ^ ` { | } ~ que admite "
     "dot-atom.", "Excluye dominios literales como [192.168.0.1] y los dominios internacionalizados (IDN).",
     "No limita longitudes (64 caracteres para la parte local, 63 por etiqueta de dominio).",
     "Acepta dominios de nivel superior inexistentes, p. ej. usuario@dominio.zz."),
    ("ana.perez@ipn.mx", "a_b+c@correo.escom.ipn.mx", "x1@a-b.com", "J.Doe%test@sub.dominio.org"),
    ("ana@ipn", ".ana@ipn.mx", "ana..perez@ipn.mx", "ana@-ipn.mx", "ana@ipn.m", "anaipn.mx", "ana perez@ipn.mx"),
)

TELEFONO = Validador(
    "telefono", "Teléfono nacional (México)",
    "Diez dígitos, juntos o agrupados 2-4-4 o 3-3-4 con espacios o con guiones (el mismo separador en todo el "
    "número), con el prefijo internacional +52 opcional.",
    "D = [0-9]\nN = [1-9]",
    "(\\+52\\ +λ)({N}{D}{D}{D}{D}{D}{D}{D}{D}{D}"
    "+{N}{D}\\ {D}{D}{D}{D}\\ {D}{D}{D}{D}+{N}{D}-{D}{D}{D}{D}-{D}{D}{D}{D}"
    "+{N}{D}{D}\\ {D}{D}{D}\\ {D}{D}{D}{D}+{N}{D}{D}-{D}{D}{D}-{D}{D}{D}{D})",
    r"(?:\+52 )?(?:[1-9]\d{9}|[1-9]\d \d{4} \d{4}|[1-9]\d-\d{4}-\d{4}|[1-9]\d{2} \d{3} \d{4}|[1-9]\d{2}-\d{3}-\d{4})",
    "Marcación nacional a 10 dígitos definida por el Instituto Federal de Telecomunicaciones (IFT). "
    "Verifique y cite el documento oficial del plan de numeración que consulte.",
    ("No comprueba que la clave de región exista; sólo que el número no empiece con 0.",
     "No acepta paréntesis, puntos ni otros agrupamientos, p. ej. (55) 1234 5678.",
     "No acepta prefijos históricos como 01, 044 o 045, ni extensiones."),
    ("5512345678", "55 1234 5678", "55-1234-5678", "222 123 4567", "+52 5512345678", "+52 81-1234-5678"),
    ("0512345678", "551234567", "55 1234-5678", "55  1234 5678", "+525512345678", "(55) 1234 5678"),
)

FECHA = Validador(
    "fecha", "Fecha",
    "Día y mes de dos dígitos con valores válidos (01-31 y 01-12) en dos formatos: DD/MM/AAAA y AAAA-MM-DD.",
    "D = [0-9]",
    "(0(1+2+3+4+5+6+7+8+9)+(1+2){D}+3(0+1))/(0(1+2+3+4+5+6+7+8+9)+1(0+1+2))/{D}{D}{D}{D}"
    "+{D}{D}{D}{D}-(0(1+2+3+4+5+6+7+8+9)+1(0+1+2))-(0(1+2+3+4+5+6+7+8+9)+(1+2){D}+3(0+1))",
    r"(?:0[1-9]|[12]\d|3[01])/(?:0[1-9]|1[0-2])/\d{4}|\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])",
    "International Organization for Standardization. (2019). ISO 8601-1:2019 Date and time — Representations "
    "for information interchange — Part 1: Basic rules (formato AAAA-MM-DD).",
    ("No verifica los días de cada mes ni los años bisiestos: acepta 31/02/2026. Sería posible con una "
     "expresión regular (el conjunto de fechas de 0000 a 9999 es finito) pero mucho más larga.",
     "No acepta días o meses de un dígito (1/2/2026) ni otros separadores."),
    ("06/11/2026", "31/12/1999", "2026-11-06", "0001-01-01", "29/02/2024"),
    ("6/11/2026", "32/01/2026", "15/13/2026", "2026-11-6", "2026/11/06", "00/10/2020"),
)

URL = Validador(
    "url", "URL (http y https)",
    "Esquema http o https, ://, nombre de host con etiquetas separadas por puntos, puerto opcional y ruta "
    "opcional formada por segmentos /…",
    "A = [a-zA-Z0-9]\nH = [a-zA-Z0-9\\-]\nD = [0-9]\nS = [a-zA-Z0-9._~%\\-]",
    "http(s+λ)://{A}({H}*{A}+λ)(.{A}({H}*{A}+λ))*(:{D}{D}*+λ)(/{S}*)*",
    r"https?://[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*"
    r"(?::\d+)?(?:/[A-Za-z0-9._~%-]*)*",
    "Berners-Lee, T., Fielding, R., y Masinter, L. (2005). Uniform Resource Identifier (URI): Generic "
    "Syntax (RFC 3986), sec. 3. https://doi.org/10.17487/RFC3986",
    ("Sólo los esquemas http y https; excluye usuario y contraseña (user@host), direcciones IPv6 y la "
     "consulta (?…) y el fragmento (#…).",
     "En la ruta sólo admite caracteres no reservados y %; no valida que cada % vaya seguido de dos "
     "dígitos hexadecimales.",
     "No limita el puerto a 0-65535 ni las longitudes de las etiquetas."),
    ("http://ipn.mx", "https://www.escom.ipn.mx/", "http://localhost:8550", "https://a-b.c/docs/v1.2/x_y%20z"),
    ("ftp://ipn.mx", "http//ipn.mx", "https://-ipn.mx", "http://ipn..mx", "https://ipn.mx:", "http://"),
)

VALIDADORES = {v.clave: v for v in (CORREO, TELEFONO, FECHA, URL)}


@lru_cache(maxsize=None)
def construir(clave: str) -> Resultado:
    """Autómatas del validador (se calculan una vez y se reutilizan)."""
    v = VALIDADORES[clave]
    return desde_expresion(v.arbol(), v.nombre)


def validar(clave: str, texto: str) -> bool:
    return acepta(construir(clave).minimo, list(texto))


def automata_minimo(clave: str) -> Automata:
    return construir(clave).minimo

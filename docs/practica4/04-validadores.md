# Ejercicio 4. Aplicaciones: validadores

Se implementaron cuatro validadores (se pedían al menos tres) en
[`algoritmos/validadores.py`](../../src/algoritmos/validadores.py). Cada uno:

* se define con **clases** declaradas y una **expresión en la notación del curso**;
* se convierte en su **AFD mínimo** con la cadena del Ejercicio 2 (Thompson → sin λ → subconjuntos →
  mínimo) y el texto se valida con ese autómata;
* tiene una **traducción escrita a mano** a la sintaxis de `re` de Python, además de la traducción
  automática que genera el software desde el árbol;
* documenta qué casos válidos o inválidos quedan fuera y la norma consultada.

La pantalla *Validadores* muestra todo lo anterior, el número de estados de cada etapa y el AFD mínimo.

## Tamaño de los autómatas (antes y después de minimizar)

| Validador | AFN-λ | AFN sin λ | AFD | AFD mínimo | \|Σ\| |
|---|---|---|---|---|---|
| Correo electrónico | 56 | 56 | 19 | 9 | 68 |
| Teléfono nacional | 130 | 130 | 54 | 26 | 13 |
| Fecha | 174 | 174 | 74 | 26 | 12 |
| URL (http y https) | 68 | 68 | 22 | 15 | 69 |

(El AFD mínimo incluye el estado de error; en el diagrama de la pantalla se omite para que se lea.)

## Expresiones

### Correo electrónico

```
L = [a-zA-Z]
A = [a-zA-Z0-9]
H = [a-zA-Z0-9\-]
P = [a-zA-Z0-9_%+\-]

{P}{P}*(.{P}{P}*)*@{A}({H}*{A}+λ).({A}({H}*{A}+λ).)*{L}{L}{L}*
```

`re`: `[A-Za-z0-9_%+-]+(?:\.[A-Za-z0-9_%+-]+)*@(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}`

Norma: Resnick (2008), RFC 5322, sec. 3.4.1 (*addr-spec* con *dot-atom*). **Fuera:** partes locales
entre comillas y los caracteres ``! # $ & ' * / = ? ^ ` { | } ~`` que admite *dot-atom*; dominios
literales (`[192.168.0.1]`) e internacionalizados; los límites de longitud; acepta dominios de nivel
superior inexistentes.

### Teléfono nacional (México)

```
D = [0-9]
N = [1-9]

(\+52\ +λ)({N}{D}{D}{D}{D}{D}{D}{D}{D}{D}
          +{N}{D}\ {D}{D}{D}{D}\ {D}{D}{D}{D} + {N}{D}-{D}{D}{D}{D}-{D}{D}{D}{D}
          +{N}{D}{D}\ {D}{D}{D}\ {D}{D}{D}{D} + {N}{D}{D}-{D}{D}{D}-{D}{D}{D}{D})
```

`re`: `(?:\+52 )?(?:[1-9]\d{9}|[1-9]\d \d{4} \d{4}|[1-9]\d-\d{4}-\d{4}|[1-9]\d{2} \d{3} \d{4}|[1-9]\d{2}-\d{3}-\d{4})`

Se escriben por separado las variantes con espacios y con guiones para exigir **el mismo separador en
todo el número**: en `re` sería tentador usar una referencia hacia atrás, `([ -])…\1`, pero eso ya no
describe un lenguaje regular en general (Ejercicio 1). Referencia: marcación nacional a 10 dígitos del
Instituto Federal de Telecomunicaciones; **verifique y cite el documento oficial**. **Fuera:** no
comprueba que la clave de región exista (sólo que no empiece con 0); no acepta paréntesis ni otros
agrupamientos, ni prefijos históricos (01, 044, 045) ni extensiones.

### Fecha

```
D = [0-9]

(0(1+2+3+4+5+6+7+8+9)+(1+2){D}+3(0+1))/(0(1+2+3+4+5+6+7+8+9)+1(0+1+2))/{D}{D}{D}{D}
+ {D}{D}{D}{D}-(0(1+2+3+4+5+6+7+8+9)+1(0+1+2))-(0(1+2+3+4+5+6+7+8+9)+(1+2){D}+3(0+1))
```

`re`: `(?:0[1-9]|[12]\d|3[01])/(?:0[1-9]|1[0-2])/\d{4}|\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])`

Norma: ISO 8601-1:2019 para AAAA-MM-DD. **Fuera:** no verifica los días de cada mes ni los años
bisiestos (acepta 31/02/2026). Hacerlo sí sería regular, porque las fechas de 0000 a 9999 son un
conjunto finito, pero la expresión sería mucho más larga. Tampoco acepta días o meses de un dígito ni
otros separadores.

### URL (http y https)

```
A = [a-zA-Z0-9]
H = [a-zA-Z0-9\-]
D = [0-9]
S = [a-zA-Z0-9._~%\-]

http(s+λ)://{A}({H}*{A}+λ)(.{A}({H}*{A}+λ))*(:{D}{D}*+λ)(/{S}*)*
```

`re`: `https?://[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*(?::\d+)?(?:/[A-Za-z0-9._~%-]*)*`

Norma: Berners-Lee, Fielding y Masinter (2005), RFC 3986, sec. 3. **Fuera:** otros esquemas; usuario y
contraseña; IPv6; la consulta (`?…`) y el fragmento (`#…`); en la ruta, que cada `%` vaya seguido de dos
dígitos hexadecimales; el rango del puerto (0-65535).

## Congruencia entre modelos (pruebas)

[`tests/test_expresiones.py`](../../tests/test_expresiones.py), `test_validador_coincide_con_re_fullmatch`:
para cada validador se generan **600 cadenas** más los ejemplos escritos a mano, y para cada una se
comprueba que el AFD mínimo, `re.fullmatch` con la expresión escrita a mano y `re.fullmatch` con la
traducción automática **coinciden**. Procedimiento de generación (semilla fija 2026, reproducible):

1. **40 % válidas:** `muestra(r)` recorre el árbol de la expresión eligiendo al azar una rama en cada
   unión y de 0 a 3 repeticiones en cada cerradura; produce cadenas del lenguaje de formas muy
   distintas.
2. **40 % mutaciones** de cadenas válidas: insertar, borrar, sustituir o duplicar un carácter, tomado de
   Σ o de caracteres fuera de Σ (espacio, `#`, `ñ`, `!`, `é`). Producen casi siempre cadenas inválidas
   «cercanas» a las válidas, que son las que más fácilmente distinguen dos implementaciones.
3. **20 % aleatorias** sobre Σ de longitud 0 a 25.

La prueba exige además que entre el 30 % y el 80 % de las cadenas sean aceptadas, para asegurar que el
conjunto mezcla de verdad válidas e inválidas. `test_todas_las_etapas_del_validador_coinciden`
comprueba que el AFN-λ, el AFN y el AFD dan el mismo resultado que el mínimo.

## Puntaje adicional (Android)

No se realizó el empaquetado para Android.

## Referencias

* Berners-Lee, T., Fielding, R., y Masinter, L. (2005). *Uniform Resource Identifier (URI): Generic
  Syntax* (RFC 3986). Internet Engineering Task Force. https://doi.org/10.17487/RFC3986
* International Organization for Standardization. (2019). *Date and time — Representations for
  information interchange — Part 1: Basic rules* (ISO 8601-1:2019).
* Resnick, P. (Ed.). (2008). *Internet Message Format* (RFC 5322). Internet Engineering Task Force.
  https://doi.org/10.17487/RFC5322
* Thompson, K. (1968). Programming techniques: Regular expression search algorithm. *Communications of
  the ACM, 11*(6), 419-422. https://doi.org/10.1145/363347.363387
* Python Software Foundation. (2026). *re — Regular expression operations*. Python 3.12 documentation.
  Recuperado el 6 de noviembre de 2026, de https://docs.python.org/3.12/library/re.html

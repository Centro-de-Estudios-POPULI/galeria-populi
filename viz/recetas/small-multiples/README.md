# Receta `small-multiples`

**Una pregunta, doce respuestas.** Cuando un agregado esconde perfiles que no se
parecen entre sí, la cuadrícula de paneles chicos los muestra todos a la vez: el
ojo compara *formas*, no cifras. Sirve para cualquier desagregación de 6 a 16
categorías sobre el mismo eje temporal.

Caso de referencia: **PIB sectorial del primer semestre** → dos láminas del mismo
molde, `output/pib_semestre_indice_2019.png` (slug `pib-semestre-indice-2019`) y
`output/pib_semestre_variacion.png` (slug `pib-semestre-variacion`).

## Anatomía

```
┌───────────────────────────────────────────────────────────────────────────┐
│ Título (Playfair) · descriptivo, no titular                               │
│ Subtítulo: qué mide el índice / la variación                              │
│                                                                           │
│ Rótulo Del Panel        Rótulo Del Panel        Rótulo Del Panel     …    │  ← Inter Bold
│ ┌────────────────────┐  ┌────────────────────┐  ┌───────────────────┐     │
│ │              2026 ⌐│  │                    │  │                   │     │  ← cifra en la
│ │ ╱╲   área por      │  │  4 × 3 = 12 paneles idénticos, mismo ancho │     │    esquina libre
│ │╱  ╲__ signo ─base──│  │                    │  │                   │     │
│ └────────────────────┘  └────────────────────┘  └───────────────────┘     │
│  2017    2020    2026     ↑ CANAL libre medido, no un hueco a ojo         │
│                                                                           │
│ Nota (qué dice el color) · Fuente                            [wordmark]   │
└───────────────────────────────────────────────────────────────────────────┘
```

Formato **`informe_mosaico`** (2400×1680 @ ESCALA 2 → 4800×3360), añadido al motor
para esta receta. `SC_REF` propio de **1700** —el más alto del motor— para que el
bloque de título no se coma la cuadrícula: doce paneles necesitan el alto mucho
más que un titular grande.

Vale la regla contraintuitiva de siempre: los márgenes de `componer()` son fijos
en px, así que **subir el alto del lienzo da más alto a los paneles**. Los 1550
px iniciales dejaban el rótulo de cada fila casi tocando las cifras de año de la
fila de arriba; la palanca fue `H`, no achicar la letra.

## Decisiones de diseño

**Cada panel con SU escala.** Es lo que distingue esta lámina de un gráfico de
líneas superpuestas: la pregunta es el *perfil* de cada categoría, no el nivel
comparado. Con escala común, la caída del −47 % de Construcción en 2020 aplasta a
los otros once paneles y la lámina no dice nada. (El embed interactivo del Monitor
de Actividad ofrece las dos, con un botón; una lámina impresa tiene que elegir.)

**El área coloreada por signo, la línea NO.** La línea es una sola, en tinta; lo
que se colorea es la **brecha contra la base** —el 100 del índice, el 0 de la
variación—, que es justo lo que la lámina viene a mostrar. Ojo: la regla del Banco
de *un solo color* se fijó para **barras**, donde el color ES la marca y pintarlo
por signo editorializa; aquí el color no marca el dato sino la distancia a una
referencia, y por eso se aparta de ella a propósito.

**El cruce se interpola.** `fill_between(..., interpolate=True)` corta exactamente
donde la serie atraviesa la base. Sin eso, el relleno inventa un escalón plano
entre dos años y el cruce aparece un año corrido.

**Lo estimado lo marca el área sombreada, y sólo eso.** La serie va continua. La
banda arranca medio paso antes de la primera observación estimada y llega al borde
del panel, para **encerrar** el punto en vez de cortarse encima de él.

**La cifra del último año va DENTRO del panel, en la esquina derecha libre.**
Pegada al último punto choca con la propia línea cuando el último tramo es
empinado, y el caso feo (Construcción) además queda contra el piso del panel y no
tiene ningún lado libre. Afuera del panel se leía perfecto, pero costaba ~175 px
de reserva por columna —**el 16 % del ancho útil para doce números**—. Adentro ese
ancho se lo quedan los paneles: la esquina se elige mirando sólo el **tercio
derecho** de la serie, que es donde va a caer la cifra, y gana la de más aire.

**El hueco entre columnas no se fija: se despeja.** Con un `gap_x` puesto a mano el
canal realmente vacío medía 258 px —tres veces, el 17 % del ancho útil— porque al
hueco se le sumaba lo que cada panel *no* usaba de su reserva. Lo que se fija es
`CANAL`, el aire que se quiere VER entre columna y columna; se **mide** cuánto
desborda de verdad cada panel por cada lado (`B` a la izquierda por las cifras del
eje, `R` a la derecha por la etiqueta de año, que va centrada sobre su marca) y se
despeja el ancho de trazado que cabe:

```
paso  = ancho + K,   con K = máx_c (R[c] + B[c+1]) + CANAL
ancho = (útil − B[0] − R[−1] − (COLS−1)·K) / COLS
```

Con `CANAL = 46` px @1080 el vacío bajó del **19,9 % al 8,9 %** del ancho útil y los
paneles crecieron cerca de un tercio, sin que nada se solape. El paso se mantiene
uniforme a propósito: dejarlo variar por frontera daría ~2 % más de ancho y
rompería la cuadrícula regular de los rótulos.

**Los doce paneles miden exactamente lo mismo.** Es la regla dura del formato: si
cada panel se ajusta al ancho de *sus* propias cifras, las columnas salen de
distinto ancho y los perfiles dejan de ser comparables —que es todo el punto—. Por
eso el encuadre va en **dos pasadas**: se dibuja una vez, se mide, y recién
entonces se reparte, con un único ancho para los doce.

**El rótulo de cada panel va al borde de su CELDA**, no del área de trazado: así el
del primer panel cae en el margen del título y los tres de cada columna quedan a
plomo. Se dibujan **al final**, después del ajuste del margen derecho: un
`fig.text` ya dibujado no se entera si las celdas se corrieron.

**La escala tipográfica es propia de la figura** y muy por debajo de la global
(`S_EJE`, `S_ROTULO`, `S_DATO` en la cabecera). `SIZES` está calibrado para UN
panel por lienzo; aquí hay doce.

**Negrita REAL:** rótulos en la familia `"Inter Bold"`, cifras en
`"JetBrains Mono SemiBold"`. `weight="bold"` sobre `Inter.ttf` no hace nada.

**Sin fantasma del PIB.** Se probó superponer el total en punteado gris en cada
panel sectorial. Obliga a que el rango del panel le haga lugar —si no, la línea
entra y sale a 45°—, y eso vuelve a ensanchar la escala justo cuando lo que se
busca es la propia. El PIB va de **primer panel**, que es su lugar.

**Escala redondeada por «lo que menos desperdicia».** `rango()` prueba varios
pasos y se queda con el que deja menos aire muerto, en vez del primero que redondea
bonito: ese abría el eje en −75 para un mínimo de −47.

## Contrato de datos

`data/populi_pib_ipaec_2026_4.xlsx`, hoja **`Sectorial semestre`**, dos bloques:

| Bloque | Qué aporta |
|---|---|
| `4 · Índice del semestre I+II, 2019 = 100` | 12 filas (11 sectores + PIB) × 2017–2026 |
| `5 · Variación interanual del semestre I+II (%)` | las mismas 12 filas × 2018–2026, **en tanto por uno** |

Los bloques se localizan **por su encabezado, no por número de fila**: el libro se
edita a mano y las filas se corren de una versión a otra. Los encabezados de año
están guardados como **texto**, no como número — buscarlos con un `isinstance(int)`
devuelve cero columnas.

`leer()` exige las doce filas en los dos bloques: si el libro cambia de forma,
falla en vez de publicar una lámina muda. El orden de los paneles sale del dato
—PIB primero y los sectores de más a menos recuperados en 2026— y es **el mismo en
las dos láminas**, para que el lector pase de una a otra sin reubicar los paneles.

El semestre de 2026 **no es dato de cuentas nacionales**: es el de 2025 movido con
las tasas del IpAEC del BCB. De ahí el área sombreada y la nota al pie.

## Replicar

```bash
python figura.py     # → output/*.png  (las dos láminas)
python publicar.py   # → public/graficas + thumb letterbox + CSV + ficha + manifest
```

Para adaptar a otro caso: cambiar `leer()`, `CORTO` (nombres de panel), los textos
de `lamina()` y, si la desagregación no es de doce, `COLS`/`ROWS`. Con más de 16
categorías esta lámina deja de funcionar: el panel se vuelve ilegible antes que la
cuadrícula.

### Verificar

El encuadre se comprueba sobre el PNG, no a ojo: no debe haber tinta fuera de
`[M, W − M]`.

```python
from PIL import Image
import numpy as np, sys; sys.path.insert(0, "viz")
import populi_style as ps
W, H, sc = ps._spec("informe_mosaico"); M = int(ps.MARGIN * sc)
for slug in ("pib-semestre-indice-2019", "pib-semestre-variacion"):
    im = np.asarray(Image.open(f"public/graficas/{slug}.png").convert("RGB")).astype(int)
    xs = np.nonzero((np.abs(im - [250, 248, 243]).sum(axis=2) > 40).any(axis=0))[0]
    assert xs.min() >= M - 2 and xs.max() <= W - M + 2, (slug, xs.min(), xs.max())
```

Y comprobar que los doce paneles quedaron del mismo ancho:

```python
anchos = {round(ax.get_position().width, 6) for ax in ejes}
assert len(anchos) == 1, anchos
```

# Receta `serie-y-ranking`

**Una figura, dos preguntas.** A la izquierda *cuánto* se mueve el agregado en el
tiempo; a la derecha *dónde* se está moviendo, hoy, por componente. Sirve cada vez
que un dato agregado esconde una dispersión que vale la pena mostrar.

Caso de referencia: **PIB trimestral e IpAEC 2026** →
`output/pib_ipaec_2026.png` · slug `pib-ipaec-2026`.

## Anatomía

```
┌──────────────────────────────────────────────────────────────────────┐
│ Título (Playfair) · descriptivo, no titular                          │
│ Subtítulo: qué variación es                                          │
│                                                                      │
│ PIB: variación trimestral        PIB: variación por actividad (1S)   │  ← rótulo
│ ▪ Interanual ── Acumulada ── 12m                                     │  ← leyenda
│ ┌────────────────────────┐      ┌────────────────────────────────┐   │
│ │ barras + 2 líneas      │      │ nombre ──── barra ──── cifra   │   │
│ │ + área = estimado      │      │ ordenado · eje X en %          │   │
│ └────────────────────────┘      └────────────────────────────────┘   │
│                                                                      │
│ Nota (una línea) · Fuente                              [wordmark]    │
└──────────────────────────────────────────────────────────────────────┘
```

Formato **`informe_panorama`** (2200×1350 @ ESCALA 2 → 4400×2700), añadido al
motor para esta receta. Tiene `SC_REF` propio (1560) para que el texto **no**
crezca al ensanchar el lienzo: el titular queda en 3,3% del ancho frente al 3,8%
de `informe_horizontal`, y eso es lo que hace respirar a los dos paneles.

Regla contraintuitiva del motor: los márgenes de `componer()` son fijos en px, así
que **subir el alto del lienzo da más alto a los paneles**, no menos. Si la figura
se ve achatada, la palanca es `H`, no el reparto de columnas.

## Decisiones de diseño

**Las barras van en un solo color** —el rojo de marca, serie principal del Banco—
en los dos paneles. No se colorean por signo: el signo ya lo dice la posición
respecto del cero, y un semáforo rojo/verde editorializa la lectura.

**Las tres variaciones a la vez, cada una en su registro.** Interanual en barras;
acumulada del año corrido y últimos 12 meses en líneas, separadas entre sí por el
par validado (`serie_teal` y `tinta`). Las tres dicen cosas distintas: el
trimestre suelto, el año corrido y la tendencia limpia de estacionalidad.

**Lo estimado lo marca el área sombreada, y solo eso.** Las series se dibujan
continuas: cortarlas o puntearlas además de sombrear repite el mismo aviso tres
veces y ensucia la lectura.

**El ranking sí lleva eje X.** Sin él las barras no se pueden medir y la figura
depende por completo de las cifras rotuladas.

**La cifra entra en la barra cuando la barra es larga** (`abs(v) >= 12`), con
`ps.contraste_texto()`. Afuera obligaría a ampliar el `xlim` hasta comerse el
ancho útil del panel, y se montaría sobre el nombre de la actividad.

**Las barras van semitransparentes** (`BARRA_ALPHA = 0.72`) y la grilla
punteada: las dos líneas cruzan por encima de las barras y con el rojo sólido se
perdían dentro de ellas.

**El encuadre lo hace `_inset_y`**, igual que en `series-eventos`: se mide el
ancho real de las etiquetas Y de cada panel y se empuja el área de trazado, de
modo que el borde izquierdo del bloque de etiquetas coincida con el margen del
título. Es lo que alinea la figura con el titular y el pie.

**Por la derecha manda el wordmark.** El ranking rotula sus barras positivas
*fuera* del área de trazado, así que la cifra se salía del encuadre. No basta con
restar un carril estimado: se mide el desborde real contra `W − M` (donde termina
el wordmark) y se encoge el eje, iterando, porque encoger mueve las barras. Hay
una comprobación a nivel de píxel para esto — ver *Verificar* abajo.

**La escala tipográfica es propia de la figura**, por debajo de la global del
motor (`S_EJE`, `S_DATO`, `S_LEYENDA`, `S_ROTULO` en la cabecera del script).
`SIZES` está calibrado para UN panel por lienzo; con dos, el texto se desborda.

**Negrita REAL, no `weight="bold"`.** `Inter.ttf` y `JetBrainsMono-Regular.ttf`
son variables/regulares y matplotlib no sintetiza pesos ni navega ejes: pedir
`weight="bold"` sobre ellas no hacía nada. Los rótulos usan la familia
**`"Inter Bold"`** (instancia estática wght=700 generada con
`fontTools.varLib.instancer`, añadida al motor en `assets/fonts/Inter-Bold.ttf`)
y las cifras **`"JetBrains Mono SemiBold"`**, que ya existía sin usarse.

**Títulos descriptivos, no titulares.** El Banco es un catálogo de referencia: la
interpretación va en el texto que acompaña la gráfica, no en la gráfica.

## Contrato de datos

`data/populi_pib_ipaec_2026.xlsx`, dos hojas:

| Hoja | Qué aporta |
|---|---|
| `PIB trimestral` | desde la fila 9: año · trimestre romano · periodo · nivel · interanual · acumulada · 12 meses (en tanto por uno) |
| `IpAEC …` | desde la fila 5: nombre de actividad · variación acumulada en % · ponderación · contribución |

`leer()` corta la serie en `DESDE` y exige que las tres variaciones estén
completas desde ahí, más las 11 actividades y la fila `Total IpAEC publicado`: si
el Excel cambia de forma, falla en vez de publicar un gráfico mudo.

**No se grafican las contribuciones en pp.** La propia hoja avisa que las
ponderaciones son un supuesto y que la suma no cuadra con el total publicado
(0,23 pp de discrepancia). Solo va lo publicado.

**Los dos trimestres de 2026 no son dato del INE**: salen de aplicar la variación
acumulada del IpAEC del BCB (*Reporte de Inflación y Política Monetaria*) sobre
los niveles del PIB del INE. De ahí el área sombreada y la nota al pie.

## Replicar

```bash
python figura.py     # → output/pib_ipaec_2026.png
python publicar.py   # → public/graficas + thumb letterbox + ficha + manifest
```

La miniatura NO usa el recorte central de `ps.guardar`: en una figura ancha
partiría los dos paneles. Va la figura completa en letterbox sobre el crema.

### Verificar

El encuadre se comprueba sobre el PNG, no a ojo: no debe haber tinta fuera de
`[M, W − M]`.

```python
from PIL import Image
import numpy as np, sys; sys.path.insert(0, "viz")
import populi_style as ps
W, H, sc = ps._spec("informe_panorama"); M = int(ps.MARGIN * sc)
im = np.asarray(Image.open("public/graficas/pib-ipaec-2026.png").convert("RGB")).astype(int)
xs = np.nonzero((np.abs(im - [250, 248, 243]).sum(axis=2) > 40).any(axis=0))[0]
assert xs.min() >= M - 2 and xs.max() <= W - M + 2, (xs.min(), xs.max())
```

Para adaptar a otro caso: cambiar `leer()`, los textos de `componer()`, los
rótulos de panel y el reparto `colW_izq` / `colW_der` (el ranking se lleva más
ancho cuanto más largos sean los nombres de categoría).

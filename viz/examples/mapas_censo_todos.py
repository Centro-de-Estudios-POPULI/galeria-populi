"""
Publica los mapas municipales del Censo 2024 al Banco de Gráficos.

★★ LO MANEJA EL CATÁLOGO DEL ATLAS, NO UNA LISTA ESCRITA ACÁ.
   Antes este archivo declaraba a mano 135 indicadores con su título, su
   subtítulo y su paleta. Eso tenía tres consecuencias, todas MEDIDAS el
   2026-08-27 antes de reescribirlo:

   1 · FALTABAN 81 DE 215. Los indicadores que se agregaron al Atlas después
       nunca llegaron al Banco, y `fecundidad` seguía en la lista aunque ya no
       existe en el catálogo.

   2 · EL DOMINIO DIFERÍA EN 176 DE 215 (82 %). La página usa el rango DECLARADO
       en `dom`, calculado sobre la UNIÓN de 2012 y 2024 para que un tono
       signifique lo mismo en los dos censos; acá se recalculaba p02/p98 sobre
       2024 solo. `pct_internet` iba de 0,0–83,7 en la web y de 33,9–86,7 en la
       lámina: el mismo indicador con dos repartos de color.

   3 · LOS RÓTULOS SE HABÍAN DESINCRONIZADO. El Atlas corrigió siete cortes de
       edad que estaban mal —«Años de estudio promedio (25+)» sobre un universo
       de 19 años o más— y la lámina seguía anunciando el viejo.

   ⇒ Ahora el título, el subtítulo, el universo, la dirección de la rampa y el
     dominio salen del MISMO catálogo que dibuja la web. Es la regla que este
     archivo ya aplicaba para `dir` —«para que no puedan divergir»— extendida a
     todo lo demás. Agregar un indicador al Atlas lo agrega acá solo.

★ POR ESO AHORA SÍ HAY MAPA DE POBLACIÓN TOTAL. La cabecera vieja decía «excluye
  pob_total: conteo crudo, no apto para coroplético en escala lineal». La razón
  real era otra: `escala_atlas` ponderaba TODO por población, y para un conteo
  ese promedio es Σp²/Σp = 441.536 contra una mediana de 12.296 — el pivote caía
  FUERA del rango dibujado y la rampa se degeneraba. Un conteo se centra en su
  MEDIANA, y con eso los seis conteos entran sin problema.

★ LOS SLUGS DE LAS 134 LÁMINAS QUE YA EXISTEN NO CAMBIAN. Salen del campo `lam`
  del catálogo, que es el mismo que usa el botón «Descargar este mapa» del
  tablero: cambiarlos rompería ese enlace en la web ya publicada.

    python viz/examples/mapas_censo_todos.py                    # publica todo
    python viz/examples/mapas_censo_todos.py --ensayo           # sólo informa
    python viz/examples/mapas_censo_todos.py --solo=pob_total   # una sola
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

import geopandas as gpd
import pandas as pd

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ))
from catalogo import publicar, build_manifest
import populi_style as ps

# la consola de Windows es cp1252 y se atraganta con las flechas del informe
sys.stdout.reconfigure(encoding="utf-8")

ENSAYO = "--ensayo" in sys.argv
# `--solo pct_x` publica un único indicador: para mirar una lámina sin
# esperar a que se dibujen las 215
SOLO = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--solo=")), None)

# Mapa MAESTRO de Bolivia: 343 municipios (339 del OEP + los 4 GAIOC de
# conversión total). Fuente: Proyectos/bo-geo-maestro (clave `sigep`).
GEO = VIZ.parent.parent / "bo-geo-maestro" / "geo" / "atlas_muni_343.topojson"
if not GEO.exists():                                   # respaldo local
    GEO = VIZ / "geo" / "atlas_muni_343.topojson"

ATLAS = (VIZ.parent.parent / "Observatorio de Presupuesto Fiscal Departamental"
         / "_github_atlas_fiscal")
CENSO = ATLAS / "data.json"
CAT_ATLAS = ATLAS / "catalogo.json"
FECHA = "2026-08-27"
AUTOR = "Carlos Aranda"
FUENTE = ("Fuente: INE Bolivia, Censo de Población y Vivienda 2024. "
          f"Elaboración: Centro de Estudios POPULI · {AUTOR}.")

if not CAT_ATLAS.exists():
    sys.exit(f"⛔ sin el catálogo del Atlas en {CAT_ATLAS}. Es la fuente de todo "
             "lo que se publica acá: título, universo, dirección y dominio.")

# --- geometría + datos ------------------------------------------------------ #
# Con el mapa maestro quedan 3 municipios SIN dato censal propio: Raqaypampa,
# Jatún Ayllu Yura y TIM. Son GAIOC cuya población el INE contabiliza dentro de
# su municipio padre, así que NO se les hereda el valor del padre —sería inventar
# un dato—: se dibujan en el gris de «sin dato». Aparecer en gris es información.
gdf = gpd.read_file(GEO)
censo = json.loads(CENSO.read_text(encoding="utf-8"))
cdf = pd.DataFrame.from_dict(censo, orient="index")
cdf.index.name = "sigep"
cdf = cdf.reset_index()
cdf = cdf.drop(columns=[c for c in ("cod_ine", "nombre", "dpto") if c in cdf.columns])
gdf = gdf.merge(cdf, on="sigep", how="left", suffixes=("", "_c"))
print(f"Unidos {gdf['pob_total'].notna().sum()}/{len(gdf)} municipios.")

# los límites departamentales se disuelven UNA vez: hacerlo dentro de cada lámina
# sería repetir el mismo trabajo doscientas quince veces
BORDES = gdf.dissolve(by="dpto").boundary
print(f"Límites departamentales: {len(BORDES)} departamentos.")

_c = json.loads(CAT_ATLAS.read_text(encoding="utf-8"))
IND = [(g["label"], i) for g in _c["grupos"] for i in g["indicadores"]]
print(f"Catálogo del Atlas: {len(IND)} indicadores.\n")

# el sufijo que acompaña a la cifra en la leyenda, por unidad declarada
SUFIJO = {"%": "%", "pp": " pp", "‰": " ‰"}


def slug_de(texto):
    """Slug para los indicadores que todavía no tienen lámina. Los que ya la
    tienen conservan el suyo (`lam`), que es el que enlaza el tablero."""
    t = unicodedata.normalize("NFD", texto.lower()).encode("ascii", "ignore").decode()
    return "censo-" + re.sub(r"[^a-z0-9]+", "-", t).strip("-")


# --- publicación ------------------------------------------------------------ #
hechos, saltados, nuevos, choques = 0, [], [], {}
for grupo, ind in IND:
    col = ind["key"]
    if SOLO and col != SOLO:
        continue
    if col not in gdf.columns:
        saltados.append((col, "no está en data.json"))
        continue
    con_dato = int(gdf[col].notna().sum())
    if con_dato < 50:
        saltados.append((col, f"sólo {con_dato} municipios con dato"))
        continue

    slug = ind.get("lam")
    if not slug:
        slug = slug_de(ind["label"])
        nuevos.append((col, slug))
    # ⚠️ dos indicadores no pueden compartir lámina: el segundo pisaría al
    #    primero en silencio y el tablero enlazaría el mapa equivocado
    if slug in choques:
        saltados.append((col, f"su slug choca con {choques[slug]}"))
        continue
    choques[slug] = col

    escala = ps.escala_atlas(
        gdf[col], pesos=gdf["pob_total"],
        direccion=ind.get("dir", 0),
        con_signo=bool(ind.get("div")),
        dominio=ind.get("dom"),           # el MISMO rango que dibuja la web
        conteo=ind.get("agg") == "suma",  # un conteo se centra en su mediana
    )
    # Decimales como la página: ninguno en los conteos de personas o viviendas
    # —«1.610.982,0 hab» no lo escribe nadie— y uno en todo lo demás. Con cero
    # decimales en un porcentaje, un p02 de 3,7 % se redondea a 4 % y hunde el
    # extremo bajo de la leyenda.
    dec = 0 if ind.get("unit") in ("hab", "viv") else 1

    # El subtítulo es la DEFINICIÓN del catálogo más su universo: es lo que hace
    # que la lámina se entienda sola cuando viaja sin la web al lado.
    # ⚠️ Dos cuidados de redacción, los dos vistos en la primera lámina de prueba:
    #    · el universo se omite en los CONTEOS — «Todas las personas censadas del
    #      municipio — sobre la población» no agrega nada, porque un conteo no se
    #      divide por nada;
    #    · «por municipio» no se repite si la definición ya nombró al municipio,
    #      que daba «…que viven en el municipio, por municipio».
    sub = (ind.get("desc") or ind["label"]).rstrip(".")
    if ind.get("universo") and ind.get("agg") != "suma":
        sub += f" — {ind['universo']}"
    if "municipio" not in sub.lower():
        sub += ", por municipio"

    if ENSAYO:
        hechos += 1
        continue
    publicar(
        meta={"slug": slug, "tipo": "mapa",
              "titulo": f"Bolivia: {ind['label']}",
              "subtitulo": sub,
              "fuente": FUENTE, "categoria": "censo",
              "tags": ["censo 2024", "municipios", col, grupo],
              "fecha": FECHA, "formato": "red_vertical"},
        df=(gdf[["sigep", "municipio", "dpto", col]]
            .rename(columns={"municipio": "nombre"}).set_index("sigep")),
        gdf=gdf, value_col=col, sufijo=SUFIJO.get(ind.get("unit"), ""),
        label_fmt="{:." + str(dec) + "f}", escala=escala, bordes=BORDES,
    )
    hechos += 1

if not ENSAYO:
    build_manifest()
print(f"\n{hechos} mapas del Censo {'a publicar' if ENSAYO else 'publicados al Banco'}.")
if nuevos:
    print(f"  {len(nuevos)} son NUEVOS (no tenían lámina):")
    for col, slug in nuevos[:10]:
        print(f"     {col:<28} → {slug}")
    if len(nuevos) > 10:
        print(f"     … y {len(nuevos) - 10} más")
    print("  ⚠️ Después hay que volver a correr `enriquecer_atlas.py`, que es el")
    print("     que escribe `lam` en el catálogo: sin eso el tablero no enlaza")
    print("     las láminas nuevas.")
if saltados:
    print(f"  {len(saltados)} saltados:")
    for col, por in saltados:
        print(f"     {col:<28} {por}")

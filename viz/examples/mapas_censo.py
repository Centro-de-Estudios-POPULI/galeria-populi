"""
Publica mapas coropléticos municipales del Censo 2024 al Banco.
Geometría: viz/geo/bolivia_municipios_sigep.topojson (339 municipios, clave 'sigep').
Datos:     viz/geo/censo_municipios_con_nbi.json (indexado por SIGEP).
"""
import sys
import json
from pathlib import Path
import geopandas as gpd
import pandas as pd

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ))
from catalogo import publicar, build_manifest

GEO = VIZ / "geo" / "bolivia_municipios_sigep.topojson"
CENSO = VIZ / "geo" / "censo_municipios_con_nbi.json"
FECHA = "2026-06-09"

gdf = gpd.read_file(GEO)                                  # sigep, municipio, dpto, geometry
censo = json.loads(CENSO.read_text(encoding="utf-8"))

# El censo usa códigos nd_XXXXXX para 7 territorios (GAIOC y reclasificados) que
# en la geometría tienen su SIGEP. Crosswalk geom_sigep -> clave del censo:
CROSSWALK = {
    "1280": "nd_020807",  # Taraco (La Paz)
    "1435": "nd_040104",  # Soracachi (ex Paria, Oruro)
    "3101": "nd_011002",  # Huacaya (Chuquisaca, GAIOC)
    "3401": "nd_040903",  # Chipaya / Uru Chipaya (Oruro, GAIOC)
    "3402": "nd_040801",  # Salinas de Garci Mendoza (Oruro)
    "3701": "nd_070702",  # Charagua Iyambae (Santa Cruz, GAIOC)
    "3702": "nd_070705",  # Gutiérrez (Santa Cruz)
}
cdf = pd.DataFrame.from_dict(censo, orient="index")
cdf.index.name = "key"
cdf = cdf.reset_index()
inv = {ck: sg for sg, ck in CROSSWALK.items()}
cdf["sigep"] = cdf["key"].map(lambda k: inv.get(k, k))     # reasigna nd_ -> sigep
gdf = gdf.merge(cdf.drop(columns="key"), on="sigep", how="left", suffixes=("", "_censo"))
print(f"Unidos {gdf['pob_total'].notna().sum()}/{len(gdf)} municipios con datos.")

FUENTE = "Fuente: INE Bolivia, Censo de Población y Vivienda 2024. Elaboración: Centro de Estudios POPULI."


def mapa(col, slug, titulo, subtitulo, leyenda, sufijo="%", label_fmt="{:.0f}",
         paleta="calido"):
    datos = gdf[["sigep", "municipio", "dpto", col]].rename(
        columns={"municipio": "nombre"}).set_index("sigep")
    publicar(
        meta={"slug": slug, "tipo": "mapa", "titulo": titulo, "subtitulo": subtitulo,
              "fuente": FUENTE, "categoria": "censo", "tags": ["censo 2024", "municipios"],
              "fecha": FECHA, "formato": "red_vertical"},
        df=datos,
        gdf=gdf, value_col=col, leyenda=leyenda, sufijo=sufijo,
        label_fmt=label_fmt, paleta=paleta,
    )


mapa("pct_agua_caneria", "censo-agua-caneria",
     "El acceso a agua por cañería es muy desigual entre municipios",
     "Hogares con agua por cañería de red, Censo 2024",
     "% de hogares del municipio")

mapa("pct_internet", "censo-internet",
     "La conexión a internet sigue concentrada en pocos municipios",
     "Hogares con acceso a internet, Censo 2024",
     "% de hogares del municipio")

mapa("pct_analfabetismo", "censo-analfabetismo",
     "El analfabetismo persiste en el altiplano y zonas rurales",
     "Tasa de analfabetismo en población de 15 años o más, Censo 2024",
     "% de la población")

mapa("pct_nbi_pobre", "censo-pobreza-nbi",
     "La pobreza por NBI marca una brecha territorial profunda",
     "Población pobre por Necesidades Básicas Insatisfechas, Censo 2024",
     "% de la población")

build_manifest()
print("\nMapas del Censo publicados al Banco.")

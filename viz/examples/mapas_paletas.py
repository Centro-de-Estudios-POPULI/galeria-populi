"""Compara el mismo mapa censal en varias paletas (no publica; solo viz/output)."""
import sys, json
from pathlib import Path
import geopandas as gpd, pandas as pd

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ)); sys.path.insert(0, str(VIZ / "charts"))
from mapas import grafico_mapa

gdf = gpd.read_file(VIZ / "geo" / "bolivia_municipios_sigep.topojson")
censo = json.loads((VIZ / "geo" / "censo_municipios_con_nbi.json").read_text(encoding="utf-8"))
CW = {"1280":"nd_020807","1435":"nd_040104","3101":"nd_011002","3401":"nd_040903",
      "3402":"nd_040801","3701":"nd_070702","3702":"nd_070705"}
cdf = pd.DataFrame.from_dict(censo, orient="index"); cdf.index.name="key"; cdf=cdf.reset_index()
inv = {ck:sg for sg,ck in CW.items()}
cdf["sigep"] = cdf["key"].map(lambda k: inv.get(k,k))
gdf = gdf.merge(cdf.drop(columns="key"), on="sigep", how="left", suffixes=("","_c"))

for pal in ["calido", "rojo", "azul", "verde"]:
    grafico_mapa(gdf, "pct_nbi_pobre",
        titulo="La pobreza por NBI marca una brecha territorial profunda",
        subtitulo="Población pobre por Necesidades Básicas Insatisfechas, Censo 2024",
        fuente="Fuente: INE Bolivia, Censo 2024. Elaboración: Centro de Estudios POPULI.",
        leyenda="% de la población", sufijo="%", paleta=pal,
        archivo=str(VIZ / "output" / f"paleta_{pal}.png"))
print("Paletas:", "calido, rojo, azul, verde")

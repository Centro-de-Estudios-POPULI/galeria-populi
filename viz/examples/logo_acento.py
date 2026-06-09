"""Compara el color del wordmark: marca roja vs acento del gráfico (no publica)."""
import sys, json
from pathlib import Path
import geopandas as gpd, pandas as pd

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ)); sys.path.insert(0, str(VIZ / "charts"))
from mapas import grafico_mapa, PALETA_ACENTO

gdf = gpd.read_file(VIZ / "geo" / "bolivia_municipios_sigep.topojson")
censo = json.loads((VIZ / "geo" / "censo_municipios_con_nbi.json").read_text(encoding="utf-8"))
CW = {"1280":"nd_020807","1435":"nd_040104","3101":"nd_011002","3401":"nd_040903",
      "3402":"nd_040801","3701":"nd_070702","3702":"nd_070705"}
cdf = pd.DataFrame.from_dict(censo, orient="index"); cdf.index.name="k"; cdf=cdf.reset_index()
inv = {ck:sg for sg,ck in CW.items()}; cdf["sigep"]=cdf["k"].map(lambda k: inv.get(k,k))
gdf = gdf.merge(cdf.drop(columns="k"), on="sigep", how="left", suffixes=("","_c"))

casos = [
    ("electricidad", "pct_electricidad", "verde", "Acceso a energía eléctrica",
     "Hogares con energía eléctrica — Censo 2024"),
    ("internet", "pct_internet", "azul", "Acceso a internet",
     "Hogares con acceso a internet — Censo 2024"),
]
for tag, col, pal, tit, sub in casos:
    ac = PALETA_ACENTO[pal]
    comun = dict(titulo=tit, subtitulo=sub, paleta=pal, sufijo="%",
                 fuente="Fuente: INE Bolivia, Censo 2024. Elaboración: Centro de Estudios POPULI.")
    # 1) marca roja (actual)
    grafico_mapa(gdf, col, **comun, archivo=str(VIZ / "output" / f"logo_{tag}_1_roja.png"))
    # 2) solo la línea teñida (P roja)
    grafico_mapa(gdf, col, **comun, acento_linea=ac,
                 archivo=str(VIZ / "output" / f"logo_{tag}_2_linea.png"))
    # 3) P + línea teñidas
    grafico_mapa(gdf, col, **comun, acento_p=ac, acento_linea=ac,
                 archivo=str(VIZ / "output" / f"logo_{tag}_3_full.png"))
print("Listo: logo_<tag>_{1_roja,2_linea,3_full}.png")

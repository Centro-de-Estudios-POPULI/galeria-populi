"""
Publica TODOS los indicadores del Censo 2024 como mapas municipales al Banco.
(Excluye pob_total: conteo crudo, no apto para coroplético en escala lineal.)
Paleta por familia/semántica: carencias y pobreza en 'calido'; servicios en
'verde'; digital, demografía y educación neutra en 'azul'; logros (cobertura,
ocupación) en 'verde'.
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
AUTOR = "Carlos Aranda"   # investigador/a responsable (a futuro puede variar por gráfico)
FUENTE = ("Fuente: INE Bolivia, Censo de Población y Vivienda 2024. "
          f"Elaboración: Centro de Estudios POPULI · {AUTOR}.")

# --- join con crosswalk de GAIOC/reclasificados (339/339) ------------------ #
gdf = gpd.read_file(GEO)
censo = json.loads(CENSO.read_text(encoding="utf-8"))
CROSSWALK = {"1280": "nd_020807", "1435": "nd_040104", "3101": "nd_011002",
             "3401": "nd_040903", "3402": "nd_040801", "3701": "nd_070702",
             "3702": "nd_070705"}
cdf = pd.DataFrame.from_dict(censo, orient="index"); cdf.index.name = "key"; cdf = cdf.reset_index()
inv = {ck: sg for sg, ck in CROSSWALK.items()}
cdf["sigep"] = cdf["key"].map(lambda k: inv.get(k, k))
gdf = gdf.merge(cdf.drop(columns="key"), on="sigep", how="left", suffixes=("", "_c"))
print(f"Unidos {gdf['pob_total'].notna().sum()}/{len(gdf)} municipios.\n")

# --- catálogo de indicadores: (col, slug, titulo, subtitulo, paleta, sufijo, dec)
P, S, A, V = "calido", "rojo", "azul", "verde"
IND = [
    # Servicios básicos (verde)
    ("pct_agua_caneria", "censo-agua-caneria", "Acceso a agua por cañería de red", "Hogares con agua por cañería de red", V, "%", 0),
    ("pct_agua_interior", "censo-agua-interior", "Agua por cañería dentro de la vivienda", "Hogares con agua por cañería dentro de la vivienda", V, "%", 0),
    ("pct_servicio_sanitario", "censo-servicio-sanitario", "Acceso a servicio sanitario", "Hogares con servicio sanitario", V, "%", 0),
    ("pct_alcantarillado", "censo-alcantarillado", "Conexión a alcantarillado", "Hogares conectados a alcantarillado", V, "%", 0),
    ("pct_electricidad", "censo-electricidad", "Acceso a energía eléctrica", "Hogares con energía eléctrica", V, "%", 0),
    ("pct_gas_natural", "censo-gas-natural", "Gas natural por red", "Hogares con gas natural por red domiciliaria", V, "%", 0),
    ("pct_basura_formal", "censo-basura-formal", "Recojo formal de basura", "Hogares con recojo formal de basura", V, "%", 0),
    # Digital / conectividad (azul)
    ("pct_internet", "censo-internet", "Acceso a internet", "Hogares con acceso a internet", A, "%", 0),
    ("pct_computadora", "censo-computadora", "Computadora en el hogar", "Hogares con al menos una computadora", A, "%", 0),
    ("pct_celular", "censo-celular", "Telefonía celular", "Hogares con servicio de telefonía celular", A, "%", 0),
    ("pct_tv_cable", "censo-tv-cable", "Televisión por cable", "Hogares con televisión por cable", A, "%", 0),
    # Educación
    ("pct_analfabetismo", "censo-analfabetismo", "Analfabetismo", "Tasa de analfabetismo en población de 15 años o más", P, "%", 0),
    ("prom_anios_estudio", "censo-anios-estudio", "Años promedio de estudio", "Años promedio de estudio de la población de 25 años o más", A, "", 1),
    ("pct_sin_educacion", "censo-sin-educacion", "Población sin instrucción", "Población sin ningún nivel de instrucción", P, "%", 0),
    ("pct_edu_primaria", "censo-edu-primaria", "Nivel educativo: primaria", "Población cuyo máximo nivel alcanzado es primaria", A, "%", 0),
    ("pct_edu_secundaria", "censo-edu-secundaria", "Nivel educativo: secundaria", "Población cuyo máximo nivel alcanzado es secundaria", A, "%", 0),
    ("pct_edu_superior", "censo-edu-superior", "Nivel educativo: superior", "Población de 25 años o más con educación superior", A, "%", 0),
    ("pct_asistencia_escolar", "censo-asistencia-escolar", "Asistencia escolar", "Asistencia escolar en edad obligatoria", V, "%", 0),
    ("pct_secundaria_mas", "censo-secundaria-mas", "Secundaria o más", "Población con secundaria completa o más", A, "%", 0),
    # Salud
    ("pct_seguro_salud", "censo-seguro-salud", "Cobertura de seguro de salud", "Población con algún seguro de salud", V, "%", 0),
    ("pct_discapacidad", "censo-discapacidad", "Población con discapacidad", "Población que declara alguna discapacidad", P, "%", 0),
    ("fecundidad", "censo-fecundidad", "Fecundidad", "Número promedio de hijos por mujer", A, "", 1),
    ("edad_1er_hijo", "censo-edad-primer-hijo", "Edad al primer hijo", "Edad promedio de la madre al primer hijo (años)", A, "", 1),
    # Empleo
    ("tasa_participacion", "censo-participacion-laboral", "Participación laboral", "Tasa de participación en la fuerza de trabajo", A, "%", 0),
    ("tasa_ocupacion", "censo-ocupacion", "Tasa de ocupación", "Población ocupada respecto a la población en edad de trabajar", V, "%", 0),
    ("tasa_desocupacion", "censo-desocupacion", "Tasa de desocupación", "Población desocupada respecto a la fuerza de trabajo", P, "%", 0),
    ("pct_sector_primario", "censo-sector-primario", "Empleo en sector primario", "Ocupados en agricultura, ganadería y minería", A, "%", 0),
    ("pct_sector_servicios", "censo-sector-servicios", "Empleo en sector servicios", "Ocupados en el sector servicios", A, "%", 0),
    ("pct_cuenta_propia", "censo-cuenta-propia", "Trabajo por cuenta propia", "Ocupados que trabajan por cuenta propia", A, "%", 0),
    # Vivienda
    ("pct_piso_tierra", "censo-piso-tierra", "Viviendas con piso de tierra", "Viviendas cuyo piso es de tierra", P, "%", 0),
    ("pct_pared_adobe", "censo-pared-adobe", "Viviendas con pared de adobe", "Viviendas cuyas paredes son de adobe o tapial", P, "%", 0),
    ("pct_techo_calamina", "censo-techo-calamina", "Viviendas con techo de calamina", "Viviendas cuyo techo es de calamina o plancha metálica", P, "%", 0),
    ("pct_hacinamiento", "censo-hacinamiento", "Hacinamiento", "Hogares en condición de hacinamiento", P, "%", 0),
    ("pct_vivienda_propia", "censo-vivienda-propia", "Vivienda propia", "Hogares con vivienda propia", V, "%", 0),
    ("pct_alquiler", "censo-alquiler", "Vivienda en alquiler", "Hogares que alquilan su vivienda", A, "%", 0),
    # Demografía
    ("pct_0_14", "censo-poblacion-0-14", "Población de 0 a 14 años", "Peso de la población de 0 a 14 años", A, "%", 0),
    ("pct_65_mas", "censo-poblacion-65-mas", "Población de 65 años o más", "Peso de la población de 65 años o más", A, "%", 0),
    ("tam_hogar", "censo-tamano-hogar", "Tamaño promedio del hogar", "Número promedio de personas por hogar", A, "", 1),
    ("pct_urbano", "censo-poblacion-urbana", "Población urbana", "Población que reside en áreas urbanas", A, "%", 0),
    ("pct_con_emigrante", "censo-hogares-emigrante", "Hogares con algún emigrante", "Hogares con al menos un emigrante internacional", A, "%", 0),
    # Pobreza por NBI
    ("pct_nbi_no_pobre", "censo-nbi-no-pobre", "Población no pobre (NBI)", "Población no pobre por Necesidades Básicas Insatisfechas", V, "%", 0),
    ("pct_nbi_satisfechas", "censo-nbi-satisfechas", "Necesidades básicas satisfechas", "Población con necesidades básicas satisfechas", V, "%", 0),
    ("pct_nbi_umbral", "censo-nbi-umbral", "Umbral de pobreza (NBI)", "Población en el umbral de la pobreza por NBI", P, "%", 0),
    ("pct_nbi_pobre", "censo-pobreza-nbi", "Pobreza por NBI", "Población pobre por Necesidades Básicas Insatisfechas", P, "%", 0),
    ("pct_nbi_moderada", "censo-nbi-moderada", "Pobreza moderada (NBI)", "Población en pobreza moderada por NBI", P, "%", 0),
    ("pct_nbi_indigente", "censo-nbi-indigente", "Indigencia (NBI)", "Población en pobreza indigente por NBI", P, "%", 0),
    ("pct_nbi_marginal", "censo-nbi-marginal", "Pobreza marginal (NBI)", "Población en pobreza marginal por NBI", P, "%", 1),
    ("pct_nbi_materiales", "censo-nbi-materiales", "Carencia en materiales de vivienda (NBI)", "Población con carencia en materiales de la vivienda", P, "%", 0),
    ("pct_nbi_espacios", "censo-nbi-espacios", "Carencia en espacios de vivienda (NBI)", "Población con carencia en espacios de la vivienda", P, "%", 0),
    ("pct_nbi_agua_sanea", "censo-nbi-agua-saneamiento", "Carencia en agua y saneamiento (NBI)", "Población con carencia en agua y saneamiento", P, "%", 0),
    ("pct_nbi_energia", "censo-nbi-energia", "Carencia en energía (NBI)", "Población con carencia en energía e iluminación", P, "%", 0),
    ("pct_nbi_educacion", "censo-nbi-educacion", "Carencia en educación (NBI)", "Población con carencia en educación", P, "%", 0),
    ("pct_nbi_salud", "censo-nbi-salud", "Carencia en salud (NBI)", "Población con carencia en atención de salud", P, "%", 0),
]

for col, slug, titulo, subtitulo, pal, suf, dec in IND:
    datos = gdf[["sigep", "municipio", "dpto", col]].rename(columns={"municipio": "nombre"}).set_index("sigep")
    publicar(
        meta={"slug": slug, "tipo": "mapa", "titulo": f"Bolivia: {titulo}",
              "subtitulo": f"{subtitulo} — por municipio", "fuente": FUENTE,
              "categoria": "censo", "tags": ["censo 2024", "municipios", col],
              "fecha": FECHA, "formato": "red_vertical"},
        df=datos, gdf=gdf, value_col=col, paleta=pal, sufijo=suf,
        label_fmt="{:." + str(dec) + "f}",
    )

build_manifest()
print(f"\n{len(IND)} mapas del Censo publicados al Banco.")

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
CENSO = VIZ / "geo" / "censo_municipios_con_nbi.json"   # v2: 136 indicadores (microdatos)
FECHA = "2026-06-10"
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
    # ── Indicadores v2 (microdatos CPV 2024, 2026-06-10) ────────────────────
    # Demografía
    ("indice_masculinidad", "censo-indice-masculinidad", "Índice de masculinidad", "Hombres por cada 100 mujeres", A, "", 0),
    ("edad_mediana", "censo-edad-mediana", "Edad mediana", "Edad mediana de la población, en años", A, "", 0),
    ("razon_dependencia", "censo-razon-dependencia", "Razón de dependencia", "Dependientes (0-14 y 65+) por cada 100 personas en edad de trabajar", P, "", 0),
    ("pct_hogar_unipersonal", "censo-hogares-unipersonales", "Hogares unipersonales", "Hogares de una sola persona", A, "%", 0),
    ("pct_hogar_extendido", "censo-hogares-extendidos", "Hogares extendidos", "Hogares extendidos o compuestos", A, "%", 0),
    # Pueblos e idiomas
    ("pct_autoident_indigena", "censo-autoident-indigena", "Autoidentificación indígena", "Población que se autoidentifica con una nación o pueblo indígena originario campesino o afroboliviano", A, "%", 0),
    ("pct_quechua", "censo-autoident-quechua", "Autoidentificación quechua", "Población que se autoidentifica quechua", A, "%", 0),
    ("pct_aymara", "censo-autoident-aymara", "Autoidentificación aymara", "Población que se autoidentifica aymara", A, "%", 0),
    ("pct_guarani", "censo-autoident-guarani", "Autoidentificación guaraní", "Población que se autoidentifica guaraní", A, "%", 1),
    ("pct_idioma_materno_originario", "censo-idioma-originario", "Idioma materno originario", "Población cuyo primer idioma de la niñez es originario", A, "%", 0),
    ("pct_idioma_materno_castellano", "censo-idioma-castellano", "Idioma materno castellano", "Población cuyo primer idioma de la niñez es el castellano", A, "%", 0),
    # Ciudadanía y educación
    ("pct_registro_civil", "censo-registro-civil", "Inscripción en el registro civil", "Personas con nacimiento inscrito en el registro civil", V, "%", 0),
    ("pct_cedula_identidad", "censo-cedula-identidad", "Tenencia de cédula de identidad", "Personas que tienen o tuvieron cédula de identidad", V, "%", 0),
    ("pct_educacion_publica", "censo-educacion-publica", "Dependencia de la educación pública", "Estudiantes que asisten a establecimientos públicos o de convenio", A, "%", 0),
    ("tasa_asistencia_4_5", "censo-asistencia-inicial", "Asistencia a educación inicial", "Niños de 4 y 5 años que asisten a un establecimiento educativo", V, "%", 0),
    ("tasa_asistencia_18_24", "censo-asistencia-18-24", "Asistencia educativa de 18 a 24 años", "Jóvenes de 18 a 24 años que continúan estudiando", V, "%", 0),
    ("pct_analfabetismo_mujeres", "censo-analfabetismo-femenino", "Analfabetismo femenino", "Mujeres de 15 años o más que no saben leer ni escribir", P, "%", 0),
    # Salud
    ("pct_salud_publica", "censo-salud-publica", "Uso de la salud pública", "Población que acude a establecimientos públicos de salud", A, "%", 0),
    ("pct_caja_salud", "censo-cajas-salud", "Uso de cajas de salud", "Población que acude a cajas de salud (seguridad social)", A, "%", 0),
    ("pct_salud_privada", "censo-salud-privada", "Uso de salud privada", "Población que acude a consultorios o clínicas privadas", A, "%", 0),
    ("pct_salud_tradicional", "censo-medicina-tradicional", "Uso de medicina tradicional", "Población que acude a médicos tradicionales ancestrales", A, "%", 0),
    ("pct_automedicacion", "censo-automedicacion", "Automedicación", "Población que se automedica o compra sin receta médica", P, "%", 0),
    ("pct_parto_calificado", "censo-parto-calificado", "Partos con personal calificado", "Últimos partos atendidos por personal de salud calificado", V, "%", 0),
    ("pct_hijos_fallecidos", "censo-hijos-fallecidos", "Mortalidad en la niñez acumulada", "Hijos fallecidos sobre nacidos vivos declarados por las madres", P, "%", 1),
    ("pct_madres_adolescentes", "censo-madres-adolescentes", "Maternidad adolescente", "Mujeres de 15 a 19 años que ya son madres", P, "%", 1),
    # Discapacidad
    ("pct_disc_ver", "censo-discapacidad-visual", "Dificultad severa para ver", "Personas con mucha o total dificultad para ver", P, "%", 1),
    ("pct_disc_oir", "censo-discapacidad-auditiva", "Dificultad severa para oír", "Personas con mucha o total dificultad para oír", P, "%", 1),
    ("pct_disc_caminar", "censo-discapacidad-motriz", "Dificultad severa para caminar", "Personas con mucha o total dificultad para caminar o usar brazos", P, "%", 1),
    ("pct_disc_cognitiva", "censo-discapacidad-cognitiva", "Dificultad severa cognitiva", "Personas con mucha o total dificultad para comunicarse o razonar", P, "%", 1),
    # Empleo
    ("pct_asalariados", "censo-asalariados", "Empleo asalariado", "Ocupados que trabajan como empleados u obreros", A, "%", 0),
    ("pct_empleadores", "censo-empleadores", "Empleadores", "Ocupados que son empleadores o socios", A, "%", 1),
    ("pct_trab_familiar", "censo-trabajo-familiar", "Trabajo familiar sin remuneración", "Ocupados en negocios familiares sin pago", P, "%", 1),
    ("pct_sector_secundario", "censo-sector-secundario", "Empleo en el sector secundario", "Ocupados en industria, construcción, electricidad y agua", A, "%", 0),
    ("pct_comercio", "censo-empleo-comercio", "Empleo en comercio", "Ocupados en comercio y reparación de vehículos", A, "%", 0),
    ("pct_admin_publica", "censo-empleo-publico", "Empleo en administración pública", "Ocupados en administración pública y defensa", A, "%", 1),
    ("tasa_participacion_fem", "censo-participacion-femenina", "Participación laboral femenina", "Mujeres en edad de trabajar dentro de la fuerza laboral", V, "%", 0),
    ("tasa_ocupacion_fem", "censo-ocupacion-femenina", "Ocupación femenina", "Mujeres en edad de trabajar que están ocupadas", V, "%", 0),
    # Migración interna y movilidad
    ("pct_nacido_otro_municipio", "censo-nacidos-otro-municipio", "Atracción migratoria histórica", "Residentes nacidos en otro municipio del país", A, "%", 0),
    ("pct_nacido_extranjero", "censo-nacidos-extranjero", "Población nacida en el extranjero", "Residentes nacidos en otro país", A, "%", 1),
    ("pct_migrante_reciente", "censo-migrantes-recientes", "Migración reciente", "Residentes que en 2019 vivían en otro municipio o país", A, "%", 0),
    ("pct_trabaja_fuera", "censo-trabaja-fuera", "Trabajo fuera del municipio", "Ocupados cuyo lugar de trabajo está fuera del municipio", A, "%", 1),
    # Emigración internacional
    ("emigrantes_x1000", "censo-emigrantes", "Emigración internacional", "Emigrantes por cada 1.000 habitantes", P, "", 0),
    ("pct_emi_argentina", "censo-emigrantes-argentina", "Emigrantes en Argentina", "Emigrantes del municipio cuyo destino es Argentina", A, "%", 0),
    ("pct_emi_espana", "censo-emigrantes-espana", "Emigrantes en España", "Emigrantes del municipio cuyo destino es España", A, "%", 0),
    ("pct_emi_brasil", "censo-emigrantes-brasil", "Emigrantes en Brasil", "Emigrantes del municipio cuyo destino es Brasil", A, "%", 0),
    ("pct_emi_chile", "censo-emigrantes-chile", "Emigrantes en Chile", "Emigrantes del municipio cuyo destino es Chile", A, "%", 0),
    ("pct_emi_eeuu", "censo-emigrantes-eeuu", "Emigrantes en Estados Unidos", "Emigrantes del municipio cuyo destino es EE.UU.", A, "%", 1),
    ("edad_prom_emigracion", "censo-edad-emigracion", "Edad promedio al emigrar", "Edad promedio a la que las personas salieron del país, en años", A, "", 1),
    # Servicios básicos
    ("pct_agua_no_mejorada", "censo-agua-no-mejorada", "Agua de fuente no mejorada", "Viviendas que se abastecen de pozo sin protección, río o aguatero", P, "%", 0),
    ("pct_agua_pozo", "censo-agua-pozo", "Abastecimiento de agua por pozo", "Viviendas que se abastecen de pozo excavado o perforado", A, "%", 0),
    ("pct_pozo_ciego", "censo-pozo-ciego", "Desagüe a pozo ciego o superficie", "Viviendas cuyo baño desagua a pozo ciego o a la superficie", P, "%", 0),
    ("pct_camara_septica", "censo-camara-septica", "Desagüe a cámara séptica", "Viviendas cuyo baño desagua a cámara séptica", A, "%", 0),
    ("pct_sin_energia", "censo-sin-electricidad", "Viviendas sin energía eléctrica", "Viviendas sin ninguna fuente de energía eléctrica", P, "%", 0),
    ("pct_panel_solar", "censo-panel-solar", "Energía por panel solar", "Viviendas cuya electricidad proviene de panel solar", A, "%", 1),
    # Energía y cocina
    ("pct_combustible_solido", "censo-cocina-lena", "Cocina con leña o guano", "Viviendas que cocinan con leña, guano, bosta o taquia", P, "%", 0),
    ("pct_gas_garrafa", "censo-gas-garrafa", "Cocina con gas en garrafa", "Viviendas cuyo combustible principal es el gas en garrafa", A, "%", 0),
    ("pct_cocina_exclusiva", "censo-cocina-exclusiva", "Cuarto exclusivo para cocinar", "Viviendas con un cuarto solo para cocinar", V, "%", 0),
    # Vivienda y materiales
    ("pct_pared_ladrillo", "censo-pared-ladrillo", "Paredes de ladrillo o bloque", "Viviendas con paredes de ladrillo, bloque u hormigón", V, "%", 0),
    ("pct_revoque", "censo-pared-revoque", "Paredes con revoque", "Viviendas con paredes interiores revocadas", V, "%", 0),
    ("pct_techo_teja", "censo-techo-teja", "Techos de teja", "Viviendas con techo de teja", A, "%", 0),
    ("pct_techo_paja", "censo-techo-paja", "Techos de paja o palma", "Viviendas con techo de paja, palma, caña o barro", P, "%", 1),
    ("pct_monoambiente", "censo-monoambiente", "Viviendas de un solo cuarto", "Viviendas que ocupan un solo cuarto", P, "%", 0),
    ("pct_choza", "censo-chozas", "Chozas y pahuichis", "Viviendas clasificadas como choza o pahuichi", P, "%", 1),
    ("pct_departamento", "censo-departamentos", "Viviendas tipo departamento", "Viviendas en edificios de departamentos", A, "%", 1),
    ("pct_vivienda_desocupada", "censo-viviendas-desocupadas", "Viviendas desocupadas", "Viviendas desocupadas sobre el total registrado", A, "%", 0),
    # Tecnología
    ("pct_internet_fijo", "censo-internet-fijo", "Internet fijo", "Hogares con internet fijo en la vivienda", V, "%", 0),
    ("pct_internet_movil", "censo-internet-movil", "Internet móvil", "Hogares con internet móvil (megas o datos)", A, "%", 0),
    ("pct_telefono_fijo", "censo-telefono-fijo", "Telefonía fija", "Hogares con servicio de telefonía fija", A, "%", 1),
    # Equipamiento del hogar
    ("pct_refrigerador", "censo-refrigerador", "Hogares con refrigerador", "Hogares que tienen refrigerador o congeladora", V, "%", 0),
    ("pct_lavadora", "censo-lavadora", "Hogares con lavadora", "Hogares que tienen lavadora de ropa", V, "%", 0),
    ("pct_microondas", "censo-microondas", "Hogares con microondas", "Hogares que tienen horno microondas", A, "%", 0),
    ("pct_aire_acond", "censo-aire-acondicionado", "Hogares con aire acondicionado", "Hogares que tienen aire acondicionado", A, "%", 1),
    ("pct_auto", "censo-vehiculo", "Hogares con vehículo", "Hogares que tienen vehículo automotor", V, "%", 0),
    ("pct_moto", "censo-motocicleta", "Hogares con motocicleta", "Hogares que tienen motocicleta o cuadratrack", A, "%", 0),
    ("pct_bicicleta", "censo-bicicleta", "Hogares con bicicleta", "Hogares que tienen bicicleta", A, "%", 0),
    ("pct_bote", "censo-bote", "Hogares con bote o canoa", "Hogares con deslizador, balsa, canoa o bote", A, "%", 1),
    ("pct_radio", "censo-radio", "Hogares con radio", "Hogares que tienen radio o equipo de sonido", A, "%", 0),
    ("pct_tv", "censo-televisor", "Hogares con televisor", "Hogares que tienen televisor", A, "%", 0),
    # Mortalidad
    ("pct_hogar_fallecido", "censo-hogares-fallecido", "Hogares con algún fallecido", "Hogares donde murió un miembro desde 2019", P, "%", 0),
    ("tasa_mortalidad", "censo-tasa-mortalidad", "Mortalidad declarada", "Fallecidos declarados por 1.000 habitantes (anualizado 2019-2024)", P, "", 1),
    ("edad_prom_fallecimiento", "censo-edad-fallecimiento", "Edad promedio de fallecimiento", "Edad promedio al morir de los fallecidos declarados, en años", V, "", 1),
    ("pct_muertes_covid", "censo-muertes-covid", "Muertes atribuidas al COVID-19", "Fallecidos 2019-2024 cuya causa declarada fue el COVID-19", P, "%", 0),
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

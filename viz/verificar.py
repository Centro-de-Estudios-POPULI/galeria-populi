# -*- coding: utf-8 -*-
"""
verificar.py — EL CONTRATO del Banco de Gráficos con la marca y con los atlas.

Corre antes de cada publicación (y lo puede correr el CI). ABORTA con código 1
si algo de esto deja de ser cierto:

  1. La paleta es UNA: viz/paleta.py es copia byte a byte de populi-marca, y la
     rampa de mapas es idéntica en populi_style, en el Atlas Socioeconómico y
     en el Atlas Fiscal.
  2. Cada ficha tiene su PNG y su miniatura; ningún slug se repite; ninguna
     categoría vacía llega al manifiesto.
  3. Cada indicador de los dos catálogos del Atlas tiene su lámina, y el índice
     que leen los atlas la nombra.
  4. El pivote que declara cada lámina censal es el que el Atlas calcula con
     la MISMA regla (ponderado por el denominador propio; brechas por
     componentes; conteos en su mediana), recomputado acá de forma
     independiente.
  5. La web del Banco no tiene colores fuera de la paleta, ni esquinas
     redondeadas, ni las fuentes derogadas; el motor no pide negrita con
     weight="bold".
  6. Los dos atlas leen el índice de láminas y no escriben Newsreader.

    python viz/verificar.py            # todo
    python viz/verificar.py --rapido   # sin recomputar los pivotes
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
VIZ = Path(__file__).resolve().parent
ROOT = VIZ.parent
PROY = ROOT.parent
MARCA = PROY / "populi-marca"
ATL = PROY / "Observatorio de Presupuesto Fiscal Departamental" / "_github_atlas_fiscal"
RAPIDO = "--rapido" in sys.argv

fallas, avisos = [], []


def falla(msg):
    fallas.append(msg)
    print("  ⛔", msg)


def aviso(msg):
    avisos.append(msg)
    print("  ⚠️ ", msg)


def ok(msg):
    print("  ✓", msg)


def hexes(texto):
    return {h.upper() for h in re.findall(r"#([0-9A-Fa-f]{6})\b", texto)}


# ── 1 · la paleta es una ────────────────────────────────────────────────────
print("1 · paleta")
sys.path.insert(0, str(VIZ))
import paleta as pal
def _colores(v):
    if isinstance(v, str):
        return [v]
    if isinstance(v, list):
        return [c for c in v if isinstance(c, str)]
    if isinstance(v, dict):
        return [c for x in v.values() for c in _colores(x)]
    return []


OFICIAL = {c.upper().lstrip("#") for k, v in vars(pal).items() if not k.startswith("_")
           for c in _colores(v) if re.fullmatch(r"#[0-9A-Fa-f]{6}", c)}
if (MARCA / "paleta.py").exists():
    if (MARCA / "paleta.py").read_bytes().replace(b"\r\n", b"\n") != (VIZ / "paleta.py").read_bytes().replace(b"\r\n", b"\n"):
        falla("viz/paleta.py difiere de populi-marca/paleta.py (copiar de nuevo)")
    else:
        ok("viz/paleta.py = populi-marca/paleta.py")
    pj = json.loads((MARCA / "paleta.json").read_text(encoding="utf-8"))
    if [c.upper() for c in pj["DIVERGING_MAPA"]] != [c.upper() for c in pal.DIVERGING_MAPA]:
        falla("paleta.json desactualizado: correr populi-marca/exportar.py")
else:
    aviso("populi-marca no está al lado: no se comparó la copia de la paleta")

import populi_style as ps
rampa = [c.upper() for c in ps.DIV_ATLAS]
if rampa != [c.upper() for c in pal.DIVERGING_MAPA]:
    falla("populi_style.DIV_ATLAS no es paleta.DIVERGING_MAPA")
for nombre, rx in (("Mapa_Censo_2024_Bolivia.html", r"const DIV=d3\.interpolateRgbBasis\(\[([^\]]+)\]\)"),
                   ("mapa.html", r"const ESP=\[([^\]]+)\]")):
    p = ATL / nombre
    if not p.exists():
        aviso(f"{nombre} no está: no se comparó su rampa")
        continue
    m = re.search(rx, p.read_text(encoding="utf-8"))
    arr = [c.strip(' "\'').upper() for c in m.group(1).split(",")] if m else None
    if arr != rampa:
        falla(f"{nombre}: la rampa difiere de DIVERGING_MAPA ({arr})")
    else:
        ok(f"{nombre}: rampa idéntica, 9 tonos")

# ── 2 · fichas, archivos, slugs, categorías ─────────────────────────────────
print("2 · fichas y archivos")
fichas = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "data" / "catalogo").glob("*.json"))]
slugs = [f["slug"] for f in fichas]
if len(slugs) != len(set(slugs)):
    falla("slugs repetidos")
for f in fichas:
    for campo in ("imagen", "thumb"):
        if not (ROOT / "public" / f[campo]).exists():
            falla(f"{f['slug']}: falta {f[campo]}")
    if not f["thumb"].endswith(".webp"):
        falla(f"{f['slug']}: miniatura no es WebP")
    if f.get("atlas") and not all(f.get(k) for k in ("clave", "modo", "enlace")):
        falla(f"{f['slug']}: lámina de atlas sin clave/modo/enlace")
sueltos = {p.name for p in (ROOT / "public" / "graficas").glob("*.png")} - {f["slug"] + ".png" for f in fichas}
if sueltos:
    falla(f"{len(sueltos)} PNG sin ficha: {sorted(sueltos)[:5]}")
sueltos_t = {p.name for p in (ROOT / "public" / "thumbs").iterdir()} - {f["slug"] + ".webp" for f in fichas}
if sueltos_t:
    falla(f"{len(sueltos_t)} miniaturas sin ficha: {sorted(sueltos_t)[:5]}")
man = json.loads((ROOT / "src" / "manifest.json").read_text(encoding="utf-8"))
usadas = {f["categoria"] for f in man["graficas"]}
vacias = [c for c in man["categorias"] if c not in usadas]
if vacias:
    falla(f"categorías vacías en el manifiesto: {vacias}")
if len(man["graficas"]) != len(fichas):
    falla(f"manifest.json tiene {len(man['graficas'])} gráficas y hay {len(fichas)} fichas: correr build_manifest")
ok(f"{len(fichas)} fichas con PNG y WebP · {len(usadas)} categorías")

# ── 3 · cada indicador del Atlas tiene lámina y el índice la nombra ─────────
print("3 · puente con los atlas")
indice = json.loads((ROOT / "public" / "indice_laminas.json").read_text(encoding="utf-8"))["laminas"]
por = {(f.get("atlas"), f.get("clave"), f.get("modo")): f["slug"] for f in fichas if f.get("atlas")}
if (ATL / "catalogo.json").exists():
    cat = json.loads((ATL / "catalogo.json").read_text(encoding="utf-8"))
    inds = [i for g in cat["grupos"] for i in g["indicadores"]]
    sin = [i["key"] for i in inds if ("censo", i["key"], "2024") not in por]
    sin12 = [i["key"] for i in inds if i.get("s12") and ("censo", i["key"], "2012") not in por]
    sinc = [i["key"] for i in inds if i.get("s12") and ("censo", i["key"], "cambio") not in por]
    for nombre, lst in (("2024", sin), ("2012", sin12), ("cambio", sinc)):
        if lst:
            falla(f"censo {nombre}: {len(lst)} indicadores sin lámina: {lst[:6]}")
    malos = [i["key"] for i in inds if i.get("lam") and por.get(("censo", i["key"], "2024")) != i["lam"]]
    if malos:
        falla(f"`lam` del catálogo no coincide con el slug publicado: {malos[:6]}")
    ok(f"censo: {len(inds)} indicadores · {sum(1 for i in inds if i.get('s12'))} con serie 2012")
if (ATL / "fiscal_catalogo.json").exists():
    fc = json.loads((ATL / "fiscal_catalogo.json").read_text(encoding="utf-8"))
    finds = [i for g in fc["grupos"] for i in g["indicadores"]]
    base = str(fc["anios"][-1])
    sinf = [i["key"] for i in finds if ("fiscal", i["key"], base) not in por]
    if sinf:
        falla(f"fiscal {base}: sin lámina {sinf}")
    sint = [i["key"] for i in finds if not i.get("titulo_lamina")]
    if sint:
        falla(f"fiscal: sin titulo_lamina en el catálogo {sint}")
    ok(f"fiscal: {len(finds)} indicadores con lámina de {base}")
for (a, k, m), s in por.items():
    if indice.get(a, {}).get(k, {}).get(m) != s:
        falla(f"índice: falta {a}/{k}/{m}")
        break
else:
    ok(f"indice_laminas.json nombra las {len(por)} láminas")

# ── 4 · el pivote de la lámina es el del Atlas (recomputado aparte) ─────────
if not RAPIDO and (ATL / "data.json").exists():
    print("4 · pivotes")
    D = {"2024": json.loads((ATL / "data.json").read_text(encoding="utf-8"))}
    DN = json.loads((ATL / "denominadores.json").read_text(encoding="utf-8"))
    orden, muni = DN["orden"], DN["municipios"]
    porkey = {i["key"]: i for i in inds}

    def w_de(r, ind):
        Dm = muni.get(r.get("cod_ine")) if r.get("cod_ine") else None
        j = orden.index(ind["den"]) if ind.get("den") in orden else -1
        return (Dm[j] if (Dm and j >= 0) else r.get("pob_total"))

    def ponderado(k, ind):
        n = d = 0.0
        for r in D["2024"].values():
            v, w = r.get(k), w_de(r, ind)
            if v is not None and w:
                n += v * w
                d += w
        return n / d if d else None

    peor, n_ok, n_dif = (0, None), 0, []
    for f in fichas:
        if f.get("atlas") != "censo" or f.get("modo") == "cambio" or not f.get("escala"):
            continue
        ind = porkey.get(f["clave"])
        if not ind:
            continue
        agg = ind.get("agg")
        if agg in ("suma", "no"):
            esperado = None                       # mediana del modo: la calcula el generador
        elif agg == "brecha":
            a, b = ponderado(ind["comp"][0], ind), ponderado(ind["comp"][1], ind)
            esperado = None if a is None or b is None else a - b
        else:
            esperado = ponderado(ind["key"], ind)
        real = f["escala"].get("piv_real")
        if esperado is None:
            if f["escala"].get("piv_tipo") != "mediana":
                n_dif.append((f["slug"], "debía ser mediana"))
            continue
        if real is None or abs(real - esperado) > 1e-6:
            n_dif.append((f["slug"], f"{real} vs {esperado}"))
        else:
            n_ok += 1
    if n_dif:
        falla(f"{len(n_dif)} pivotes difieren del Atlas: {n_dif[:4]}")
    else:
        ok(f"{n_ok} pivotes de 2024/2012 coinciden con la regla del Atlas")

# ── 5 · la web del Banco y el motor, dentro de la marca ─────────────────────
print("5 · marca")
PERMITIDOS = OFICIAL | {"FFFFFF", "000000"}
web = ""
for p in list((ROOT / "src").rglob("*.astro")) + list((ROOT / "src").rglob("*.css")) + list((ROOT / "src").rglob("*.ts")):
    if p.name == "manifest.json":
        continue
    t = p.read_text(encoding="utf-8")
    web += t
    fuera = hexes(t) - PERMITIDOS
    if fuera:
        falla(f"{p.relative_to(ROOT)}: colores fuera de paleta {sorted(fuera)[:8]}")
    radios = [m for m in re.findall(r"border-radius\s*:\s*([^;}]+)", t) if m.strip() not in ("0", "0px")]
    if radios:
        falla(f"{p.relative_to(ROOT)}: border-radius distinto de 0 ({radios[:4]})")
    if re.search(r"Public\+?Sans|IBM\+?Plex|Newsreader|Fraunces|Manrope", t):
        falla(f"{p.relative_to(ROOT)}: fuente derogada")
if web:
    ok("src/: sin colores fuera de paleta, sin radios, sin fuentes derogadas")
for p in list((VIZ / "charts").glob("*.py")) + [VIZ / "populi_style.py", VIZ / "catalogo.py"]:
    t = p.read_text(encoding="utf-8")
    codigo = "\n".join(l.split("#", 1)[0] if not l.lstrip().startswith("#") else "" for l in t.splitlines())
    if 'weight="bold"' in codigo:
        falla(f"{p.name}: pide negrita con weight=\"bold\" (usar ps.BOLD / ps.MONO_BOLD)")
    fuera = hexes(codigo) - PERMITIDOS
    if fuera:
        falla(f"{p.name}: hexadecimales sueltos {sorted(fuera)[:6]}")
ok("viz/: sin negritas falsas ni hexadecimales sueltos")

# ── 6 · los atlas ───────────────────────────────────────────────────────────
print("6 · atlas")
for nombre in ("Mapa_Censo_2024_Bolivia.html", "mapa.html", "index.html"):
    p = ATL / nombre
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    if "Newsreader" in t:
        falla(f"{nombre}: Newsreader (el display es Playfair Display)")
    if nombre != "index.html" and "indice_laminas.json" not in t:
        falla(f"{nombre}: no lee indice_laminas.json")
    radios = [m for m in re.findall(r"border-radius\s*:\s*([^;}]+)", t) if m.strip() not in ("0", "0px")]
    if radios:
        aviso(f"{nombre}: border-radius {radios} (sólo se admite el de la hoja móvil)")
ok("atlas revisados")

print()
if fallas:
    print(f"⛔ {len(fallas)} fallas · {len(avisos)} avisos")
    sys.exit(1)
print(f"✅ contrato íntegro · {len(avisos)} avisos")

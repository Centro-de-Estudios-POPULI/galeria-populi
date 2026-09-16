# -*- coding: utf-8 -*-
"""
vitrina.py — el mapa vivo de la cabecera del Banco (src/vitrina.json).

Un solo dibujo de los 343 municipios (arcos del topojson simplificados YA
proyectados, para que los vecinos sigan compartiendo el borde) y, para unas
pocas láminas elegidas, el color de cada municipio calculado con LA MISMA
escala de la lámina (`escala_atlas` con el dominio, el pivote y la dirección
declarados en su ficha). La portada rota entre ellas cambiando sólo el `fill`.

    python viz/vitrina.py
"""
import io
import json
import math
import sys
from pathlib import Path

from shapely.geometry import LineString

VIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(VIZ))
import populi_style as ps

sys.stdout.reconfigure(encoding="utf-8")
ROOT = VIZ.parent
ATL = ROOT.parent / "Observatorio de Presupuesto Fiscal Departamental" / "_github_atlas_fiscal"
GEO = ATL / "municipios.topojson"
if not GEO.exists():
    GEO = VIZ / "geo" / "atlas_muni_343.topojson"
OUT = ROOT / "src" / "vitrina.json"
W, H, TOL = 420.0, 500.0, 1.1

# las láminas de la vitrina: (slug de la ficha). El resto sale de la ficha y del catálogo.
SLUGS = ["censo-poblacion-urbana", "censo-acceso-a-fuente-mejorada", "censo-poblacion-total-cambio",
         "fiscal-ic-pc", "censo-analfabetismo", "censo-hogares-con-internet"]

# ── geometría ────────────────────────────────────────────────────────────────
topo = json.loads(GEO.read_text(encoding="utf-8"))
tr = topo["transform"]
sx, sy = tr["scale"]
tx, ty = tr["translate"]


def arco(a):
    x = y = 0
    pts = []
    for dx, dy in a:
        x += dx
        y += dy
        pts.append((x * sx + tx, y * sy + ty))
    return pts


ARCS = [arco(a) for a in topo["arcs"]]


def merc(lon, lat):
    return math.radians(lon), math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


todos = [merc(*p) for a in ARCS for p in a]
x0, x1 = min(p[0] for p in todos), max(p[0] for p in todos)
y0, y1 = min(p[1] for p in todos), max(p[1] for p in todos)
k = min(W / (x1 - x0), H / (y1 - y0))
ox, oy = (W - (x1 - x0) * k) / 2, (H - (y1 - y0) * k) / 2


def proy(p):
    x, y = merc(*p)
    return ((x - x0) * k + ox, (y1 - y) * k + oy)


ARCS_P = []
for a in ARCS:
    pts = [proy(p) for p in a]
    if len(pts) > 2:
        pts = list(LineString(pts).simplify(TOL, preserve_topology=False).coords)
    ARCS_P.append(pts)


def anillo(idx):
    out = []
    for i in idx:
        a = ARCS_P[~i][::-1] if i < 0 else ARCS_P[i]
        out += a[1:] if out else a
    return out


obj = topo["objects"][next(iter(topo["objects"]))]
geo, orden = [], []
for g in obj["geometries"]:
    sig = g["properties"]["sigep"]
    polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
    d = ""
    for poly in polys:
        for ring in poly:
            pts = anillo(ring)
            if len(pts) >= 3:
                d += "M" + "L".join(f"{round(p[0])} {round(p[1])}" for p in pts) + "Z"
    if d:
        geo.append({"s": sig, "d": d})
        orden.append(sig)
print(f"geometría: {len(geo)} municipios, {sum(len(x['d']) for x in geo) // 1024} KB de trazos")

# ── colores por lámina, con la escala de su ficha ────────────────────────────
cat = json.loads((ATL / "catalogo.json").read_text(encoding="utf-8"))
IND = {i["key"]: i for g in cat["grupos"] for i in g["indicadores"]}
fcat = json.loads((ATL / "fiscal_catalogo.json").read_text(encoding="utf-8"))
FIND = {i["key"]: i for g in fcat["grupos"] for i in g["indicadores"]}
D24 = json.loads((ATL / "data.json").read_text(encoding="utf-8"))
D12 = json.loads((ATL / "data_2012.json").read_text(encoding="utf-8"))
FD = json.loads((ATL / "fiscal_data.json").read_text(encoding="utf-8"))


def valores(f):
    k = f["clave"]
    if f["atlas"] == "fiscal":
        yi = fcat["anios"].index(int(f["modo"]))
        return [(FD.get(s, {}).get("s", {}).get(k) or [None] * (yi + 1))[yi] for s in orden]
    ind = IND[k]
    conteo = ind.get("agg") == "suma"
    if f["modo"] == "cambio":
        out = []
        for s in orden:
            a, b = (D12.get(s) or {}).get(k), (D24.get(s) or {}).get(k)
            out.append(None if a is None or b is None else ((100 * (b - a) / a if a else None) if conteo else b - a))
        return out
    src = D12 if f["modo"] == "2012" else D24
    return [(src.get(s) or {}).get(k) for s in orden]


def hexa(rgba):
    return "#%02x%02x%02x" % tuple(int(round(c * 255)) for c in rgba[:3])


items = []
for slug in SLUGS:
    p = ROOT / "data" / "catalogo" / f"{slug}.json"
    if not p.exists():
        print(f"  ⚠️ sin ficha: {slug}")
        continue
    f = json.loads(p.read_text(encoding="utf-8"))
    e = f["escala"]
    ind = FIND[f["clave"]] if f["atlas"] == "fiscal" else IND[f["clave"]]
    vals = valores(f)
    cambio = f.get("modo") == "cambio"
    cmap, norm, info = ps.escala_atlas(
        [v if v is not None else float("nan") for v in vals],
        direccion=ind.get("dir", 0), con_signo=cambio or bool(ind.get("div")),
        dominio=[e["lo"], e["hi"]], pivote=None if cambio else e["piv_real"], piv_tipo=e["piv_tipo"])
    colores = [hexa(cmap(norm(v))) if v is not None else "" for v in vals]
    u = f.get("unidad") or ""
    dec = 0 if (u in ("hab", "viv") and not cambio) else 1
    fmt = lambda v: (("+" if cambio and v > 0 else "") + ps.es_num(v, dec, miles=(u == "hab")))
    suf = "%" if u == "%" else ("" if not u else " " + u)
    corte = {"2024": "Censo 2024", "2012": "Censo 2012", "cambio": "Cambio 2012–2024"}.get(f.get("modo"), "Gestión " + str(f.get("modo")))
    items.append({
        "slug": slug, "titulo": f["titulo"].replace("Bolivia: ", ""),
        "sub": corte + " · " + (f.get("grupo") or ""),
        "lo": fmt(e["lo"]) + suf, "hi": fmt(e["hi"]) + suf,
        "piv": (e["piv_tipo"] + " " + fmt(e["piv_real"]) + suf) if e.get("piv_real") is not None else "",
        "invertida": ind.get("dir", 0) == 1,
        "colores": colores,
    })
    print(f"  {slug}: {sum(1 for c in colores if c)} con color · {items[-1]['lo']} → {items[-1]['hi']}")

out = {"vb": [W, H], "rampa": ps.DIV_ATLAS, "geo": geo, "items": items}
OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"→ {OUT} ({OUT.stat().st_size // 1024} KB, {len(items)} láminas)")

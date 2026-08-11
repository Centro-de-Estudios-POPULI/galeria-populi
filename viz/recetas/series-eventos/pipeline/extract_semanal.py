"""
Extrae la serie SEMANAL de Reservas Internacionales del BCB desde varios
Excel semanales y las fusiona en una sola serie continua.

Cada Excel del BCB trae los meses anteriores como columnas mensuales y SOLO
las semanas del mes en curso. Por eso descargamos un archivo por cada semana
disponible y unimos sus columnas semanales (oro, divisas, DEG, FMI, RIB/RIN).

El mapeo de filas se hace por ETIQUETA (find_row_map del scraper del monitor),
porque el BCB mueve las filas entre versiones del Excel.
"""
import sys, json, time, datetime, re
from pathlib import Path
import requests, openpyxl

# Reusar el detector de filas por etiqueta del scraper del monitor
sys.path.insert(0, r"C:\Users\HP\OneDrive\Desktop\Proyectos\populi-monetario\scraper")
from scrape_rin import find_row_map  # noqa: E402

BASE = "https://www.bcb.gob.bo/webdocs/05_estadisticassemanales/Semanal%20{w}_{y}{suf}.xlsx"
SUFFIXES = ["", "_0", "_1", "%20(1)", "%20(2)"]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,"
              "application/vnd.ms-excel,*/*",
    "Referer": "https://www.bcb.gob.bo/",
}
RAW = Path(__file__).parent / "raw"
KEYS = ("rib", "rin", "oro", "divisas", "deg", "fmi")


def url_for(w, y, sess):
    for suf in SUFFIXES:
        u = BASE.format(w=w, y=y, suf=suf)
        try:
            r = sess.head(u, headers=HEADERS, timeout=15, allow_redirects=True)
            if r.status_code == 200:
                return u
        except requests.RequestException:
            continue
    return None


def download(w, y, sess):
    path = RAW / f"semanal_{y}_{w:02d}.xlsx"
    if path.exists() and path.stat().st_size > 50_000:
        return path
    u = url_for(w, y, sess)
    if not u:
        return None
    for _ in range(3):
        try:
            r = sess.get(u, headers=HEADERS, timeout=90)
            r.raise_for_status()
            path.write_bytes(r.content)
            return path
        except requests.RequestException:
            time.sleep(5)
    return None


def extract_weekly(path):
    """Devuelve lista de obs semanales {year,month,week, <KEYS>} de un Excel."""
    wb = openpyxl.load_workbook(str(path), data_only=True)
    ws = wb[wb.sheetnames[0]]
    rmap = find_row_map(ws)
    out, last_month = [], None
    for c in range(5, ws.max_column + 1):
        dv = ws.cell(3, c).value
        if dv is None:
            continue
        if isinstance(dv, datetime.datetime):
            last_month = (dv.year, dv.month)
            continue
        if isinstance(dv, str) and "semana" in dv.lower():
            if last_month is None:
                continue
            y, m = last_month
            nm, ny = (m % 12) + 1, y + (1 if m == 12 else 0)
            mwk = re.search(r"\d+", dv)        # 'Semana 5/1' -> 5 (1er número)
            wk = int(mwk.group()) if mwk else 1
            # La fila 4 trae la FECHA REAL del corte semanal del BCB
            dreal = ws.cell(4, c).value
            date_iso = dreal.strftime("%Y-%m-%d") if isinstance(dreal, datetime.datetime) else None
            rec = {"year": ny, "month": nm, "week": wk, "date": date_iso}
            any_val = False
            for k, r in rmap.items():
                v = ws.cell(r, c).value
                if isinstance(v, (int, float)):
                    rec[k] = round(float(v), 2)
                    any_val = True
                else:
                    rec[k] = None
            if any_val:
                out.append(rec)
    return out


def main():
    # Rango de semanas a recorrer (argumentos: y1 w1 y2 w2 ...), default 2026 S1..S24
    targets = []
    if len(sys.argv) > 1:
        # pares "year:wstart-wend"
        for tok in sys.argv[1:]:
            y, rng = tok.split(":")
            a, b = rng.split("-")
            targets += [(int(y), w) for w in range(int(a), int(b) + 1)]
    else:
        targets = [(2026, w) for w in range(1, 25)]

    sess = requests.Session()
    merged = {}  # (y,m,wk) -> rec ; archivos posteriores sobrescriben (revisiones)
    got_files = 0
    for (y, w) in targets:
        p = download(w, y, sess)
        if not p:
            print(f"  S{w}/{y}: no disponible")
            continue
        got_files += 1
        try:
            recs = extract_weekly(p)
        except Exception as e:
            print(f"  S{w}/{y}: error parse: {e}")
            continue
        for rec in recs:
            merged[(rec["year"], rec["month"], rec["week"])] = rec
        wk_lbls = ",".join(f"{r['month']:02d}-S{r['week']}" for r in recs)
        print(f"  S{w}/{y}: {len(recs)} semanas [{wk_lbls}]")

    serie = list(merged.values())
    for r in serie:
        r["label"] = f"{r['year']}-{r['month']:02d}-S{r['week']}"
    # Ordenar por fecha real del corte (fallback a año/mes/semana)
    serie.sort(key=lambda r: (r.get("date") or f"{r['year']}-{r['month']:02d}-{r['week']:02d}"))
    out_path = Path(__file__).parent / "data" / "reservas_semanal.json"
    out_path.write_text(json.dumps(serie, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nArchivos OK: {got_files} | Semanas unicas: {len(serie)}")
    print((f"Rango: {serie[0]['label']} -> {serie[-1]['label']}") if serie else "sin datos")
    print(f"-> {out_path}")


if __name__ == "__main__":
    main()

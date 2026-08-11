"""
Construye el dataset final de la publicación a partir de los extractos:
  - ancla mensual 30-nov-2025
  - serie semanal 5-dic-2025 .. 1-jun-2026 (oficial BCB)
  - punto ESTIMADO 15-jun-2026 (impacto del pago de oro pignorado, NP10/2026)

Y escribe los eventos (callouts) en events.json.
Fuente de verdad: data/reservas_semanal.json + data/anclas_mensuales_2025.json
"""
import json
from pathlib import Path

D = Path(__file__).parent / "data"
PIGNORADO_MM = 586.0          # NP10/2026: caída de reservas de oro por la entrega
FECHA_PIGNORADO = "2026-06-15"


def pt(date, label, tipo, src):
    return {"date": date, "label": label, "tipo": tipo,
            "oro": src["oro"], "divisas": src["divisas"], "deg": src["deg"],
            "fmi": src["fmi"], "rin": src["rin"]}


def main():
    weekly = json.loads((D / "reservas_semanal.json").read_text(encoding="utf-8"))
    anchors = json.loads((D / "anclas_mensuales_2025.json").read_text(encoding="utf-8"))
    nov = next(a for a in anchors if a["date"] == "2025-11-30")

    serie = [pt("2025-11-30", "Nov 2025", "mensual", nov)]
    for w in weekly:
        serie.append(pt(w["date"], w["label"], "semanal", w))

    # Punto estimado: entrega del oro pignorado (-586 MM al oro), resto constante
    last = serie[-1]
    oro_est = round(last["oro"] - PIGNORADO_MM, 2)
    rin_est = round(oro_est + last["divisas"] + last["deg"] + last["fmi"], 2)
    serie.append({
        "date": FECHA_PIGNORADO, "label": "15-jun (est.)", "tipo": "estimado",
        "oro": oro_est, "divisas": last["divisas"], "deg": last["deg"],
        "fmi": last["fmi"], "rin": rin_est,
    })

    out = {"meta": {
        "titulo": "Reservas Internacionales del BCB — evolución semanal",
        "fuente": "Banco Central de Bolivia — Estadísticas Semanales · NP10/2026",
        "unidad": "Millones de USD",
        "nota": ("Punto inicial (nov-2025) es dato mensual; tramo semanal con corte real del BCB. "
                 "El último punto (15-jun-2026) es ESTIMACIÓN POPULI del impacto de la entrega de "
                 "4,3 t de oro pignorado (NP10/2026, −USD 586 MM en oro), manteniendo constantes los "
                 "demás componentes respecto al 1-jun-2026; el BCB aún no publica esa semana. "
                 "Oro valuado a precio de mercado."),
        "primer_dato": serie[0]["date"], "ultimo_dato": serie[-1]["date"],
        "n_puntos": len(serie)},
        "serie": serie}
    (D / "serie_final.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    eventos = [
        {"date": "2025-12-24", "comp": "divisas", "dir": "up",
         "title": "Desembolso CAF", "short": "Desembolso CAF",
         "panels": ["stack", "divisas"],
         "desc": "Ingreso de divisas por desembolso de la CAF."},
        {"date": "2026-03-20", "comp": "rin", "dir": "down",
         "title": "Pago de deuda externa + caída del precio del oro",
         "short": "Deuda externa + precio oro",
         "panels": ["stack", "oro", "divisas"],
         "desc": "Vencimientos de deuda externa (divisas) y desplome de la cotización internacional del oro (>10% en marzo 2026)."},
        {"date": "2026-05-15", "comp": "divisas", "dir": "up",
         "title": "Colocación de bonos soberanos", "short": "Bonos soberanos",
         "panels": ["stack", "divisas"],
         "desc": "Ingreso de divisas por emisión de bonos en mercados internacionales."},
        {"date": "2026-06-15", "comp": "oro", "dir": "down",
         "title": "Entrega de oro pignorado (−USD 586 MM)", "short": "Oro pignorado −586",
         "panels": ["stack", "oro"], "estimated": True,
         "desc": "Pago de la operación de pignoración de 4,3 t de oro (NP10/2026). Punto estimado."},
    ]
    (D / "events.json").write_text(json.dumps(eventos, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"serie_final.json: {len(serie)} puntos ({serie[0]['date']} -> {serie[-1]['date']})")
    print(f"  estimado 15-jun: oro {last['oro']} -> {oro_est} | RIN {last['rin']} -> {rin_est}")
    print(f"events.json: {len(eventos)} eventos")


if __name__ == "__main__":
    main()

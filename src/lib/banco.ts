// Utilidades compartidas por las páginas del Banco (corren en el build).
import manifest from "../manifest.json";

export type Ficha = {
  slug: string; titulo: string; subtitulo?: string; categoria: string; fuente?: string;
  tags?: string[]; fecha?: string; tipo: string; formato?: string; imagen: string; thumb: string;
  datos?: string | null; clave?: string; atlas?: string; modo?: string; anio?: string;
  enlace?: string; grupo?: string; universo?: string; unidad?: string;
  ancho?: number; alto?: number; kb?: number;
};
export type Categoria = { label: string; color: string };

export const SITE = "https://centro-de-estudios-populi.github.io/galeria-populi/";
export const categorias = manifest.categorias as Record<string, Categoria>;
export const graficas = manifest.graficas as Ficha[];
export const meta = (manifest as any).meta as { generado: string; n: number; municipios: number };

/** une base + ruta con exactamente una barra */
export const u = (base: string, p: string) => `${base.replace(/\/$/, "")}/${p.replace(/^\//, "")}`;

/** sin tildes ni mayúsculas: lo que se compara al buscar */
export const norm = (t: string) => (t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

/** el «corte» legible de una lámina: qué censo, qué gestión */
export const modoLabel = (g: Ficha) => {
  if (g.atlas === "censo") return g.modo === "cambio" ? "Cambio 2012–2024" : `Censo ${g.modo}`;
  if (g.atlas === "fiscal") return `Gestión ${g.modo}`;
  if (g.tipo === "mapa_mundial") return "Último dato";
  return "";
};

/** otras versiones del mismo indicador (2024 · 2012 · cambio) */
export const versionesDe = (g: Ficha) =>
  g.atlas && g.clave ? graficas.filter((x) => x.atlas === g.atlas && x.clave === g.clave) : [];

/** el tema de una ficha: lo declarado; en los mapas mundiales el segundo tag
 *  (`["mundo", categoría del atlas, código]`) y en las láminas viejas el cuarto */
export const grupoDe = (g: Ficha) => {
  if (g.grupo) return g.grupo;
  if (g.categoria === "mundo") return g.tags?.[1] ?? "";
  return g.tags && g.tags.length >= 4 ? g.tags[3] : "";
};

/** etiquetas que vale la pena mostrar (las que comparten al menos dos gráficas) */
const conteo = new Map<string, number>();
for (const g of graficas) for (const t of g.tags || []) conteo.set(t, (conteo.get(t) || 0) + 1);
export const tagsVisibles = (g: Ficha) => (g.tags || []).filter((t) => (conteo.get(t) || 0) >= 2);

/** temas por categoría, con su cuenta, ordenados por cuenta */
export function temasPorCategoria() {
  const out: Record<string, { tema: string; n: number }[]> = {};
  const acc = new Map<string, Map<string, number>>();
  for (const g of graficas) {
    const t = grupoDe(g);
    if (!t) continue;
    const m = acc.get(g.categoria) || new Map<string, number>();
    m.set(t, (m.get(t) || 0) + 1);
    acc.set(g.categoria, m);
  }
  for (const [cat, m] of acc) out[cat] = [...m].map(([tema, n]) => ({ tema, n })).sort((a, b) => a.tema.localeCompare(b.tema, "es"));
  return out;
}

/** cortes por categoría (Censo 2024 · Censo 2012 · Cambio · Gestión 2025 …) */
export function cortesPorCategoria() {
  const out: Record<string, { corte: string; n: number }[]> = {};
  const acc = new Map<string, Map<string, number>>();
  for (const g of graficas) {
    const c = modoLabel(g);
    if (!c) continue;
    const m = acc.get(g.categoria) || new Map<string, number>();
    m.set(c, (m.get(c) || 0) + 1);
    acc.set(g.categoria, m);
  }
  const orden = ["Censo 2024", "Censo 2012", "Cambio 2012–2024"];
  for (const [cat, m] of acc)
    out[cat] = [...m].map(([corte, n]) => ({ corte, n }))
      .sort((a, b) => (orden.indexOf(a.corte) + 99) % 99 - (orden.indexOf(b.corte) + 99) % 99 || a.corte.localeCompare(b.corte, "es"));
  return out;
}

/** ficha técnica de la tarjeta */
export const fichaTecnica = (g: Ficha) => (g.ancho && g.alto ? `${g.ancho} × ${g.alto}${g.kb ? ` · ${g.kb} KB` : ""}` : "");

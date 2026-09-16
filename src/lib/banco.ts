// Utilidades compartidas por las páginas del Banco (corren en el build).
import manifest from "../manifest.json";

export type Ficha = {
  slug: string; titulo: string; subtitulo?: string; categoria: string; fuente?: string;
  tags?: string[]; fecha?: string; tipo: string; formato?: string; imagen: string; thumb: string;
  datos?: string | null; clave?: string; atlas?: string; modo?: string; anio?: string;
  enlace?: string; grupo?: string; universo?: string; unidad?: string;
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

/** el «modo» legible de una lámina municipal */
export const modoLabel = (g: Ficha) => {
  if (g.atlas === "censo") return g.modo === "cambio" ? "Cambio 2012–2024" : `Censo ${g.modo}`;
  if (g.atlas === "fiscal") return `Gestión ${g.modo}`;
  return "";
};

/** otras versiones del mismo indicador (2024 · 2012 · cambio) */
export const versionesDe = (g: Ficha) =>
  g.atlas && g.clave ? graficas.filter((x) => x.atlas === g.atlas && x.clave === g.clave) : [];

/** el grupo/tema de una ficha: lo declarado, o el cuarto tag (los mapas viejos) */
export const grupoDe = (g: Ficha) => g.grupo || (g.tags && g.tags.length >= 4 ? g.tags[3] : "");

/** etiquetas que vale la pena mostrar (las que comparten al menos dos gráficas) */
const conteo = new Map<string, number>();
for (const g of graficas) for (const t of g.tags || []) conteo.set(t, (conteo.get(t) || 0) + 1);
export const tagsVisibles = (g: Ficha) => (g.tags || []).filter((t) => (conteo.get(t) || 0) >= 2);

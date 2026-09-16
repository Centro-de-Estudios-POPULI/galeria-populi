import { graficas, meta, SITE } from "../lib/banco";

export function GET() {
  const hoy = meta?.generado || new Date().toISOString().slice(0, 10);
  const urls = [
    `<url><loc>${SITE}</loc><lastmod>${hoy}</lastmod><changefreq>weekly</changefreq></url>`,
    ...graficas.map((g) => `<url><loc>${SITE}g/${g.slug}/</loc><lastmod>${g.fecha || hoy}</lastmod></url>`),
  ];
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join("\n")}\n</urlset>\n`;
  return new Response(xml, { headers: { "Content-Type": "application/xml; charset=utf-8" } });
}

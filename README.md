# Banco de Datos POPULI

Galería buscable de gráficas e indicadores de Bolivia, con **branding POPULI**,
**marca de agua** y **fuente verificada**, listas para descargar y compartir en
redes sociales. Publicada en GitHub Pages.

Es el repositorio central: cada uno de los proyectos POPULI (inflación, actividad
económica, monetario, etc.) aporta su gráfica cruda + metadata, y aquí se aplica
la marca y se publica.

## Cómo funciona

```
chart crudo (ECharts/Plotly/…)  +  metadata.json
                │
                ▼
   scripts/make_card.py   ← aplica logo, título subrayado, fuente, marca de agua
                │
                ▼
   public/graficas/<slug>.png  (1080×1080)  +  public/thumbs/<slug>.png
                │
                ▼
   scripts/build_manifest.py  →  src/manifest.json
                │
                ▼
   Astro  →  galería con buscador + filtros + descarga  →  GitHub Pages
```

El branding vive en **un solo lugar** (`brand.json` + `scripts/`), así todas las
gráficas salen idénticas en estilo aunque vengan de 16 repos distintos.

## Uso local

```bash
# 1. Instalar (una vez)
pip install pillow matplotlib       # matplotlib solo para los charts de ejemplo
npm install

# 2. Regenerar TODAS las tarjetas + el índice
python scripts/build_all.py

# 3. Previsualizar la galería
npm run dev          # http://localhost:4321

# 4. Publicar
npm run build        # genera dist/  (el Action lo hace automático al hacer push)
```

### Agregar una gráfica a mano

1. Deja el chart crudo en `data/charts/mi-grafica.png`
2. Crea `data/charts/mi-grafica.json`:
   ```json
   {
     "slug": "mi-grafica",
     "chart": "mi-grafica.png",
     "title": "Título que aparece en grande con subrayado",
     "subtitle": "Aclaración opcional",
     "category": "Inflación",
     "source": "INE Bolivia — …",
     "date": "2026-05",
     "tags": ["inflación", "ipc"],
     "project": "populi-inflacion"
   }
   ```
3. `python scripts/build_all.py` y listo.

### Agregar desde otro repo (automático)

Copia `templates/aportar-a-galeria.yml` a `.github/workflows/` del repo fuente,
configura el secret `GALERIA_TOKEN` y ajusta la metadata. Cada vez que ese repo
actualice datos, empuja su gráfica aquí y se republica sola.

## Estructura

| Ruta | Qué es |
|---|---|
| `brand.json` | Paleta, tipografías y textos de marca |
| `assets/fonts/` | Tipografías empaquetadas (Playfair, Inter, IBM Plex Mono) |
| `scripts/make_card.py` | Generador de la tarjeta branded 1080×1080 |
| `scripts/render_chart.py` | Charts de ejemplo (matplotlib) — reemplazable |
| `scripts/build_all.py` | Rebrandea todo + reconstruye el índice |
| `data/charts/` | Charts crudos + metadata (lo que aportan los repos) |
| `public/graficas/` | PNGs finales 1080×1080 |
| `src/pages/index.astro` | La galería (buscador, filtros, descarga, lightbox) |
| `.github/workflows/deploy.yml` | Build + deploy a GitHub Pages |

## Branding

- **Wordmark**: `P` (Playfair Display bold, rojo `#C71E1D`) + `opuli` (italic)
- **Acento**: subrayado rojo bajo el título
- **Tipos**: Playfair Display · Inter · IBM Plex Mono
- **Formato**: 1080×1080 (feed Instagram/Facebook/LinkedIn)

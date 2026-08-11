# `viz/recetas/` — guías de figuras de publicación

Una **receta** es un *estilo* de gráfico complejo documentado de punta a punta:
un caso real, su código de autoría, sus datos y una guía para replicarlo.

Se diferencia de `viz/charts/`:

| | `viz/charts/` | `viz/recetas/` |
|---|---|---|
| Qué es | un **tipo** reusable (función) | una **guía** de un estilo + caso de referencia |
| Cómo se usa | `publicar(tipo="areas", …)` o `import` | se lee el README y se copia/adapta el script |
| Cuándo | gráficos templables de 1 panel | **figuras compuestas** (multi-panel, layout a mano) |

Las recetas existen porque no todo gráfico cabe en un `publicar()` de una línea:
las **figuras de publicación** (varios paneles, anotaciones de eventos colocadas
a mano, escalas distintas por panel) necesitan código de composición propio. La
receta codifica las decisiones de diseño para que el siguiente sea más rápido.

## Recetas

| Receta | Estilo | Caso de referencia |
|---|---|---|
| [`series-eventos/`](series-eventos/) | Serie temporal económica anotada con hitos (bandas + callouts), multi-panel | Reservas del BCB y el oro pignorado |

## Crear una receta nueva

1. Resuelve primero el gráfico como caso real (datos + figura) hasta que estés conforme.
2. Si reaprovecha estilo, extrae los helpers genéricos a `viz/charts/` (no dejes
   color/fuente hardcodeados: todo sale de `populi_style.py`).
3. Crea `viz/recetas/<estilo>/` con `figura.py`, `data/`, `output/` y un
   `README.md` que explique **anatomía, contrato de datos y cómo replicar**.
4. Añádela a la tabla de arriba.

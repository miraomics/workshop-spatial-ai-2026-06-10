# Visual design language

The figures share one look so they read as a set. The machine-readable version
of everything here is **`config/style.json`** — the `src/` toolkit loads that
file, and the prompts point your agent at it instead of repeating hex codes. If
you change a color, change it there once.

## Canvas
- **Black background.** Tissue is sparse; black makes faint immune cells pop.
- **Cells are filled segmentation polygons**, not dots — you see real cell shape
  and packing, which is the whole point of imaging-based spatial data.
- **1 pixel per micron**, so distances on screen are distances in tissue.
- Coordinates are **absolute slide microns**. Before drawing, subtract the
  render box's min corner; never build a full-slide-sized canvas for a crop.

## Two ways to color a cell
**1. Continuous (Figure 1) — "where is the tumor, where is the immune system".**
- Non-immune cells: **red**, brightness held constant, **saturation = malignancy
  probability** (white = benign → saturated red = malignant).
- Immune cells: a **green→blue** ramp where hue is set by *how related the cell
  types are in the Cell Ontology* (1-D MDS on shortest-path distance). Lymphoid
  lands green, myeloid lands blue, cousins sit next to each other. This turns a
  60-way categorical into something the eye can actually read.

**2. Categorical (Figures 2–3) — "which immune cells, exactly".**
A fixed swatch per lineage. The constants live in `config/style.json`; the
recurring ones:
| lineage | swatch |
|---|---|
| CD8 T | gold |
| CD4 T | cyan |
| B cell | pink |
| Plasma | magenta |
| Dendritic | green |
| NK | blue |
| Macrophage | tan |
| Malignant (p ≥ 0.5) | red |

When a cell could match two sets (a cytotoxic CD8 cell is also "a T cell"), the
**`draw_order` in `config/cell_types.json`** decides who wins — paint general
first, specific last.

## Motif rings
Spatial motifs are marked with **outline rings**, never fills, so the cells
underneath stay visible: **magenta = triad**, **orange = tetrad**. Rings are
greedy-thinned for display so they don't pile up; that's cosmetic and never
changes the counts.

## Why split style, cell types, and motifs into separate config files
So a prompt can stay in plain language — "color the cells with the workshop
palette, find triads using the radius in the motif config" — instead of carrying
a wall of hex codes and ontology terms. The biology (what a lineage *is*, what a
triad *is*) lives in `config/` and in the cited paper, not buried in a prompt.

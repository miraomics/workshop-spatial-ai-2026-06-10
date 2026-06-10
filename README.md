# Spatial-AI workshop — cervical triads & TLS (2026-06-10)

Hands-on workshop: drive a spatial-transcriptomics analysis **by prompting an AI
agent**, reproducing the key figures from the Mira Omics case study
[*Cervical triads & tertiary lymphoid structures*](https://miraomics.bio/case-studies/cervical-triads-tls/)
on a small, self-contained crop of the 10x Xenium WTA cervical-cancer slide.

The crop is **~1/35 of the slide** (26,047 cells, 1500 µm square) centered on the
slide's most mature **tertiary lymphoid structure (TLS)**, but carries every
native Xenium layer at full resolution so it downloads in seconds.

## Layout
```
prompts/workshop_prompts.md   the whole workshop as one script — the prompts you speak, in order
config/                       single source of truth, referenced by the prompts
  style.json                    palette + render conventions (companion to DESIGN.md)
  cell_types.json               obs columns + lineage -> Cell Ontology mapping
  motifs.json                   triad/tetrad params + paper citation + TLS score
DESIGN.md                     the visual design language, in plain English
data/cervical_tls_workshop/   the crop (h5ad, segmentation, transcripts, morphology image)
assets/cell_ontology_graph.pkl   Cell Ontology graph used for immune coloring / lineages
src/                          the workshop toolkit the notebook imports
  config.py                     loads config/*.json
  workshop_lib.py               vetted mechanics (render, MDS, triad-finding, legend rollup)
workshop_figures.ipynb        the figures, one cell per figure (run this)
figures/                      figure PNGs written by the notebook
```

The biology (what a lineage is, what a triad is) and the styling live in
`config/` and the cited paper — **not** baked into the prompts. That's what keeps
the prompts short and in plain language.

## The crop in one paragraph
`cervical_tls_crop.h5ad` — 26,047 cells × 18,028 genes, raw counts in `X`.
`obs` already carries the MiraTyper cell-type calls
(`cell_type_cdiam_miratyper_v1_constrained_alpha0100`, major rollups, CL ids),
`p_malignant` / `malignant_class`, a convenience `lineage` column
(CD4_T / CD8_T / DC / NK_cell / B_cell / macrophage / malignant / …), and
`is_triad` / `is_anchor` / `region`. All coordinates (`obs.x_centroid/y_centroid`,
`obsm['spatial']`, boundary vertices, transcript locations) are **absolute slide
microns** — an analysis written for the full slide runs unchanged here. The crop
origin (L0 pixel 0,0 of the morphology image) is slide µm (3807.86, 3091.55);
`PIXEL_UM = 0.21249222`. See `data/cervical_tls_workshop/README.md` for full
provenance.

## Inspecting the crop with DuckDB (optional)
To browse the h5ad's cell metadata without loading the expression matrix, use
DuckDB with the [`anndata` community extension](https://duckdb.org/community_extensions/extensions/anndata)
([source](https://github.com/honicky/anndata-duckdb-extension)).

Install the DuckDB CLI (macOS):
```bash
brew install duckdb        # or see https://duckdb.org/docs/installation/
```

Then, in `duckdb`, install and load the extension once (needs network):
```sql
INSTALL anndata FROM community;
LOAD anndata;
```

Query the crop's `obs` directly — this reads only the metadata, not `X`:
```sql
-- malignant vs non-malignant
SELECT malignant_class, count(*) AS n
FROM anndata_scan_obs('data/cervical_tls_workshop/cervical_tls_crop.h5ad')
GROUP BY 1;

-- or attach it and explore
ATTACH 'data/cervical_tls_workshop/cervical_tls_crop.h5ad' AS crop (TYPE ANNDATA);
SELECT * FROM crop.info;
SHOW all tables;
```
Other scan functions: `anndata_scan_var` (genes), `anndata_scan_obsm`
(embeddings / `spatial`), `anndata_scan_x` (expression). Read-only.

## Environment
Self-contained `uv` project — dependencies pinned in `uv.lock`, Python 3.11:
```bash
uv sync     # creates ./.venv (scanpy, matplotlib, nbconvert, ipykernel, …)
```
No Jupyter server needed. A kernel named **"Python (workshop .venv)"** is
registered for VS Code.

## The notebook
`workshop_figures.ipynb` — run the **setup cell** once (loads config + ontology +
the Step-0 labels), then run one figure cell at a time. Each figure is produced by
a single one-shot prompt → one cell.

- **View / run interactively:** open the notebook in **VS Code** and pick the
  *Python (workshop .venv)* kernel (or the `./.venv` interpreter).
- **Run from the command line** (execute every cell, write results back in place):
  ```bash
  uv run jupyter nbconvert --to notebook --execute --inplace workshop_figures.ipynb
  ```
  Figures are also written to `figures/` as PNGs as a side effect.

## Data distribution
The large files (`*.h5ad`, `*.parquet`, `*.ome.tif`) are git-ignored and
distributed via Hugging Face (CC BY 4.0):
**[honicky/cervical-tls-workshop-crop](https://huggingface.co/datasets/honicky/cervical-tls-workshop-crop)**.
Fetch them into place with:
```bash
hf download honicky/cervical-tls-workshop-crop --repo-type dataset \
    --local-dir data/cervical_tls_workshop
```

## Provenance
Crop + original full-slide analysis:
an internal Mira analysis repo (`notebooks/atera_xenium_wta{,_workshop_subset}`). The `src/` toolkit is
subset-adapted from that project's `render_combined_mask.py`, `render_zoom_panels.py`,
and `render_tls_vs_immune_zooms.py`.

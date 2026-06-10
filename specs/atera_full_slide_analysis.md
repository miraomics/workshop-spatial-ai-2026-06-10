# Spec — run the triads & TLS analysis on the full Atera WTA reference slides

## Goal

Take the workshop pipeline (Step 0 labels → Figure 1/2/3 → report), which the repo
runs on a 1500 µm **crop**, and run it on the **full-size Atera WTA reference
slides** it was derived from. Reuse `config/`, `src/workshop_lib.py`, and the
notebook unchanged; the only per-slide knobs are the data path and the tissue
prior. This lets a participant go from the toy crop to the whole slide (and a
second organ) without re-deriving any styling or biology.

## Reference slides

The "Atera reference slides" are 10x Genomics' two public **Atera WTA Preview**
FFPE datasets (pre-commercial whole-transcriptome assay, **18,028 genes**, files
in **Xenium Onboard Analysis v4** format, **CC BY 4.0**):

| slide | 10x dataset page | cells | organ / tissue prior |
|---|---|---|---|
| Cervical cancer | https://www.10xgenomics.com/datasets/atera-wta-ffpe-human-cervical-cancer | 717,576 | cervix → `UBERON:0000002` |
| Breast cancer | https://www.10xgenomics.com/datasets/atera-wta-ffpe-human-breast-cancer | see page | breast → `UBERON:0000310` (verify against MiraTyper's supported tissues) |

The workshop crop is a 3.6% window of the **cervical** slide (its 717,576-cell
count matches the repo's `data/cervical_tls_workshop/README.md`), so the cervical
full-slide run is the natural validation case.

> Note the breast UBERON id should be confirmed against the tissue list MiraTyper
> actually supports (the miratyper-inference workflow / its tissue-prior table);
> use the term for the slide's organ, exactly as Step 0 uses `UBERON:0000002`
> for cervix.

## Downloading the data

Per slide:

1. Open the dataset page above and go to its **Download** section. Accept the
   **CC BY 4.0** terms; 10x then exposes the file list (served from
   `cf.10xgenomics.com`) with a `curl` command per file or a bundle.
2. Download the Xenium **`outs`** bundle (or the individual files). The pipeline
   needs:
   - `cell_feature_matrix.h5` (or `.zarr`) — cell × gene **raw counts**, gene
     symbols in `var` (the `all`/WTA panel, 18,028 genes).
   - `cells.parquet` — per-cell metadata incl. `x_centroid`, `y_centroid`.
   - `cell_boundaries.parquet` — segmentation polygons (`cell_id`, `vertex_x`,
     `vertex_y`), absolute slide microns.
   - `transcripts.parquet` — optional; only if you want molecule-level overlays
     (the figures read gene positivity from `X`, not transcripts).
   - `morphology_focus*.ome.tif` — optional; not used by Figures 1–3.
3. Place them under a per-slide directory, mirroring the crop layout:
   ```
   data/atera_cervical/{cell_feature_matrix.h5, cells.parquet, cell_boundaries.parquet, ...}
   data/atera_breast/{...}
   ```
   These are large (the cervical `outs` is tens of GB vs the crop's ~660 MB for
   3.6% of the slide) — keep them git-ignored like `data/cervical_tls_workshop/*`.

## Input preparation (outs → workshop h5ad)

The workshop toolkit expects an `.h5ad` whose `obs` carries `x_centroid` /
`y_centroid` and whose `X` is raw counts with gene symbols in `var`, plus the
matching `cell_boundaries.parquet`. Build it per slide:

- Load `cell_feature_matrix.h5` into an AnnData (`scanpy.read_10x_h5` or
  `spatialdata_io.xenium`, which the 10x page lists as tested), then merge
  `cells.parquet` into `obs` and set `obsm['spatial']` = the centroid columns.
- Confirm gene symbols (e.g. `CXCL13`, `MS4A1`, `LAMP3`, `CD8A`) are present in
  `var_names` — the immune ontology coloring and the TLS markers depend on them.
- Save as `data/atera_<slide>/<slide>.h5ad`.

This is the one genuinely new code module the spec introduces (see Testing).

## Pipeline (per slide)

Run the existing workshop steps; the prompts in `prompts/workshop_prompts.md`
apply almost verbatim — only the data path and tissue prior change.

1. **Step 0 — labels.** MiraTyper `--panel all --run-malignant` with the slide's
   tissue prior (`UBERON:0000002` cervix / the breast term), alpha `0.1` (add
   `1 10` if you want the stronger-prior columns). Write
   `results/atera_<slide>/labels_miratyper.parquet`. On ~700K cells this is well
   beyond the crop's ~20 s — budget accordingly and run on the full panel once.
2. **Figure 1** — malignancy + immune-ontology mask, `config/style.json` palette,
   legend rolled up via `immune_legend_groups`.
3. **Figure 2** — triads (CD8 + CD4 + DC within the `config/motifs.json` radius),
   magenta/orange rings. On the full cervical slide expect a far larger anchor
   count than the crop's ~16 (the published case study reports ~406 slide-wide).
4. **Figure 3** — TLS: the Fig-3 prompt already **searches** for the
   max-TLS-score core, so it generalizes directly; on the full slide it will find
   the strongest follicle on the whole section (the crop was built around exactly
   this aggregate).
5. **Report** — `reports/atera_<slide>_results.md`, figures embedded inline.

Drive it either by speaking the existing prompts (pointing the data path at the
slide) or by parameterizing the notebook setup cell with a `SLIDE` variable that
selects the data dir + tissue prior.

## Scaling & compute

Full slides are 170K–717K cells, not 26K. Implications, all handled by reusing
the existing helpers but with care:

- **Rendering** at 1 px/µm produces a slide-sized image (many thousands of px per
  side). `wl.render_polygons` already groups by `cell_id`; expect minutes and
  high memory. Render the whole slide once; for iteration, crop to a sub-window
  (Figure 3 already does, via its 700 µm window).
- **h5ad reads** should stay backed (`sc.read_h5ad(..., backed="r")`) and gene
  columns pulled one at a time, per the repo's sparse-matrix conventions — never
  densify the full matrix.
- **MiraTyper** runtime scales with cell count; run once and cache the parquet.

No new rendering code is required — the toolkit is already streaming/polygon-based.

## Outputs layout

```
data/atera_<slide>/        downloaded outs + built <slide>.h5ad
results/atera_<slide>/     labels_miratyper.parquet, tls/triad tables
figures/atera_<slide>/     fig1/2/3 PNGs
reports/atera_<slide>_results.md
```

## Testing

Per repo convention, the new code module (outs → h5ad builder + per-slide driver)
needs unit tests:

- **Builder:** on a tiny synthetic `outs` (or a down-sampled slice), assert the
  produced AnnData has raw-count `X`, gene symbols in `var_names`, `obs.x/y_centroid`,
  `obsm['spatial']`, and that `cell_id`s align with `cell_boundaries.parquet`.
- **Tissue-prior selection:** assert the per-slide config maps cervical →
  `UBERON:0000002` and breast → its term, and that an unknown slide errors loudly.
- **Pipeline smoke test:** run Step 0 + Figures 1–3 on a small crop of the full
  slide (e.g. reuse the existing 1500 µm crop as the cervical fixture) and assert
  each figure file is written and the triad/TLS counts are finite and non-zero.
- Reuse/extend any tests already covering `src/workshop_lib.py`.

## Validation

The cervical full-slide run is checkable against the **published case study**
(linked from the repo README:
https://miraomics.bio/case-studies/cervical-triads-tls/): 717,576 cells, a broad
immune band crossing the malignant lobules (Fig 1), ~406 triad anchors (Fig 2),
and the focal TLS the workshop crop is centered on (Fig 3). Matching those is the
acceptance bar for "the analysis reproduces at full-slide scale." The breast slide
has no published reference here, so treat it as exploratory.

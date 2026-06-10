# Cervical triads & TLS — workshop prompts

The whole workshop as one script. You **speak each prompt** (e.g. via WisprFlow);
the agent runs it against the crop and, for the figures, appends a cell to
`workshop_figures.ipynb` and executes it, leaving the result in the notebook for
you to review in VS Code.

How it stays simple: the biology and styling live in `config/` and the cited
paper, **not** in the prompts. Colors → `config/style.json`; cell vocabulary →
`config/cell_types.json`; motif/TLS definitions → `config/motifs.json`
(`DESIGN.md` explains the look in plain English). So a prompt can say "use the
workshop palette" instead of reciting hex codes.

Run them in order. Each figure prompt is a self-contained **one-shot**.

---

## Step 0 — Get oriented & label the cells

Everything downstream is colored by cell type and malignancy, so settle those
first. Two messages.

**You:**
> I'm working in this repo on a small crop of a 10x Atera cervical cancer slide.
> `data/cervical_tls_workshop/cervical_tls_crop.h5ad` Load it and tell me what's
> in obs. Focus on any existing cell type or malignancy columns and what the
> spatial coordinates look like. Don't make any changes.

*Expect: 26,047 cells × 18,028 genes, MiraTyper cell-type + `p_malignant` columns
already present, coordinates in absolute slide microns (~1500 µm square).*

**You:**
> Let's regenerate the labels using the MiraTyper inference workflow to run cell
> typing plus malignant classification. Use alpha values 0.1 and 10 and a cervix
> tissue prior. Write the predictions to a Parquet file in the results directory.
> Walk me through the command before you run it.

*The agent fills in the rest from context: `all` panel (WTA is whole-transcriptome),
tissue id `UBERON:0000002`, output `results/labels_miratyper.parquet`, and it
pauses to explain the command before running. ~20 s. If you can't run MiraTyper,
tell it to use the pre-baked `obs` columns and move on. The figures use the
alpha-0.1 call (`..._constrained_alpha0010`).*

---

## Figure 1 — where is the tumor, where is the immune system

**You:**
> Using the cell-type column from Step 0, split the cells into immune (leukocyte
> or any ontology descendant — see `config/cell_types.json`) and everything else.
> Draw every cell as a filled segmentation polygon on a black canvas at one pixel
> per micron, like the other figures. Color the non-immune cells by the malignancy
> ramp in `config/style.json` — red, with saturation = `p_malignant`. Color the
> immune cells by the green-to-blue ontology ramp in `config/style.json`, assigning
> each immune type a hue with 1-D MDS on cell-ontology shortest-path distance over
> the immune types present. Add a legend on the right of the same image: the
> malignancy ramp, then the immune types rolled up to the major lineages in
> `config/cell_types.json` (so sparse lineages like CD8 still show). Put it in the
> notebook.

*Expect ~6,500 immune (13 legend lineages, CD8 ≈ 60) / ~19,500 non-immune with a
malignancy score — a teal immune island threading between red malignant lobules.*

---

## Figure 2 — immune triads (CD8 + CD4 + dendritic cell)

Triad definition is recorded with citation in `config/motifs.json` →
`triad.source` (Espinosa-Carrasco et al., *Cancer Cell* 2024); the tetrad is our
own extension.

**You:**
> A CD8 T cell is a triad anchor if and only if at least one CD4 T cell and at
> least one dendritic cell lie within 20 µm of its centroid. Map those three cell
> types to lineages in `config/cell_types.json`. Find every anchor in the crop.
> Draw the cells filled as polygons on a black canvas, like Figure 1, but this
> time color with the categorical palette in `config/style.json` — CD8, CD4,
> dendritic, NK, macrophage, malignant. Mark the triads: draw a magenta outline
> ring on each anchor, thinned greedily so they don't overlap (the thinning
> distance is in `config/motifs.json`). Do the same for a tetrad — a triad that
> additionally has a macrophage nearby — and flag those with an orange ring. Add
> a legend, and put it in the notebook.

*Expect ~16 anchors, ~11 rings after thinning, ~7 tetrads, clustered in the immune
regions rather than the red malignant sheets.*

---

## Figure 3 — anatomy of one tertiary lymphoid structure

Unlike a fixed location, this **searches** for the best TLS. Score, core radius,
and markers live in `config/motifs.json` → `tls_score`.

**You:**
> Look at the TLS score in `config/motifs.json`. Find the centroid of a 100-micron
> core that corresponds to the highest TLS score on the crop. Count B cells, plasma
> cells, T cells, dendritic cells, and the marker-positive cells — CXCL13⁺,
> CCL19⁺/CCL21⁺ (the T-zone chemokines), and LAMP3⁺ dendritic cells — and compute
> the TLS score from the formula there. Report the numbers. Then create a 700 µm
> window around that centroid: draw the cells as filled polygons on a black canvas,
> using the categorical palette in `config/style.json` — this time include B cells
> in pink and plasma cells in magenta so the follicle stands out, plus T, DC, NK,
> macrophage, and malignant colors. Overlay the same triad/tetrad rings from
> Figure 2, put those core counts and the TLS score in the title, add a legend, and
> put it in the notebook.

*Expect the search to land at ~(4320, 3700) µm — within ~70 µm of the crop's known
focal follicle — TLS-score ≈ 125 (B≈52, plasma≈14, T≈258, DC≈20, CXCL13⁺≈106,
CCL19/21⁺≈130, LAMP3⁺DC≈3): a pink B-cell follicle wrapped in a blue T-zone.*

---

## Report — write up the results

Once the figures are built, summarize the run in one markdown file.

**You:**
> OK, please report out these results from the notebook in a markdown file.
> Include the images we've generated inline.

*Writes `reports/workshop_results.md`: the Step-0 label counts and each figure's
numbers pulled from the notebook's cell outputs, with the figure PNGs embedded
inline. Open it in VS Code's markdown preview to see the figures.*

## Spec

> Okay, now I want you to create a spec for doing this entire analysis on all of the Atera reference slides.
> Please put it in a directory called specs. Include how to download reference data. 

---

## Appendix — Figure 1, step-by-step (for teaching)

Build the same Figure 1 in four small messages instead of one, checking each.

**You:**
> Okay, using the crop and cell type column from Step 0, split the cells into
> immune — such as leukocyte or any ontology descendants, and you can look at
> `src/config.py` — versus everything else. How many of each? Just give me
> the numbers.

**You:**
> Now start the picture. Draw every cell as its filled segmentation polygon from
> `data/cervical_tls_workshop/cell_boundaries.parquet`, on the black canvas
> described in `config/style.json` (1 px/µm, subtract the box min-corner). For the
> non-immune cells, color them by the malignancy ramp in that style file: red,
> saturation = `p_malignant`. Show me the result.

**You:**
> Now color the immune cells with the green→blue ontology ramp from
> `config/style.json`: assign each immune type a hue by running 1-D MDS on the
> cell-ontology shortest-path distances between the immune types present, mapped
> onto the 120°→240° hue range. Drop these on top of the same image.

**You:**
> Good. Put a legend on the right of the same image — a 0→1 `P(malignant)` red
> ramp, then the immune types rolled up to the major lineages in
> `config/cell_types.json` (so sparse lineages like CD8 still show), each swatch
> colored by the lineage's most-common subtype. Save it to
> `figures/fig1_malignancy_immune_mask.png`.

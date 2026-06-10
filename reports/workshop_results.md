# Cervical triads & TLS — workshop results

Auto-generated from `workshop_figures.ipynb`. All figures are built on a 1500 µm
crop of the Atera cervical Xenium WTA slide (26,047 cells), using the Step-0
MiraTyper labels at tissue-prior alpha 0.1.

## Data & labels (Step 0)

```
labels: Step-0 regenerated · cell_type_cdiam_miratyper_v1_constrained_alpha0010 (alpha 0.1)
26,047 cells · immune 6,512 · malignant(p>=0.5) 7,333
```

Cell types and malignancy come from MiraTyper (`--panel all --run-malignant`,
cervix tissue prior). ~25% of cells are immune; ~28% are called malignant.

## Figure 1 — malignancy + immune-ontology mask

The orientation map: non-immune cells are red with saturation = P(malignant)
(white→red), immune cells run a green→blue ontology-MDS ramp. A teal immune
island threads between the red malignant lobules.

![Figure 1 — malignancy + immune mask](../figures/fig1_malignancy_immune_mask.png)

```
immune 6,512 (67 fine types -> 13 legend lineages) | CD8 in legend: [('CD8 T cell', 60)]
```

The legend rolls the 67 fine immune types up to 13 major lineages (config
`immune_legend_groups`) so sparse, fragmented lineages like CD8 (~60 cells) still
appear.

## Figure 2 — immune triads (CD8 + CD4 + dendritic cell)

A triad anchor is a CD8 T cell with ≥1 CD4 T cell **and** ≥1 dendritic cell within
20 µm (Espinosa-Carrasco et al., *Cancer Cell* 2024). Tetrads (orange ring)
additionally have a macrophage nearby — our own extension.

![Figure 2 — triads](../figures/fig2_triad_zoom.png)

```
triad anchors in crop: 16  |  rings after thinning: 11  |  tetrads (+macrophage): 7
```

Triads are sparse on this crop because alpha-0.1 typing resolves only ~60 CD8
cells; the rings cluster in the immune regions rather than the malignant sheets.

## Figure 3 — anatomy of one tertiary lymphoid structure

The 100 µm core with the highest TLS-score
(`log1p(B)·log1p(CXCL13⁺)·log1p(CCL19/21⁺)·log1p(LAMP3⁺DC)`) was found by searching
the crop, then rendered in a 700 µm window with B cells pink and plasma magenta.

![Figure 3 — single TLS](../figures/fig3_single_tls.png)

```
highest-TLS-score core centroid: (4319.9, 3700.4) um   TLS-score = 125.4
  core(100um): B=52  plasma=14  T=258  DC=20  CXCL13+=106  CCL19/21+=130  LAMP3+DC=3
```

The search landed within ~70 µm of the crop's known focal follicle — a pink
B-cell core wrapped in a blue T-zone, the textbook B/T zonation of a mature TLS.

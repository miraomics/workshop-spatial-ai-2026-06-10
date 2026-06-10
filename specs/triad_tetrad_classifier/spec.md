# Spec — Triad / Tetrad classifier and training-set generation

Status: **draft for review**. This document is design only. No data has been
downloaded and no code has been written; the data-acquisition and label steps
described here are deferred until the open design questions (§12) are resolved.

Author context: extends the cervical-TLS workshop. The triad/tetrad *definitions*
and spatial parameters already live in `config/motifs.json`; the rule mechanics
already exist in `src/workshop_lib.py` (`find_triad_anchors`, `greedy_thin`). This
spec is about turning that deterministic rule into (a) a multi-slide labeled
training set and (b) a *learned* classifier — and being honest about when a learned
model adds value over the rule and when it does not.

---

## 1. The one decision that shapes everything: rule vs. learned model

A triad is currently defined by a **deterministic geometric rule**: a CD8 T cell
is an anchor iff ≥1 CD4 T cell **and** ≥1 dendritic cell lie within 20 µm of its
centroid; a tetrad additionally requires a macrophage within the radius
(`config/motifs.json`). The labels for any classifier are produced by this rule.

This creates a circularity that must be confronted before anything else:

> If the classifier's input features include the neighborhood cell-type
> composition and inter-cell distances, it will simply re-implement the rule and
> score ~100% — a tautology, not a finding.

A learned classifier is only worth building if it predicts something the rule
*cannot read directly*. This spec therefore commits to a primary target where the
rule's defining inputs are **withheld** from the model:

**Primary task — anchor-level expression-signature classifier.** Given a CD8 T
cell, predict whether it is a triad anchor (and, separately, a tetrad anchor)
**from transcriptomic/proteomic features only** — the anchor cell's own expression
and the *molecular* context of its microenvironment — **without** being told the
cell-type identities or distances of its neighbors. The scientific hypothesis,
taken from Espinosa-Carrasco et al. (*Cancer Cell* 2024; CD4 "licenses" CD8 on a
shared DC), is that sitting in a licensing niche leaves a readable molecular
signature on the CD8 cell (activation / IFN-γ program / reduced exhaustion). If
expression predicts triad membership above chance, that is a real, falsifiable
result and a detector that can transfer to data where DC/CD4 typing is unreliable.

The rule-reconstruction model (neighbor cell-type counts within *r*) is retained
**only as a ceiling baseline and a leakage tripwire** (§7), never as a deployed
predictor.

Secondary / extension targets (designed for, not required in v1): region-level
"does this FOV/biopsy contain ≥1 triad" classification (§3); cross-platform
transfer (train on one platform, test on another, §9).

If on review the intended deliverable is actually just "compute the rule on more
slides" (no learning), then this is a **detection pipeline**, not a classifier, and
most of §6–§11 collapses. Resolving that is open question Q1 (§12).

---

## 2. Scope and the single-cell vs. spatial requirement

Triads/tetrads are **spatial** objects: the label is a function of cell positions.
Dissociated single-cell RNA-seq has no coordinates and therefore **cannot carry
triad labels**. The user's "single-cell or spatial" framing is reconciled as:

- **Label-bearing data (required): single-cell-resolution *spatial* assays with
  segmentation and per-cell x/y centroids** — the imaging/probe-based platforms
  emphasized in the request: 10x Xenium, NanoString/Bruker CosMx, Vizgen MERFISH,
  and (protein) CODEX / PhenoCycler / IMC.
- **Auxiliary data (optional): dissociated scRNA-seq** — used only as a cell-typing
  reference and for expression-signature pretraining, never as triad-labeled
  examples.

In scope: human tumor and lymphoid tissue (where these niches occur), cervical
cancer prioritized for domain match. Out of scope for v1: sequencing-based
spot-level spatial (Visium / Stereo-seq) — spots aggregate multiple cells, so a
single spot cannot be a CD8 anchor. Visium HD (8 µm bins) is borderline and
deferred.

---

## 3. Prediction targets and unit of analysis

| Target | Unit | Positive class | Notes |
|---|---|---|---|
| **Triad anchor** (primary) | one CD8 T cell | CD8 with ≥1 CD4 **and** ≥1 DC within *r* | binary |
| **Tetrad anchor** (primary) | one CD8 T cell | triad anchor **and** ≥1 macrophage within *r* | binary; nested in triad |
| **Region has-triad** (secondary) | FOV / tile / biopsy | region contains ≥1 triad anchor | multiple-instance framing |

Triad and tetrad are modeled as **two heads / two labels**, not one 3-way class,
because tetrad ⊂ triad. A natural ordinal/hierarchical formulation (none → triad →
tetrad) is an option (Q4).

The unit for the primary task is the **CD8 cell** (the anchor candidate), so the
candidate pool is *all CD8 T cells*, not all cells. This matters for negatives (§7)
and base rates (triads are rare — 16 anchors in the workshop crop).

---

## 4. Label generation pipeline (programmatic / weak supervision)

The rule is the labeler. One module computes labels identically on every slide so
labels are reproducible and platform-agnostic.

1. **Input per slide**: a per-cell table with `cell_id`, `x`, `y` (microns), and a
   harmonized cell-type call (§5). Coordinates must be in microns; record and
   apply any pixel→micron scale per platform (Q3).
2. **Resolve the four lineages** (CD8 T, CD4 T, dendritic, macrophage) to each
   dataset's label vocabulary via the Cell-Ontology mapping already used in the
   workshop (`config/cell_types.json` lineages + `assets/cell_ontology_graph.pkl`
   descendants). Generalize `lineage_set` to each dataset's ontology.
3. **Apply the geometric rule** (reuse/generalize `find_triad_anchors`): for each
   CD8 cell, KD-tree query CD4 and DC within `radius_um`; tetrad adds macrophage.
   Radius from `config/motifs.json` (default 20 µm).
4. **Emit a label table**: `cell_id, slide_id, is_cd8, is_triad_anchor,
   is_tetrad_anchor, n_cd4_within_r, n_dc_within_r, n_mac_within_r` plus the
   distances to nearest partner of each type (kept for analysis/ceiling baseline,
   **excluded from deployable features**, §7).
5. **Radius sensitivity**: emit labels at a small sweep of radii (e.g. 15/20/30 µm)
   so the classifier's dependence on the arbitrary 20 µm cutoff can be measured.
   The 20 µm is *our* operationalization for Xenium centroids, not a number from
   the paper — treat it as a hyperparameter, not ground truth.

Label noise is dominated by **cell-typing error**, not the geometry. A missed DC
call flips a true triad to negative. This is the single largest validity threat
(§11) and the reason DC marker coverage gates dataset selection (§5, §8).

---

## 5. Cell typing — making the four lineages comparable across datasets

The label depends entirely on CD8 / CD4 / DC / macrophage calls, which arrive in
three inconsistent forms across sources:

- **Provider-annotated** (CosMx NSCLC ships 18 types incl. 4 T-cell subtypes;
  S-BIAD2378 annotates CD8/CD4/Tregs/cDC/pDC/macrophage). Prefer when present.
- **Protein / antibody** (CODEX, IMC): CD8/CD4/CD3/CD68/CD163/CD11c measured
  directly — the cleanest DC and macrophage calls available (§8 Schürch CRC).
- **Compute-it-yourself** (most Xenium bundles ship only unsupervised clusters):
  run a consistent cell-typer. Use **MiraTyper** (already in this repo's workflow)
  with the dataset's panel, mapping to Cell-Ontology names so the lineage
  resolution in §4 works unchanged.

Design requirement: a **harmonization layer** that maps every dataset's labels —
provider, protein, or MiraTyper — onto the four canonical lineages via the ontology
graph, with a per-dataset mapping file checked in for provenance. Disagreement
between provider labels and MiraTyper on overlapping datasets is a useful label-
noise estimate and should be reported, not hidden.

**Dendritic cells are the weak link** in RNA panels (CLEC9A / LAMP3 / CD1C / ITGAX
often partial). Each dataset is gated on confirmed DC-marker presence before it can
contribute *positive* triad labels (§8). Protein datasets are the DC backstop.

---

## 6. Feature design — leakage-controlled views

Features are organized as explicit "views" so the circularity (§1) is testable, not
assumed away. Every view is evaluated; the contrast between them *is* the result.

- **V0 — rule reconstruction (ceiling / tripwire, NOT deployed).** Neighbor
  cell-type counts within *r* (`n_cd4_within_r`, `n_dc_within_r`, `n_mac_within_r`).
  By construction this reproduces the label → expect PR-AUC ≈ 1.0. Its only jobs:
  prove the pipeline wired up correctly, and detect leakage (if a "real" model
  matches V0 on held-out slides, a defining feature leaked in).
- **V1 — anchor expression only (primary).** The CD8 cell's own panel expression
  vector (log-normalized; panel-intersected across datasets, §9). No neighbor info.
  Tests the molecular-signature hypothesis directly.
- **V2 — microenvironment expression (no cell-type labels).** Aggregated neighbor
  expression within *r* (mean / attention-pooled), or GNN message passing on the
  spatial k-NN graph using **expression only as node features** — never neighbor
  cell-type identity or partner distances. Tests whether the niche's molecular
  context predicts triad membership.
- **V3 — hybrid deployable.** V1 + V2 + cell-agnostic local density features (total
  neighbor count, local cell density). Explicitly **excludes** per-lineage
  within-*r* counts and partner distances. This is the model intended for transfer.

Leakage rule (enforced in code and tests, §10): no feature may encode
"count/distance of CD4, DC, or macrophage within any radius." V0 is the *only* view
permitted to violate this, and it is never deployed.

---

## 7. Negatives, class imbalance, and matched controls

Triads are rare and the candidate pool is CD8 cells only, so naïve negative
sampling produces a trivial "always negative" model. Design:

- **Negative pool**: CD8 T cells that are not anchors. Report base rate per slide
  (workshop crop: 60 CD8, 16 triad anchors → ~27% of CD8 are anchors *on this
  enriched crop*; whole slides will be far lower).
- **Hard negatives / matched controls**: CD8 cells adjacent to *exactly one* required
  partner (CD4 xor DC within *r*) — "almost a triad." If the model only separates
  triads from CD8 cells in empty stroma, it learned lymphoid density, not the
  licensing niche. The hard-negative contrast is the meaningful evaluation.
- **Imbalance handling**: class weights / focal loss; evaluate with PR-AUC and
  precision@k, not accuracy or ROC-AUC (which flatter rare-positive problems).
- Tetrad positives are rarer still (7 in the crop) — pool tetrad labels across many
  slides before treating tetrad as a standalone supervised target; otherwise report
  tetrad as rule-derived only and defer learning it (Q4).

---

## 8. Data sources (from the public-repository search)

Confirmed-public unless noted. "DC" column = confidence the panel/assay resolves
dendritic cells (the gating marker). License/access flags matter for redistribution
and for staying within workshop scope (participant-reachable, public web only).

### Tier 1 — primary training substrate (cervical, domain match)

- **Cervical cancer Xenium — BioImage Archive `S-BIAD2378`** (open; FTP/Globus).
  10x Xenium, 430-gene panel (380 Human Immuno-Oncology + 50 custom), ~1.96M cells,
  22 patients (adeno/SCC/adenosquamous). Annotates CD8/CD4/Treg/cDC/pDC/macrophage —
  **all four lineages**, DC included. Paired scRNA-seq reference: ArrayExpress
  `E-MTAB-15983` (open; the OMIX mirrors are controlled — use EBI accessions).
  License CC BY-NC-ND 4.0 (verify per-file). **Likely overlaps the repo's crop** —
  must check patient/section identity to avoid train/test contamination with the
  workshop crop (Q5).

### Tier 2 — tumor-immune / TLS spatial (transfer + DC-clean)

- **Schürch CRC CODEX** (TCIA `10.7937/TCIA.2020.FQN0-0326`; **CC BY 4.0, open**).
  56-protein CODEX, advanced colorectal cancer, ~240k cells, **explicitly
  TLS-stratified**. CD8/CD4/CD3/CD68/CD163/CD11c by antibody → **cleanest DC +
  macrophage calls of any source**. Processed single-cell CSV is small and ML-ready.
  Best protein backstop for DC label quality.
- **HNSCC Xenium — GEO `GSE300147`** (open). Xenium V1, 377-gene multi-tissue+cancer
  + 100 custom (incl. TCR CDR3, HPV), 17 sections, TLS-focused, 4 T subtypes.
  DC coverage partial (377-gene) — verify before using for DC-dependent positives.
- **CosMx NSCLC FFPE 960-plex** (open; vendor click-through). ~800k cells, 8 NSCLC
  samples, ships 18 cell types incl. 4 T subtypes. DC partial. Canonical open CosMx
  tumor-immune benchmark; good cross-platform test set.
- **Vizgen MERSCOPE FFPE Immuno-Oncology release** (free but **registration-gated**).
  MERFISH 500-gene IO panel, 8 tumor types, ~9M cells. Scale + platform diversity;
  DC partial — verify the 500-gene list.

### Tier 3 — lymphoid / controls / breadth (10x Xenium catalog, all CC BY 4.0)

- **Cervical cancer (Xenium Prime 5K)** — ~840k cells, 5,100 genes; deepest panel,
  highest chance all four markers present; cervical domain match.
- **Tonsil** (~2.2M cells) and **lymph node** (~378k cells), Multi-Tissue & Cancer
  377-gene panel — lymphoid → high triad/tetrad density, good positive-rich source
  (verify DC markers in 377-gene panel).
- **Lung cancer, Immuno-Oncology 380-gene panel** — open, frictionless, clean cell
  table; tumor-immune.
- **HuBMAP intestine CODEX** — healthy gut lymphoid follicles; **not cancer** — use
  only as positive control / pretraining, flagged.
- **HTAN** — richest atlas (CODEX/Xenium/CosMx) but **mixed access**: use Level-4
  single-cell tables / IDC imaging (open, CC BY 4.0); raw is dbGaP-controlled
  (phs002371) and out of scope.

### Not usable as training data

- **Triad paper (Espinosa-Carrasco 2024) spatial data — NOT public.** Only mouse
  bulk RNA-seq (`GSE265846`) + ATAC-seq (`GSE265847`) + analysis code
  (github.com/abcwcm/Espinosa-Carrasco2024) are deposited. The human IMC 35-plex
  cell tables that define triads are not released. Take the marker logic and panel
  design from the methods; **re-derive labels ourselves**.
- **CELLxGENE** has no cervical-cancer dataset (confirmed by full API enumeration);
  and being dissociated scRNA-seq it could only be an auxiliary reference anyway.

**Caveats to carry forward**: (a) verify per-dataset DC-marker presence by
downloading the panel gene list *before* trusting positive labels; (b) distinguish
*gated-but-free* (Vizgen, vendor click-throughs) from *truly controlled* (HTAN raw /
dbGaP) — only the latter is out of scope; (c) confirm S-BIAD2378 ≠ the repo crop.

---

## 9. Splits, batch/panel harmonization, and transfer

- **Split by patient/slide, never by cell.** Cells from one slide are spatially and
  technically correlated; a cell-level random split leaks. Group splits at the
  patient level (slide if patient unknown).
- **Held-out platform.** Reserve at least one platform entirely for test (e.g. train
  Xenium+CosMx, test CODEX, or vice-versa) to measure genuine transfer rather than
  panel memorization.
- **Panel intersection.** Expression features (V1/V2) use the **intersection of gene
  panels** across the datasets in a given experiment, or a learned per-panel
  encoder. Mixing a 377-gene and a 5,000-gene panel naïvely is invalid. Protein
  (CODEX) and RNA are different modalities — keep protein experiments separate from
  RNA experiments unless explicitly doing cross-modality transfer.
- **Batch effects** between slides/platforms are a confounder for the
  expression-signature hypothesis: a model can "predict triad" by predicting slide.
  Mitigations: per-slide normalization, batch-aware CV, and reporting performance
  *within* held-out slides.

---

## 10. Modeling approach (staged, simplest first)

1. **Baselines (must run first):** majority-class floor; V0 ceiling; the geometric
   rule itself evaluated as a "predictor" (defines the achievable upper bound when
   cell types are known). Any learned model is judged against these two bookends.
2. **Tabular models on V1/V3:** logistic regression and gradient-boosted trees on
   expression features. Cheap, interpretable, establishes whether a linear/shallow
   expression signature exists. Feature importance answers "which genes signal a
   licensing niche."
3. **Graph models on V2:** a GNN (e.g. GraphSAGE/GAT) over the spatial k-NN graph
   with expression-only node features, anchor-cell node classification. Tests
   whether message-passing over molecular context beats per-cell expression.
4. **Region head (secondary):** multiple-instance learning over tiles for the
   "has-triad" question.

Out-of-fold discipline (repo convention): any predictions written to disk for
downstream visualization/analysis must be **out-of-fold** — each cell scored by a
model that never saw its slide. In-sample scores overstate performance.

---

## 11. Evaluation, confounders, and validity threats

- **Metrics**: PR-AUC (primary, given rarity), precision@k, recall at fixed
  precision, calibration. Report per-slide and pooled. ROC-AUC reported but not
  used for selection.
- **The decisive comparisons**: V1/V3 vs. the majority floor (is there *any* signal)
  and V1/V3 vs. hard negatives (§7) (is it niche signal or just lymphoid density);
  cross-platform test (does it transfer); ablation V1 vs V2 vs V3.
- **Radius robustness**: re-evaluate against labels at 15/20/30 µm (§4) — a model
  that only works at exactly 20 µm has fit an artifact.
- **Confounders / threats, stated up front**:
  - *Circularity / leakage* — the central risk; controlled by the V0 tripwire and
    the leakage rule in §6, enforced by tests (§13).
  - *Cell-typing label noise*, DC especially — quantified via provider-vs-MiraTyper
    disagreement (§5) and protein-vs-RNA on overlapping tissue.
  - *Batch/platform as a shortcut* (§9).
  - *Segmentation differences* across platforms change "within 20 µm" semantics
    (centroid spacing differs by assay/segmentation method) — document per platform.
  - *Class rarity* → unstable tetrad estimates (§7).
  - *Selection bias* — TLS-enriched datasets (Schürch, tonsil) inflate base rates
    vs. whole tumors; report base rates and don't pool blindly.

A legitimate negative result is in scope and worth stating: if expression alone
does **not** beat the floor and hard negatives, the conclusion is "triads are not
recoverable from transcriptome beyond cell-type geometry," which is itself a finding
about the biology and should be reported, not buried.

---

## 12. Open questions / decisions needed before build

- **Q1.** Is the deliverable a *learned classifier* (this spec's framing) or just a
  *multi-slide detection pipeline* applying the rule? Determines whether §6–§11 apply.
- **Q2.** Primary modality: transcriptomic (Xenium/CosMx/MERFISH, larger but DC-noisy)
  or protein (CODEX/IMC, DC-clean but small and different modality)? Recommend RNA
  primary + CODEX as DC-quality control. Confirm.
- **Q3.** Coordinate units/scale per platform — confirm micron conversion for each
  source (Xenium native µm; CosMx/MERFISH/CODEX vary).
- **Q4.** Triad vs tetrad as two heads, a 3-way ordinal, or tetrad deferred until
  enough positives are pooled?
- **Q5.** Confirm S-BIAD2378 does not overlap the repo's workshop crop (train/test
  contamination); if it does, hold those sections out.
- **Q6.** Compute budget / where labeling + training runs (local vs EC2 GPU for the
  GNN). Multi-million-cell datasets need streaming (no densifying sparse matrices,
  per repo rules).
- **Q7.** Redistribution: which datasets may be cached in this repo vs. fetched by
  script at run time (licenses differ — CC BY 4.0 vs CC BY-NC-ND vs vendor RUO).

---

## 13. Module breakdown and unit-testing plan

Each module is independently testable; tests are part of the module (repo rule).
Tests use **tiny synthetic fixtures with known geometry**, not real downloads, so
they run fast and deterministically.

- **`data_acquisition`** — per-dataset fetch + manifest (URLs, license, checksum,
  panel file). *Tests*: manifest schema validation; checksum verification on a
  fixture; license field present and recognized. Network fetches are mocked.
- **`celltype_harmonization`** — map provider/protein/MiraTyper labels → 4 canonical
  lineages via the ontology graph. *Tests*: a synthetic ontology where known
  descendants must resolve (CD8 subtype → "CD8 T cell"); unmapped labels raise/flag;
  the `"T cell other"` canonical-naming trap (no parens) is asserted; DC-marker-
  absent dataset is flagged ineligible for positive labels.
- **`label_generator`** — the geometric rule (generalized `find_triad_anchors`).
  *Tests*: hand-placed cells where the triad/tetrad answer is known by construction
  (a CD8 with CD4+DC at 19 µm = anchor; at 21 µm = not; tetrad iff macrophage in
  range); radius sweep monotonicity; reproduces `workshop_lib.find_triad_anchors` on
  the crop (regression: 16 anchors / 7 tetrads at 20 µm); coordinate-unit scaling.
- **`feature_extractor`** — builds V0–V3. *Tests*: **leakage test** — V1/V2/V3 must
  contain no per-lineage within-*r* count or partner-distance column (asserted by
  schema); V0 *does* (positive control); aggregation correctness on a fixture;
  panel-intersection logic with two mismatched panels.
- **`splitter`** — group splits by patient/slide; held-out platform. *Tests*: no
  cell_id or patient appears in two folds; platform holdout actually excludes the
  platform.
- **`models`** — baselines + tabular + GNN wrappers. *Tests*: V0 achieves ~perfect
  on its own training labels (wiring sanity); fit/predict shape contracts;
  determinism with fixed seed.
- **`evaluation`** — PR-AUC, precision@k, calibration, per-slide aggregation.
  *Tests*: metric values on tiny known-answer arrays; out-of-fold assembly never
  scores a cell with a model trained on its slide (assertion).

---

## 14. Deliverables and layout

Self-contained under this directory (`specs/triad_tetrad_classifier/` for the spec;
implementation under a sibling experiment dir when built):

- `spec.md` (this file).
- On build: `data/manifest.*` (dataset URLs/licenses/checksums — data itself
  gitignored), `labels/` (per-slide rule-derived label tables), `features/`,
  `splits/`, `models/`, `reports/` (metrics + the decisive comparisons of §11),
  and a notebook mirroring the workshop convention (run-and-keep-outputs).
- General-purpose, reusable pieces (ontology harmonization, label generator) belong
  in the repo's `src/`, extending `workshop_lib`, not buried in the experiment dir.

## 15. Milestones

1. Resolve Q1–Q2, Q5 (framing, modality, crop overlap). 2. Acquire Tier-1
   (S-BIAD2378) + one Tier-2 DC-clean set (Schürch CODEX); verify panels/DC markers.
3. Harmonize cell types; generate rule labels; reproduce the crop regression number.
4. Build features V0–V3 with leakage tests green. 5. Baselines + tabular V1/V3;
   read the floor-vs-signal-vs-hard-negative result. 6. GNN V2 + cross-platform
   transfer. 7. Report, including a negative result if that's what the data says.

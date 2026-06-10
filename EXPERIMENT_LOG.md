# Workshop prompt experiment log

Running log of dialing in the workshop prompts. Method: the prompts are **spoken
aloud via WisprFlow**, one message at a time, exactly as they'll be delivered in
the workshop — so we're testing that the *spoken* wording produces good results,
not just that a polished written spec does. I (the agent) execute each spoken
message against the real crop; we judge the output; the wording is reworded and
re-tried until it's liked, then locked into the matching file under `prompts/`.

Each entry records the **verbatim spoken transcript** (WisprFlow output, warts and
all), what the agent did with it, the verdict, and the change for the next try.

Legend: 🎤 spoken transcript · 🤖 what the agent did · ✅/❌ verdict · → next.

---

## prompts/00_setup_and_labels.md
Status: **messages 1 & 2 locked; message 3 (sanity check) SKIPPED, untested** —
revisit later if desired.

### Attempt 00.1.a — message 1 (orient / inspect obs)
🎤 *"I'm working in this repo on a small crop of a 10x Atera cervical cancer
slide. data/cervical_tls_workshop/cervical_tls_crop.h5ad Load it and tell me
what's in OBS. Focus on any existing cell type or malignancy columns and what the
spatial coordinates look like. Don't make any changes."*

🤖 Loaded backed/read-only; summarized: 26,047 × 18,028 raw counts; the MiraTyper
cell-type column family (main = `..._constrained_alpha0100`, 168 types) + major
rollups + confidences; convenience `lineage`/`region`/`is_triad`/`is_anchor`;
malignancy via `malignant_class` (7,479 malignant), `p_malignant` (0–1, 1 NaN);
spatial coords = absolute slide microns, ~1500 µm square. No changes made.

✅ **liked — locked into `00_setup_and_labels.md` message 1.**

Notes on the spoken wording vs the written draft: said "10x **Atera**" (the file
draft says "10x Xenium WTA"); dictation rendered "OBS" uppercased. Path spoken as
a literal string landed fine.

### Attempt 00.2.a — message 2 (regenerate labels with MiraTyper)
🎤 *"Let's regenerate the labels using the MiraTyper inference workflow to run
cell typing plus malignant classification. Use alpha values 0.1 and ten and a
cervix tissue prior. Write the predictions to a Parquet file in the results
directory. Walk me through the command before you run it."*

🤖 Loaded the miratyper-inference skill; presented the ARM64 docker command
(`--panel all --run-malignant --tissue-id UBERON:0000002 --tissue-prior-alpha
0.1 10`, output `results/labels_miratyper.parquet`), walked through every flag,
and **paused without running** (as the message asked). Surfaced two caveats: (a)
no cervix entry in the prior table → uterus fallback; (b) "alpha ten" yields an
`_alpha10000` column, whereas the baked second variant is alpha 1.0.

Wording notes: "alpha values 0.1 and **ten**" — dictation spelled the number; the
agent had to map "ten" → `10`. "Walk me through the command before you run it"
worked perfectly as a stop-and-confirm trigger. Did not specify panel or tissue
id out loud (left "cervix tissue prior" generic) — agent filled `all` +
`UBERON:0000002` from context; worth deciding if the prompt should say them.

### Attempt 00.2.b — message 2, RUN (after user updated the model)
🎤 *"Okay, I've updated the model now, and it should run using the cervix tissue
prior. Let's run the command."*

🤖 Ran the ARM64 docker command. ✅ **Success in ~20 s** → `results/labels_miratyper.parquet`
(26,047 rows, 20 cols). 7,333 malignant (28.2%), 178 cell types, 98.3% genes
matched. Malignant cols came out as `p_malignant`/`malignant_class`/
`malignant_confidence` (match the baked names — no remap needed).

🔬 **FINDING — alpha column naming (CORRECTED; my first read was wrong).**
Encoding is a stable **alpha × 100**, 4-digit zero-pad. There was NO encoding
change. The column-name difference vs the baked obs is only because the alphas
differed: baked run used `1 10`, this run used `0.1 10`.
- `_alpha0100` = alpha **1.0**  (baked obs; what config/figures default to)
- `_alpha1000` = alpha **10**   (BOTH baked obs and this fresh run — no collision)
- `_alpha0010` = alpha **0.1**  (this fresh run only)
- My attempt-00.2.a guesses (alpha-10 → `_alpha10000`; baked `_alpha0100` = 0.1)
  were both wrong. Reconciles with the published workflow `--tissue-prior-alpha 1 10`.
- **Real leftover:** figures/config default to `_alpha0100` (alpha 1.0). A
  `0.1 10` regeneration produces `_alpha0010` + `_alpha1000`, i.e. no alpha-1.0
  column. So either regenerate with `1 10` (matches baked + published figures),
  or repoint the figure column to `_alpha0010` to run the workshop at alpha 0.1.

✅ **liked — locked into `00_setup_and_labels.md` message 2.** Kept the spoken
wording verbatim (panel + tissue id left for the agent to infer, as it did here);
added an italic note listing what the agent should fill in. The locked wording
runs alpha `0.1 10`, which commits the workshop to **alpha 0.1** for the figures
(no 1.0 column produced) unless we later repoint — figure-column choice deferred
to the figure steps.

---

## prompts/01_figure1_malignancy_immune_mask.md
Status: **in progress** — message 1 locked; on message 2

Carry-over from Step 0: the regenerated `results/labels_miratyper.parquet` has the
alpha-0.1 call in `cell_type_cdiam_miratyper_v1_constrained_alpha0010` (+ `p_malignant`);
it is NOT merged into the h5ad obs yet. Figure column choice (`_alpha0010` vs the
baked `_alpha0100`=alpha 1.0) still open.

### Attempt 01.1.a — message 1 (split immune vs rest)
🎤 *"Okay, using the crop and cell type column from step 0, split the cells into
immune, such as leukocyte or any ontology descendants, and you can look at
reference/config.py, Versus everything else How many of each type? Just give me
the numbers."*

🤖 Used Step-0 regenerated labels (`results/labels_miratyper.parquet`, alpha-0.1
col `_alpha0010`) + `immune_root='leukocyte'` from config (via reference/config.py)
+ ontology descendants. Reported: 26,047 total → 6,512 immune (25.0%) / 19,535
else (75.0%). No image yet (as asked).

✅ **liked — locked into `01_figure1_malignancy_immune_mask.md` message 1.**

Wording notes: "you can look at reference/config.py" worked as a pointer (it's the
loader for config/cell_types.json, where `immune_root` lives) — agent resolved it.
"How many of each type?" is slightly ambiguous (each lineage? or the 2 groups?) —
agent read it as the 2-way immune/non-immune split, which matches intent. The
phrase "cell type column from step 0" correctly pulled the regenerated alpha-0.1
labels rather than the baked obs.

### Attempt 01.2.a — message 2 (draw polygons, non-immune by malignancy ramp)
🎤 *"Okay, now draw every cell as its filled segmentation polygon from
data/cervical_tls_workshop/cell_boundaries.parquet On a black canvas as described
in config/style.json. One pixel per micron, For the non-immune cells, color them
by the malignancy ramp in the style file. Red with saturation meaning malignant."*

🤖 Rendered all cell polygons at 1 px/µm on black (box from boundaries, origin
subtracted). Non-immune cells (Step-0 alpha-0.1 labels) colored by the
config/style.json malignancy ramp (hue 0, sat=p_malignant, sat_max 0.85, V=1);
immune left black. 19,534 non-immune colored, 6,512 immune black. Saved to a WIP
path (`figures/wip_fig1_malignancy_only.png`) to avoid clobbering final fig1.
Visual: red malignant lobules + white benign stroma + black immune void. Correct.

⏳ awaiting verdict.

Wording notes: clean. "Red with saturation meaning malignant" mapped correctly to
the ramp. Dictation kept stray capitalization/commas ("One pixel per micron, For
the non-immune") — no effect. Implicit that immune stays black this step; agent
inferred it. Didn't say "subtract the box origin" but agent did it (it's in the
style.json / DESIGN note).

### Attempt 01.3.a — message 3 (immune ontology-MDS coloring on top)
🎤 *"Okay, now add the color for the immune cells with a blue-to-green ontology
ramp from config_style.json. Again, assign each immune type a hue by running
one-dimensional MDS on the cell ontology shortest path distances between immune
types that are actually present, and map that onto the hue range. Drop these on
top of the same image."*

🤖 Colored the 6,512 immune cells across 67 types via 1-D MDS on ontology
shortest-path distance → green→blue hue (config/style.json ramp), composited over
the malignancy layer. Saved `figures/wip_fig1_mask.png`. Visual: teal immune
island threads between red malignant lobules — matches case-study Fig 1. Full
mask; legend is the next step.

⏳ awaiting verdict.

Wording notes: said "blue-to-green" / "config_style.json" (underscore) — both
resolved fine to the green→blue ramp in config/style.json. The participant
re-stated the MDS method out loud even though it's in the style file; redundant
but harmless, and arguably good teaching. "Drop these on top of the same image"
correctly meant composite, not new canvas.

### ↪ METHODOLOGY PIVOT (after 01.3) — one-shot prompts into a shared notebook
Switching from message-by-message build-up to **one-shot prompts**: each figure is
one spoken prompt that the agent turns into **one cell** appended to a single
notebook, `workshop_figures.ipynb`, run one cell at a time. Setup cell loads
config + ontology + Step-0 labels (alpha 0.1, falls back to baked alpha 1.0) into
`df`/`cb`/`box`/`immune_set`. Figure 1 ported in as the first worked cell and
re-runs clean (26,047 cells · 6,512 immune · 7,333 malignant; 67 immune types).
Notebook executed via `jupyter nbconvert --execute`, outputs then cleared (ships
at ~7 KB). The earlier incremental Fig-1 messages stay locked in
`prompts/01_*.md` as the "explained" version; the notebook is the fast path.

Open: still on alpha 0.1 vs baked 1.0 for the final look (setup honors whichever
labels file is present).

### Fig 1 legend — rolled up to major lineages (config-driven)
Issue (spotted in VS Code review): CD8 absent from Fig 1 legend. Cause: legend
listed top-18 *fine* types by count; CD8 is split across 6 subtypes (max 39,
rank 22) so none cracked the top 18, while generic "T cell" ate 1,975.
Fix (config-driven, minimal prompting): added `immune_legend_groups` to
config/cell_types.json (ordered specific->general, first-match-wins, leukocyte
catch-all) + `wl.immune_legend_rollup()`. Legend now shows 13 major lineages incl.
**CD8 T cell (60)**. Rollup also absorbs ontology children correctly (microglial
717 -> Macrophage=892; conv+pDC -> Dendritic=586). Updated notebook Fig-1 cell,
reference/fig1 script, and prompts/01 legend wording to point at the config.

---

## prompts/02_figure2_triad_zoom.md  (one-shot, into notebook)
Status: **LOCKED** (one-shot, attempt 1)

### Attempt 02.1.a — one-shot Figure 2 (triads)
🎤 *"A CD8 T cell is a triad anchor if and only if at least one CD4 T cell and at
least one dendritic cell lie within 20 μm of its centroid. Map those three cell
types to lineages in config/cell_types.json Find every anchor in the crop. Draw
the cells filled as polygons as a black canvas, like Figure 1, but this time color
with a categorical palette in config/style.json - CD8 - CD4 - dendritic - NK -
macrophage - malignant. Mark the triads. Draw a magenta outline ring on each
anchor. Thin them greedily so they don't overlap. The thinning distance is in
config/motifs.json. Do similar for a tetrad, which is a triad that additionally
has a macrophage nearby. Flag those with an orange ring and said Added legend and
put that in the notebook."*

🤖 Appended a markdown + code cell to `workshop_figures.ipynb` using
wl.find_triad_anchors / greedy_thin / categorical_colors / draw_circles, all
config-driven. Ran via nbconvert (outputs kept). Result on Step-0 alpha-0.1
labels: **16 anchors, 11 rings after thinning, 7 tetrads** → figures/fig2_triad_zoom.png.
Correct palette + rings; triads sit in immune regions, not the red tumor.

✅ **liked — locked into `prompts/02_figure2_triad_zoom.md` as the one-shot.**
(Cleaned the two dictation garbles for the written file; kept the wording.)

Wording notes: long single utterance, fully self-contained — worked as a true
one-shot. Spoke the 20 µm explicitly even though it's in config; harmless (matches
config). Listed the palette members out loud (good — disambiguates which lineages
to show vs hide; generic T cells correctly left black). Dictation garble "and said
Added legend" → read as "add a legend"; "as a black canvas" → "on a black canvas".
No effect. Anchor count lower than baked (16 vs 21) purely due to alpha-0.1 CD8
sparsity (60 vs 66 CD8).

---

## prompts/03_figure3_single_tls.md  (one-shot, into notebook)
Status: **LOCKED** (one-shot, attempt 1)

### Attempt 03.1.a — one-shot Figure 3 (single TLS, searched)
🎤 *"...look at the TLS score in config/motifs.json. Find the centroid of a 100-micron
core that corresponds to the highest TLS score on the crop. Count B, plasma, T, DC,
and marker-positive cells (CXCL13, CCL19/CCL21, LAMP3+ DCs) and compute the TLS score
from the formula there. Report the numbers. Then overlay the same triad/tetrad rings
from step two. Put those core counts and the TLS score in the title, add a legend, and
create another image that is a 700 μm window around the centroid. Draw cells as filled
polygons on a black canvas, categorical palette in config/style.json, this time include
B cells in pink and plasma cells in magenta so follicles stand out, plus T, DC, NK,
macrophage, malignant colors."*

🤖 New behavior vs the reference: **searched** for the max-TLS-score 100 µm core
(grid over the interior, 15 µm step) instead of a hardcoded centroid. Found
**(4319.9, 3700.4) µm, TLS-score 125.4** — ~67 µm from the documented focal
follicle (4380.7, 3664.4), i.e. it rediscovered the same structure independently.
core(100µm): B=52 plasma=14 T=258 DC=20 CXCL13+=106 CCL19/21+=130 LAMP3+DC=3.
Rendered 700 µm window + rings + legend → figures/fig3_single_tls.png. Looks like a
real TLS (pink B follicle in a blue T-zone).

🐛 **Bug hit + fixed:** KeyError `'T cell (other)'`. Config naming collision —
`lineages`/`categorical_colors`/`draw_order` use **`"T cell other"`** (no parens),
but `immune_legend_groups` (Fig-1 legend) uses **`"T cell (other)"`**. My cell used
the parenthesized form for `lineage_set`. Trap for any agent; consider renaming the
legend group to match so there's one canonical name.

✅ **liked — locked into `prompts/03_figure3_single_tls.md` as the one-shot.**
🔧 Config aligned: `immune_legend_groups` name `"T cell (other)"` → `"T cell other"`
(now one canonical name across lineages/palette/draw_order/legend; no more parens
trap). Full notebook re-runs clean (cells 1–4).

Wording notes: true one-shot, and the "find the highest-TLS-score core" framing made
the agent *search* rather than reuse the known centroid — nice. Dictation garble
"TDC and K macrophage" → "T, DC, NK, macrophage". B-pink/plasma-magenta call-out
worked. Numbers differ from the baked focal core (B=52 vs 96) because of alpha-0.1
labels + the score-maximizing center being slightly off the documented point.

---

### Fig 1 — added a one-shot variant
`prompts/01` now leads with a one-shot prompt (consistent with 02/03), keeping the
4-message incremental flow below as the teaching variant. One-shot mirrors the
verified notebook Fig-1 cell (immune split + malignancy ramp + ontology-MDS immune
ramp + lineage-rollup legend), all config-referenced. All three figures now have
one-shot prompts. Remaining: HF upload; clean figures/wip_fig1_*.png scratch.

---

## Report step (added to prompts/workshop_prompts.md)
🎤 *"OK, please report out these results from the notebook in a markdown file.
Include images that we've generated inline."*
🤖 Generated `reports/workshop_results.md` by extracting each cell's stdout from
`workshop_figures.ipynb` (warnings filtered) + embedding the figure PNGs inline
(`../figures/*.png`). Added the prompt as a "Report" step before the appendix.
✅ added.

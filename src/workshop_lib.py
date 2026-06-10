"""Shared helpers for the cervical-TLS workshop figures.

Subset-adapted from the full-slide scripts in an internal Mira analysis repo
(notebooks/atera_xenium_wta/scripts/). All colors, lineage
definitions, and motif parameters come from ../config/*.json via config.py --
this module holds only the mechanics (load obs, render polygons, find motifs).

Coordinates stay in absolute slide microns; we render into a box and subtract
the box origin so the output image is the tight crop extent.
"""
import colorsys
import pickle

import networkx as nx
import numpy as np
import pandas as pd
import scanpy as sc
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
from sklearn.manifold import MDS

from config import STYLE, CELL_TYPES, MOTIFS, rgb, lineage_roots

# ── constants sourced from config ────────────────────────────────────────────
BLACK = tuple(STYLE["canvas"]["background_rgb"])
UM_PER_PX = STYLE["canvas"]["um_per_px"]

_imm = STYLE["immune_ontology_ramp"]
HUE_GREEN = _imm["hue_start_deg"] / 360.0
HUE_BLUE = _imm["hue_end_deg"] / 360.0
IMMUNE_SAT = _imm["saturation"]
IMMUNE_VAL = _imm["value"]
MISSING_PATH = _imm["missing_path_distance"]
MDS_KW = _imm["mds_params"]

_mal = STYLE["malignancy_ramp"]
HUE_RED = _mal["hue_deg"] / 360.0
MAL_SAT_MAX = _mal["saturation_max"]
MAL_VAL = _mal["value"]

RING = STYLE["motif_rings"]
COLOR_TRIAD = tuple(RING["triad_rgb"])
COLOR_TETRA = tuple(RING["tetrad_rgb"])

DEFAULT_CT_COL = CELL_TYPES["label_column"]
MAL_COL = CELL_TYPES["malignancy_column"]
MAL_THR = CELL_TYPES["malignant_threshold"]
IMMUNE_ROOT = CELL_TYPES["immune_root"]

TRIAD_RADIUS_UM = MOTIFS["triad"]["radius_um"]
THINNING_DIST_UM = MOTIFS["triad"]["display_thinning_um"]
TETRA_RADIUS_UM = MOTIFS["tetrad"]["radius_um"]


def hsv255(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


def dset(g, root):
    return (set(nx.descendants(g, root)) | {root}) if root in g.nodes() else set()


def lineage_set(graph, name):
    """Union of ontology descendants for a named lineage (config-driven)."""
    out = set()
    for root in lineage_roots(name):
        out |= dset(graph, root)
    return out


def load_ontology(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def load_obs(h5ad_path, ct_col=DEFAULT_CT_COL):
    """Return DataFrame[cell_id, x_centroid, y_centroid, ct, p_malignant]."""
    ad = sc.read_h5ad(h5ad_path, backed="r")
    obs = ad.obs
    return pd.DataFrame({
        "cell_id": obs.index.astype(str),
        "x_centroid": obs["x_centroid"].to_numpy(float),
        "y_centroid": obs["y_centroid"].to_numpy(float),
        "ct": obs[ct_col].astype(str).to_numpy(),
        "p_malignant": obs[MAL_COL].to_numpy(float),
    })


def gene_positive_mask(h5ad_path, cell_ids, gene):
    """Boolean mask (aligned to cell_ids) of cells with >0 raw counts of gene."""
    import scipy.sparse as sp
    ad = sc.read_h5ad(h5ad_path, backed="r")
    if gene not in ad.var_names:
        return np.zeros(len(cell_ids), dtype=bool)
    col = ad[:, ad.var_names.get_loc(gene)].X
    col = (col.toarray().ravel() if sp.issparse(col) else np.asarray(col).ravel())
    s = pd.Series(col > 0, index=ad.obs.index.astype(str))
    return s.reindex(cell_ids).fillna(False).to_numpy()


def load_boundaries(parquet_path):
    return pd.read_parquet(parquet_path, columns=["cell_id", "vertex_x", "vertex_y"])


def box_from_boundaries(cb, pad=2.0):
    return (float(cb.vertex_x.min()) - pad, float(cb.vertex_y.min()) - pad,
            float(cb.vertex_x.max()) + pad, float(cb.vertex_y.max()) + pad)


# ── coloring ─────────────────────────────────────────────────────────────────
def malignant_color(p):
    return hsv255(HUE_RED, float(p) * MAL_SAT_MAX, MAL_VAL)


def immune_ontology_colors(immune_types, graph):
    """dict[type] -> RGB via 1-D MDS on ontology distance, green->blue ramp."""
    u = graph.to_undirected()
    n = len(immune_types)
    D = np.zeros((n, n), np.float32)
    for i, t in enumerate(immune_types):
        paths = nx.single_source_shortest_path_length(u, t) if t in u else {}
        for j, s in enumerate(immune_types):
            D[i, j] = paths.get(s, MISSING_PATH)
    D = (D + D.T) / 2
    coords = MDS(**MDS_KW).fit_transform(D).ravel()
    lo, hi = coords.min(), coords.max()
    norm = (coords - lo) / (hi - lo + 1e-9)
    return {t: hsv255(HUE_GREEN + x * (HUE_BLUE - HUE_GREEN), IMMUNE_SAT, IMMUNE_VAL)
            for t, x in zip(immune_types, norm)}


def immune_legend_rollup(immune_ct, immune_colors, graph):
    """Roll immune fine cell types up to the major lineages in
    config/cell_types.json -> ordered [(group_name, rep_rgb, count)] for legends.

    `immune_ct`     : Series of fine cell-type labels for immune cells only.
    `immune_colors` : dict fine-type -> rgb (the ontology-MDS colors); the swatch
                      for each group is the color of its most-common subtype.
    First-match-wins over the configured group order (specific -> general).
    """
    groups = CELL_TYPES["immune_legend_groups"]
    gsets = [(g["name"], set().union(*(dset(graph, r) for r in g["roots"]))) for g in groups]

    def lookup(ct):
        for name, s in gsets:
            if ct in s:
                return name
        return None

    grp = immune_ct.map(lookup)
    out = []
    for name, _ in gsets:
        sub = immune_ct[grp == name]
        if len(sub) == 0:
            continue
        rep_fine = sub.value_counts().index[0]
        out.append((name, immune_colors.get(rep_fine, (180, 180, 180)), len(sub)))
    out.sort(key=lambda r: -r[2])
    return out


def categorical_colors(df, graph, lineages, ct_col="ct"):
    """Per-cell flat color from config draw_order. `lineages` = names to use
    (besides 'Malignant', which fills any p>=threshold cell a lineage didn't)."""
    use = set(lineages)
    c = {}
    for name in CELL_TYPES["draw_order"]:
        if name == "Malignant":
            for cid in df[df.p_malignant.ge(MAL_THR)].cell_id:
                c[cid] = rgb("Malignant")
        elif name in use:
            col = rgb(name)
            for cid in df[df[ct_col].isin(lineage_set(graph, name))].cell_id:
                c[cid] = col
    return c


# ── rendering ────────────────────────────────────────────────────────────────
def render_polygons(cb, cell2color, box, um_per_px=UM_PER_PX, bg=BLACK):
    x0, y0, x1, y1 = box
    scale = 1.0 / um_per_px
    W, H = int(round((x1 - x0) * scale)), int(round((y1 - y0) * scale))
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)
    for cid, grp in cb.groupby("cell_id", sort=False):
        color = cell2color.get(cid)
        if color is None:
            continue
        xs = (grp.vertex_x.to_numpy() - x0) * scale
        ys = (grp.vertex_y.to_numpy() - y0) * scale
        pts = list(zip(xs.tolist(), ys.tolist()))
        if len(pts) >= 3:
            draw.polygon(pts, fill=color)
    return img


# ── spatial motifs ───────────────────────────────────────────────────────────
def greedy_thin(points, min_dist):
    if len(points) == 0:
        return np.zeros(0, dtype=bool)
    tree = cKDTree(points)
    keep = np.zeros(len(points), bool)
    blocked = np.zeros(len(points), bool)
    for i in range(len(points)):
        if blocked[i]:
            continue
        keep[i] = True
        for j in tree.query_ball_point(points[i], min_dist):
            if j != i:
                blocked[j] = True
    return keep


def find_triad_anchors(df, graph, ct_col="ct",
                       radius_um=TRIAD_RADIUS_UM, tetra_radius_um=TETRA_RADIUS_UM):
    """CD8 anchor iff >=1 CD4 AND >=1 DC within radius. Returns
    (anchor_xy, has_mac) where has_mac flags a tetrad (+macrophage)."""
    xy = lambda name: df[df[ct_col].isin(lineage_set(graph, name))][["x_centroid", "y_centroid"]].to_numpy()
    cd8, cd4, dc, mac = xy("CD8 T cell"), xy("CD4 T cell"), xy("Dendritic cell"), xy("Macrophage")
    if len(cd8) == 0 or len(cd4) == 0 or len(dc) == 0:
        return np.zeros((0, 2)), np.zeros(0, bool)
    cd4_t, dc_t = cKDTree(cd4), cKDTree(dc)
    has_cd4 = np.array([bool(cd4_t.query_ball_point(p, radius_um, return_length=True)) for p in cd8])
    has_dc = np.array([bool(dc_t.query_ball_point(p, radius_um, return_length=True)) for p in cd8])
    anchors = cd8[has_cd4 & has_dc]
    if len(mac):
        mac_t = cKDTree(mac)
        has_mac = np.array([bool(mac_t.query_ball_point(p, tetra_radius_um, return_length=True)) for p in anchors])
    else:
        has_mac = np.zeros(len(anchors), bool)
    return anchors, has_mac


def draw_circles(img, centers, has_mac, box, um_per_px=UM_PER_PX,
                 radius_um=None, width_px=None):
    radius_um = RING["radius_um"] if radius_um is None else radius_um
    width_px = RING["line_width_px"] if width_px is None else width_px
    draw = ImageDraw.Draw(img)
    scale = 1.0 / um_per_px
    r = radius_um * scale
    W, H = img.size
    for (cx, cy), m in zip(centers, has_mac):
        px, py = (cx - box[0]) * scale, (cy - box[1]) * scale
        if -r <= px <= W + r and -r <= py <= H + r:
            draw.ellipse([px - r, py - r, px + r, py + r],
                         outline=(COLOR_TETRA if m else COLOR_TRIAD), width=width_px)

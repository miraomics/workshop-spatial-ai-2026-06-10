"""Load the workshop JSON config (config/style.json, cell_types.json, motifs.json).

This is the single source of truth for colors, lineage definitions, and motif
parameters. The figure scripts read from here; the prompts point the agent at
the same JSON files.
"""
import json
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _load(name):
    return json.loads((CONFIG_DIR / name).read_text())


STYLE = _load("style.json")
CELL_TYPES = _load("cell_types.json")
MOTIFS = _load("motifs.json")


def rgb(name):
    """Categorical fill color (tuple) for a named lineage / 'Malignant'."""
    return tuple(STYLE["categorical_colors"][name])


def lineage_roots(name):
    """Ontology root(s) for a lineage as a list of strings."""
    v = CELL_TYPES["lineages"][name]
    return v if isinstance(v, list) else [v]

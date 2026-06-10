#!/usr/bin/env bash
# Download the workshop crop from Hugging Face into data/cervical_tls_workshop/.
#
# Public dataset (CC BY 4.0) — no token needed. Pulls the full ~692 MB crop
# (h5ad, segmentation/nucleus parquets, transcripts, morphology OME-TIFF, card).
# Re-running is incremental: hf verifies local files and only fetches what changed.
set -euo pipefail

REPO="honicky/cervical-tls-workshop-crop"
DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/data/cervical_tls_workshop"
mkdir -p "$DEST"

echo "Downloading $REPO -> $DEST"
if command -v hf >/dev/null 2>&1; then
  hf download "$REPO" --repo-type dataset --local-dir "$DEST"
elif command -v uvx >/dev/null 2>&1; then
  uvx --from huggingface_hub hf download "$REPO" --repo-type dataset --local-dir "$DEST"
else
  echo "ERROR: need 'hf' (pip install huggingface_hub) or 'uv' (https://docs.astral.sh/uv) on PATH." >&2
  exit 1
fi
echo "Done -> $DEST"

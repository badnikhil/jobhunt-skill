#!/usr/bin/env bash
# Verify a resume PDF survives ATS text extraction.
# LaTeX silently drops fi/fl/ffi ligatures without \usepackage{cmap},
# so "profiling" extracts as "proling" and keyword matching scores zero.
set -euo pipefail
PDF="${1:?usage: check_ats_safe.sh resume.pdf}"
echo "== words extractable =="
pdftotext "$PDF" - | wc -w
echo "== broken-ligature scan (any output below = BROKEN) =="
pdftotext "$PDF" - | grep -oE '\b(oine|proling|specic|ows|rst|dierent|eciency|conguration|veried|dened)\b' | sort -u || true
echo "== first 30 lines as an ATS sees them =="
pdftotext "$PDF" - | head -30

#!/usr/bin/env bash
# -------------------------------------------------------------------
# crawl.sh – Miroir incrémental du site DIW IUT Le Havre
#
# Usage :
#   SITE_USER=etInfo SITE_PASSWORD='t[0]!=1' bash scripts/crawl.sh [--pdf-only]
#
# Options :
#   --pdf-only : Ne collecter que les fichiers PDF
#
# Les variables SITE_USER et SITE_PASSWORD peuvent aussi être lues
# depuis un fichier .env à la racine du projet.
# -------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Charger .env s'il existe
if [ -f "$PROJECT_ROOT/.env" ]; then
  set -a
  # shellcheck source=/dev/null
  . "$PROJECT_ROOT/.env"
  set +a
fi

: "${SITE_USER:?Variable SITE_USER requise}"
: "${SITE_PASSWORD:?Variable SITE_PASSWORD requise}"

OUTPUT_DIR="$PROJECT_ROOT/site"

# Vérifier l'option --pdf-only
PDF_ONLY=""
if [ "${1:-}" = "--pdf-only" ]; then
  PDF_ONLY="--pdf-only"
  echo "==> Mode PDF uniquement activé"
fi

# Supprimer l'ancien miroir pour un crawl propre
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

echo "==> Lancement du crawler Python..."
python3 "$SCRIPT_DIR/crawler.py" "$OUTPUT_DIR" "$SITE_USER" "$SITE_PASSWORD" $PDF_ONLY

echo "==> Miroir terminé. Fichiers dans $OUTPUT_DIR"

# Lancer l'analyseur automatiquement
echo ""
echo "==> Lancement de l'analyseur..."
python3 "$SCRIPT_DIR/analyzer.py" "$OUTPUT_DIR"

echo ""
echo "==> ✓ Terminé ! Résultats disponibles dans $OUTPUT_DIR"


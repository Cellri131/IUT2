#!/usr/bin/env bash
# -------------------------------------------------------------------
# crawl.sh – Miroir incrémental du site DIW IUT Le Havre
#
# Usage :
#   SITE_USER=etInfo SITE_PASSWORD='t[0]!=1' bash scripts/crawl.sh
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

SITE_URL="https://diw.iut.univ-lehavre.fr/"
OUTPUT_DIR="$PROJECT_ROOT/site"

mkdir -p "$OUTPUT_DIR"

echo "==> Démarrage du miroir de $SITE_URL"

wget \
  --mirror \
  --convert-links \
  --adjust-extension \
  --page-requisites \
  --no-parent \
  --directory-prefix="$OUTPUT_DIR" \
  --http-user="$SITE_USER" \
  --http-password="$SITE_PASSWORD" \
  --no-check-certificate \
  --reject-regex='.*(/jdk|/JDK|javadoc|java-doc|docs/api).*' \
  --exclude-directories='*/jdk*,*/JDK*,*/javadoc*' \
  --timeout=30 \
  --tries=3 \
  --wait=0.5 \
  --random-wait \
  "$SITE_URL" \
  2>&1 | tee "$PROJECT_ROOT/crawl.log" || true

echo "==> Miroir terminé. Fichiers dans $OUTPUT_DIR"

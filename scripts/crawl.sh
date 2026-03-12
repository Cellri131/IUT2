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

# Écrire les identifiants dans un fichier temporaire pour éviter qu'ils
# apparaissent dans la liste des processus (ps aux).
WGETRC_TMP="$(mktemp)"
COOKIE_JAR="$(mktemp)"
chmod 600 "$WGETRC_TMP" "$COOKIE_JAR"
printf 'http_user=%s\nhttp_password=%s\n' "$SITE_USER" "$SITE_PASSWORD" > "$WGETRC_TMP"
export WGETRC="$WGETRC_TMP"
trap 'rm -f "$WGETRC_TMP" "$COOKIE_JAR"' EXIT

echo "==> Démarrage du miroir de $SITE_URL"

wget \
  --mirror \
  --convert-links \
  --adjust-extension \
  --page-requisites \
  --no-parent \
  --recursive \
  --level=inf \
  --directory-prefix="$OUTPUT_DIR" \
  --no-check-certificate \
  --auth-no-challenge \
  --keep-session-cookies \
  --save-cookies="$COOKIE_JAR" \
  --load-cookies="$COOKIE_JAR" \
  --reject-regex='.*(/[Jj][Dd][Kk]|[Jj]ava[Dd]oc|java-doc|docs/api|apidocs|jdoc).*' \
  --exclude-directories=/jdk,/JDK,/javadoc,/apidocs \
  --timeout=30 \
  --tries=3 \
  --wait=0.5 \
  --random-wait \
  "$SITE_URL" \
  2>&1 | tee "$PROJECT_ROOT/crawl.log" || true

echo "==> Miroir terminé. Fichiers dans $OUTPUT_DIR"

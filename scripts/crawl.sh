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

# Phase 1 : crawl récursif complet du site
wget \
  --mirror \
  --convert-links \
  --adjust-extension \
  --page-requisites \
  --recursive \
  --level=inf \
  --no-parent \
  --directory-prefix="$OUTPUT_DIR" \
  --no-check-certificate \
  --auth-no-challenge \
  --keep-session-cookies \
  --save-cookies="$COOKIE_JAR" \
  --load-cookies="$COOKIE_JAR" \
  -e robots=off \
  --reject-regex='.*((/[Jj][Dd][Kk]|[Jj]ava[Dd]oc|java-doc|docs/api|apidocs|jdoc)|/pedago/Enseignement/).*' \
  --exclude-directories=/jdk,/JDK,/javadoc,/apidocs,/pedago/Enseignement \
  --follow-tags=a,area,img,link,script \
  --timeout=30 \
  --tries=3 \
  --wait=0.5 \
  --random-wait \
  "$SITE_URL" \
  2>&1 | tee "$PROJECT_ROOT/crawl.log" || true

# Phase 2 : extraire les liens depuis les fichiers XML (sitemaps, index.xml, etc.)
# wget ne parse pas les XML → on extrait les URLs manuellement et on les télécharge
MIRROR_DIR="$OUTPUT_DIR/diw.iut.univ-lehavre.fr"
if [ -d "$MIRROR_DIR" ]; then
  echo "==> Phase 2 : extraction des liens depuis les fichiers XML..."
  URL_LIST="$(mktemp)"
  trap 'rm -f "$WGETRC_TMP" "$COOKIE_JAR" "$URL_LIST"' EXIT

  # Cherche les URLs dans tous les .xml téléchargés
  find "$MIRROR_DIR" -name '*.xml' -o -name '*.xml.html' 2>/dev/null | while read -r xmlfile; do
    grep -oP '(?:href|src|loc)=["\x27]?\Khttps?://diw\.iut\.univ-lehavre\.fr[^"\x27<>\s]*' "$xmlfile" 2>/dev/null || true
    grep -oP '<loc>\K[^<]+' "$xmlfile" 2>/dev/null || true
  done | sort -u | grep -v -iE '(jdk|javadoc|java-doc|apidocs|/pedago/Enseignement/)' > "$URL_LIST" || true

  if [ -s "$URL_LIST" ]; then
    EXTRA_COUNT=$(wc -l < "$URL_LIST")
    echo "    → $EXTRA_COUNT URL(s) trouvées dans les XML"
    wget \
      --no-clobber \
      --convert-links \
      --adjust-extension \
      --page-requisites \
      --directory-prefix="$OUTPUT_DIR" \
      --no-check-certificate \
      --auth-no-challenge \
      --keep-session-cookies \
      --save-cookies="$COOKIE_JAR" \
      --load-cookies="$COOKIE_JAR" \
      -e robots=off \
      --reject-regex='.*((/[Jj][Dd][Kk]|[Jj]ava[Dd]oc|java-doc|docs/api|apidocs|jdoc)|/pedago/Enseignement/).*' \
      --timeout=30 \
      --tries=3 \
      --wait=0.5 \
      --random-wait \
      --input-file="$URL_LIST" \
      2>&1 | tee -a "$PROJECT_ROOT/crawl.log" || true
  else
    echo "    → Aucune URL supplémentaire trouvée dans les XML"
  fi
fi

echo "==> Miroir terminé. Fichiers dans $OUTPUT_DIR"

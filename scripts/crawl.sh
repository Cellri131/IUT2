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
MIRROR_DIR="$OUTPUT_DIR/diw.iut.univ-lehavre.fr"

# Supprimer l'ancien miroir pour forcer un crawl complet
# (--mirror + cache provoque des 304 qui empêchent wget de suivre les liens)
rm -rf "$MIRROR_DIR"
mkdir -p "$OUTPUT_DIR"

COOKIE_JAR="$(mktemp)"
chmod 600 "$COOKIE_JAR"
trap 'rm -f "$COOKIE_JAR"' EXIT

# Options wget communes (auth + exclusions)
WGET_OPTS=(
  --http-user="$SITE_USER"
  --http-password="$SITE_PASSWORD"
  --auth-no-challenge
  --no-check-certificate
  --keep-session-cookies
  --save-cookies="$COOKIE_JAR"
  --load-cookies="$COOKIE_JAR"
  -e robots=off
  --reject-regex='.*((/[Jj][Dd][Kk]|[Jj]ava[Dd]oc|java-doc|docs/api|apidocs|jdoc)|/pedago/Enseignement/).*'
  --exclude-directories=/jdk,/JDK,/javadoc,/apidocs,/pedago/Enseignement
  --timeout=60
  --tries=3
  --wait=0.5
  --random-wait
)

echo "==> Démarrage du miroir de $SITE_URL"

# Phase 1 : crawl récursif complet du site
wget \
  --recursive \
  --level=inf \
  --no-parent \
  --convert-links \
  --adjust-extension \
  --page-requisites \
  --directory-prefix="$OUTPUT_DIR" \
  --follow-tags=a,area,img,link,script \
  "${WGET_OPTS[@]}" \
  "$SITE_URL" \
  2>&1 | tee "$PROJECT_ROOT/crawl.log" || true

# Phase 2 : boucle d'extraction des liens depuis XML/HTML
# wget ne parse pas les fichiers XML pour y trouver des liens,
# donc on les extrait manuellement et on re-télécharge en boucle
# jusqu'à ce qu'il n'y ait plus de nouvelles URLs.
if [ -d "$MIRROR_DIR" ]; then
  PASS=0
  while true; do
    PASS=$((PASS + 1))
    echo "==> Phase 2 (passe $PASS) : extraction des liens..."
    URL_LIST="$(mktemp)"

    # Extraire toutes les URLs du même domaine depuis XML et HTML
    find "$MIRROR_DIR" \( -name '*.xml' -o -name '*.xml.html' -o -name '*.html' -o -name '*.htm' \) 2>/dev/null | while read -r f; do
      grep -oiP 'https?://diw\.iut\.univ-lehavre\.fr[^"'"'"'<>\s)]*' "$f" 2>/dev/null || true
    done | sort -u | grep -v -iE '(jdk|javadoc|java-doc|apidocs|/pedago/Enseignement/)' > "$URL_LIST" || true

    if [ ! -s "$URL_LIST" ]; then
      echo "    → Aucune URL trouvée, fin."
      rm -f "$URL_LIST"
      break
    fi

    # Compter combien de fichiers on a AVANT le téléchargement
    BEFORE=$(find "$MIRROR_DIR" -type f | wc -l)

    EXTRA_COUNT=$(wc -l < "$URL_LIST")
    echo "    → $EXTRA_COUNT URL(s) à vérifier"
    wget \
      --no-clobber \
      --convert-links \
      --adjust-extension \
      --page-requisites \
      --recursive \
      --level=inf \
      --no-parent \
      --directory-prefix="$OUTPUT_DIR" \
      "${WGET_OPTS[@]}" \
      --input-file="$URL_LIST" \
      2>&1 | tee -a "$PROJECT_ROOT/crawl.log" || true

    rm -f "$URL_LIST"

    # Compter APRÈS : si aucun nouveau fichier, on arrête
    AFTER=$(find "$MIRROR_DIR" -type f | wc -l)
    NEW_FILES=$((AFTER - BEFORE))
    echo "    → $NEW_FILES nouveau(x) fichier(s) téléchargé(s)"

    if [ "$NEW_FILES" -le 0 ]; then
      echo "    → Plus rien de nouveau, fin."
      break
    fi

    # Sécurité : max 20 passes
    if [ "$PASS" -ge 20 ]; then
      echo "    → Limite de passes atteinte, fin."
      break
    fi
  done
fi

echo "==> Miroir terminé. Fichiers dans $OUTPUT_DIR"

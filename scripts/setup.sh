#!/usr/bin/env bash
# -------------------------------------------------------------------
# setup.sh – Installation des dépendances pour le crawler
#
# Usage :
#   bash scripts/setup.sh
# -------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "==> Installation des dépendances Python..."

# Vérifier si python3 et pip sont disponibles
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 n'est pas installé. Installez-le d'abord."
    exit 1
fi

if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo "✗ pip n'est pas installé. Installez-le d'abord."
    exit 1
fi

# Installer les dépendances
cd "$PROJECT_ROOT"
python3 -m pip install -r requirements.txt

echo ""
echo "==> ✓ Dépendances installées avec succès !"
echo ""
echo "Usage :"
echo "  SITE_USER=etInfo SITE_PASSWORD='t[0]!=1' bash scripts/crawl.sh"
echo "  SITE_USER=etInfo SITE_PASSWORD='t[0]!=1' bash scripts/crawl.sh --pdf-only"

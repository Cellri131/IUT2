#!/usr/bin/env bash
# Script de lancement rapide pour Windows (Git Bash)
cd "$(dirname "$0")"

# Créer .env si inexistant
if [ ! -f .env ]; then
  cp .env.example .env
fi

# Installer dépendances
echo "==> Installation des dépendances..."
pip install -r requirements.txt

# Lancer le crawler
echo ""
echo "==> Lancement du crawler..."
bash scripts/crawl.sh

echo ""
echo "==> Résultats dans ./site/"

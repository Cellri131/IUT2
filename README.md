# Crawler IUT Le Havre

Crawler automatisé du site DIW IUT Le Havre avec déploiement GitHub Pages.

## Utilisation locale

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Lancer le crawler
```bash
# Crawl complet
SITE_USER=etInfo SITE_PASSWORD='t[0]!=1' bash scripts/crawl.sh

# Mode PDF uniquement
SITE_USER=etInfo SITE_PASSWORD='t[0]!=1' bash scripts/crawl.sh --pdf-only
```

### 3. Ou avec un fichier .env
Créez un fichier `.env` :
```env
SITE_USER=etInfo
SITE_PASSWORD=t[0]!=1
```

Puis :
```bash
bash scripts/crawl.sh
```

## Résultats

Les fichiers sont générés dans `site/` :
- `crawl_results.json` / `.csv` - Données structurées
- `sitemap.txt` - Liste des URLs
- `link.data` - Liens par page
- `diw.iut.univ-lehavre.fr/` - Miroir du site
- `crawler.log` - Logs

## GitHub Actions

Le workflow `.github/workflows/sync.yml` s'exécute automatiquement tous les jours à 4h00 UTC.

Lancement manuel : **Actions** > **Sync Mirror Site** > **Run workflow**

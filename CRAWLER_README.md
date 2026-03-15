# Crawler IUT Le Havre - Version améliorée

Crawler avancé pour dupliquer les pages du site DIW IUT Le Havre avec authentification automatique.

## Fonctionnalités

- ✅ Authentification automatique (HTTP Basic + formulaires)
- ✅ Support des redirections meta
- ✅ Mode PDF uniquement (optionnel)
- ✅ Export des résultats en JSON/CSV/TXT
- ✅ Logging détaillé avec fichier crawler.log
- ✅ Analyse statistique automatique
- ✅ Génération de sitemap
- ✅ Détection des liens cassés

## Installation

```bash
# Installer les dépendances Python
pip install -r requirements.txt
```

## Configuration

### Option 1 : Variables d'environnement

```bash
export SITE_USER="etInfo"
export SITE_PASSWORD='t[0]!=1'
```

### Option 2 : Fichier .env

Créez un fichier `.env` à la racine du projet :

```env
SITE_USER=etInfo
SITE_PASSWORD=t[0]!=1
```

## Utilisation

### Méthode 1 : Script Bash (recommandé)

```bash
# Crawl complet
SITE_USER=etInfo SITE_PASSWORD='t[0]!=1' bash scripts/crawl.sh

# Crawl PDF uniquement
SITE_USER=etInfo SITE_PASSWORD='t[0]!=1' bash scripts/crawl.sh --pdf-only
```

### Méthode 2 : Python direct

```bash
# Crawl complet
python3 scripts/crawler.py ./site etInfo 't[0]!=1'

# Crawl PDF uniquement
python3 scripts/crawler.py ./site etInfo 't[0]!=1' --pdf-only
```

### Analyse des résultats

```bash
# Analyse automatique (déjà incluse dans crawl.sh)
python3 scripts/analyzer.py ./site
```

## Fichiers générés

Après le crawl, vous trouverez dans le dossier `site/` :

- `link.data` : Liste des liens trouvés sur chaque page (format texte)
- `crawl_results.json` : Résultats complets au format JSON
- `crawl_results.csv` : Résultats complets au format CSV
- `sitemap.txt` : Liste de toutes les URLs crawlées avec succès
- `diw.iut.univ-lehavre.fr/` : Miroir complet du site avec tous les fichiers téléchargés

## Logs

Le fichier `crawler.log` contient tous les détails du crawl :
- URLs visitées
- Erreurs rencontrées
- Tentatives d'authentification
- PDFs trouvés (en mode PDF uniquement)

## Exemples

### Crawl complet du site

```bash
SITE_USER=etInfo SITE_PASSWORD='t[0]!=1' bash scripts/crawl.sh
```

Résultat : Télécharge toutes les pages HTML, XML, PDF, images, etc.

### Crawl PDF uniquement

```bash
SITE_USER=etInfo SITE_PASSWORD='t[0]!=1' bash scripts/crawl.sh --pdf-only
```

Résultat : Ne télécharge et ne sauvegarde que les fichiers PDF

## Personnalisation

### Modifier les patterns d'exclusion

Éditez `scripts/crawler.py` et modifiez `EXCLUDE_PATTERNS` :

```python
EXCLUDE_PATTERNS = [
    re.compile(r"/jdk", re.IGNORECASE),
    re.compile(r"/javadoc", re.IGNORECASE),
    # Ajoutez vos patterns ici
]
```

### Modifier l'URL de départ

Éditez `scripts/crawler.py` et modifiez `START_URL` :

```python
START_URL = "https://diw.iut.univ-lehavre.fr/pedago/index.xml"
```

## Dépannage

### Erreur d'authentification

Si vous voyez "401 Unauthorized", vérifiez :
- Les identifiants sont corrects
- Les quotes dans le mot de passe (utilisez des quotes simples)

### Erreur SSL

Le crawler désactive automatiquement la vérification SSL. Si vous voulez l'activer, modifiez `scripts/crawler.py` :

```python
session.verify = True  # Au lieu de False
```

### Timeout

Pour augmenter le timeout, modifiez dans `scripts/crawler.py` :

```python
resp = session.get(url, timeout=120)  # Au lieu de 60
```

## Auteurs

Basé sur crawler2.py et analyzer.py du projet original.
Amélioré avec support avancé d'authentification et mode PDF.

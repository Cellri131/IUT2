# siteIUT2 – Miroir personnalisé du site DIW IUT Le Havre

Ce projet clone automatiquement le site [diw.iut.univ-lehavre.fr](https://diw.iut.univ-lehavre.fr/) et y applique une feuille de style CSS personnalisée. Le miroir est mis à jour quotidiennement via GitHub Actions et publié sur GitHub Pages.

## Structure du projet

```
siteIUT2/
├── .github/workflows/sync.yml    # Workflow GitHub Actions (crawl + deploy)
├── assets/custom-style.css        # CSS personnalisée appliquée au miroir
├── scripts/
│   ├── crawl.sh                   # Script wget pour le miroir incrémental
│   └── inject_css.py              # Injection du <link> CSS dans les HTML
├── site/                          # (généré) Fichiers du miroir (ignoré par git)
├── .gitignore
└── README.md
```

## Mise en place

### 1. Créer le dépôt GitHub privé

```bash
cd siteIUT2
git init
git add .
git commit -m "init: structure du projet miroir"
gh repo create siteIUT2 --private --source=. --push
```

### 2. Configurer les secrets GitHub

Dans **Settings → Secrets and variables → Actions**, ajouter :

| Secret          | Valeur          |
|-----------------|-----------------|
| `SITE_USER`     | *(identifiant)* |
| `SITE_PASSWORD` | *(mot de passe)* |

### 3. Activer GitHub Pages

- Aller dans **Settings → Pages**
- Source : **Deploy from a branch**
- Branche : `gh-pages` / `/ (root)`

> **Note :** GitHub Pages sur un dépôt privé nécessite un plan GitHub Pro, Team ou Enterprise.

### 4. Lancer la première synchronisation

- Aller dans **Actions → Sync Mirror Site → Run workflow**
- Ou attendre l'exécution automatique (chaque jour à 4h UTC)

## Exécution locale (optionnel)

```bash
# Installer wget si nécessaire (Linux/Mac : déjà installé)
# Windows : utiliser WSL ou Git Bash

# Définir les identifiants
export SITE_USER="etInfo"
export SITE_PASSWORD='t[0]!=1'

# Lancer le crawl
bash scripts/crawl.sh

# Injecter la CSS custom
python3 scripts/inject_css.py site/diw.iut.univ-lehavre.fr
```

## Personnaliser le style

Modifiez le fichier `assets/custom-style.css`. Les changements seront appliqués au prochain crawl (ou en relançant `inject_css.py` localement).

## Exclusions

- La documentation JDK est exclue du crawl (trop volumineuse)
- Seul le contenu sous `diw.iut.univ-lehavre.fr/` est téléchargé (pas de liens externes)

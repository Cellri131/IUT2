# Scripts de Conversion et d'Adaptation

Ce dossier contient les scripts nécessaires pour convertir les fichiers XML du site IUT en HTML et adapter les liens.

## Scripts disponibles

### 1. `xml_to_html_converter.py` - Conversion XML → HTML + Adaptation des liens

Convertit les fichiers XML personnalisés en HTML standard et adapte automatiquement les liens.

**Fonctionnalités :**
- Parse les fichiers XML avec le format personnalisé du site IUT
- Convertit les balises XML (`<lien>`, `<cadre>`, `<cellule>`, etc.) en HTML
- Remplace les liens absolus par des liens relatifs
- Convertit les références `.xml` en `.html`
- Génère des fichiers HTML modernes avec CSS intégré

**Usage :**
```bash
# Conversion normale
python scripts/xml_to_html_converter.py sortie

# Mode simulation (aucune modification)
python scripts/xml_to_html_converter.py sortie --dry-run
```

**Exemple :**
```bash
# Convertir tous les fichiers XML dans le dossier sortie
python scripts/xml_to_html_converter.py sortie

# Les fichiers XML seront convertis en HTML avec le même nom
# Exemple: pedago/index.xml → pedago/index.html
```

---

### 2. `fix_links.py` - Adaptation des liens uniquement

Adapte les liens dans les fichiers HTML/XML existants sans faire de conversion de structure.

**Fonctionnalités :**
- Remplace les liens absolus (`https://diw.iut.univ-lehavre.fr/...`) par des liens relatifs
- Convertit les chemins Windows (`C:\Users\...`) en liens relatifs
- Transforme les extensions `.xml` en `.html`
- Traite tous les fichiers HTML, XML, HTM, XHTML

**Usage :**
```bash
# Adaptation normale
python scripts/fix_links.py sortie

# Mode simulation (aucune modification)
python scripts/fix_links.py sortie --dry-run
```

**Exemple :**
```bash
# Adapter tous les liens dans le dossier sortie
python scripts/fix_links.py sortie
```

---

## Workflow recommandé

### Option A : Conversion complète (recommandée)

Pour convertir les XML et adapter les liens en une seule étape :

```bash
# 1. Tester d'abord en mode dry-run
python scripts/xml_to_html_converter.py sortie --dry-run

# 2. Lancer la conversion réelle
python scripts/xml_to_html_converter.py sortie
```

### Option B : Deux étapes séparées

Si vous préférez séparer la conversion et l'adaptation des liens :

```bash
# 1. Convertir les XML en HTML
python scripts/xml_to_html_converter.py sortie

# 2. Adapter tous les liens (y compris dans les HTML existants)
python scripts/fix_links.py sortie
```

---

## Exemples de transformations

### Conversion XML → HTML

**Avant (XML) :**
```xml
<cadre type="double">
    <cellule titre="Réglement">
        <para>
            <puce /> <lien image="aucune" dest="./reglement/charte.xml">Charte</lien> <br />
        </para>
    </cellule>
</cadre>
```

**Après (HTML) :**
```html
<div class="cadre cadre-double">
    <div class="cellule">
        <div class="cellule-titre">Réglement</div>
        <p>
            <span class="puce"></span>
            <a href="./reglement /charte.html">Charte</a>
            <br>
        </p>
    </div>
</div>
```

### Adaptation des liens

**Avant :**
```html
<a href="https://diw.iut.univ-lehavre.fr/pedago/info1/index.xml">Info 1</a>
<a href="C:\Users\R_BAR\Desktop\projet\IUT2\IUT2\sortie\pedago\info2\index.xml">Info 2</a>
```

**Après :**
```html
<a href="./info1/index.html">Info 1</a>
<a href="./info2/index.html">Info 2</a>
```

---

## Logs et débogage

Les deux scripts génèrent des fichiers de log :

- `xml_converter.log` - Logs de la conversion XML → HTML
- `fix_links.log` - Logs de l'adaptation des liens

Ces fichiers contiennent des informations détaillées sur chaque opération effectuée.

---

## Dépendances

Aucune dépendance externe requise, seulement la bibliothèque standard Python 3.

**Modules utilisés :**
- `os`, `sys`, `re` - Manipulation de fichiers et regex
- `pathlib` - Gestion des chemins
- `logging` - Journalisation
- `urllib.parse` - Parsing d'URLs

---

## Notes importantes

1. **Toujours tester avec `--dry-run` d'abord** pour voir quelles modifications seront effectuées
2. Les fichiers originaux ne sont **pas sauvegardés** - faites une copie si nécessaire
3. Les liens externes (hors domaine) sont conservés tels quels
4. Les chemins relatifs existants sont préservés autant que possible
5. Le CSS est intégré directement dans les fichiers HTML générés

---

## Troubleshooting

### Problème : "Impossible de lire le fichier"
- Vérifiez les permissions du fichier
- Assurez-vous que le fichier n'est pas ouvert dans un autre programme

### Problème : "n'est pas un répertoire valide"
- Vérifiez le chemin fourni
- Utilisez un chemin absolu ou relatif correct

### Problème : Liens incorrects après conversion
- Vérifiez la structure des dossiers
- Les liens relatifs dépendent de la position du fichier dans l'arborescence
- Utilisez le mode `--dry-run` et vérifiez les logs

---

## Support

Pour tout problème, consultez les fichiers de log générés par les scripts.

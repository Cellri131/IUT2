# ✅ Checklist de vérification du workflow

## 1. Vérifier que GitHub Pages est activé

1. Allez dans **Settings** > **Pages** de votre dépôt
2. Vérifiez que :
   - **Source** : Deploy from a branch
   - **Branch** : `gh-pages` / `(root)`
   - **Save** si ce n'est pas déjà fait

## 2. Vérifier les permissions du workflow

1. Allez dans **Settings** > **Actions** > **General**
2. Scrollez jusqu'à **Workflow permissions**
3. Cochez **"Read and write permissions"**
4. Cochez **"Allow GitHub Actions to create and approve pull requests"**
5. Cliquez sur **Save**

## 3. Relancer le workflow

1. Allez dans **Actions**
2. Sélectionnez le dernier workflow (celui qui a "échoué")
3. Cliquez sur **Re-run jobs** > **Re-run all jobs**

## 4. Vérifier les logs pendant l'exécution

Surveillez particulièrement ces étapes :

### ✓ Étape "Crawl site"
Doit afficher :
```
==> Crawl de https://diw.iut.univ-lehavre.fr/pedago/index.xml
...
==> XXX fichier(s) téléchargé(s)
```

### ✓ Étape "Verify crawl results"
Doit afficher :
```
==> Nombre de fichiers téléchargés :
XXX
```
Si vous voyez **0**, le crawl a échoué.

### ✓ Étape "Deploy to GitHub Pages"
Doit afficher :
```
[gh-pages xxxxx] sync: mise à jour miroir
```

## 5. Télécharger les artifacts

1. Dans l'onglet **Actions**, cliquez sur le workflow terminé
2. Scrollez en bas de la page
3. Téléchargez **"crawl-reports-XXX"**
4. Ouvrez `crawl_results.json` ou `crawler.log` pour voir les détails

## 6. Vérifier le déploiement

Une fois le workflow terminé avec succès :

1. Allez dans **Settings** > **Pages**
2. Vous devriez voir : **"Your site is live at https://[username].github.io/[repo]/"**
3. Cliquez sur ce lien pour voir le site

## 7. Si ça ne marche toujours pas

### Vérifier la branche gh-pages

1. Dans le dépôt, changez de branche (menu déroulant en haut à gauche)
2. Sélectionnez `gh-pages`
3. Vérifiez que des fichiers sont bien là

### Si la branche gh-pages est vide ou n'existe pas

Le déploiement a échoué. Vérifiez :

1. Les **permissions** (étape 2 ci-dessus)
2. Les **logs** de l'étape "Deploy to GitHub Pages"
3. Que `site/diw.iut.univ-lehavre.fr/` contient bien des fichiers

## Commandes de debug utiles

Si vous voulez tester localement avant de pousser sur GitHub :

```bash
cd iut/IUT2

# Lancer le crawler
bash scripts/crawl.sh

# Vérifier les résultats
ls -lah site/
ls -lah site/diw.iut.univ-lehavre.fr/
find site/diw.iut.univ-lehavre.fr -type f | wc -l
```

## Problèmes courants

### ❌ "Error: Process completed with exit code 1"

Causes possibles :
- Identifiants incorrects (SITE_USER / SITE_PASSWORD)
- Le dossier `site/diw.iut.univ-lehavre.fr` n'existe pas
- Erreur Python (voir crawler.log)

### ❌ Aucun fichier dans gh-pages

Causes possibles :
- Permissions insuffisantes
- GitHub Pages désactivé
- Le dossier `site/diw.iut.univ-lehavre.fr` est vide

### ❌ 900+ fichiers téléchargés mais site vide

Le crawl a réussi mais le déploiement a échoué. Vérifiez :
- L'étape "Deploy to GitHub Pages" dans les logs
- Les permissions du workflow
- Que GitHub Pages est activé

---

**Note** : Après avoir fait des modifications, attendez la fin complète du workflow (cela peut prendre 10-20 minutes) avant de vérifier les résultats.

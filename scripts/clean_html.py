#!/usr/bin/env python3
"""
clean_html.py - Nettoie les fichiers HTML et ajoute le CSS personnalisé

Ce script:
1. Supprime toutes les balises <style> et attributs style inline
2. Ajoute un lien vers le fichier CSS externe (style.css)
3. Ajoute un bouton retour en haut de chaque page
4. Enveloppe le contenu dans un conteneur

Usage:
    python scripts/clean_html.py <input_dir>
"""

import os
import sys
import logging
import re
from pathlib import Path
from bs4 import BeautifulSoup

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clean_html.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HTMLCleaner:
    """Nettoie les fichiers HTML et ajoute le style personnalisé."""

    def __init__(self, input_dir: str):
        self.input_dir = Path(input_dir)
        self.cleaned_count = 0
        self.error_count = 0

    def clean_all(self):
        """Nettoie tous les fichiers HTML trouvés."""
        logger.info(f"Recherche des fichiers HTML dans {self.input_dir}")

        html_files = list(self.input_dir.rglob("*.html"))
        logger.info(f"Trouvé {len(html_files)} fichier(s) HTML")

        for html_file in html_files:
            try:
                self.clean_file(html_file)
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage de {html_file}: {e}")
                self.error_count += 1

        logger.info(f"\n{'='*60}")
        logger.info(f"RÉSUMÉ:")
        logger.info(f"  Fichiers nettoyés: {self.cleaned_count}")
        logger.info(f"  Erreurs: {self.error_count}")
        logger.info(f"{'='*60}")

    def clean_file(self, html_file: Path):
        """Nettoie un fichier HTML."""
        logger.debug(f"Nettoyage: {html_file.relative_to(self.input_dir)}")

        # Lire le fichier
        with open(html_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Parser avec BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')

        # 1. Supprimer toutes les balises <style>
        for style_tag in soup.find_all('style'):
            style_tag.decompose()

        # 2. Supprimer tous les attributs style inline
        for tag in soup.find_all(style=True):
            del tag['style']

        # 2b. Supprimer les attributs de style ancien (bgcolor, text, link, vlink, etc.)
        for tag in soup.find_all():
            for attr in ['bgcolor', 'text', 'link', 'vlink', 'alink', 'color', 'width', 'height', 'align', 'valign']:
                if tag.has_attr(attr):
                    del tag[attr]

        # 3. Ajouter le lien vers le CSS externe dans le <head>
        head = soup.find('head')
        if head:
            # Calculer le chemin relatif vers pedago/css/rb.css
            depth = len(html_file.relative_to(self.input_dir).parts) - 1

            # Déterminer si on est dans pedago ou dans un sous-dossier
            relative_path = html_file.relative_to(self.input_dir)
            if relative_path.parts[0] == 'pedago':
                # On est dans pedago, calculer depuis la position actuelle
                css_path = '../' * (depth - 1) + 'css/rb.css'
            else:
                # On est à la racine ou ailleurs
                css_path = 'pedago/css/rb.css'

            # Vérifier si le lien CSS existe déjà
            existing_link = head.find('link', {'rel': 'stylesheet'})
            if existing_link:
                existing_link['href'] = css_path
            else:
                # Créer le lien CSS
                link_tag = soup.new_tag('link', rel='stylesheet', href=css_path)
                head.append(link_tag)

        # 4. Ajouter le bouton retour et envelopper le contenu
        body = soup.find('body')
        if body:
            # Créer le bouton retour
            back_button = soup.new_tag('a', href='javascript:history.back()')
            back_button['class'] = 'back-button'
            back_button.string = '← Retour'

            # Créer le conteneur
            container = soup.new_tag('div')
            container['class'] = 'container'

            # Déplacer tout le contenu du body dans le conteneur
            for child in list(body.children):
                container.append(child.extract())

            # Vider le body et ajouter le bouton + conteneur
            body.clear()
            body.append(back_button)
            body.append(container)

        # 5. Nettoyer les redirections meta inutiles (qui pointent vers .xml)
        meta_refresh = soup.find('meta', {'http-equiv': 'refresh'})
        if meta_refresh and meta_refresh.has_attr('content'):
            content_attr = meta_refresh['content']
            # Supprimer si redirection vers .xml
            if '.xml' in content_attr.lower():
                meta_refresh.decompose()

        # Sauvegarder le fichier nettoyé
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))

        logger.debug(f"  ✓ Nettoyé: {html_file.name}")
        self.cleaned_count += 1


def main():
    """Point d'entrée principal."""
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <input_dir>")
        print()
        print("Exemple:")
        print(f"  python {sys.argv[0]} ./sortie")
        sys.exit(1)

    input_dir = sys.argv[1]

    if not os.path.isdir(input_dir):
        logger.error(f"Erreur: {input_dir} n'est pas un répertoire valide")
        sys.exit(1)

    logger.info(f"{'='*60}")
    logger.info(f"NETTOYAGE HTML + AJOUT CSS PERSONNALISÉ")
    logger.info(f"Répertoire: {input_dir}")
    logger.info(f"{'='*60}\n")

    cleaner = HTMLCleaner(input_dir)
    cleaner.clean_all()


if __name__ == "__main__":
    main()

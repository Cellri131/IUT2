#!/usr/bin/env python3
"""
setup_custom_css.py - Configure le CSS personnalisé et nettoie tous les styles

Ce script:
1. Supprime tout le contenu de sortie/pedago/css
2. Copie rb.css depuis assets vers ce dossier
3. Retire tous les styles des pages HTML
4. Ajoute le lien vers rb.css dans toutes les pages

Usage:
    python scripts/setup_custom_css.py <input_dir>
"""

import os
import sys
import logging
import shutil
from pathlib import Path
from bs4 import BeautifulSoup

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('setup_css.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)



class CSSSetup:
    """Configure le CSS personnalisé."""

    def __init__(self, input_dir: str):
        self.input_dir = Path(input_dir)
        self.css_dir = self.input_dir / "pedago" / "css"
        self.assets_dir = Path(__file__).parent.parent / "assets"
        self.cleaned_count = 0
        self.error_count = 0

    def setup_all(self):
        """Configure tout le CSS."""
        logger.info(f"Configuration du CSS personnalisé dans {self.input_dir}")

        # Étape 1: Nettoyer et créer le dossier CSS
        self._setup_css_directory()

        # Étape 2: Créer le fichier rb.css
        self._create_custom_css()

        # Étape 3: Nettoyer tous les fichiers HTML
        self._clean_all_html_files()

        logger.info(f"\n{'='*60}")
        logger.info(f"RÉSUMÉ:")
        logger.info(f"  CSS créé: {self.css_dir / 'rb.css'}")
        logger.info(f"  Fichiers HTML nettoyés: {self.cleaned_count}")
        logger.info(f"  Erreurs: {self.error_count}")
        logger.info(f"{'='*60}")

    def _setup_css_directory(self):
        """Supprime et recrée le dossier CSS."""
        logger.info("Nettoyage du dossier CSS...")

        if self.css_dir.exists():
            # Supprimer tout le contenu
            shutil.rmtree(self.css_dir)
            logger.info(f"  ✓ Dossier CSS supprimé")

        # Recréer le dossier
        self.css_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"  ✓ Dossier CSS recréé")

    def _create_custom_css(self):
        """Copie les fichiers depuis assets (CSS, JS, scripts Python)."""
        logger.info("Copie des fichiers depuis assets...")

        # Liste des fichiers à copier
        files_to_copy = [
            ('rb.css', True),           # (nom, obligatoire)
            ('rb.js', True),
        ]

        for filename, required in files_to_copy:
            source = self.assets_dir / filename
            dest = self.css_dir / filename

            if not source.exists():
                if required:
                    logger.error(f"Erreur: {source} n'existe pas!")
                    raise FileNotFoundError(f"Le fichier {filename} n'existe pas dans assets")
                else:
                    logger.warning(f"  ⚠ {filename} non trouvé dans assets")
                    continue

            shutil.copy2(source, dest)
            logger.info(f"  ✓ Fichier {filename} copié")

    def _clean_all_html_files(self):
        """Nettoie tous les fichiers HTML."""
        logger.info("Nettoyage des fichiers HTML...")

        html_files = list(self.input_dir.rglob("*.html"))
        logger.info(f"Trouvé {len(html_files)} fichier(s) HTML à nettoyer")

        for html_file in html_files:
            try:
                self._clean_html_file(html_file)
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage de {html_file}: {e}")
                self.error_count += 1

    def _clean_html_file(self, html_file: Path):
        """Nettoie un fichier HTML."""
        logger.debug(f"  Nettoyage: {html_file.relative_to(self.input_dir)}")

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

        # 3. Supprimer les attributs de style ancien
        for tag in soup.find_all():
            for attr in ['bgcolor', 'text', 'link', 'vlink', 'alink', 'color', 'width', 'height', 'align', 'valign']:
                if tag.has_attr(attr):
                    del tag[attr]

        # 4. Supprimer tous les liens CSS existants
        head = soup.find('head')
        if head:
            for link in head.find_all('link', {'rel': 'stylesheet'}):
                link.decompose()

            # Ajouter le nouveau lien vers rb.css
            # Calculer le chemin relatif depuis le fichier actuel vers pedago/css/rb.css
            relative_path = html_file.relative_to(self.input_dir)

            # Compter le nombre de niveaux pour remonter
            if 'pedago' in relative_path.parts:
                # On est dans pedago ou un sous-dossier
                pedago_index = relative_path.parts.index('pedago')
                # Nombre de dossiers entre pedago et le fichier (sans compter le fichier lui-même)
                depth = len(relative_path.parts) - pedago_index - 2
                # Générer le chemin: ../ pour chaque niveau
                if depth > 0:
                    css_path = '../' * depth + 'css/rb.css'
                else:
                    css_path = 'css/rb.css'
            else:
                # On est à la racine
                css_path = 'pedago/css/rb.css'

            # Créer le lien CSS
            link_tag = soup.new_tag('link', rel='stylesheet', href=css_path)
            head.append(link_tag)

            # Ajouter le script JS
            if 'pedago' in relative_path.parts:
                pedago_index = relative_path.parts.index('pedago')
                depth = len(relative_path.parts) - pedago_index - 2
                if depth > 0:
                    js_path = '../' * depth + 'css/rb.js'
                else:
                    js_path = 'css/rb.js'
            else:
                js_path = 'pedago/css/rb.js'

            # Vérifier si le script existe déjà
            existing_script = head.find('script', {'src': lambda x: x and 'rb.js' in x})
            if not existing_script:
                script_tag = soup.new_tag('script', src=js_path)
                script_tag['defer'] = ''
                head.append(script_tag)

            # Ajouter la meta tag avec l'URL originale
            # Déduire l'URL originale depuis le chemin du fichier
            original_url_meta = soup.find('meta', {'name': 'original-url'})
            if not original_url_meta:
                # Construire l'URL originale
                rel_path = html_file.relative_to(self.input_dir)
                url_path = '/'.join(rel_path.parts)
                # Remplacer .html par .xml pour les fichiers convertis
                if url_path.endswith('.html'):
                    # Vérifier si c'était un fichier XML converti
                    xml_path = html_file.with_suffix('.xml')
                    if not xml_path.exists():
                        url_path = url_path[:-5] + '.xml'
                original_url = f'https://diw.iut.univ-lehavre.fr/{url_path}'
                meta_tag = soup.new_tag('meta')
                meta_tag['name'] = 'original-url'
                meta_tag['content'] = original_url
                head.insert(0, meta_tag)

        # 5. Ajouter le conteneur si pas déjà présent (pas de button retour, le JS va les créer)
        body = soup.find('body')
        if body:
            # Vérifier si le conteneur existe déjà
            container = body.find('div', class_='container')
            if not container:
                # Créer le conteneur
                container = soup.new_tag('div')
                container['class'] = 'container'

                # Déplacer tout le contenu du body dans le conteneur
                for child in list(body.children):
                    container.append(child.extract())

                # Ajouter le conteneur au body
                body.append(container)

        # 6. Nettoyer les redirections meta inutiles
        meta_refresh = soup.find('meta', {'http-equiv': 'refresh'})
        if meta_refresh and meta_refresh.has_attr('content'):
            content_attr = meta_refresh['content']
            if '.xml' in content_attr.lower():
                meta_refresh.decompose()

        # Sauvegarder le fichier
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))

        logger.debug(f"    ✓ Nettoyé")
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
    logger.info(f"CONFIGURATION CSS PERSONNALISÉ")
    logger.info(f"Répertoire: {input_dir}")
    logger.info(f"{'='*60}\n")

    setup = CSSSetup(input_dir)
    setup.setup_all()


if __name__ == "__main__":
    main()

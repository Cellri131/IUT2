#!/usr/bin/env python3
"""
xml_to_html_converter.py - Convertit les fichiers XML personnalisés en HTML
et adapte les liens absolus en liens relatifs.

Ce script :
1. Parse les fichiers XML avec le format personnalisé du site IUT
2. Convertit les balises XML en HTML standard
3. Remplace les liens absolus (URLs complètes) par des liens relatifs locaux
4. Sauvegarde les fichiers HTML convertis

Usage:
    python scripts/xml_to_html_converter.py <input_dir> [--dry-run]
"""

import os
import re
import sys
import logging
from pathlib import Path
from xml.etree import ElementTree as ET
from urllib.parse import urljoin, urlparse, unquote
from typing import Dict, List, Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('xml_converter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# URL de base du site source
BASE_URL = "https://diw.iut.univ-lehavre.fr/"
BASE_DOMAIN = "diw.iut.univ-lehavre.fr"


class XMLToHTMLConverter:
    """Convertisseur de XML personnalisé vers HTML standard."""

    def __init__(self, input_dir: str, dry_run: bool = False):
        self.input_dir = Path(input_dir)
        self.dry_run = dry_run
        self.converted_count = 0
        self.error_count = 0
        self.url_replacements = {}

    def convert_all(self):
        """Convertit tous les fichiers XML trouvés dans le répertoire."""
        logger.info(f"Recherche des fichiers XML dans {self.input_dir}")

        xml_files = list(self.input_dir.rglob("*.xml"))
        logger.info(f"Trouvé {len(xml_files)} fichier(s) XML")

        for xml_file in xml_files:
            try:
                self.convert_file(xml_file)
            except Exception as e:
                logger.error(f"Erreur lors de la conversion de {xml_file}: {e}")
                self.error_count += 1

        # Deuxième passe: adapter les liens dans tous les fichiers HTML
        logger.info("\n=== Adaptation des liens dans les fichiers HTML ===")
        self.fix_links_in_html_files()

        logger.info(f"\n{'='*60}")
        logger.info(f"RÉSUMÉ:")
        logger.info(f"  Fichiers convertis: {self.converted_count}")
        logger.info(f"  Erreurs: {self.error_count}")
        logger.info(f"  Mode: {'DRY-RUN (aucune modification)' if self.dry_run else 'PRODUCTION'}")
        logger.info(f"{'='*60}")

    def convert_file(self, xml_file: Path):
        """Convertit un fichier XML en HTML."""
        logger.info(f"Traitement: {xml_file.relative_to(self.input_dir)}")

        # Lire le contenu XML brut (ne pas parser car format non-standard)
        with open(xml_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Extraire les métadonnées du document
        metadata = self.extract_metadata(content)

        # Convertir le contenu XML en HTML
        html_content = self.convert_xml_to_html(content, metadata)

        # Remplacer les liens absolus par des liens relatifs
        html_content = self.replace_absolute_links(html_content, xml_file)

        # Déterminer le nom du fichier de sortie
        html_file = xml_file.with_suffix('.html')

        if not self.dry_run:
            # Sauvegarder le fichier HTML
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"  -> Converti en {html_file.name}")
        else:
            logger.info(f"  -> [DRY-RUN] Serait converti en {html_file.name}")

        self.converted_count += 1

    def extract_metadata(self, content: str) -> Dict[str, str]:
        """Extrait les métadonnées du document XML."""
        metadata = {
            'title': 'Document',
            'year': '',
            'subject': '',
            'style': 'java'
        }

        # Extraire l'année
        year_match = re.search(r'annee\s*=\s*"([^"]+)"', content)
        if year_match:
            metadata['year'] = year_match.group(1)

        # Extraire la matière
        matiere_match = re.search(r'matiere\s*=\s*"([^"]+)"', content)
        if matiere_match:
            metadata['subject'] = matiere_match.group(1)
            metadata['title'] = matiere_match.group(1)

        # Extraire le style
        style_match = re.search(r'style\s*=\s*"([^"]+)"', content)
        if style_match:
            metadata['style'] = style_match.group(1)

        return metadata

    def convert_xml_to_html(self, content: str, metadata: Dict[str, str]) -> str:
        """Convertit le contenu XML en HTML."""

        # Créer l'en-tête HTML
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata['title']}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 20px;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .cadre {{
            border: 1px solid #ddd;
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
        }}
        .cadre-double {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .cellule {{
            padding: 10px;
        }}
        .cellule-titre {{
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 10px;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        td {{
            padding: 8px;
            vertical-align: top;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        .center {{
            text-align: center;
        }}
        a {{
            color: #0066cc;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .puce {{
            display: inline-block;
            margin-right: 5px;
        }}
        .puce::before {{
            content: "• ";
        }}
        h1 {{ font-size: 1.8em; margin-top: 20px; }}
        h2 {{ font-size: 1.4em; margin-top: 15px; }}
        h3 {{ font-size: 1.2em; margin-top: 10px; }}
        .bold {{ font-weight: bold; }}
        .italic {{ font-style: italic; }}
        .fixed {{ font-family: monospace; background-color: #f0f0f0; padding: 2px 5px; }}
    </style>
</head>
<body>
"""

        # Convertir les balises XML en HTML
        body = content

        # Supprimer les déclarations XML et DOCTYPE
        body = re.sub(r'<\?xml[^?]*\?>', '', body)
        body = re.sub(r'<!DOCTYPE[^>]*>', '', body)
        body = re.sub(r'<\?xml-stylesheet[^?]*\?>', '', body)

        # Supprimer la balise <document>
        body = re.sub(r'<document[^>]*>', '', body)
        body = re.sub(r'</document>', '', body)

        # Supprimer les balises propriete et entete
        body = re.sub(r'<propriete[^>]*/?>', '', body)
        body = re.sub(r'<entete[^>]*>.*?</entete>', '', body, flags=re.DOTALL)
        body = re.sub(r'<entete-gene[^>]*>.*?</entete-gene>', '', body, flags=re.DOTALL)

        # Convertir les cadres
        body = self.convert_cadres(body)

        # Convertir les titres
        body = re.sub(r'<titre\s+niveau\s*=\s*"1"[^>]*>(.*?)</titre>', r'<h1>\1</h1>', body)
        body = re.sub(r'<titre\s+niveau\s*=\s*"2"[^>]*>(.*?)</titre>', r'<h2>\1</h2>', body)
        body = re.sub(r'<titre\s+niveau\s*=\s*"3"[^>]*>(.*?)</titre>', r'<h3>\1</h3>', body)

        # Convertir les liens
        body = self.convert_links(body)

        # Convertir les images
        body = self.convert_images(body)

        # Convertir les tableaux
        body = self.convert_tables(body)

        # Convertir les paragraphes
        body = re.sub(r'<para[^>]*>', '<p>', body)
        body = re.sub(r'</para>', '</p>', body)

        # Convertir les balises de mise en forme
        body = re.sub(r'<g>', '<strong class="bold">', body)
        body = re.sub(r'</g>', '</strong>', body)
        body = re.sub(r'<i>', '<em class="italic">', body)
        body = re.sub(r'</i>', '</em>', body)
        body = re.sub(r'<fix>', '<code class="fixed">', body)
        body = re.sub(r'</fix>', '</code>', body)
        body = re.sub(r'<coul[^>]*>', '', body)
        body = re.sub(r'</coul>', '', body)

        # Convertir les puces
        body = re.sub(r'<puce\s*/>', '<span class="puce"></span>', body)

        # Convertir <br /> et <br/>
        body = re.sub(r'<br\s*/>', '<br>', body)

        # Convertir <center>
        body = re.sub(r'<center>', '<div class="center">', body)
        body = re.sub(r'</center>', '</div>', body)

        # Nettoyer les caractères spéciaux
        body = body.replace('¨', '&nbsp;')
        body = body.replace('&#x02192;', '→')

        # Supprimer les commentaires XML
        body = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL)

        html += body
        html += "\n</body>\n</html>"

        return html

    def convert_cadres(self, content: str) -> str:
        """Convertit les balises <cadre> en divs HTML."""

        def replace_cadre(match):
            attrs = match.group(1)
            cadre_content = match.group(2)

            # Déterminer le type de cadre
            type_match = re.search(r'type\s*=\s*"([^"]+)"', attrs)
            cadre_type = type_match.group(1) if type_match else 'simple'

            if cadre_type == 'double':
                # Convertir les cellules en colonnes
                cadre_content = self.convert_cellules(cadre_content)
                return f'<div class="cadre cadre-double">{cadre_content}</div>'
            elif cadre_type == 'vide':
                return f'<div class="cadre-vide">{cadre_content}</div>'
            else:
                cadre_content = self.convert_cellules(cadre_content)
                return f'<div class="cadre">{cadre_content}</div>'

        return re.sub(r'<cadre([^>]*)>(.*?)</cadre>', replace_cadre, content, flags=re.DOTALL)

    def convert_cellules(self, content: str) -> str:
        """Convertit les balises <cellule> en divs HTML."""

        def replace_cellule(match):
            attrs = match.group(1)
            cellule_content = match.group(2)

            # Extraire le titre s'il existe
            titre_match = re.search(r'titre\s*=\s*"([^"]+)"', attrs)
            titre = titre_match.group(1) if titre_match else ''

            html = '<div class="cellule">'
            if titre:
                html += f'<div class="cellule-titre">{titre}</div>'
            html += cellule_content
            html += '</div>'

            return html

        return re.sub(r'<cellule([^>]*)>(.*?)</cellule>', replace_cellule, content, flags=re.DOTALL)

    def convert_links(self, content: str) -> str:
        """Convertit les balises <lien> en liens HTML."""

        def replace_lien(match):
            attrs = match.group(1)
            link_text = match.group(2)

            # Extraire l'attribut dest
            dest_match = re.search(r'dest\s*=\s*"([^"]+)"', attrs)
            if not dest_match:
                return link_text  # Pas de destination, retourner juste le texte

            dest = dest_match.group(1)

            # Extraire l'attribut image (optionnel)
            image_match = re.search(r'image\s*=\s*"([^"]+)"', attrs)
            has_image = image_match and image_match.group(1) != 'aucune'

            return f'<a href="{dest}">{link_text}</a>'

        return re.sub(r'<lien([^>]*)>(.*?)</lien>', replace_lien, content, flags=re.DOTALL)

    def convert_images(self, content: str) -> str:
        """Convertit les balises <image> en balises img HTML."""

        def replace_image(match):
            attrs = match.group(1)

            # Extraire l'attribut fichier
            fichier_match = re.search(r'fichier\s*=\s*"([^"]+)"', attrs)
            if not fichier_match:
                return ''

            fichier = fichier_match.group(1)

            # Extraire alt si présent
            alt_match = re.search(r'alt\s*=\s*"([^"]+)"', attrs)
            alt = alt_match.group(1) if alt_match else ''

            return f'<img src="{fichier}" alt="{alt}">'

        return re.sub(r'<image([^>]*)/>', replace_image, content)

    def convert_tables(self, content: str) -> str:
        """Convertit les balises <tableau>, <ligne>, <case> en HTML."""

        # Convertir les tableaux
        content = re.sub(r'<tableau[^>]*>', '<table>', content)
        content = re.sub(r'</tableau>', '</table>', content)

        # Convertir les lignes
        content = re.sub(r'<ligne[^>]*>', '<tr>', content)
        content = re.sub(r'</ligne>', '</tr>', content)

        # Convertir les cases
        content = re.sub(r'<case[^>]*>', '<td>', content)
        content = re.sub(r'</case>', '</td>', content)

        return content

    def replace_absolute_links(self, content: str, current_file: Path) -> str:
        """Remplace les liens absolus par des liens relatifs."""

        def replace_link(match):
            prefix = match.group(1)
            url = match.group(2)
            suffix = match.group(3)

            # Si c'est une URL externe (commençant par http/https)
            if url.startswith('http://') or url.startswith('https://'):
                parsed = urlparse(url)

                # Si c'est une URL du domaine cible, la convertir en lien relatif
                if BASE_DOMAIN in parsed.netloc:
                    # Extraire le chemin relatif
                    relative_path = unquote(parsed.path.lstrip('/'))

                    # Calculer le chemin relatif depuis le fichier actuel
                    current_dir = current_file.parent
                    input_dir_depth = len(current_file.relative_to(self.input_dir).parts) - 1

                    # Créer le chemin relatif
                    if relative_path:
                        # Remonter d'autant de niveaux que nécessaire
                        prefix_path = '../' * input_dir_depth
                        new_url = prefix_path + relative_path
                    else:
                        new_url = '../' * input_dir_depth + 'index.html'

                    logger.debug(f"    Lien converti: {url} -> {new_url}")
                    return f'{prefix}{new_url}{suffix}'

            # Sinon, garder le lien tel quel
            return match.group(0)

        # Remplacer dans les attributs href et src
        content = re.sub(r'(href\s*=\s*")([^"]+)(")', replace_link, content, flags=re.IGNORECASE)
        content = re.sub(r"(href\s*=\s*')([^']+)(')", replace_link, content, flags=re.IGNORECASE)
        content = re.sub(r'(src\s*=\s*")([^"]+)(")', replace_link, content, flags=re.IGNORECASE)
        content = re.sub(r"(src\s*=\s*')([^']+)(')", replace_link, content, flags=re.IGNORECASE)

        return content

    def fix_links_in_html_files(self):
        """Deuxième passe: adapter les liens dans tous les fichiers HTML."""
        html_files = list(self.input_dir.rglob("*.html"))
        logger.info(f"Adaptation des liens dans {len(html_files)} fichier(s) HTML")

        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()

                # Remplacer les liens absolus
                new_content = self.replace_absolute_links(content, html_file)

                # Adapter les liens .xml en .html
                new_content = re.sub(r'\.xml(["\'])', r'.html\1', new_content)

                if not self.dry_run and new_content != content:
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    logger.debug(f"  Liens adaptés dans {html_file.name}")

            except Exception as e:
                logger.error(f"Erreur lors de l'adaptation des liens dans {html_file}: {e}")


def main():
    """Point d'entrée principal."""
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <input_dir> [--dry-run]")
        print()
        print("Exemple:")
        print(f"  python {sys.argv[0]} ./sortie")
        print(f"  python {sys.argv[0]} ./sortie --dry-run")
        sys.exit(1)

    input_dir = sys.argv[1]
    dry_run = '--dry-run' in sys.argv

    if not os.path.isdir(input_dir):
        logger.error(f"Erreur: {input_dir} n'est pas un répertoire valide")
        sys.exit(1)

    logger.info(f"{'='*60}")
    logger.info(f"CONVERSION XML -> HTML")
    logger.info(f"Répertoire: {input_dir}")
    logger.info(f"Mode: {'DRY-RUN (simulation)' if dry_run else 'PRODUCTION'}")
    logger.info(f"{'='*60}\n")

    converter = XMLToHTMLConverter(input_dir, dry_run)
    converter.convert_all()


if __name__ == "__main__":
    main()

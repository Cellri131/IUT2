#!/usr/bin/env python3
"""
fix_links.py - Adapte les liens absolus en liens relatifs

Ce script parcourt tous les fichiers HTML/XML et remplace:
1. Les liens absolus du site (https://diw.iut.univ-lehavre.fr/...) par des liens relatifs
2. Les références .xml par .html
3. Les chemins Windows (C:\...) par des chemins relatifs

Usage:
    python scripts/fix_links.py <directory> [--dry-run]
"""

import os
import re
import sys
import logging
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Tuple, Set

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_links.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurations
BASE_URL = "https://diw.iut.univ-lehavre.fr/"
BASE_DOMAIN = "diw.iut.univ-lehavre.fr"
FILE_EXTENSIONS = {'.html', '.xml', '.htm', '.xhtml'}


class LinkFixer:
    """Classe pour adapter les liens dans les fichiers."""

    def __init__(self, root_dir: str, dry_run: bool = False):
        self.root_dir = Path(root_dir).resolve()
        self.dry_run = dry_run
        self.files_processed = 0
        self.files_modified = 0
        self.links_replaced = 0
        self.errors = 0

    def process_all_files(self):
        """Traite tous les fichiers HTML/XML dans le répertoire."""
        logger.info(f"Recherche des fichiers dans {self.root_dir}")

        # Trouver tous les fichiers avec les extensions supportées
        files = []
        for ext in FILE_EXTENSIONS:
            files.extend(self.root_dir.rglob(f'*{ext}'))

        logger.info(f"Trouvé {len(files)} fichier(s) à traiter\n")

        for file_path in files:
            try:
                self.process_file(file_path)
            except Exception as e:
                logger.error(f"Erreur lors du traitement de {file_path}: {e}")
                self.errors += 1

        # Afficher le résumé
        self.print_summary()

    def process_file(self, file_path: Path):
        """Traite un fichier individuel."""
        logger.info(f"Traitement: {file_path.relative_to(self.root_dir)}")
        self.files_processed += 1

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                original_content = f.read()
        except Exception as e:
            logger.error(f"  Impossible de lire le fichier: {e}")
            self.errors += 1
            return

        # Traiter le contenu
        modified_content, replacements = self.fix_links_in_content(
            original_content,
            file_path
        )

        # Vérifier si des modifications ont été faites
        if modified_content != original_content:
            self.files_modified += 1
            self.links_replaced += replacements

            if not self.dry_run:
                # Sauvegarder le fichier modifié
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                    logger.info(f"  ✓ {replacements} lien(s) adapté(s)")
                except Exception as e:
                    logger.error(f"  Impossible d'écrire le fichier: {e}")
                    self.errors += 1
            else:
                logger.info(f"  [DRY-RUN] {replacements} lien(s) seraient adaptés")
        else:
            logger.debug(f"  Aucune modification nécessaire")

    def fix_links_in_content(self, content: str, current_file: Path) -> Tuple[str, int]:
        """
        Adapte tous les liens dans le contenu.

        Returns:
            Tuple[str, int]: (contenu modifié, nombre de remplacements)
        """
        modified_content = content
        replacement_count = 0

        # 1. Remplacer les URLs absolues du domaine par des liens relatifs
        modified_content, count1 = self.replace_absolute_urls(modified_content, current_file)
        replacement_count += count1

        # 2. Remplacer les chemins Windows absolus (C:\Users\...) par des liens relatifs
        modified_content, count2 = self.replace_windows_paths(modified_content, current_file)
        replacement_count += count2

        # 3. Convertir les extensions .xml en .html
        modified_content, count3 = self.replace_xml_extensions(modified_content)
        replacement_count += count3

        return modified_content, replacement_count

    def replace_absolute_urls(self, content: str, current_file: Path) -> Tuple[str, int]:
        """Remplace les URLs absolues du site par des liens relatifs."""
        count = 0

        def replace_url(match):
            nonlocal count
            prefix = match.group(1)
            url = match.group(2)
            suffix = match.group(3)

            # Vérifier si c'est une URL du domaine cible
            if BASE_DOMAIN in url:
                parsed = urlparse(url)
                path = unquote(parsed.path.lstrip('/'))

                # Calculer le chemin relatif
                relative_link = self.calculate_relative_path(current_file, path)

                if relative_link != url:
                    count += 1
                    logger.debug(f"    {url} -> {relative_link}")
                    return f'{prefix}{relative_link}{suffix}'

            return match.group(0)

        # Remplacer dans les attributs href, src, et dest
        patterns = [
            (r'(href\s*=\s*")([^"]+)(")', re.IGNORECASE),
            (r"(href\s*=\s*')([^']+)(')", re.IGNORECASE),
            (r'(src\s*=\s*")([^"]+)(")', re.IGNORECASE),
            (r"(src\s*=\s*')([^']+)(')", re.IGNORECASE),
            (r'(dest\s*=\s*")([^"]+)(")', re.IGNORECASE),
            (r"(dest\s*=\s*')([^']+)(')", re.IGNORECASE),
        ]

        for pattern, flags in patterns:
            content = re.sub(pattern, replace_url, content, flags=flags)

        return content, count

    def replace_windows_paths(self, content: str, current_file: Path) -> Tuple[str, int]:
        """Remplace les chemins Windows absoluts par des liens relatifs."""
        count = 0

        def replace_path(match):
            nonlocal count
            prefix = match.group(1)
            path_str = match.group(2)
            suffix = match.group(3)

            # Convertir le chemin Windows en Path
            try:
                # Normaliser le chemin (enlever \\?\\ si présent)
                clean_path = path_str.replace('\\\\?\\', '')
                abs_path = Path(clean_path)

                # Vérifier si le chemin est dans notre arborescence
                if abs_path.is_absolute():
                    try:
                        # Essayer de calculer le chemin relatif
                        rel_path = abs_path.relative_to(self.root_dir)

                        # Calculer le chemin relatif depuis le fichier actuel
                        relative_link = self.calculate_relative_path(current_file, str(rel_path))

                        # Convertir les backslashes en forward slashes pour le web
                        relative_link = relative_link.replace('\\', '/')

                        count += 1
                        logger.debug(f"    {path_str} -> {relative_link}")
                        return f'{prefix}{relative_link}{suffix}'
                    except ValueError:
                        # Le chemin n'est pas relatif à root_dir
                        pass
            except Exception as e:
                logger.debug(f"    Impossible de traiter le chemin {path_str}: {e}")

            return match.group(0)

        # Patterns pour les chemins Windows (C:\..., \\?\C:\...)
        patterns = [
            (r'(href\s*=\s*")((?:\\\\?\\\w:)?[^"]*\\[^"]+)(")', re.IGNORECASE),
            (r"(href\s*=\s*')((?:\\\\?\\\w:)?[^']*\\[^']+)(')", re.IGNORECASE),
            (r'(src\s*=\s*")((?:\\\\?\\\w:)?[^"]*\\[^"]+)(")', re.IGNORECASE),
            (r"(src\s*=\s*')((?:\\\\?\\\w:)?[^']*\\[^']+)(')", re.IGNORECASE),
        ]

        for pattern, flags in patterns:
            content = re.sub(pattern, replace_path, content, flags=flags)

        return content, count

    def replace_xml_extensions(self, content: str) -> Tuple[str, int]:
        """Convertit les extensions .xml en .html dans les liens."""
        # Compter les remplacements
        count = len(re.findall(r'(href|src|dest)\s*=\s*["\'][^"\']*\.xml["\']', content, re.IGNORECASE))

        # Remplacer .xml par .html dans les attributs
        patterns = [
            r'((?:href|src|dest)\s*=\s*"[^"]+)\.xml(")',
            r"((?:href|src|dest)\s*=\s*'[^']+)\.xml(')",
        ]

        for pattern in patterns:
            content = re.sub(pattern, r'\1.html\2', content, flags=re.IGNORECASE)

        if count > 0:
            logger.debug(f"    {count} extension(s) .xml -> .html")

        return content, count

    def calculate_relative_path(self, current_file: Path, target_path: str) -> str:
        """
        Calcule le chemin relatif depuis le fichier actuel vers le fichier cible.

        Args:
            current_file: Fichier actuel
            target_path: Chemin cible (relatif à root_dir)

        Returns:
            Chemin relatif
        """
        # Répertoire du fichier actuel
        current_dir = current_file.parent

        # Chemin absolu du fichier cible
        target_file = self.root_dir / target_path

        # Si le fichier cible n'a pas d'extension et n'existe pas,
        # essayer d'ajouter .html
        if not target_file.suffix and not target_file.exists():
            if (target_file / 'index.html').exists():
                target_file = target_file / 'index.html'
            elif target_file.with_suffix('.html').exists():
                target_file = target_file.with_suffix('.html')

        # Calculer le chemin relatif
        try:
            relative = os.path.relpath(target_file, current_dir)
            # Normaliser les séparateurs pour le web
            relative = relative.replace('\\', '/')
            return relative
        except ValueError:
            # Si on ne peut pas calculer de chemin relatif, retourner le chemin original
            return target_path.replace('\\', '/')

    def print_summary(self):
        """Affiche un résumé des opérations."""
        logger.info(f"\n{'='*60}")
        logger.info("RÉSUMÉ")
        logger.info(f"{'='*60}")
        logger.info(f"Fichiers traités:        {self.files_processed}")
        logger.info(f"Fichiers modifiés:       {self.files_modified}")
        logger.info(f"Liens adaptés:           {self.links_replaced}")
        logger.info(f"Erreurs:                 {self.errors}")
        logger.info(f"Mode:                    {'DRY-RUN (simulation)' if self.dry_run else 'PRODUCTION'}")
        logger.info(f"{'='*60}")


def main():
    """Point d'entrée principal."""
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <directory> [--dry-run]")
        print()
        print("Options:")
        print("  --dry-run    Simule les modifications sans les appliquer")
        print()
        print("Exemple:")
        print(f"  python {sys.argv[0]} ./sortie")
        print(f"  python {sys.argv[0]} ./sortie --dry-run")
        sys.exit(1)

    directory = sys.argv[1]
    dry_run = '--dry-run' in sys.argv

    if not os.path.isdir(directory):
        logger.error(f"Erreur: {directory} n'est pas un répertoire valide")
        sys.exit(1)

    logger.info(f"{'='*60}")
    logger.info("ADAPTATION DES LIENS")
    logger.info(f"Répertoire: {directory}")
    logger.info(f"Mode: {'DRY-RUN (simulation)' if dry_run else 'PRODUCTION'}")
    logger.info(f"{'='*60}\n")

    fixer = LinkFixer(directory, dry_run)
    fixer.process_all_files()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
download_images.py - Télécharge toutes les images référencées dans les fichiers HTML

Ce script:
1. Parse tous les fichiers HTML
2. Trouve toutes les balises <img>
3. Télécharge les images manquantes depuis le site source
4. Met à jour les chemins dans les fichiers HTML

Usage:
    python scripts/download_images.py <input_dir> <user> <password>
"""

import os
import sys
import logging
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import urllib3

# Supprimer les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_images.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://diw.iut.univ-lehavre.fr/"


class ImageDownloader:
    """Télécharge les images manquantes."""

    def __init__(self, input_dir: str, user: str, password: str):
        self.input_dir = Path(input_dir)
        self.user = user
        self.password = password
        self.session = self._create_session()
        self.downloaded_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def _create_session(self):
        """Crée une session avec authentification."""
        session = requests.Session()
        session.auth = HTTPBasicAuth(self.user, self.password)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        session.verify = False
        return session

    def download_all(self):
        """Télécharge toutes les images manquantes."""
        logger.info(f"Recherche des images dans {self.input_dir}")

        html_files = list(self.input_dir.rglob("*.html"))
        logger.info(f"Analyse de {len(html_files)} fichier(s) HTML")

        images_to_download = set()

        # Première passe: collecter toutes les images
        for html_file in html_files:
            try:
                images = self._extract_images(html_file)
                images_to_download.update(images)
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction des images de {html_file}: {e}")

        logger.info(f"Trouvé {len(images_to_download)} image(s) à vérifier")

        # Deuxième passe: télécharger les images manquantes
        for img_url, local_path in images_to_download:
            try:
                self._download_image(img_url, local_path)
            except Exception as e:
                logger.error(f"Erreur lors du téléchargement de {img_url}: {e}")
                self.error_count += 1

        logger.info(f"\n{'='*60}")
        logger.info(f"RÉSUMÉ:")
        logger.info(f"  Images téléchargées: {self.downloaded_count}")
        logger.info(f"  Images déjà présentes: {self.skipped_count}")
        logger.info(f"  Erreurs: {self.error_count}")
        logger.info(f"{'='*60}")

    def _extract_images(self, html_file: Path):
        """Extrait toutes les images d'un fichier HTML."""
        images = []

        with open(html_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')

        # Chercher dans les balises <img>
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src:
                images.extend(self._resolve_image_path(src, html_file))

        # Chercher aussi dans les attributs style (background-image)
        for tag in soup.find_all(style=True):
            style = tag['style']
            urls = re.findall(r'url\(["\']?([^"\'()]+)["\']?\)', style)
            for url in urls:
                images.extend(self._resolve_image_path(url, html_file))

        return images

    def _resolve_image_path(self, src: str, html_file: Path):
        """Résout le chemin d'une image et retourne (url, local_path)."""
        results = []

        if not src or src.startswith('data:'):
            return results

        # Convertir le chemin en URL absolue
        if src.startswith('http://') or src.startswith('https://'):
            img_url = src
        else:
            # Chemin relatif
            # Nettoyer le chemin (enlever ../ au début)
            clean_src = src.lstrip('./')

            # Construire l'URL absolue depuis BASE_URL
            img_url = urljoin(BASE_URL, clean_src)

        # Calculer le chemin local
        parsed = urlparse(img_url)
        path_parts = unquote(parsed.path.lstrip('/')).split('/')

        # Créer le chemin local
        local_path = self.input_dir / Path(*path_parts)

        results.append((img_url, local_path))
        return results

    def _download_image(self, img_url: str, local_path: Path):
        """Télécharge une image si elle n'existe pas déjà."""
        if local_path.exists():
            logger.debug(f"  Déjà présente: {local_path.name}")
            self.skipped_count += 1
            return

        logger.info(f"  Téléchargement: {img_url}")

        try:
            response = self.session.get(img_url, timeout=30)
            response.raise_for_status()

            # Créer le répertoire si nécessaire
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Sauvegarder l'image
            with open(local_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"    ✓ Sauvegardé: {local_path.relative_to(self.input_dir)}")
            self.downloaded_count += 1

        except requests.RequestException as e:
            logger.error(f"    ✗ Erreur: {e}")
            raise


def main():
    """Point d'entrée principal."""
    if len(sys.argv) < 4:
        print(f"Usage: python {sys.argv[0]} <input_dir> <user> <password>")
        print()
        print("Exemple:")
        print(f"  python {sys.argv[0]} ./sortie etInfo \"for(:)\"")
        sys.exit(1)

    input_dir = sys.argv[1]
    user = sys.argv[2]
    password = sys.argv[3]

    if not os.path.isdir(input_dir):
        logger.error(f"Erreur: {input_dir} n'est pas un répertoire valide")
        sys.exit(1)

    logger.info(f"{'='*60}")
    logger.info(f"TÉLÉCHARGEMENT DES IMAGES")
    logger.info(f"Répertoire: {input_dir}")
    logger.info(f"{'='*60}\n")

    downloader = ImageDownloader(input_dir, user, password)
    downloader.download_all()


if __name__ == "__main__":
    main()

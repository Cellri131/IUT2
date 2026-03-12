#!/usr/bin/env python3
"""
crawler.py – Crawler récursif du site DIW IUT Le Havre.

Parcourt toutes les pages à partir d'une URL de départ,
télécharge les fichiers, et génère un fichier link.data
qui répertorie les liens trouvés sur chaque page.

Usage :
    python scripts/crawler.py <output_dir> <user> <password>
"""
import os
import re
import sys
import time
import random
import urllib.parse
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── Configuration ───────────────────────────────────────────────
START_URL = "https://diw.iut.univ-lehavre.fr/pedago/index.xml"
BASE_DOMAIN = "diw.iut.univ-lehavre.fr"

# Patterns à exclure
EXCLUDE_PATTERNS = [
    re.compile(r"/jdk", re.IGNORECASE),
    re.compile(r"/javadoc", re.IGNORECASE),
    re.compile(r"/java-doc", re.IGNORECASE),
    re.compile(r"/docs/api", re.IGNORECASE),
    re.compile(r"/apidocs", re.IGNORECASE),
    re.compile(r"/pedago/Enseignement/", re.IGNORECASE),
]


def is_excluded(url: str) -> bool:
    """Vérifie si l'URL matche un pattern d'exclusion."""
    return any(p.search(url) for p in EXCLUDE_PATTERNS)


def is_same_domain(url: str) -> bool:
    """Vérifie que l'URL appartient au même domaine."""
    parsed = urllib.parse.urlparse(url)
    return parsed.hostname == BASE_DOMAIN


def normalize_url(url: str) -> str:
    """Normalise l'URL (supprime fragment, trailing spaces)."""
    url = url.strip()
    parsed = urllib.parse.urlparse(url)
    # Supprimer le fragment (#...)
    normalized = urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, "")
    )
    return normalized


def url_to_filepath(url: str, output_dir: str) -> str:
    """Convertit une URL en chemin de fichier local."""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    if not path or path.endswith("/"):
        path = path + "index.html"
    # Décoder les %XX
    path = urllib.parse.unquote(path)
    # Construire le chemin local
    local_path = os.path.join(output_dir, parsed.hostname, path.lstrip("/"))
    return local_path


def extract_links(content: str, base_url: str) -> list:
    """Extrait tous les liens (href, src) d'un contenu HTML/XML."""
    links = set()

    # Patterns pour href="..." et src="..."
    patterns = [
        re.compile(r'href\s*=\s*"([^"]*)"', re.IGNORECASE),
        re.compile(r"href\s*=\s*'([^']*)'", re.IGNORECASE),
        re.compile(r'src\s*=\s*"([^"]*)"', re.IGNORECASE),
        re.compile(r"src\s*=\s*'([^']*)'", re.IGNORECASE),
        # Pour les XML : <loc>...</loc>
        re.compile(r"<loc>\s*(.*?)\s*</loc>", re.IGNORECASE),
        # Pour les XML : url="..."
        re.compile(r'url\s*=\s*"([^"]*)"', re.IGNORECASE),
    ]

    for pattern in patterns:
        for match in pattern.finditer(content):
            raw = match.group(1).strip()
            if not raw or raw.startswith("#") or raw.startswith("javascript:"):
                continue
            if raw.startswith("mailto:"):
                continue
            # Résoudre les URLs relatives
            absolute = urllib.parse.urljoin(base_url, raw)
            links.add(absolute)

    return sorted(links)


def create_session(user: str, password: str) -> requests.Session:
    """Crée une session HTTP avec auth et retry."""
    session = requests.Session()
    session.auth = (user, password)
    session.verify = False

    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def crawl(start_url: str, output_dir: str, user: str, password: str):
    """Crawl récursif à partir de start_url."""
    session = create_session(user, password)

    visited = set()
    to_visit = [normalize_url(start_url)]
    # Aussi crawler la page d'accueil
    to_visit.append(normalize_url("https://diw.iut.univ-lehavre.fr/"))

    link_data_path = os.path.join(output_dir, "link.data")
    downloaded_count = 0
    skipped_count = 0

    with open(link_data_path, "w", encoding="utf-8") as link_file:
        while to_visit:
            url = to_visit.pop(0)
            url = normalize_url(url)

            if url in visited:
                continue
            visited.add(url)

            if not is_same_domain(url):
                continue
            if is_excluded(url):
                skipped_count += 1
                continue

            # Télécharger la page
            try:
                print(f"  → {url}")
                resp = session.get(url, timeout=60)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"    ✗ Erreur : {e}")
                continue

            # Sauvegarder le fichier
            filepath = url_to_filepath(url, output_dir)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Détecter si c'est du texte ou du binaire
            content_type = resp.headers.get("Content-Type", "")
            is_text = any(
                t in content_type
                for t in ["text/", "xml", "html", "json", "javascript", "css"]
            )

            if is_text:
                with open(filepath, "w", encoding="utf-8", errors="replace") as f:
                    f.write(resp.text)
            else:
                with open(filepath, "wb") as f:
                    f.write(resp.content)

            downloaded_count += 1

            # Extraire les liens et écrire dans link.data
            if is_text:
                links = extract_links(resp.text, url)

                link_file.write(f"-------------------\n")
                link_file.write(f"page {url}\n")
                link_file.write(f"===========\n")
                for link in links:
                    link_file.write(f"{link}\n")
                link_file.write("\n")
                link_file.flush()

                # Ajouter les nouveaux liens à visiter
                for link in links:
                    normalized = normalize_url(link)
                    if (
                        normalized not in visited
                        and is_same_domain(normalized)
                        and not is_excluded(normalized)
                    ):
                        to_visit.append(normalized)

            # Politesse : petite pause entre les requêtes
            time.sleep(0.3 + random.uniform(0, 0.3))

    print(f"\n==> {downloaded_count} fichier(s) téléchargé(s), {skipped_count} exclu(s)")
    print(f"==> link.data : {link_data_path}")


def main():
    if len(sys.argv) < 4:
        print(f"Usage : python {sys.argv[0]} <output_dir> <user> <password>")
        sys.exit(1)

    output_dir = os.path.abspath(sys.argv[1])
    user = sys.argv[2]
    password = sys.argv[3]

    os.makedirs(output_dir, exist_ok=True)

    print(f"==> Crawl de {START_URL}")
    print(f"    Sortie : {output_dir}")

    crawl(START_URL, output_dir, user, password)


if __name__ == "__main__":
    main()

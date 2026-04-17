#!/usr/bin/env python3
"""
refresh_single_page.py - Rafraîchit une seule page depuis le serveur original

Usage:
    python refresh_single_page.py <file_path> <user> <password>
"""

import re
import sys
import urllib.parse
from pathlib import Path

import urllib3
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://diw.iut.univ-lehavre.fr"


def detect_encoding(raw_bytes: bytes, content_type: str = "") -> str:
    """Détecte l'encodage correct du contenu."""
    header = raw_bytes[:500]

    # 1. Déclaration XML
    xml_match = re.search(rb'<\?xml[^?]*encoding=["\']([^"\']+)["\']', header)
    if xml_match:
        declared = xml_match.group(1).decode('ascii').lower()
        if declared in ('iso-8859-1', 'iso_8859_1', 'latin-1', 'latin1'):
            return 'windows-1252'
        return declared

    # 2. Meta charset HTML
    meta_match = re.search(rb'<meta[^>]*charset=["\']?([^"\';\s>]+)', header, re.IGNORECASE)
    if meta_match:
        declared = meta_match.group(1).decode('ascii').lower()
        if declared in ('iso-8859-1', 'iso_8859_1', 'latin-1', 'latin1'):
            return 'windows-1252'
        return declared

    # 3. Content-Type header
    if 'charset=' in content_type.lower():
        charset_match = re.search(r'charset=([^\s;]+)', content_type, re.IGNORECASE)
        if charset_match:
            declared = charset_match.group(1).lower().strip('"\'')
            if declared in ('iso-8859-1', 'iso_8859_1', 'latin-1', 'latin1'):
                return 'windows-1252'
            return declared

    # 4. Essayer UTF-8
    try:
        raw_bytes.decode('utf-8')
        return 'utf-8'
    except UnicodeDecodeError:
        return 'windows-1252'


def file_to_url(file_path: Path, output_dir: Path) -> str:
    """Convertit un chemin local en URL originale."""
    try:
        rel_path = file_path.relative_to(output_dir)
    except ValueError:
        rel_path = Path(file_path.name)

    url_path = '/'.join(rel_path.parts)

    if url_path.endswith('.html'):
        url_path = url_path[:-5] + '.xml'

    return f"{BASE_URL}/pedago/{url_path}"


def download_page(url: str, user: str, password: str) -> str:
    """Télécharge une page avec gestion correcte de l'encodage."""
    session = requests.Session()
    session.auth = HTTPBasicAuth(user, password)
    session.verify = False

    resp = session.get(url, timeout=30)
    resp.raise_for_status()

    # Décoder avec le bon encodage
    encoding = detect_encoding(resp.content, resp.headers.get('Content-Type', ''))
    try:
        text = resp.content.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        text = resp.content.decode('windows-1252', errors='replace')

    return text


def apply_transformations(content: str, file_path: Path, output_dir: Path) -> str:
    """Applique les transformations CSS/JS."""
    soup = BeautifulSoup(content, 'html.parser')

    # Nettoyer les styles
    for style in soup.find_all('style'):
        style.decompose()
    for tag in soup.find_all(style=True):
        del tag['style']

    head = soup.find('head')
    if not head:
        head = soup.new_tag('head')
        if soup.html:
            soup.html.insert(0, head)

    # UTF-8 charset
    existing_charset = head.find('meta', charset=True)
    if not existing_charset:
        meta = soup.new_tag('meta')
        meta['charset'] = 'utf-8'
        head.insert(0, meta)

    # Supprimer anciens CSS/JS
    for link in head.find_all('link', {'rel': 'stylesheet'}):
        link.decompose()
    for script in head.find_all('script', {'src': lambda x: x and 'rb.js' in x}):
        script.decompose()

    # Calculer profondeur vers pedago/css/
    try:
        rel_path = file_path.relative_to(output_dir)
        depth = len(rel_path.parts) - 1
        if depth > 0:
            css_path = '../' * depth + 'css/rb.css'
            js_path = '../' * depth + 'css/rb.js'
        else:
            css_path = 'css/rb.css'
            js_path = 'css/rb.js'
    except ValueError:
        css_path = 'css/rb.css'
        js_path = 'css/rb.js'

    # Ajouter CSS/JS
    link = soup.new_tag('link', rel='stylesheet', href=css_path)
    head.append(link)

    script = soup.new_tag('script', src=js_path)
    script['defer'] = ''
    head.append(script)

    # Conteneur
    body = soup.find('body')
    if body and not body.find('div', class_='container'):
        container = soup.new_tag('div')
        container['class'] = 'container'
        for child in list(body.children):
            container.append(child.extract())
        body.append(container)

    return str(soup.prettify())


def main():
    if len(sys.argv) < 4:
        print("Usage: python refresh_single_page.py <file_path> <user> <password>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    user = sys.argv[2]
    password = sys.argv[3]

    # Trouver output_dir (le dossier pedago)
    output_dir = file_path.parent
    while output_dir != output_dir.parent:
        if output_dir.name == "pedago":
            break
        output_dir = output_dir.parent

    if output_dir.name != "pedago":
        print(f"[ERREUR] Impossible de trouver le dossier pedago pour {file_path}")
        sys.exit(1)

    # Construire URL
    url = file_to_url(file_path, output_dir)

    print(f"Téléchargement: {url}")
    content = download_page(url, user, password)

    print(f"Application des transformations...")
    transformed = apply_transformations(content, file_path, output_dir)

    # Sauvegarder
    save_path = file_path
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(transformed)

    print(f"Sauvegardé: {save_path}")


if __name__ == "__main__":
    main()

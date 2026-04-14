#!/usr/bin/env python3
"""
refresh_page.py - Rafraîchit une page locale depuis le serveur original

Compatible Windows et Linux.

Usage:
    python refresh_page.py <local_file_path>
    python refresh_page.py "iut-refresh://chemin/vers/fichier.html"

Ce script:
1. Déduit l'URL originale depuis le chemin local
2. Télécharge la page depuis le serveur
3. Applique les transformations CSS/JS
4. Sauvegarde le fichier
"""

import os
import sys
import json
import logging
import urllib.parse
import platform
from pathlib import Path
from datetime import datetime

import urllib3
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup

# Supprimer les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
BASE_URL = "https://diw.iut.univ-lehavre.fr"

# Fichier credentials à côté du script
SCRIPT_DIR = Path(__file__).parent.absolute()
CREDENTIALS_FILE = SCRIPT_DIR / ".credentials.json"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_credentials():
    """Charge les identifiants depuis le fichier de configuration."""
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    return None


def save_credentials(user: str, password: str):
    """Sauvegarde les identifiants."""
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump({'user': user, 'password': password}, f)
    logger.info(f"Identifiants sauvegardés dans {CREDENTIALS_FILE}")


def get_credentials():
    """Récupère les identifiants (fichier ou input)."""
    creds = load_credentials()
    if creds:
        return creds['user'], creds['password']

    print("Identifiants non trouvés. Entrez-les une fois pour les sauvegarder:")
    user = input("Utilisateur: ").strip()
    password = input("Mot de passe: ").strip()
    save_credentials(user, password)
    return user, password


def parse_file_path(arg: str) -> Path:
    """Parse le chemin du fichier (supporte le protocole iut-refresh://)."""
    # Supprimer le protocole si présent
    if arg.startswith("iut-refresh://"):
        arg = arg[14:]  # Enlever "iut-refresh://"

    # Décoder les caractères URL
    arg = urllib.parse.unquote(arg)

    # Nettoyer le chemin selon l'OS
    if platform.system() == 'Windows':
        # Nettoyer le chemin Windows
        arg = arg.replace('/', '\\').lstrip('\\')
    else:
        # Linux/Mac: s'assurer que c'est un chemin Unix
        arg = arg.replace('\\', '/')

    path = Path(arg)

    # Si c'est un chemin relatif, essayer de le résoudre
    if not path.is_absolute():
        # Chercher dans le dossier parent du script (css -> pedago -> sortie)
        output_dir = SCRIPT_DIR.parent.parent
        if (output_dir / arg).exists():
            path = output_dir / arg
        elif (output_dir / "pedago" / arg).exists():
            path = output_dir / "pedago" / arg

    return path.resolve()


def find_output_dir(file_path: Path) -> Path:
    """Trouve le répertoire de sortie (celui qui contient pedago)."""
    current = file_path.parent
    while current != current.parent:
        if (current / "pedago").exists():
            return current
        if current.name == "pedago":
            return current.parent
        current = current.parent

    # Fallback: remonter jusqu'à trouver un dossier avec pedago
    for parent in file_path.parents:
        if (parent / "pedago").exists():
            return parent

    return file_path.parent


def file_to_url(file_path: Path, output_dir: Path) -> str:
    """Convertit un chemin de fichier local en URL originale."""
    try:
        rel_path = file_path.relative_to(output_dir)
    except ValueError:
        rel_path = Path(file_path.name)

    # Convertir en chemin URL (toujours avec des /)
    url_path = '/'.join(rel_path.parts)

    # Remplacer .html par .xml (fichiers convertis)
    if url_path.endswith('.html'):
        url_path_xml = url_path[:-5] + '.xml'
        url = f"{BASE_URL}/{url_path_xml}"
    else:
        url = f"{BASE_URL}/{url_path}"

    return url


def download_page(url: str, user: str, password: str) -> tuple:
    """Télécharge une page depuis le serveur."""
    session = requests.Session()
    session.auth = HTTPBasicAuth(user, password)
    session.verify = False
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0"
    })

    resp = session.get(url, timeout=30)
    resp.raise_for_status()

    return resp.text, resp.headers.get('Content-Type', '')


def extract_new_links(content: str, base_url: str) -> list:
    """Extrait les liens d'une page."""
    links = set()
    soup = BeautifulSoup(content, 'html.parser')

    for tag in soup.find_all(['a', 'link', 'script', 'img']):
        href = tag.get('href') or tag.get('src')
        if href and not href.startswith(('#', 'javascript:', 'mailto:')):
            absolute = urllib.parse.urljoin(base_url, href)
            if BASE_URL in absolute:
                links.add(absolute)

    return list(links)


def apply_transformations(content: str, file_path: Path, output_dir: Path) -> str:
    """Applique les transformations CSS/JS au contenu."""
    soup = BeautifulSoup(content, 'html.parser')

    # Supprimer les anciens styles
    for style_tag in soup.find_all('style'):
        style_tag.decompose()
    for tag in soup.find_all(style=True):
        del tag['style']

    # Supprimer les attributs de style ancien
    for tag in soup.find_all():
        for attr in ['bgcolor', 'text', 'link', 'vlink', 'alink', 'color']:
            if tag.has_attr(attr):
                del tag[attr]

    head = soup.find('head')
    if not head:
        head = soup.new_tag('head')
        if soup.html:
            soup.html.insert(0, head)

    # Supprimer les anciens liens CSS
    for link in head.find_all('link', {'rel': 'stylesheet'}):
        link.decompose()

    # Supprimer les anciens scripts rb.js
    for script in head.find_all('script', {'src': lambda x: x and 'rb.js' in x}):
        script.decompose()

    # Calculer le chemin relatif vers rb.css
    try:
        relative_path = file_path.relative_to(output_dir)
        if 'pedago' in relative_path.parts:
            pedago_index = relative_path.parts.index('pedago')
            depth = len(relative_path.parts) - pedago_index - 2
            if depth > 0:
                css_path = '../' * depth + 'css/rb.css'
                js_path = '../' * depth + 'css/rb.js'
            else:
                css_path = 'css/rb.css'
                js_path = 'css/rb.js'
        else:
            css_path = 'pedago/css/rb.css'
            js_path = 'pedago/css/rb.js'
    except ValueError:
        css_path = 'css/rb.css'
        js_path = 'css/rb.js'

    # Ajouter le nouveau CSS
    link_tag = soup.new_tag('link', rel='stylesheet', href=css_path)
    head.append(link_tag)

    # Ajouter le script JS
    script_tag = soup.new_tag('script', src=js_path)
    script_tag['defer'] = ''
    head.append(script_tag)

    # Ajouter/mettre à jour la meta original-url
    original_url = file_to_url(file_path, output_dir)
    meta = soup.find('meta', {'name': 'original-url'})
    if meta:
        meta['content'] = original_url
    else:
        meta = soup.new_tag('meta')
        meta['name'] = 'original-url'
        meta['content'] = original_url
        head.insert(0, meta)

    # Ajouter le conteneur si nécessaire
    body = soup.find('body')
    if body:
        container = body.find('div', class_='container')
        if not container:
            container = soup.new_tag('div')
            container['class'] = 'container'
            for child in list(body.children):
                container.append(child.extract())
            body.append(container)

    return str(soup.prettify())


def refresh_page(file_path: Path):
    """Rafraîchit une page locale."""
    print(f"\n{'='*60}")
    print(f"RAFRAÎCHISSEMENT DE PAGE")
    print(f"{'='*60}")
    print(f"Fichier: {file_path}")

    if not file_path.exists():
        print(f"[ERREUR] Le fichier n'existe pas: {file_path}")
        return False

    # Trouver le répertoire de sortie
    output_dir = find_output_dir(file_path)
    print(f"Répertoire de sortie: {output_dir}")

    # Obtenir les identifiants
    user, password = get_credentials()

    # Construire l'URL originale
    original_url = file_to_url(file_path, output_dir)
    print(f"URL originale: {original_url}")

    try:
        # Télécharger la page
        print(f"\n[1/3] Téléchargement...")
        content, content_type = download_page(original_url, user, password)
        print(f"      Téléchargé: {len(content)} caractères")

        # Extraire les nouveaux liens
        print(f"\n[2/3] Extraction des liens...")
        new_links = extract_new_links(content, original_url)
        print(f"      {len(new_links)} liens trouvés")

        # Appliquer les transformations
        print(f"\n[3/3] Application des transformations...")
        transformed = apply_transformations(content, file_path, output_dir)

        # Si c'était un XML, sauvegarder en HTML
        save_path = file_path
        if original_url.endswith('.xml'):
            save_path = file_path.with_suffix('.html')

        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(transformed)
        print(f"      Sauvegardé: {save_path}")

        # Afficher les nouveaux liens
        if new_links:
            print(f"\n[INFO] Nouveaux liens détectés:")
            for link in new_links[:10]:
                print(f"       - {link}")
            if len(new_links) > 10:
                print(f"       ... et {len(new_links) - 10} autres")

        print(f"\n{'='*60}")
        print(f"[SUCCESS] Page rafraîchie avec succès !")
        print(f"Rechargez la page dans votre navigateur (F5)")
        print(f"{'='*60}\n")

        return True

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"\n[ERREUR] Authentification échouée. Supprimez {CREDENTIALS_FILE} et réessayez.")
        else:
            print(f"\n[ERREUR] Erreur HTTP: {e}")
        return False
    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <fichier_local>")
        print(f"       python {sys.argv[0]} iut-refresh://chemin/vers/fichier.html")
        print()
        print("Exemple:")
        print(f'  python {sys.argv[0]} ./sortie/pedago/index.html')
        sys.exit(1)

    # Parser le chemin
    file_path = parse_file_path(sys.argv[1])

    # Rafraîchir la page
    success = refresh_page(file_path)

    # Pause pour voir le résultat (si lancé par double-clic sur Windows)
    if platform.system() == 'Windows' and sys.stdin.isatty():
        input("\nAppuyez sur Entrée pour fermer...")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
crawler.py – Crawler récursif avancé du site DIW IUT Le Havre.

Parcourt toutes les pages à partir d'une URL de départ,
télécharge les fichiers, et génère un fichier link.data
qui répertorie les liens trouvés sur chaque page.

Fonctionnalités avancées :
- Authentification automatique (HTTP Basic + formulaires)
- Support des redirections meta
- Mode PDF uniquement (optionnel)
- Export JSON/CSV des résultats
- Logging détaillé

Usage :
    python scripts/crawler.py <output_dir> <user> <password> [--pdf-only]
"""
import os
import re
import sys
import time
import random
import urllib.parse
import json
import csv
import logging
from pathlib import Path
from datetime import datetime

import urllib3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

# Supprimer les warnings SSL (certificat non vérifié)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ── Configuration ───────────────────────────────────────────────
START_URL = "https://diw.iut.univ-lehavre.fr/pedago/index.xml"
BASE_DOMAIN = "diw.iut.univ-lehavre.fr"
BASE_URL = "https://diw.iut.univ-lehavre.fr/"

# Patterns à exclure
EXCLUDE_PATTERNS = [
    re.compile(r"/jdk", re.IGNORECASE),
    re.compile(r"/javadoc", re.IGNORECASE),
    re.compile(r"/java-doc", re.IGNORECASE),
    re.compile(r"/docs/api", re.IGNORECASE),
    re.compile(r"/apidocs", re.IGNORECASE),
    re.compile(r"/pedago/Enseignement/", re.IGNORECASE),
]

PDF_ONLY_MODE = False  # Peut être activé via --pdf-only


def is_excluded(url: str) -> bool:
    """Vérifie si l'URL matche un pattern d'exclusion."""
    return any(p.search(url) for p in EXCLUDE_PATTERNS)


def is_same_domain(url: str) -> bool:
    """Vérifie que l'URL appartient au même domaine."""
    parsed = urllib.parse.urlparse(url)
    return parsed.hostname == BASE_DOMAIN


def is_pdf_url(url: str) -> bool:
    """Vérifie si une URL pointe vers un fichier PDF."""
    parsed_url = urllib.parse.urlparse(url)
    path = parsed_url.path.lower()
    return path.endswith('.pdf')


def normalize_url(url: str) -> str:
    """Normalise l'URL (supprime fragment, trailing spaces, paramètres de tracking)."""
    url = url.strip()
    parsed = urllib.parse.urlparse(url)

    # Supprimer les paramètres de tracking
    query_params = urllib.parse.parse_qs(parsed.query)
    tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'fbclid', 'gclid']
    for param in tracking_params:
        query_params.pop(param, None)

    new_query = urllib.parse.urlencode(query_params, doseq=True)

    # Supprimer le fragment (#...)
    normalized = urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, "")
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


def extract_links(content: str, base_url: str, pdf_only: bool = False) -> list:
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
        # Pour les XML : url="..." et dest="..."
        re.compile(r'url\s*=\s*"([^"]*)"', re.IGNORECASE),
        re.compile(r'dest\s*=\s*"([^"]*)"', re.IGNORECASE),
    ]

    for pattern in patterns:
        for match in pattern.finditer(content):
            raw = match.group(1).strip()
            if not raw or raw.startswith("#") or raw.startswith("javascript:"):
                continue
            if raw.startswith("mailto:"):
                continue
            # Ignorer les expressions XSL/XSLT ({$var}, {@attr}, {.}, etc.)
            if "{" in raw or "}" in raw:
                continue
            # Résoudre les URLs relatives
            absolute = urllib.parse.urljoin(base_url, raw)
            normalized = normalize_url(absolute)

            if is_same_domain(normalized):
                # En mode PDF, garder tous les liens pour découvrir les PDFs
                if not pdf_only or is_pdf_url(normalized) or not is_pdf_url(normalized):
                    links.add(normalized)

    # Meta redirections
    try:
        soup = BeautifulSoup(content, "html.parser")
        for meta in soup.find_all("meta", attrs={'http-equiv': re.compile(r'refresh', re.I)}):
            content_attr = meta.get('content', '')
            match = re.search(r'url\s*=\s*[\'"]?([^\'"\s>]+)', content_attr, re.I)
            if match:
                redirect_url = match.group(1)
                absolute_url = urllib.parse.urljoin(base_url, redirect_url)
                normalized_url = normalize_url(absolute_url)
                if is_same_domain(normalized_url):
                    links.add(normalized_url)
                    logger.info(f"Meta redirection détectée: {redirect_url} -> {normalized_url}")
    except Exception as e:
        logger.debug(f"Erreur lors du parsing des meta redirections: {e}")

    return sorted(links)


def create_session(user: str, password: str) -> requests.Session:
    """Crée une session HTTP avec auth et retry."""
    session = requests.Session()
    session.auth = (user, password)
    session.verify = False
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    })

    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def find_login_form(html_content: str):
    """Analyse la page pour trouver les formulaires de connexion."""
    soup = BeautifulSoup(html_content, "html.parser")
    forms = []

    for form in soup.find_all("form"):
        form_info = {
            'action': form.get('action', ''),
            'method': form.get('method', 'get').lower(),
            'fields': {}
        }

        for input_tag in form.find_all("input"):
            name = input_tag.get('name', '')
            input_type = input_tag.get('type', 'text')
            value = input_tag.get('value', '')

            form_info['fields'][name] = {
                'type': input_type,
                'value': value
            }

        forms.append(form_info)
        logger.debug(f"Formulaire trouvé - Action: {form_info['action']}, Méthode: {form_info['method']}")

    return forms


def check_authentication_success(response) -> bool:
    """Vérifie si l'authentification a réussi."""
    if response.status_code == 401:
        return False

    # Rechercher des indicateurs d'échec dans le contenu
    failure_indicators = [
        'login failed', 'authentication failed', 'invalid credentials',
        'mot de passe incorrect', 'identifiant incorrect', 'erreur de connexion',
        'access denied', 'unauthorized'
    ]

    content_lower = response.text.lower()
    for indicator in failure_indicators:
        if indicator in content_lower:
            return False

    # Si on arrive sur une page différente après le login, c'est probablement bon
    if 'login' not in response.url.lower() and response.status_code == 200:
        return True

    # Rechercher des indicateurs de succès
    success_indicators = [
        'welcome', 'bienvenue', 'dashboard', 'logout', 'déconnexion',
        'profile', 'profil', 'settings', 'paramètres'
    ]

    for indicator in success_indicators:
        if indicator in content_lower:
            return True

    return response.status_code == 200


def attempt_authentication(session: requests.Session, user: str, password: str) -> bool:
    """Tente différentes méthodes d'authentification."""
    logger.info("Tentative d'authentification...")

    try:
        # 1. Tenter d'accéder à la page principale
        response = session.get(BASE_URL, timeout=15)
        logger.info(f"Réponse initiale: {response.status_code}")

        # Vérifier si on a déjà accès au contenu
        if check_authentication_success(response):
            logger.info("Accès déjà autorisé sans authentification supplémentaire")
            return True

        # 2. Essayer l'authentification HTTP Basic (déjà configurée dans la session)
        logger.info("Authentification HTTP Basic activée dans la session")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de l'authentification: {e}")
        return False


def crawl(start_url: str, output_dir: str, user: str, password: str, pdf_only: bool = False):
    """Crawl récursif à partir de start_url avec fonctionnalités avancées."""
    session = create_session(user, password)

    # Tenter l'authentification
    if not attempt_authentication(session, user, password):
        logger.warning("Authentification échouée, continue quand même...")

    visited = set()
    to_visit = [normalize_url(start_url)]
    # Aussi crawler la page d'accueil
    to_visit.append(normalize_url(BASE_URL))

    results = []  # Pour l'export JSON/CSV
    link_data_path = os.path.join(output_dir, "link.data")
    downloaded_count = 0
    skipped_count = 0
    pdfs_found = 0

    if pdf_only:
        logger.info(f"🔍 Mode PDF UNIQUEMENT activé")

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
                is_pdf = is_pdf_url(url)
                logger.info(f"  → {url}" + (f" [PDF]" if is_pdf else ""))
                resp = session.get(url, timeout=60)

                # Si on a un 401, l'auth est déjà configurée dans la session
                if resp.status_code == 401:
                    logger.warning(f"    ⚠ 401 Unauthorized pour {url}")

                resp.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"    ✗ Erreur : {e}")
                results.append({
                    'url': url,
                    'status_code': 'ERROR',
                    'content_type': '',
                    'content_length': 0,
                    'timestamp': datetime.now().isoformat()
                })
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

            # En mode PDF uniquement, ne sauvegarder que les PDFs dans les résultats
            should_save_result = not pdf_only or is_pdf

            if should_save_result:
                results.append({
                    'url': url,
                    'status_code': resp.status_code,
                    'content_type': content_type,
                    'content_length': len(resp.content),
                    'timestamp': datetime.now().isoformat()
                })
                downloaded_count += 1

                if is_pdf:
                    pdfs_found += 1
                    logger.info(f"    📄 PDF trouvé ({len(resp.content)} bytes)")

            # Extraire les liens et écrire dans link.data
            if is_text:
                links = extract_links(resp.text, url, pdf_only)

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

                if pdf_only:
                    pdf_links = [link for link in links if is_pdf_url(link)]
                    if pdf_links:
                        logger.info(f"    📄 {len(pdf_links)} liens PDF trouvés")

            # Politesse : petite pause entre les requêtes
            time.sleep(0.3 + random.uniform(0, 0.3))

            # Affichage du progrès
            if (downloaded_count + skipped_count) % 10 == 0:
                if pdf_only:
                    logger.info(f"📊 Explorées: {len(visited)}, PDFs: {pdfs_found}, En attente: {len(to_visit)}")
                else:
                    logger.info(f"📊 Téléchargées: {downloaded_count}, En attente: {len(to_visit)}")

    logger.info(f"\n==> {downloaded_count} fichier(s) téléchargé(s), {skipped_count} exclu(s)")
    if pdf_only:
        logger.info(f"==> {pdfs_found} PDFs collectés")
    logger.info(f"==> link.data : {link_data_path}")

    # Sauvegarder les résultats en JSON et CSV
    save_results(output_dir, results)

    return results


def save_results(output_dir: str, results: list):
    """Sauvegarde les résultats au format CSV et JSON."""
    if not results:
        return

    # Export CSV
    csv_file = os.path.join(output_dir, "crawl_results.csv")
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = results[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    logger.info(f"==> Résultats CSV : {csv_file}")

    # Export JSON
    json_file = os.path.join(output_dir, "crawl_results.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"==> Résultats JSON : {json_file}")


def print_summary(results: list, pdf_only: bool = False):
    """Affiche un résumé des résultats."""
    total_pages = len(results)
    success_pages = len([r for r in results if isinstance(r['status_code'], int) and r['status_code'] == 200])
    error_pages = len([r for r in results if r['status_code'] in ['ERROR', 'TIMEOUT']])
    pdf_pages = len([r for r in results if is_pdf_url(r['url'])])

    print(f"\n{'='*50}")
    if pdf_only:
        print(f"📄 RÉSUMÉ DU CRAWLING PDF")
    else:
        print(f"RÉSUMÉ DU CRAWLING")
    print(f"{'='*50}")
    print(f"Site crawlé: {BASE_URL}")
    print(f"Total des pages: {total_pages}")
    if pdf_only:
        print(f"📄 PDFs collectés: {pdf_pages}")
    print(f"Pages réussies (200): {success_pages}")
    print(f"Pages en erreur: {error_pages}")
    if pdf_only:
        print(f"Mode: PDF UNIQUEMENT")
    print(f"{'='*50}")


def main():
    # Vérifier les arguments
    if len(sys.argv) < 4:
        print(f"Usage : python {sys.argv[0]} <output_dir> <user> <password> [--pdf-only]")
        sys.exit(1)

    output_dir = os.path.abspath(sys.argv[1])
    user = sys.argv[2]
    password = sys.argv[3]

    # Vérifier l'option --pdf-only
    pdf_only = False
    if len(sys.argv) > 4 and sys.argv[4] == '--pdf-only':
        pdf_only = True

    os.makedirs(output_dir, exist_ok=True)

    if pdf_only:
        print(f"🔍 Crawl PDF UNIQUEMENT de {START_URL}")
        print(f"📄 Seuls les fichiers PDF seront collectés")
    else:
        print(f"==> Crawl de {START_URL}")

    print(f"    Sortie : {output_dir}")

    try:
        results = crawl(START_URL, output_dir, user, password, pdf_only)
        print_summary(results, pdf_only)
    except KeyboardInterrupt:
        print("\n⚠ Crawling interrompu par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

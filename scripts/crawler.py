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
import hashlib
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
    level=logging.INFO,  # Retour à INFO
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


def detect_encoding(raw_bytes: bytes, content_type: str = "") -> str:
    """Détecte l'encodage correct du contenu.

    Ordre de priorité :
    1. Déclaration XML (<?xml ... encoding="..."?>)
    2. Meta charset HTML
    3. Content-Type header
    4. Fallback: utf-8
    """
    # 1. Vérifier la déclaration XML
    header = raw_bytes[:500]
    xml_match = re.search(rb'<\?xml[^?]*encoding=["\']([^"\']+)["\']', header)
    if xml_match:
        declared = xml_match.group(1).decode('ascii').lower()
        # iso-8859-1 est souvent du windows-1252 en pratique
        if declared in ('iso-8859-1', 'iso_8859_1', 'latin-1', 'latin1'):
            return 'windows-1252'
        return declared

    # 2. Vérifier meta charset HTML
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


def decode_content(raw_bytes: bytes, content_type: str = "") -> str:
    """Décode le contenu brut avec le bon encodage et renvoie de l'UTF-8."""
    encoding = detect_encoding(raw_bytes, content_type)
    try:
        text = raw_bytes.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        # Fallback
        text = raw_bytes.decode('windows-1252', errors='replace')

    return text


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
    """Convertit une URL en chemin de fichier local en préservant la structure."""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path

    # Nettoyer le chemin : enlever le / initial et décoder les caractères URL
    clean_path = urllib.parse.unquote(path.lstrip('/'))

    # Si le chemin est vide ou se termine par /, c'est une page d'accueil
    if not clean_path or clean_path.endswith('/'):
        clean_path = clean_path.rstrip('/') + '/index.html'

    # Remplacer les / par le séparateur du système d'exploitation
    clean_path = clean_path.replace('/', os.sep)

    # Remplacer les caractères invalides pour Windows
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        clean_path = clean_path.replace(char, '_')

    # Construire le chemin complet avec le chemin absolu
    local_path = os.path.abspath(os.path.join(output_dir, clean_path))

    # Sur Windows, utiliser le préfixe \\?\ pour supporter les chemins longs
    if os.name == 'nt' and not local_path.startswith('\\\\?\\'):
        local_path = '\\\\?\\' + local_path

    return local_path


def extract_links(content: str, base_url: str, pdf_only: bool = False) -> list:
    """Extrait tous les liens (href, src) d'un contenu HTML/XML."""
    links = set()

    # Détecter si c'est une page "Index of" Apache
    is_index_page = '<title>Index of' in content or '<h1>Index of' in content

    if is_index_page:
        logger.info(f"    [INDEX] Page de répertoire détectée, extraction de tous les fichiers...")

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
            # Ignorer les liens de tri Apache (Name, Last modified, Size, Description)
            if raw.startswith("?"):
                continue
            # Ignorer le lien "Parent Directory"
            if raw == "../" and not is_index_page:
                continue

            # Résoudre les URLs relatives
            absolute = urllib.parse.urljoin(base_url, raw)
            normalized = normalize_url(absolute)

            if is_same_domain(normalized):
                # En mode PDF, garder tous les liens pour découvrir les PDFs
                if not pdf_only or is_pdf_url(normalized) or not is_pdf_url(normalized):
                    links.add(normalized)

                    # Si c'est une page Index of, log les fichiers trouvés
                    if is_index_page and not raw.endswith('/') and raw != "../":
                        logger.debug(f"      Fichier trouvé: {raw}")

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
    url_mapping = {}  # Mapping hash -> URL original
    link_data_path = os.path.join(output_dir, "link.data")
    mapping_path = os.path.join(output_dir, "url_mapping.json")
    cache_path = os.path.join(output_dir, ".content_cache.json")

    downloaded_count = 0
    skipped_count = 0
    skipped_identical = 0  # Fichiers identiques non re-téléchargés
    pdfs_found = 0

    # Charger le cache de contenu (hashes des fichiers)
    content_cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                content_cache = json.load(f)
            logger.info(f"Cache chargé: {len(content_cache)} fichiers en cache")
        except Exception as e:
            logger.warning(f"Impossible de charger le cache: {e}")

    if pdf_only:
        logger.info(f"[CRAWL] Mode PDF UNIQUEMENT active")

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

                # Calculer le filepath AVANT pour pouvoir lire la taille locale
                filepath = url_to_filepath(url, output_dir)

                # Si c'est du HTML/XML et que l'URL n'a pas d'extension, ajouter .html
                parsed = urllib.parse.urlparse(url)
                has_extension = '.' in parsed.path.split('/')[-1] if parsed.path else False

                # D'abord, essayer une requête HEAD pour obtenir la taille sans télécharger
                head_resp = None
                remote_size = None
                content_type = None

                try:
                    head_resp = session.head(url, timeout=10, allow_redirects=True)

                    # Si on a un 401 sur HEAD mais que le fichier existe, utiliser la taille locale
                    if head_resp.status_code == 401:
                        logger.debug(f"    HEAD  401, utilisation taille locale si disponible")
                        # Essayer de lire la taille du fichier local
                        if os.path.exists(filepath):
                            remote_size = os.path.getsize(filepath)
                            logger.debug(f"    Taille locale: {remote_size} bytes")
                        # Vérifier aussi avec extension .html
                        elif not has_extension and os.path.exists(filepath + '.html'):
                            remote_size = os.path.getsize(filepath + '.html')
                            filepath = filepath + '.html'
                            logger.debug(f"    Taille locale (.html): {remote_size} bytes")
                    else:
                        remote_size = int(head_resp.headers.get("Content-Length", 0))
                        content_type = head_resp.headers.get("Content-Type", "")
                        logger.debug(f"    HEAD: Content-Length={remote_size}, Content-Type={content_type}")

                except Exception as head_error:
                    logger.debug(f"    HEAD échoué: {head_error}")
                    # Essayer de lire la taille du fichier local
                    if os.path.exists(filepath):
                        remote_size = os.path.getsize(filepath)
                        logger.debug(f"    Fallback taille locale: {remote_size} bytes")

                # Déterminer si c'est du texte
                is_text = content_type and any(
                    t in content_type
                    for t in ["text/", "xml", "html", "json", "javascript", "css"]
                ) if content_type else True

                # Ajuster le filepath si nécessaire
                if content_type and is_text and 'html' in content_type.lower() and not has_extension:
                    if filepath.endswith('\\\\?\\'):
                        filepath = filepath + 'index.html'
                    else:
                        filepath = filepath + '.html'

                # Vérifier le cache
                file_exists = os.path.exists(filepath)
                cached_info = content_cache.get(url, {})
                cached_size = cached_info.get('size', 0) if isinstance(cached_info, dict) else 0

                logger.debug(f"    Cache: file_exists={file_exists}, cached_size={cached_size}, remote_size={remote_size}")

                # Comparer la taille distante avec le cache
                # Seulement si on a pu obtenir une taille distante valide
                if file_exists and remote_size and remote_size > 0 and cached_size == remote_size:
                    logger.info(f"  -> {url}" + (f" [PDF]" if is_pdf else "") + " [SKIP - Identique]")
                    skipped_identical += 1

                    # Mettre à jour le timestamp dans le cache
                    content_cache[url] = {
                        'size': remote_size,
                        'timestamp': datetime.now().isoformat(),
                        'filepath': filepath
                    }

                    # Quand même faire un GET pour extraire les liens (pour HTML/XML)
                    if is_text and not is_pdf:
                        try:
                            resp = session.get(url, timeout=60)
                            page_text = decode_content(resp.content, resp.headers.get('Content-Type', ''))
                            links = extract_links(page_text, url, pdf_only)

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
                        except Exception as link_error:
                            logger.debug(f"    Erreur extraction liens: {link_error}")

                    continue

                # Télécharger le fichier complet
                logger.info(f"  -> {url}" + (f" [PDF]" if is_pdf else "") + " [DOWNLOAD]")
                resp = session.get(url, timeout=60)

                # Si on a un 401, l'auth est déjà configurée dans la session
                if resp.status_code == 401:
                    logger.warning(f"    [WARN] 401 Unauthorized pour {url}")

                resp.raise_for_status()

                # Obtenir la taille réelle du contenu téléchargé
                content_type = resp.headers.get("Content-Type", "")
                is_text = any(
                    t in content_type
                    for t in ["text/", "xml", "html", "json", "javascript", "css"]
                )

                if is_text:
                    actual_size = len(decode_content(resp.content, content_type).encode('utf-8'))
                else:
                    actual_size = len(resp.content)

                logger.debug(f"    Téléchargé: {actual_size} bytes")

            except requests.RequestException as e:
                logger.error(f"    [ERROR] Erreur : {e}")
                results.append({
                    'url': url,
                    'status_code': 'ERROR',
                    'content_type': '',
                    'content_length': 0,
                    'timestamp': datetime.now().isoformat()
                })
                continue

            try:
                dir_path = os.path.dirname(filepath)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                logger.error(f"    [ERROR] Impossible de créer le répertoire {dir_path}: {e}")
                continue

            if is_text:
                page_text = decode_content(resp.content, content_type)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(page_text)
            else:
                # Télécharger en streaming pour les fichiers volumineux
                with open(filepath, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            # Sauvegarder la taille réelle dans le cache
            content_cache[url] = {
                'size': actual_size if 'actual_size' in locals() else remote_size,
                'timestamp': datetime.now().isoformat(),
                'filepath': filepath
            }

            # En mode PDF uniquement, ne sauvegarder que les PDFs dans les résultats
            should_save_result = not pdf_only or is_pdf

            if should_save_result:
                # Utiliser remote_size ou calculer depuis le fichier
                content_length = remote_size if remote_size else (
                    os.path.getsize(filepath) if os.path.exists(filepath) else 0
                )

                # Ajouter au mapping
                url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                url_mapping[url_hash] = url

                results.append({
                    'url': url,
                    'status_code': resp.status_code,
                    'content_type': content_type,
                    'content_length': content_length,
                    'timestamp': datetime.now().isoformat(),
                    'hash': url_hash
                })
                downloaded_count += 1

                if is_pdf:
                    pdfs_found += 1
                    logger.info(f"    [PDF] Fichier trouvé ({content_length} bytes)")

            # Extraire les liens et écrire dans link.data
            if is_text:
                links = extract_links(page_text, url, pdf_only)

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
                        logger.info(f"    [PDF] {len(pdf_links)} liens PDF trouves")

            # Explorer le répertoire parent pour découvrir d'autres fichiers
            # (pages "Index of" Apache)
            parsed_url = urllib.parse.urlparse(url)
            path = parsed_url.path
            if '/' in path and not path.endswith('/'):
                # C'est un fichier, essayer de visiter son répertoire parent
                parent_path = '/'.join(path.split('/')[:-1]) + '/'
                parent_url = urllib.parse.urlunparse(
                    (parsed_url.scheme, parsed_url.netloc, parent_path, '', '', '')
                )
                parent_url = normalize_url(parent_url)

                if (
                    parent_url not in visited
                    and is_same_domain(parent_url)
                    and not is_excluded(parent_url)
                    and parent_url not in to_visit
                ):
                    logger.debug(f"    [DIR] Ajout du répertoire parent: {parent_url}")
                    to_visit.append(parent_url)

            # Politesse : petite pause entre les requêtes
            time.sleep(0.3 + random.uniform(0, 0.3))

            # Affichage du progrès
            if (downloaded_count + skipped_count + skipped_identical) % 10 == 0:
                if pdf_only:
                    logger.info(f"[PROGRESS] Explorees: {len(visited)}, PDFs: {pdfs_found}, En attente: {len(to_visit)}")
                else:
                    logger.info(f"[PROGRESS] Telecharges: {downloaded_count}, Ignores: {skipped_identical}, En attente: {len(to_visit)}")

    # Sauvegarder le cache de contenu
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(content_cache, f, indent=2)
        logger.info(f"Cache sauvegardé: {len(content_cache)} fichiers")
    except Exception as e:
        logger.warning(f"Impossible de sauvegarder le cache: {e}")

    logger.info(f"\n==> {downloaded_count} fichier(s) telecharge(s), {skipped_count} exclu(s), {skipped_identical} identique(s)")
    if pdf_only:
        logger.info(f"==> {pdfs_found} PDFs collectes")
    logger.info(f"==> link.data : {link_data_path}")

    # Sauvegarder le mapping des hashes -> URLs
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(url_mapping, f, indent=2, ensure_ascii=False)
    logger.info(f"==> url_mapping.json : {mapping_path}")

    # Sauvegarder les résultats en JSON et CSV
    save_results(output_dir, results)

    return results


def save_results(output_dir: str, results: list):
    """Sauvegarde les résultats au format CSV et JSON."""
    if not results:
        return

    # Export CSV - s'assurer que tous les champs sont présents
    csv_file = os.path.join(output_dir, "crawl_results.csv")
    # Définir tous les champs possibles
    all_fields = {'url', 'status_code', 'content_type', 'content_length', 'timestamp', 'hash'}

    # Collecter tous les champs utilisés
    for result in results:
        all_fields.update(result.keys())

    fieldnames = sorted(list(all_fields))

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        # S'assurer que tous les résultats ont tous les champs
        for result in results:
            row = {field: result.get(field, '') for field in fieldnames}
            writer.writerow(row)
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
        print(f"[PDF] RESUME DU CRAWLING PDF")
    else:
        print(f"RESUME DU CRAWLING")
    print(f"{'='*50}")
    print(f"Site crawle: {BASE_URL}")
    print(f"Total des pages: {total_pages}")
    if pdf_only:
        print(f"[PDF] PDFs collectes: {pdf_pages}")
    print(f"Pages reussies (200): {success_pages}")
    print(f"Pages en erreur: {error_pages}")
    if pdf_only:
        print(f"Mode: PDF UNIQUEMENT")
    print(f"{'='*50}")


def run_xml_to_html_converter(output_dir: str):
    """Lance la conversion XML → HTML."""
    try:
        print("\n" + "="*60)
        print("[CONVERSION] Conversion XML → HTML en cours...")
        print("="*60)

        from pathlib import Path

        input_dir = Path(output_dir)
        converted_count = 0
        error_count = 0

        xml_files = list(input_dir.rglob("*.xml"))
        logger.info(f"Trouvé {len(xml_files)} fichier(s) XML à convertir")

        from xml_to_html_converter import XMLToHTMLConverter
        converter = XMLToHTMLConverter(output_dir, dry_run=False)
        converter.convert_all()

        print(f"✓ Conversion terminée: {converter.converted_count} fichier(s)")

    except Exception as e:
        logger.error(f"Erreur lors de la conversion XML → HTML: {e}")
        print(f"[WARN] La conversion XML → HTML a échoué : {e}")


def run_link_fixer(output_dir: str):
    """Lance l'adaptation des liens."""
    try:
        print("\n" + "="*60)
        print("[LIENS] Adaptation des liens en cours...")
        print("="*60)

        from fix_links import LinkFixer

        fixer = LinkFixer(output_dir, dry_run=False)
        fixer.process_all_files()

        print(f"✓ Adaptation terminée: {fixer.links_replaced} lien(s) adapté(s)")

    except Exception as e:
        logger.error(f"Erreur lors de l'adaptation des liens: {e}")
        print(f"[WARN] L'adaptation des liens a échoué : {e}")


def generate_navigation_tree(output_dir: str):
    """Génère navigation.json pour le sidebar de navigation."""
    try:
        print("\n" + "="*60)
        print("[NAVIGATION] Génération de l'arbre de navigation...")
        print("="*60)

        from pathlib import Path

        pedago_dir = Path(output_dir)
        if not pedago_dir.exists():
            logger.warning(f"Dossier {pedago_dir} introuvable")
            return

        def build_tree(directory: Path, base_path: Path) -> dict:
            """Construit récursivement l'arbre de navigation."""
            relative = directory.relative_to(base_path)
            rel_str = str(relative).replace('\\', '/')
            if rel_str == '.':
                rel_str = ''

            node = {
                "name": directory.name if directory != base_path else "pedago",
                "path": "/" + rel_str if rel_str else "/",
                "type": "folder",
                "children": []
            }

            # Lister les éléments
            try:
                items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            except PermissionError:
                return node

            for item in items:
                # Ignorer les fichiers cachés et fichiers de config
                if item.name.startswith('.') or item.name in ['navigation.json', 'link.data', 'url_mapping.json']:
                    continue

                if item.is_dir():
                    # Récursion dans les sous-dossiers
                    child_node = build_tree(item, base_path)
                    node["children"].append(child_node)

                elif item.is_file() and item.suffix.lower() in ['.html', '.htm']:
                    # Ajouter uniquement les fichiers HTML
                    item_rel = item.relative_to(base_path)
                    item_path = "/" + str(item_rel).replace('\\', '/')

                    file_node = {
                        "name": item.name,
                        "path": item_path,
                        "type": "file"
                    }
                    node["children"].append(file_node)

            return node

        # Construire l'arbre
        tree = build_tree(pedago_dir, pedago_dir)

        # Sauvegarder navigation.json
        nav_file = pedago_dir / "navigation.json"
        with open(nav_file, 'w', encoding='utf-8') as f:
            json.dump(tree, f, indent=2, ensure_ascii=False)

        print(f"✓ Arbre de navigation généré: {nav_file}")
        logger.info(f"Navigation tree saved to {nav_file}")

    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'arbre de navigation: {e}")
        print(f"[WARN] La génération de navigation.json a échoué : {e}")


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
        print(f"[CRAWL] Crawl PDF UNIQUEMENT de {START_URL}")
        print(f"[PDF] Seuls les fichiers PDF seront collectes")
    else:
        print(f"[CRAWL] Crawl de {START_URL}")

    print(f"    Sortie : {output_dir}")

    try:
        # 1. Crawling
        results = crawl(START_URL, output_dir, user, password, pdf_only)
        print_summary(results, pdf_only)

        # 2. Conversion XML → HTML
        run_xml_to_html_converter(output_dir)

        # 3. Adaptation des liens
        run_link_fixer(output_dir)

        # 4. Génération de l'arbre de navigation
        generate_navigation_tree(output_dir)

        print("\n" + "="*60)
        print("[SUCCESS] ✓ Pipeline complet terminé avec succès !")
        print("="*60)

    except KeyboardInterrupt:
        print("\n[WARN] Execution interrompue par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

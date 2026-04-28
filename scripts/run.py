#!/usr/bin/env python3
"""
Launcher pour le crawler.
Peut être utilisé en interactif ou avec des arguments (pour le serveur/cron).

Usage interactif:
    python run.py

Usage automatique (serveur/cron):
    python run.py <site_url> <output_dir> [<user> <password>]
"""

import os
import sys
import subprocess
from urllib.parse import urlparse


def main():
    scripts_dir = os.path.dirname(os.path.abspath(__file__))

    # Mode automatique (arguments fournis)
    if len(sys.argv) >= 3:
        site_url = sys.argv[1]
        output_dir = sys.argv[2]
        user = sys.argv[3] if len(sys.argv) > 3 else None
        password = sys.argv[4] if len(sys.argv) > 4 else None
        needs_auth = user is not None and password is not None
        convert_xml = True
        setup_css = True
    else:
        # Mode interactif
        print("="*60)
        print("CRAWLER IUT2 - LAUNCHER INTERACTIF")
        print("="*60)
        print()

        # 1. URL du site
        default_url = "https://diw.iut.univ-lehavre.fr/pedago/index.xml"
        site_url = input(f"Lien du site à crawler [{default_url}]: ").strip() or default_url

        # Valider l'URL
        try:
            parsed = urlparse(site_url)
            if not parsed.scheme or not parsed.netloc:
                print("Erreur: URL invalide!")
                sys.exit(1)
        except Exception as e:
            print(f"Erreur: URL invalide - {e}")
            sys.exit(1)

        # 2. Authentification
        needs_auth_input = input("Login ? (Y/N): ").strip().upper()
        needs_auth = needs_auth_input == 'Y'

        if needs_auth:
            default_user = "etInfo"
            user = input(f"Login [{default_user}]: ").strip() or default_user
            password = input("Mdp: ").strip()
            if not password:
                print("Erreur: Le mot de passe ne peut pas être vide!")
                sys.exit(1)
        else:
            user = None
            password = None

        # 3. Dossier de sortie
        default_output = "sortie"
        output_dir = input(f"Sortie [{default_output}]: ").strip() or default_output

        # 4. Setup CSS
        setup_css_input = input("Setup custom CSS ? (Y/N): ").strip().upper()
        setup_css = setup_css_input == 'Y'

        # 5. Conversion XML vers HTML
        convert_xml_input = input("XML to HTML (si c'est du xml) ? (Y/N): ").strip().upper()
        convert_xml = convert_xml_input == 'Y'

    print()
    print("="*60)
    print("Lancement du crawler...")
    print("="*60)
    print()

    # Construire la commande du crawler
    crawler_script = os.path.join(scripts_dir, "crawler.py")
    cmd = [sys.executable, crawler_script, site_url, output_dir]

    if needs_auth and user and password:
        cmd.extend([user, password])

    # Lancer les étapes
    try:
        print("ÉTAPE 1: Crawling des pages...")
        print("="*60)
        subprocess.run(cmd, check=True)

        # Conversion XML → HTML (optionnelle)
        if convert_xml:
            print()
            print("="*60)
            print("ÉTAPE 2: Conversion XML → HTML...")
            print("="*60)
            converter_script = os.path.join(scripts_dir, "xml_to_html_converter.py")
            subprocess.run([sys.executable, converter_script, output_dir], check=True)

        # Téléchargement des images (si authentification)
        if needs_auth and user and password:
            print()
            print("="*60)
            print("ÉTAPE 3: Téléchargement des images...")
            print("="*60)
            images_script = os.path.join(scripts_dir, "download_images.py")
            subprocess.run([sys.executable, images_script, output_dir, user, password], check=True)

        # Configuration du CSS (optionnelle)
        if setup_css:
            print()
            print("="*60)
            print("ÉTAPE 4: Configuration du CSS personnalisé...")
            print("="*60)
            css_setup_script = os.path.join(scripts_dir, "setup_custom_css.py")
            subprocess.run([sys.executable, css_setup_script, output_dir], check=True)

        print()
        print("="*60)
        print("TERMINÉ !")
        print("="*60)
        print(f"Les fichiers sont disponibles dans: {output_dir}")

    except subprocess.CalledProcessError as e:
        print(f"\nErreur lors de l'exécution: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\nErreur: Impossible de trouver un script: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAnnulé par l'utilisateur")
        sys.exit(0)

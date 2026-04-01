#!/usr/bin/env python3
"""
Launcher interactif pour le crawler.
Double-clique sur ce fichier pour lancer le crawler facilement.
"""

import os
import sys
import subprocess

def main():
    print("="*60)
    print("CRAWLER IUT2 - LAUNCHER INTERACTIF")
    print("="*60)
    print()

    # Demander le dossier de sortie
    default_output = "sortie"
    output_dir = input(f"Dossier de sortie [{default_output}]: ").strip() or default_output

    # Demander l'identifiant
    default_user = "etInfo"
    user = input(f"Identifiant [{default_user}]: ").strip() or default_user

    # Demander le mot de passe
    password = input("Mot de passe: ").strip()
    if not password:
        print("Erreur: Le mot de passe ne peut pas être vide!")
        sys.exit(1)

    # Demander le mode PDF (optionnel)
    pdf_only = input("Mode PDF uniquement ? (o/N): ").strip().lower() == 'o'

    print()
    print("="*60)
    print("Lancement du crawler...")
    print("="*60)
    print()

    # Construire la commande
    crawler_script = os.path.join(os.path.dirname(__file__), "crawler.py")
    cmd = [sys.executable, crawler_script, output_dir, user, password]

    if pdf_only:
        cmd.append("--pdf-only")

    # Lancer le crawler
    try:
        print("ÉTAPE 1/4: Crawling des pages...")
        print("="*60)
        subprocess.run(cmd, check=True)

        print()
        print("="*60)
        print("ÉTAPE 2/4: Conversion XML → HTML...")
        print("="*60)
        converter_script = os.path.join(os.path.dirname(__file__), "xml_to_html_converter.py")
        subprocess.run([sys.executable, converter_script, output_dir], check=True)

        print()
        print("="*60)
        print("ÉTAPE 3/4: Téléchargement des images...")
        print("="*60)
        images_script = os.path.join(os.path.dirname(__file__), "download_images.py")
        subprocess.run([sys.executable, images_script, output_dir, user, password], check=True)

        print()
        print("="*60)
        print("ÉTAPE 4/4: Nettoyage HTML et application du CSS personnalisé...")
        print("="*60)
        cleaner_script = os.path.join(os.path.dirname(__file__), "clean_html.py")
        subprocess.run([sys.executable, cleaner_script, output_dir], check=True)

        print()
        print("="*60)
        print("✓ TERMINÉ !")
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

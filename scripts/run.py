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
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\nErreur lors de l'exécution: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\nErreur: Impossible de trouver crawler.py")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAnnulé par l'utilisateur")
        sys.exit(0)

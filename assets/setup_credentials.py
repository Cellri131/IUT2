#!/usr/bin/env python3
"""
setup_credentials.py - Configure les identifiants pour le rafraîchissement

Ce script sauvegarde les identifiants une seule fois.
Ils seront utilisés automatiquement pour tous les rafraîchissements.

Usage:
    python setup_credentials.py
"""

import json
import sys
import platform
from pathlib import Path


def setup_credentials():
    """Configure les identifiants."""
    script_dir = Path(__file__).parent.absolute()
    credentials_file = script_dir / ".credentials.json"

    print(f"\n{'='*60}")
    print(f"CONFIGURATION DES IDENTIFIANTS")
    print(f"{'='*60}")
    print(f"Ces identifiants seront utilisés pour télécharger les pages")
    print(f"depuis le serveur diw.iut.univ-lehavre.fr")
    print(f"{'='*60}\n")

    # Vérifier si les identifiants existent déjà
    if credentials_file.exists():
        try:
            with open(credentials_file, 'r') as f:
                existing = json.load(f)
            print(f"Identifiants existants trouvés :")
            print(f"  Utilisateur: {existing.get('user', '???')}")
            print()
            response = input("Voulez-vous les remplacer ? (o/N) : ").strip().lower()
            if response not in ['o', 'oui', 'y', 'yes']:
                print("\nIdentifiants conservés. Rien n'a été modifié.")
                return True
        except Exception as e:
            print(f"[AVERTISSEMENT] Fichier existant illisible: {e}")

    # Demander les identifiants
    print("Entrez vos identifiants :")
    user = input("  Utilisateur : ").strip()

    if not user:
        print("[ERREUR] L'utilisateur ne peut pas être vide.")
        return False

    # Demander le mot de passe (sans l'afficher)
    try:
        import getpass
        password = getpass.getpass("  Mot de passe : ")
    except:
        # Fallback si getpass ne fonctionne pas
        password = input("  Mot de passe : ").strip()

    if not password:
        print("[ERREUR] Le mot de passe ne peut pas être vide.")
        return False

    # Sauvegarder
    try:
        with open(credentials_file, 'w') as f:
            json.dump({'user': user, 'password': password}, f, indent=2)

        # Rendre le fichier lisible uniquement par l'utilisateur (Linux/Mac)
        if platform.system() != 'Windows':
            import os
            os.chmod(credentials_file, 0o600)

        print(f"\n{'='*60}")
        print(f"[SUCCESS] Identifiants sauvegardés !")
        print(f"Fichier: {credentials_file}")
        print(f"{'='*60}")
        print(f"\nVous n'aurez plus besoin de les rentrer pour les")
        print(f"rafraîchissements de pages.")
        print(f"{'='*60}\n")

        return True

    except Exception as e:
        print(f"\n[ERREUR] Impossible de sauvegarder : {e}")
        return False


def main():
    success = setup_credentials()

    # Pause sur Windows
    if platform.system() == 'Windows' and sys.stdin.isatty():
        input("\nAppuyez sur Entrée pour fermer...")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

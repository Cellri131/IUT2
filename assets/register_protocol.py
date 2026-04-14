#!/usr/bin/env python3
"""
register_protocol.py - Enregistre le protocole iut-refresh://

Compatible Windows et Linux.

Usage:
    python register_protocol.py           # Enregistrer
    python register_protocol.py --unregister  # Supprimer

Ce script permet au navigateur de lancer refresh_page.py
directement en cliquant sur le bouton de rafraîchissement.
"""

import os
import sys
import platform
from pathlib import Path


def get_handler_command():
    """Retourne la commande pour le handler selon l'OS."""
    script_dir = Path(__file__).parent.absolute()
    refresh_script = script_dir / "refresh_page.py"

    if platform.system() == 'Windows':
        return f'python "{refresh_script}" "%1"'
    else:
        return f'python3 "{refresh_script}" "%s"'


def register_windows():
    """Enregistre le protocole sur Windows."""
    import winreg

    script_dir = Path(__file__).parent.absolute()
    handler_bat = script_dir / "refresh_handler.bat"

    # Créer le fichier .bat
    bat_content = f'''@echo off
cd /d "{script_dir}"
python refresh_page.py %1
if errorlevel 1 py refresh_page.py %1
'''
    with open(handler_bat, 'w') as f:
        f.write(bat_content)

    protocol = "iut-refresh"
    command = f'"{handler_bat}" "%1"'

    try:
        # Créer la clé principale
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"URL:{protocol} Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

        # Créer la sous-clé shell\open\command
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}\\shell\\open\\command") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)

        print(f"[SUCCESS] Protocole {protocol}:// enregistré sur Windows")
        return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False


def unregister_windows():
    """Supprime le protocole sur Windows."""
    import winreg

    protocol = "iut-refresh"

    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}\\shell\\open\\command")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}\\shell\\open")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}\\shell")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}")
        print(f"[SUCCESS] Protocole {protocol}:// supprimé")
        return True
    except FileNotFoundError:
        print(f"[INFO] Le protocole n'était pas enregistré")
        return True
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False


def register_linux():
    """Enregistre le protocole sur Linux."""
    script_dir = Path(__file__).parent.absolute()
    refresh_script = script_dir / "refresh_page.py"

    # Créer le fichier .desktop
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)

    desktop_file = desktop_dir / "iut-refresh.desktop"
    desktop_content = f'''[Desktop Entry]
Type=Application
Name=IUT Refresh Handler
Exec=python3 "{refresh_script}" %u
StartupNotify=false
MimeType=x-scheme-handler/iut-refresh;
NoDisplay=true
'''

    try:
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)

        # Rendre exécutable
        os.chmod(desktop_file, 0o755)
        os.chmod(refresh_script, 0o755)

        # Mettre à jour la base de données MIME
        os.system('update-desktop-database ~/.local/share/applications/ 2>/dev/null')

        # Enregistrer le handler avec xdg-mime
        os.system('xdg-mime default iut-refresh.desktop x-scheme-handler/iut-refresh 2>/dev/null')

        print(f"[SUCCESS] Protocole iut-refresh:// enregistré sur Linux")
        print(f"          Fichier: {desktop_file}")
        return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False


def unregister_linux():
    """Supprime le protocole sur Linux."""
    desktop_file = Path.home() / ".local" / "share" / "applications" / "iut-refresh.desktop"

    try:
        if desktop_file.exists():
            desktop_file.unlink()
            os.system('update-desktop-database ~/.local/share/applications/ 2>/dev/null')
            print(f"[SUCCESS] Protocole supprimé")
        else:
            print(f"[INFO] Le protocole n'était pas enregistré")
        return True
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False


def main():
    unregister = len(sys.argv) > 1 and sys.argv[1] == "--unregister"

    print(f"\n{'='*60}")
    if unregister:
        print(f"SUPPRESSION DU PROTOCOLE iut-refresh://")
    else:
        print(f"ENREGISTREMENT DU PROTOCOLE iut-refresh://")
    print(f"{'='*60}")
    print(f"Système: {platform.system()}")

    if platform.system() == 'Windows':
        if unregister:
            success = unregister_windows()
        else:
            success = register_windows()
    else:
        if unregister:
            success = unregister_linux()
        else:
            success = register_linux()

    if success and not unregister:
        print(f"\nLe bouton de rafraîchissement lancera maintenant")
        print(f"automatiquement le script Python.")

    print(f"{'='*60}\n")

    # Pause sur Windows
    if platform.system() == 'Windows' and sys.stdin.isatty():
        input("Appuyez sur Entrée pour fermer...")


if __name__ == "__main__":
    main()

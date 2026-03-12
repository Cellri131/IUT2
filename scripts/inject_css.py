#!/usr/bin/env python3
"""
inject_css.py – Injecte un lien vers la feuille de style custom
dans tous les fichiers HTML du miroir.

Usage :
    python scripts/inject_css.py site/diw.iut.univ-lehavre.fr
"""
import os
import sys
import re

# Chemin relatif depuis chaque fichier HTML vers la CSS custom
# La CSS sera copiée à la racine du site miroir
CSS_FILENAME = "custom-style.css"


def relative_css_path(html_path: str, site_root: str) -> str:
    """Calcule le chemin relatif entre un fichier HTML et la CSS à la racine."""
    rel = os.path.relpath(site_root, os.path.dirname(html_path))
    return os.path.join(rel, CSS_FILENAME).replace("\\", "/")


def inject(html_path: str, site_root: str) -> bool:
    """Injecte le <link> custom dans un fichier HTML. Renvoie True si modifié."""
    with open(html_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Ne pas ré-injecter si déjà présent
    if CSS_FILENAME in content:
        return False

    css_href = relative_css_path(html_path, site_root)
    link_tag = f'<link rel="stylesheet" href="{css_href}" />'

    # Insère juste avant </head> (ou à la fin de <head>)
    if re.search(r"</head>", content, re.IGNORECASE):
        content = re.sub(
            r"(</head>)",
            f"  {link_tag}\n\\1",
            content,
            count=1,
            flags=re.IGNORECASE,
        )
    elif re.search(r"<head[^>]*>", content, re.IGNORECASE):
        content = re.sub(
            r"(<head[^>]*>)",
            f"\\1\n  {link_tag}",
            content,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        # Pas de <head> : on préfixe le document
        content = f"{link_tag}\n{content}"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def main():
    if len(sys.argv) < 2:
        print(f"Usage : python {sys.argv[0]} <répertoire_site_miroir>")
        sys.exit(1)

    site_root = os.path.abspath(sys.argv[1])

    if not os.path.isdir(site_root):
        print(f"Erreur : {site_root} n'est pas un répertoire.")
        sys.exit(1)

    count = 0
    for dirpath, _, filenames in os.walk(site_root):
        for fn in filenames:
            if fn.lower().endswith((".html", ".htm")):
                fpath = os.path.join(dirpath, fn)
                if inject(fpath, site_root):
                    count += 1
                    print(f"  ✓ {os.path.relpath(fpath, site_root)}")

    print(f"\n==> {count} fichier(s) modifié(s).")


if __name__ == "__main__":
    main()

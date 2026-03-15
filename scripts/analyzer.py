#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyseur pour les résultats du crawler
Génère des rapports et visualisations de l'arbre du site

Usage :
    python scripts/analyzer.py <results_dir>
"""

import sys
import json
import csv
import urllib.parse
from collections import defaultdict, Counter
from pathlib import Path
import re


class SiteAnalyzer:
    def __init__(self, json_file=None, csv_file=None):
        self.results = []
        self.load_data(json_file, csv_file)

    def load_data(self, json_file, csv_file):
        """Charge les données depuis les fichiers de résultats"""
        if json_file and Path(json_file).exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    self.results = json.load(f)
                print(f"✓ Données chargées depuis {json_file}")
                return
            except Exception as e:
                print(f"✗ Erreur lors du chargement de {json_file}: {e}")

        if csv_file and Path(csv_file).exists():
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.results = list(reader)
                    # Convertir les types
                    for result in self.results:
                        try:
                            result['status_code'] = int(result['status_code'])
                        except:
                            pass  # Garder comme string pour ERROR/TIMEOUT
                        try:
                            result['content_length'] = int(result['content_length'])
                        except:
                            result['content_length'] = 0
                print(f"✓ Données chargées depuis {csv_file}")
                return
            except Exception as e:
                print(f"✗ Erreur lors du chargement de {csv_file}: {e}")

        if not self.results:
            print("⚠ Aucune donnée chargée")

    def generate_tree_structure(self):
        """Génère une structure d'arbre du site"""
        tree = {}

        for result in self.results:
            url = result['url']
            parsed = urllib.parse.urlparse(url)
            path = parsed.path.strip('/')

            if not path:
                path = 'index'

            # Diviser le chemin en segments
            segments = path.split('/')

            # Construire la hiérarchie
            current_level = tree

            for i, segment in enumerate(segments):
                if i == len(segments) - 1:
                    # C'est la page finale
                    if segment not in current_level:
                        current_level[segment] = []

                    if isinstance(current_level[segment], list):
                        current_level[segment].append({
                            'url': url,
                            'status': result['status_code'],
                            'content_type': result.get('content_type', ''),
                            'size': result.get('content_length', 0)
                        })
                    else:
                        # Convertir en liste si c'était un dict
                        temp_dict = current_level[segment]
                        current_level[segment] = [{
                            'url': url,
                            'status': result['status_code'],
                            'content_type': result.get('content_type', ''),
                            'size': result.get('content_length', 0)
                        }]
                else:
                    # C'est un dossier
                    if segment not in current_level:
                        current_level[segment] = {}
                    elif isinstance(current_level[segment], list):
                        # Si c'était une liste (fichier), on garde le dossier parent
                        current_level[segment + "_files"] = current_level[segment]
                        current_level[segment] = {}
                    current_level = current_level[segment]

        return tree

    def print_tree(self, tree=None, indent=0, max_depth=10):
        """Affiche l'arbre du site"""
        if tree is None:
            tree = self.generate_tree_structure()

        if indent > max_depth:
            return

        for key, value in sorted(tree.items()):
            prefix = "  " * indent + "├── "

            if isinstance(value, list):
                # C'est une page finale
                for page in value:
                    status_color = ""
                    if page['status'] == 200:
                        status_color = "✓"
                    elif page['status'] in ['ERROR', 'TIMEOUT']:
                        status_color = "✗"
                    else:
                        status_color = f"({page['status']})"

                    size_str = ""
                    if page['size'] > 0:
                        if page['size'] > 1024*1024:
                            size_str = f" [{page['size']//1024//1024}MB]"
                        elif page['size'] > 1024:
                            size_str = f" [{page['size']//1024}KB]"
                        else:
                            size_str = f" [{page['size']}B]"

                    print(f"{prefix}{key} {status_color}{size_str}")
            else:
                # C'est un dossier
                print(f"{prefix}{key}/")
                self.print_tree(value, indent + 1, max_depth)

    def generate_statistics(self):
        """Génère des statistiques sur le crawling"""
        if not self.results:
            return {}

        stats = {
            'total_pages': len(self.results),
            'status_codes': Counter(),
            'content_types': Counter(),
            'extensions': Counter(),
            'directories': Counter(),
            'total_size': 0,
            'largest_pages': [],
            'errors': []
        }

        for result in self.results:
            url = result['url']
            status = result['status_code']
            content_type = result.get('content_type', '').split(';')[0].strip()
            size = result.get('content_length', 0)

            # Statistiques des codes de statut
            stats['status_codes'][status] += 1

            # Statistiques des types de contenu
            if content_type:
                stats['content_types'][content_type] += 1

            # Statistiques des extensions
            parsed = urllib.parse.urlparse(url)
            path = parsed.path
            if '.' in path:
                ext = path.split('.')[-1].lower()
                if len(ext) <= 5:  # Extensions raisonnables
                    stats['extensions'][ext] += 1
            else:
                stats['extensions']['no_extension'] += 1

            # Statistiques des répertoires
            directory = '/'.join(path.split('/')[:-1]) if '/' in path else '/'
            stats['directories'][directory] += 1

            # Taille totale
            stats['total_size'] += size

            # Pages les plus volumineuses
            if size > 0:
                stats['largest_pages'].append((url, size))

            # Erreurs
            if status in ['ERROR', 'TIMEOUT'] or (isinstance(status, int) and status >= 400):
                stats['errors'].append((url, status))

        # Trier les plus grandes pages
        stats['largest_pages'].sort(key=lambda x: x[1], reverse=True)
        stats['largest_pages'] = stats['largest_pages'][:10]

        return stats

    def print_statistics(self):
        """Affiche les statistiques"""
        stats = self.generate_statistics()

        if not stats:
            print("⚠ Aucune statistique disponible")
            return

        print(f"\n{'='*60}")
        print(f"STATISTIQUES DU SITE")
        print(f"{'='*60}")

        print(f"Total des pages crawlées: {stats['total_pages']}")
        print(f"Taille totale: {self.format_size(stats['total_size'])}")

        print(f"\n📊 Codes de statut:")
        for status, count in stats['status_codes'].most_common():
            percentage = (count / stats['total_pages']) * 100
            print(f"  {status}: {count} ({percentage:.1f}%)")

        print(f"\n📄 Types de contenu:")
        for content_type, count in stats['content_types'].most_common(10):
            percentage = (count / stats['total_pages']) * 100
            print(f"  {content_type}: {count} ({percentage:.1f}%)")

        print(f"\n📁 Extensions de fichiers:")
        for ext, count in stats['extensions'].most_common(10):
            percentage = (count / stats['total_pages']) * 100
            print(f"  .{ext}: {count} ({percentage:.1f}%)")

        print(f"\n📂 Répertoires principaux:")
        for directory, count in stats['directories'].most_common(10):
            percentage = (count / stats['total_pages']) * 100
            print(f"  {directory}: {count} pages ({percentage:.1f}%)")

        if stats['largest_pages']:
            print(f"\n📦 Pages les plus volumineuses:")
            for url, size in stats['largest_pages']:
                print(f"  {self.format_size(size)}: {url}")

        if stats['errors']:
            print(f"\n❌ Erreurs ({len(stats['errors'])}):")
            for url, status in stats['errors'][:10]:
                print(f"  {status}: {url}")
            if len(stats['errors']) > 10:
                print(f"  ... et {len(stats['errors']) - 10} autres erreurs")

    def format_size(self, size):
        """Formate une taille en octets"""
        if size >= 1024*1024*1024:
            return f"{size/1024/1024/1024:.1f} GB"
        elif size >= 1024*1024:
            return f"{size/1024/1024:.1f} MB"
        elif size >= 1024:
            return f"{size/1024:.1f} KB"
        else:
            return f"{size} B"

    def export_sitemap(self, filename):
        """Exporte une sitemap simple"""
        urls = [result['url'] for result in self.results if result['status_code'] == 200]
        urls.sort()

        with open(filename, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(url + '\n')

        print(f"✓ Sitemap exportée dans {filename} ({len(urls)} URLs)")

    def find_broken_links(self):
        """Identifie les liens cassés"""
        broken = []
        for result in self.results:
            status = result['status_code']
            if status in ['ERROR', 'TIMEOUT'] or (isinstance(status, int) and status >= 400):
                broken.append(result)

        if broken:
            print(f"\n🔗 Liens cassés ({len(broken)}):")
            for link in broken[:20]:  # Limiter l'affichage
                print(f"  {link['status_code']}: {link['url']}")
            if len(broken) > 20:
                print(f"  ... et {len(broken) - 20} autres liens cassés")
        else:
            print("\n✅ Aucun lien cassé trouvé")

        return broken


def main():
    """Fonction principale d'analyse"""
    print("Analyseur des résultats du crawler")
    print("="*40)

    # Déterminer le répertoire des résultats
    if len(sys.argv) > 1:
        results_dir = sys.argv[1]
    else:
        # Chercher dans le répertoire site par défaut
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        results_dir = project_root / "site"

    results_dir = Path(results_dir)

    # Chercher les fichiers de résultats
    json_file = results_dir / "crawl_results.json"
    csv_file = results_dir / "crawl_results.csv"

    print(f"Répertoire des résultats: {results_dir}")

    # Créer l'analyseur
    analyzer = SiteAnalyzer(json_file, csv_file)

    if not analyzer.results:
        print("\n⚠ Aucune donnée trouvée. Lancez d'abord crawler.py")
        print(f"   Recherché dans: {results_dir}")
        return

    # Afficher les statistiques
    analyzer.print_statistics()

    # Afficher l'arbre du site
    print(f"\n{'='*60}")
    print(f"STRUCTURE DU SITE")
    print(f"{'='*60}")
    analyzer.print_tree(max_depth=6)

    # Liens cassés
    analyzer.find_broken_links()

    # Exporter la sitemap
    sitemap_file = results_dir / "sitemap.txt"
    analyzer.export_sitemap(sitemap_file)

    print(f"\n{'='*60}")
    print("✓ Analyse terminée!")


if __name__ == "__main__":
    main()

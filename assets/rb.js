// rb.js - Gestion du thème, toolbar, refresh API, sidebar navigation et améliorations UX
(function() {
  'use strict';

  var navigationData = null; // Stockage de l'arbre de navigation

  // Créer l'overlay dès le chargement
  var pageTransitionOverlay = null;

  // ========== Transitions de page avec effet DONUT ==========
  function initPageTransitions() {
    // Créer l'overlay de transition
    if (!pageTransitionOverlay) {
      pageTransitionOverlay = document.createElement('div');
      pageTransitionOverlay.className = 'page-transition-overlay';
      document.body.appendChild(pageTransitionOverlay);
    }

    // Intercepter les clics sur les liens internes
    document.addEventListener('click', function(e) {
      var target = e.target.closest('a');
      if (!target) return;

      var href = target.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('http') || href.startsWith('mailto')) return;

      e.preventDefault();

      // Calculer la position du clic en pourcentage
      var absoluteX = (e.clientX / window.innerWidth) * 100;
      var absoluteY = (e.clientY / window.innerHeight) * 100;

      // Sauvegarder la position pour la page suivante
      sessionStorage.setItem('transitionClickX', absoluteX + '%');
      sessionStorage.setItem('transitionClickY', absoluteY + '%');
      sessionStorage.setItem('transitionInProgress', 'true');

      pageTransitionOverlay.style.setProperty('--click-x', absoluteX + '%');
      pageTransitionOverlay.style.setProperty('--click-y', absoluteY + '%');

      // Rendre l'overlay visible
      pageTransitionOverlay.style.opacity = '1';
      pageTransitionOverlay.style.pointerEvents = 'all';

      // Animation du donut avec JS (plus fiable que CSS @keyframes avec variables)
      var startTime = Date.now();
      var duration = 1200;
      var holeSize = 15;
      var startRadius = 40;
      var endRadius = 150 * Math.max(window.innerWidth, window.innerHeight) / 100;

      function animateDonut() {
        var elapsed = Date.now() - startTime;
        var progress = Math.min(elapsed / duration, 1);
        var easedProgress = 1 - Math.pow(1 - progress, 3); // ease-out cubic

        var currentRadius = startRadius + (endRadius - startRadius) * easedProgress;
        var mask = 'radial-gradient(circle at ' + absoluteX + '% ' + absoluteY + '%, transparent 0, transparent ' + holeSize + 'px, black ' + holeSize + 'px, black ' + currentRadius + 'px)';

        pageTransitionOverlay.style.webkitMaskImage = mask;
        pageTransitionOverlay.style.maskImage = mask;

        if (progress < 1) {
          requestAnimationFrame(animateDonut);
        } else {
          // Animation terminée, naviguer
          window.location.href = href;
        }
      }

      requestAnimationFrame(animateDonut);
    });
  }

  // Fonction pour lancer l'animation de reveal une fois la page chargée
  function revealNewPage() {
    var hasTransition = sessionStorage.getItem('transitionInProgress');

    if (hasTransition === 'true') {
      // Récupérer la position du clic
      var clickX = sessionStorage.getItem('transitionClickX') || '50%';
      var clickY = sessionStorage.getItem('transitionClickY') || '50%';

      // Créer l'overlay si pas déjà fait
      if (!pageTransitionOverlay) {
        pageTransitionOverlay = document.createElement('div');
        pageTransitionOverlay.className = 'page-transition-overlay';
        document.body.appendChild(pageTransitionOverlay);
      }

      // Mettre l'overlay en plein écran bleu avec le donut (trou petit)
      pageTransitionOverlay.style.opacity = '1';
      pageTransitionOverlay.style.pointerEvents = 'all';

      var holeSize = 15;
      var maxRadius = 150 * Math.max(window.innerWidth, window.innerHeight) / 100;

      // État initial : grand donut (petit trou, grand extérieur)
      var initialMask = 'radial-gradient(circle at ' + clickX + ' ' + clickY + ', transparent 0, transparent ' + holeSize + 'px, black ' + holeSize + 'px, black ' + maxRadius + 'px)';
      pageTransitionOverlay.style.webkitMaskImage = initialMask;
      pageTransitionOverlay.style.maskImage = initialMask;

      // Animation du trou qui grandit avec JS
      setTimeout(function() {
        var startTime = Date.now();
        var duration = 1200;

        function animateHole() {
          var elapsed = Date.now() - startTime;
          var progress = Math.min(elapsed / duration, 1);
          var easedProgress = 1 - Math.pow(1 - progress, 3); // ease-out cubic

          var currentHole = holeSize + (maxRadius - holeSize) * easedProgress;
          var mask = 'radial-gradient(circle at ' + clickX + ' ' + clickY + ', transparent 0, transparent ' + currentHole + 'px, black ' + currentHole + 'px, black ' + maxRadius + 'px)';

          pageTransitionOverlay.style.webkitMaskImage = mask;
          pageTransitionOverlay.style.maskImage = mask;

          if (progress < 1) {
            requestAnimationFrame(animateHole);
          } else {
            // Animation terminée, nettoyer
            pageTransitionOverlay.style.opacity = '0';
            pageTransitionOverlay.style.webkitMaskImage = 'none';
            pageTransitionOverlay.style.maskImage = 'none';
            pageTransitionOverlay.style.pointerEvents = 'none';

            // Nettoyer le sessionStorage
            sessionStorage.removeItem('transitionClickX');
            sessionStorage.removeItem('transitionClickY');
            sessionStorage.removeItem('transitionInProgress');
          }
        }

        requestAnimationFrame(animateHole);
      }, 100);
    }
  }

  document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    setupToolbar();
    loadNavigationTree();
    enhanceImages();
    animateElements();
    initFavorites();
    initPageTransitions();
    initScrollAnimations();
    initMagneticButtons();
    initCustomCursor();
  });

  // Attendre que TOUT soit chargé avant de révéler la page
  window.addEventListener('load', function() {
    revealNewPage();
  });

  // ========== Gestion du thème ==========
  function initTheme() {
    // Prioriser themeLevel pour éviter de réinitialiser aux valeurs extrêmes
    var savedLevel = localStorage.getItem('themeLevel');
    var themeLevel = 1;

    if (savedLevel) {
      // Utiliser le niveau sauvegardé directement
      themeLevel = parseInt(savedLevel, 10);
    } else {
      // Migration de l'ancien système (dark/light) vers le nouveau (niveau 1-5)
      var saved = localStorage.getItem('theme');
      if (saved === 'dark') {
        themeLevel = 5;
      } else if (saved === 'light') {
        themeLevel = 1;
      } else {
        // Utiliser la préférence système
        var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        themeLevel = prefersDark ? 5 : 1;
      }
    }

    setTheme(themeLevel);

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
      if (!localStorage.getItem('themeLevel')) setTheme(e.matches ? 5 : 1);
    });
  }

  function setTheme(level) {
    var html = document.documentElement;
    var btn = document.querySelector('.theme-toggle');

    // Assurer que le niveau est entre 1 et 5
    level = Math.max(1, Math.min(5, level));

    // Appliquer le thème
    if (level === 1) {
      html.removeAttribute('data-theme');
    } else {
      html.setAttribute('data-theme', 'level' + level);
    }

    // Sauvegarder le niveau
    localStorage.setItem('themeLevel', level.toString());
    // Supprimer l'ancien 'theme' pour éviter les conflits
    localStorage.removeItem('theme');

    // Mettre à jour le bouton
    if (btn) {
      updateThemeButton(btn, level);
    }
  }

  function updateThemeButton(btn, level) {
    var labels = ['', 'Clair', 'Léger', 'Moyen', 'Foncé', 'Sombre'];

    btn.innerHTML =
      '<div class="theme-label">' + labels[level] + '</div>' +
      '<div class="theme-level-indicator">' +
        '<span class="theme-level-dot' + (level === 1 ? ' active' : '') + '"></span>' +
        '<span class="theme-level-dot' + (level === 2 ? ' active' : '') + '"></span>' +
        '<span class="theme-level-dot' + (level === 3 ? ' active' : '') + '"></span>' +
        '<span class="theme-level-dot' + (level === 4 ? ' active' : '') + '"></span>' +
        '<span class="theme-level-dot' + (level === 5 ? ' active' : '') + '"></span>' +
      '</div>';
  }

  function toggleTheme() {
    var currentLevel = parseInt(localStorage.getItem('themeLevel') || '1', 10);
    var nextLevel = currentLevel >= 5 ? 1 : currentLevel + 1;
    setTheme(nextLevel);
  }

  // ========== Toolbar ==========
  function setupToolbar() {
    if (document.querySelector('.toolbar')) return;

    var toolbar = document.createElement('div');
    toolbar.className = 'toolbar';

    // Bouton hamburger (navigation)
    var menuBtn = document.createElement('button');
    menuBtn.className = 'btn menu-button';
    menuBtn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>';
    menuBtn.title = 'Navigation (Alt+N)';
    menuBtn.onclick = toggleSidebar;

    // Bouton retour
    var backBtn = document.createElement('button');
    backBtn.className = 'btn back-button';
    backBtn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19 12H5M12 19l-7-7 7-7"/></svg> Retour';
    backBtn.onclick = function() { history.back(); };

    // Conteneur pour les favoris (sera rempli dynamiquement)
    var favoritesContainer = document.createElement('div');
    favoritesContainer.className = 'favorites-container';
    favoritesContainer.id = 'favorites-container';

    // Bouton favori
    var favoriteBtn = document.createElement('button');
    favoriteBtn.className = 'btn favorite-button';
    favoriteBtn.id = 'favorite-button';
    favoriteBtn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>';
    favoriteBtn.title = 'Ajouter aux favoris (Alt+F)';
    favoriteBtn.onclick = toggleFavorite;

    // Bouton thème
    var themeBtn = document.createElement('button');
    themeBtn.className = 'btn theme-toggle';
    themeBtn.title = 'Changer le thème (Alt+T) - Cliquer pour passer au niveau suivant';
    themeBtn.onclick = toggleTheme;

    // Bouton rafraîchir
    var refreshBtn = document.createElement('button');
    refreshBtn.className = 'btn refresh-button';
    refreshBtn.innerHTML = '<svg class="refresh-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>';
    refreshBtn.title = 'Rafraîchir depuis le serveur (Alt+R)';
    refreshBtn.onclick = refreshPage;

    toolbar.appendChild(menuBtn);
    toolbar.appendChild(backBtn);
    toolbar.appendChild(favoritesContainer);
    toolbar.appendChild(favoriteBtn);
    toolbar.appendChild(themeBtn);
    toolbar.appendChild(refreshBtn);
    document.body.insertBefore(toolbar, document.body.firstChild);

    // Appliquer le thème initial au bouton
    var savedLevel = parseInt(localStorage.getItem('themeLevel') || '1', 10);
    setTheme(savedLevel);
  }

  // ========== Navigation Sidebar ==========
  function loadNavigationTree() {
    // Le fichier navigation.js définit window.NAVIGATION_TREE
    // Il est chargé via <script> dans le HTML (pas de CORS)
    if (window.NAVIGATION_TREE) {
      navigationData = window.NAVIGATION_TREE;
      setupSidebar();
    } else {
      console.warn('Navigation tree not loaded (window.NAVIGATION_TREE not found)');
    }
  }

  function getBasePath() {
    // Calculer le chemin relatif vers la racine pedago
    var path = window.location.pathname;

    // Pour les fichiers locaux (file://), extraire seulement la partie après /pedago/
    if (window.location.protocol === 'file:') {
      var pedagogIndex = path.indexOf('/pedago/');
      if (pedagogIndex !== -1) {
        path = path.substring(pedagogIndex + 7); // +7 pour sauter '/pedago'
      } else {
        // Fallback: chercher juste 'pedago/'
        pedagogIndex = path.indexOf('pedago/');
        if (pedagogIndex !== -1) {
          path = path.substring(pedagogIndex + 6); // +6 pour sauter 'pedago'
        }
      }
    }

    // Compter les niveaux de profondeur
    var parts = path.split('/').filter(Boolean);
    // Retirer le nom du fichier
    if (parts.length > 0 && parts[parts.length - 1].indexOf('.') !== -1) {
      parts.pop();
    }

    var depth = parts.length;
    return depth > 0 ? '../'.repeat(depth) : './';
  }

  function setupSidebar() {
    if (!navigationData) return;
    if (document.querySelector('.nav-sidebar')) return;

    // Créer le sidebar
    var sidebar = document.createElement('div');
    sidebar.className = 'nav-sidebar';

    // Header avec breadcrumb
    var header = document.createElement('div');
    header.className = 'nav-header';
    header.innerHTML = '<h3>Navigation</h3>';

    var breadcrumb = buildBreadcrumb();
    if (breadcrumb) {
      var breadcrumbEl = document.createElement('div');
      breadcrumbEl.className = 'nav-breadcrumb';
      breadcrumbEl.innerHTML = breadcrumb;
      header.appendChild(breadcrumbEl);
    }

    // Champ de recherche
    var searchDiv = document.createElement('div');
    searchDiv.className = 'nav-search';
    var searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.placeholder = 'Rechercher...';
    searchInput.id = 'nav-search-input';
    searchDiv.appendChild(searchInput);
    header.appendChild(searchDiv);

    // Contenu (arbre)
    var content = document.createElement('div');
    content.className = 'nav-content';
    content.id = 'nav-tree-content';
    content.appendChild(buildTree(navigationData));

    // Bouton fermer
    var closeBtn = document.createElement('button');
    closeBtn.className = 'nav-close';
    closeBtn.innerHTML = '×';
    closeBtn.onclick = toggleSidebar;

    sidebar.appendChild(closeBtn);
    sidebar.appendChild(header);
    sidebar.appendChild(content);

    document.body.appendChild(sidebar);

    // Calculer et ajuster la largeur dynamique
    adjustSidebarWidth(sidebar, navigationData);

    // Highlight de la page active
    highlightActivePage();

    // Gestion de la recherche
    searchInput.addEventListener('input', function(e) {
      filterTree(e.target.value);
    });
  }

  function adjustSidebarWidth(sidebar, tree) {
    // Calculer la longueur maximale des noms de dossiers
    var maxLength = 0;

    function getMaxLength(node, depth) {
      depth = depth || 0;
      if (node.name && node.type === 'folder') {
        // Compter la longueur du nom + indentation
        var length = node.name.length + (depth * 2);
        maxLength = Math.max(maxLength, length);
      }
      if (node.children) {
        node.children.forEach(function(child) {
          getMaxLength(child, depth + 1);
        });
      }
    }

    getMaxLength(tree, 0);

    // Largeur de base : 350px
    // Ajouter ~8px par caractère au-delà de 30 caractères
    var baseWidth = 350;
    var extraWidth = Math.max(0, (maxLength - 30) * 8);
    var totalWidth = Math.min(baseWidth + extraWidth, 600); // Max 600px

    sidebar.style.width = totalWidth + 'px';
    sidebar.style.left = '-' + totalWidth + 'px';
  }

  function buildBreadcrumb() {
    var path = window.location.pathname;

    // Pour les fichiers locaux (file://), extraire seulement la partie après /pedago/
    if (window.location.protocol === 'file:') {
      var pedagogIndex = path.indexOf('/pedago/');
      if (pedagogIndex !== -1) {
        path = path.substring(pedagogIndex + 7); // +7 pour sauter '/pedago'
      }
    }

    var parts = path.split('/').filter(Boolean);

    if (parts.length === 0) return '';

    var breadcrumb = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" style="vertical-align:middle;margin-right:4px"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>';
    var currentPath = '';

    parts.forEach(function(part, i) {
      currentPath += '/' + part;
      var displayName = part.replace(/\.[^.]+$/, ''); // Enlever l'extension
      if (i > 0) breadcrumb += ' › ';
      breadcrumb += '<span>' + displayName + '</span>';
    });

    return breadcrumb;
  }

  function buildTree(node, level) {
    level = level || 0;
    var ul = document.createElement('ul');
    ul.className = 'nav-tree-level';
    if (level === 0) ul.classList.add('nav-tree-root');

    // Calculer le chemin de base pour les liens relatifs
    var basePath = getBasePath();

    // Sauvegarder l'état expand/collapse dans localStorage
    var expandedKey = 'nav-expanded-' + node.path;
    var isExpanded = localStorage.getItem(expandedKey) !== 'false';

    if (node.children && node.children.length > 0) {
      node.children.forEach(function(child) {
        // Ne montrer que les dossiers (pas les fichiers individuels)
        if (child.type !== 'folder') return;

        var li = document.createElement('li');
        li.className = 'nav-tree-item';
        li.dataset.path = child.path;

        var folderDiv = document.createElement('div');
        folderDiv.className = 'nav-folder';

        // Icône expand/collapse (seulement si le dossier a des enfants)
        var toggle = document.createElement('span');
        toggle.className = 'nav-toggle';
        if (child.children && child.children.length > 0) {
          toggle.innerHTML = isExpanded ? '▼' : '▶';
          toggle.onclick = function(e) {
            e.stopPropagation();
            toggleFolder(li, child.path);
          };
        } else {
          toggle.innerHTML = ''; // Pas de toggle si pas d'enfants
          toggle.style.width = '16px'; // Garder l'espace
        }

        // Icône dossier
        var icon = document.createElement('span');
        icon.className = 'nav-icon';
        icon.innerHTML = '📁';

        // Nom (cliquable pour aller à index.html)
        var name = document.createElement('span');
        name.textContent = child.name;
        name.style.cursor = 'pointer';
        name.onclick = function() {
          var indexPath = child.path + (child.path.endsWith('/') ? '' : '/') + 'index.html';
          var relativePath = basePath + indexPath.substring(1);
          window.location.href = relativePath;
        };

        folderDiv.appendChild(toggle);
        folderDiv.appendChild(icon);
        folderDiv.appendChild(name);
        li.appendChild(folderDiv);

        // Sous-arbre (si le dossier a des enfants)
        if (child.children && child.children.length > 0) {
          var subtree = buildTree(child, level + 1);
          subtree.style.display = isExpanded ? 'block' : 'none';
          li.appendChild(subtree);
          if (isExpanded) li.classList.add('expanded');
        }

        ul.appendChild(li);
      });
    }

    return ul;
  }

  function toggleFolder(li, path) {
    var isExpanded = li.classList.contains('expanded');
    var toggle = li.querySelector('.nav-toggle');
    var subtree = li.querySelector('.nav-tree-level');

    if (isExpanded) {
      li.classList.remove('expanded');
      toggle.innerHTML = '▶';
      if (subtree) subtree.style.display = 'none';
      localStorage.setItem('nav-expanded-' + path, 'false');
    } else {
      li.classList.add('expanded');
      toggle.innerHTML = '▼';
      if (subtree) subtree.style.display = 'block';
      localStorage.setItem('nav-expanded-' + path, 'true');
    }
  }

  function toggleSidebar() {
    var sidebar = document.querySelector('.nav-sidebar');
    if (!sidebar) return;

    var isOpen = sidebar.classList.contains('open');
    if (isOpen) {
      sidebar.classList.remove('open');
    } else {
      sidebar.classList.add('open');
    }
  }

  function highlightActivePage() {
    var currentPath = window.location.pathname;

    // Pour les fichiers locaux (file://), extraire seulement la partie après /pedago/
    if (window.location.protocol === 'file:') {
      var pedagogIndex = currentPath.indexOf('/pedago/');
      if (pedagogIndex !== -1) {
        currentPath = '/' + currentPath.substring(pedagogIndex + 8); // +8 pour avoir /xxx après /pedago/
      }
    }

    var items = document.querySelectorAll('.nav-tree-item');

    items.forEach(function(item) {
      if (item.dataset.path === currentPath) {
        item.classList.add('active');
        // Expand tous les parents
        var parent = item.parentElement;
        while (parent && parent.classList.contains('nav-tree-level')) {
          parent.style.display = 'block';
          var parentLi = parent.parentElement;
          if (parentLi && parentLi.classList.contains('nav-tree-item')) {
            parentLi.classList.add('expanded');
            var toggle = parentLi.querySelector('.nav-toggle');
            if (toggle) toggle.innerHTML = '▼';
          }
          parent = parentLi ? parentLi.parentElement : null;
        }
      }
    });
  }

  function filterTree(searchText) {
    searchText = searchText.toLowerCase().trim();
    var items = document.querySelectorAll('.nav-tree-item');

    if (!searchText) {
      // Réafficher tout
      items.forEach(function(item) {
        item.style.display = '';
        var subtree = item.querySelector('.nav-tree-level');
        if (subtree) {
          var isExpanded = item.classList.contains('expanded');
          subtree.style.display = isExpanded ? 'block' : 'none';
        }
      });
      return;
    }

    // Filtrer
    items.forEach(function(item) {
      var name = item.textContent.toLowerCase();
      var matches = name.indexOf(searchText) !== -1;

      if (matches) {
        // Afficher l'item
        item.style.display = '';
        // Expand et afficher tous les parents
        var parent = item.parentElement;
        while (parent) {
          if (parent.classList.contains('nav-tree-level')) {
            parent.style.display = 'block';
            var parentLi = parent.parentElement;
            if (parentLi && parentLi.classList.contains('nav-tree-item')) {
              parentLi.style.display = '';
              parentLi.classList.add('expanded');
              var toggle = parentLi.querySelector('.nav-toggle');
              if (toggle) toggle.innerHTML = '▼';
            }
            parent = parentLi ? parentLi.parentElement : null;
          } else {
            break;
          }
        }
      } else {
        // Cacher l'item (sauf s'il a des enfants visibles)
        item.style.display = 'none';
      }
    });
  }

  // ========== Favoris ==========
  function initFavorites() {
    updateFavoriteButton();
    renderFavorites();
  }

  function getFavorites() {
    var stored = localStorage.getItem('favorites');
    return stored ? JSON.parse(stored) : [];
  }

  function saveFavorites(favorites) {
    localStorage.setItem('favorites', JSON.stringify(favorites));
  }

  function getCurrentPageInfo() {
    var path = window.location.pathname;

    // Pour les fichiers locaux, normaliser le chemin
    if (window.location.protocol === 'file:') {
      var pedagogIndex = path.indexOf('/pedago/');
      if (pedagogIndex !== -1) {
        path = path.substring(pedagogIndex);
      }
    }

    // Extraire le nom du dossier parent
    var parts = path.split('/').filter(Boolean);
    var folderName = '';

    // Si on est sur un index.html, prendre le dossier parent
    if (parts.length > 0) {
      var lastPart = parts[parts.length - 1];
      if (lastPart.indexOf('.') !== -1) {
        // C'est un fichier, prendre le dossier parent
        parts.pop();
      }
      if (parts.length > 0) {
        folderName = parts[parts.length - 1];
      }
    }

    var label = extractFolderLabel(folderName);

    return {
      path: path,
      label: label || 'Page'
    };
  }

  function extractFolderLabel(folderName) {
    if (!folderName) return '';
    // Prendre les 5 premiers caractères et les mettre en majuscules
    return folderName.substring(0, 5).toUpperCase();
  }

  function isFavorite(path) {
    var favorites = getFavorites();
    return favorites.some(function(fav) {
      return fav.path === path;
    });
  }

  function toggleFavorite() {
    var pageInfo = getCurrentPageInfo();
    var favorites = getFavorites();
    var index = favorites.findIndex(function(fav) {
      return fav.path === pageInfo.path;
    });

    if (index !== -1) {
      // Retirer des favoris
      favorites.splice(index, 1);
      showNotification('Retiré des favoris', 'info');
    } else {
      // Ajouter aux favoris
      favorites.push(pageInfo);
      showNotification('Ajouté aux favoris', 'success');
    }

    saveFavorites(favorites);
    updateFavoriteButton();
    renderFavorites();
  }

  function updateFavoriteButton() {
    var btn = document.getElementById('favorite-button');
    if (!btn) return;

    var pageInfo = getCurrentPageInfo();
    var isCurrentFavorite = isFavorite(pageInfo.path);

    if (isCurrentFavorite) {
      btn.classList.add('active');
      btn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>';
      btn.title = 'Retirer des favoris (Alt+F)';
    } else {
      btn.classList.remove('active');
      btn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>';
      btn.title = 'Ajouter aux favoris (Alt+F)';
    }
  }

  function renderFavorites() {
    var container = document.getElementById('favorites-container');
    if (!container) return;

    var favorites = getFavorites();
    container.innerHTML = '';

    if (favorites.length === 0) return;

    // Ajouter le séparateur
    var separator = document.createElement('div');
    separator.className = 'favorites-separator';
    container.appendChild(separator);

    // Ajouter chaque favori
    favorites.forEach(function(fav, index) {
      var item = document.createElement('div');
      item.className = 'favorite-item';
      item.textContent = fav.label;
      item.title = fav.path;

      // Clic pour naviguer
      item.onclick = function(e) {
        if (e.target.classList.contains('favorite-item-remove')) return;
        navigateToFavorite(fav.path);
      };

      // Bouton de suppression
      var removeBtn = document.createElement('span');
      removeBtn.className = 'favorite-item-remove';
      removeBtn.innerHTML = '×';
      removeBtn.title = 'Retirer des favoris';
      removeBtn.onclick = function(e) {
        e.stopPropagation();
        removeFavorite(index);
      };

      item.appendChild(removeBtn);
      container.appendChild(item);
    });
  }

  function removeFavorite(index) {
    var favorites = getFavorites();
    favorites.splice(index, 1);
    saveFavorites(favorites);
    updateFavoriteButton();
    renderFavorites();
    showNotification('Favori supprimé', 'info');
  }

  function navigateToFavorite(path) {
    // Calculer le chemin relatif depuis la page actuelle
    var currentPath = window.location.pathname;

    // Pour les fichiers locaux
    if (window.location.protocol === 'file:') {
      var pedagogIndex = currentPath.indexOf('/pedago/');
      if (pedagogIndex !== -1) {
        currentPath = currentPath.substring(pedagogIndex);
      }
    }

    // Calculer le nombre de niveaux à remonter
    var currentParts = currentPath.split('/').filter(Boolean);
    if (currentParts.length > 0 && currentParts[currentParts.length - 1].indexOf('.') !== -1) {
      currentParts.pop(); // Retirer le fichier
    }

    var targetParts = path.split('/').filter(Boolean);
    var depth = currentParts.length;
    var relativePath = depth > 0 ? '../'.repeat(depth) : './';
    relativePath += targetParts.join('/');

    window.location.href = relativePath;
  }


  // ========== Animations au scroll ==========
  function initScrollAnimations() {
    var observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
        }
      });
    }, observerOptions);

    // Observer tous les éléments avec data-scroll
    var scrollElements = document.querySelectorAll('.cadre, .cellule, tbody tr');
    scrollElements.forEach(function(el, index) {
      el.setAttribute('data-scroll', '');
      el.style.transitionDelay = (index * 0.05) + 's';
      observer.observe(el);
    });
  }

  // ========== Boutons magnétiques ==========
  function initMagneticButtons() {
    var buttons = document.querySelectorAll('.btn, .favorite-item');

    buttons.forEach(function(btn) {
      btn.classList.add('btn-magnetic');

      btn.addEventListener('mousemove', function(e) {
        var rect = btn.getBoundingClientRect();
        var x = e.clientX - rect.left - rect.width / 2;
        var y = e.clientY - rect.top - rect.height / 2;

        // Effet magnétique subtil (max 5px)
        var moveX = x * 0.15;
        var moveY = y * 0.15;

        btn.style.transform = 'translate(' + moveX + 'px, ' + moveY + 'px)';
      });

      btn.addEventListener('mouseleave', function() {
        btn.style.transform = 'translate(0, 0)';
      });
    });
  }

  // ========== Curseur personnalisé ==========
  function initCustomCursor() {
    // Désactiver sur mobile
    if ('ontouchstart' in window) return;

    var cursor = document.createElement('div');
    cursor.className = 'custom-cursor';
    document.body.appendChild(cursor);

    var cursorX = 0;
    var cursorY = 0;
    var currentX = 0;
    var currentY = 0;

    document.addEventListener('mousemove', function(e) {
      cursorX = e.clientX;
      cursorY = e.clientY;
    });

    // Animation fluide du curseur
    function animateCursor() {
      var diffX = cursorX - currentX;
      var diffY = cursorY - currentY;

      currentX += diffX * 0.15;
      currentY += diffY * 0.15;

      cursor.style.left = currentX + 'px';
      cursor.style.top = currentY + 'px';

      requestAnimationFrame(animateCursor);
    }

    animateCursor();

    // Effet hover sur les éléments interactifs
    var interactiveElements = document.querySelectorAll('a, button, .btn, .favorite-item, .nav-file, .nav-folder');

    interactiveElements.forEach(function(el) {
      el.addEventListener('mouseenter', function() {
        cursor.classList.add('hover');
      });

      el.addEventListener('mouseleave', function() {
        cursor.classList.remove('hover');
      });
    });
  }

  // ========== Parallaxe subtil au mouvement de la souris ==========
  function initParallax() {
    var parallaxElements = document.querySelectorAll('.cadre, h1, h2');

    parallaxElements.forEach(function(el) {
      el.setAttribute('data-parallax', '');
    });

    document.addEventListener('mousemove', function(e) {
      var x = (e.clientX / window.innerWidth - 0.5) * 20;
      var y = (e.clientY / window.innerHeight - 0.5) * 20;

      parallaxElements.forEach(function(el, index) {
        var depth = (index % 3 + 1) * 0.5;
        el.style.transform = 'translate(' + (x * depth) + 'px, ' + (y * depth) + 'px)';
      });
    });
  }

  // Initialiser le parallaxe (désactivé par défaut, peut être activé si souhaité)
  // initParallax();

  // ========== Rafraîchissement via API serveur ==========
  function refreshPage() {
    var btn = document.querySelector('.refresh-button');
    var icon = btn.querySelector('.refresh-icon');

    btn.disabled = true;
    btn.classList.add('loading');
    icon.style.animation = 'spin 1s linear infinite';

    var pagePath = window.location.pathname;

    fetch('/api/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: pagePath })
    })
    .then(function(resp) { return resp.json(); })
    .then(function(data) {
      if (data.success) {
        showNotification('Page rafraîchie !', 'success');
        setTimeout(function() { window.location.reload(); }, 600);
      } else {
        throw new Error(data.error || 'Erreur inconnue');
      }
    })
    .catch(function(err) {
      showNotification('Erreur: ' + err.message, 'error');
    })
    .finally(function() {
      btn.disabled = false;
      btn.classList.remove('loading');
      icon.style.animation = '';
    });
  }

  // ========== Notifications ==========
  function showNotification(message, type) {
    var old = document.querySelector('.rb-notification');
    if (old) old.remove();

    var icons = { success: '\u2713', error: '\u2717', info: '\u2139' };
    var colors = {
      success: 'linear-gradient(135deg, #10b981, #059669)',
      error:   'linear-gradient(135deg, #ef4444, #dc2626)',
      info:    'linear-gradient(135deg, #3b82f6, #2563eb)'
    };

    var el = document.createElement('div');
    el.className = 'rb-notification';
    el.innerHTML = '<span>' + (icons[type] || '') + '</span> ' + message;
    el.style.cssText = 'position:fixed;bottom:20px;right:20px;padding:12px 20px;border-radius:8px;' +
      'background:' + colors[type] + ';color:#fff;font-weight:500;z-index:10001;' +
      'box-shadow:0 4px 20px rgba(0,0,0,.3);animation:slideInUp .3s ease;' +
      'font-family:"JetBrains Mono",monospace;font-size:14px;';

    document.body.appendChild(el);
    setTimeout(function() { el.remove(); }, 4000);
  }

  // ========== Animations ==========
  function animateElements() {
    document.querySelectorAll('.cadre').forEach(function(el, i) {
      el.style.opacity = '0';
      el.style.animation = 'fadeInUp 0.5s ease forwards';
      el.style.animationDelay = i * 0.1 + 's';
    });
    document.querySelectorAll('tbody tr').forEach(function(el, i) {
      el.style.opacity = '0';
      el.style.animation = 'fadeInUp 0.3s ease forwards';
      el.style.animationDelay = i * 0.05 + 's';
    });
  }

  // ========== Images avec reveal sophistiqué ==========
  function enhanceImages() {
    document.querySelectorAll('img').forEach(function(img) {
      // Wrapper pour l'effet de reveal
      if (!img.parentElement.classList.contains('img-reveal')) {
        var wrapper = document.createElement('div');
        wrapper.className = 'img-reveal';
        img.parentNode.insertBefore(wrapper, img);
        wrapper.appendChild(img);

        // Observer pour déclencher l'animation au scroll
        var observer = new IntersectionObserver(function(entries) {
          entries.forEach(function(entry) {
            if (entry.isIntersecting) {
              wrapper.classList.add('animate');
              observer.unobserve(entry.target);
            }
          });
        }, { threshold: 0.2 });

        observer.observe(wrapper);
      }

      // Gestion du chargement
      if (!img.complete) {
        img.style.opacity = '0';
        img.addEventListener('load', function() {
          this.style.transition = 'opacity 0.6s var(--transition-smooth)';
          this.style.opacity = '1';
        });
      }

      // Erreur de chargement
      img.addEventListener('error', function() {
        this.style.opacity = '0.4';
        this.style.border = '1px dashed var(--border-color)';
        this.title = 'Image non disponible';
      });

      // Modal au clic
      img.addEventListener('click', function() {
        if (this.title !== 'Image non disponible') openModal(this.src, this.alt);
      });
    });
  }

  // ========== Modal Image avec animations ==========
  function openModal(src, alt) {
    var modal = document.createElement('div');
    modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.95);' +
      'display:flex;align-items:center;justify-content:center;z-index:10000;cursor:pointer;padding:20px;' +
      'opacity:0;transition:opacity 0.3s var(--transition-smooth);backdrop-filter:blur(10px);';

    var img = document.createElement('img');
    img.src = src;
    img.alt = alt || '';
    img.style.cssText = 'max-width:90%;max-height:90%;object-fit:contain;border-radius:8px;' +
      'box-shadow:0 20px 60px rgba(0,0,0,.5);transform:scale(0.9);opacity:0;' +
      'transition:all 0.4s var(--transition-smooth);';

    var closeBtn = document.createElement('button');
    closeBtn.innerHTML = '×';
    closeBtn.style.cssText = 'position:absolute;top:20px;right:20px;background:var(--bg-tertiary);' +
      'color:var(--text-primary);border:1px solid var(--border-color);font-size:24px;' +
      'padding:8px 14px;cursor:pointer;border-radius:6px;transition:all 0.2s var(--transition-smooth);' +
      'opacity:0;transform:translateY(-10px);';

    closeBtn.addEventListener('mouseenter', function() {
      this.style.background = 'var(--accent-color)';
      this.style.color = 'white';
      this.style.borderColor = 'var(--accent-color)';
    });

    closeBtn.addEventListener('mouseleave', function() {
      this.style.background = 'var(--bg-tertiary)';
      this.style.color = 'var(--text-primary)';
      this.style.borderColor = 'var(--border-color)';
    });

    function close() {
      modal.style.opacity = '0';
      img.style.transform = 'scale(0.9)';
      img.style.opacity = '0';
      closeBtn.style.opacity = '0';
      setTimeout(function() {
        if (document.body.contains(modal)) document.body.removeChild(modal);
      }, 300);
    }

    modal.appendChild(img);
    modal.appendChild(closeBtn);
    document.body.appendChild(modal);

    // Animations d'entrée
    setTimeout(function() {
      modal.style.opacity = '1';
      img.style.transform = 'scale(1)';
      img.style.opacity = '1';
      closeBtn.style.opacity = '1';
      closeBtn.style.transform = 'translateY(0)';
    }, 10);

    modal.onclick = function(e) { if (e.target === modal) close(); };
    closeBtn.onclick = close;

    document.addEventListener('keydown', function handler(e) {
      if (e.key === 'Escape') {
        close();
        document.removeEventListener('keydown', handler);
      }
    });
  }

  // ========== Raccourcis clavier ==========
  document.addEventListener('keydown', function(e) {
    if (e.altKey && (e.key === 't' || e.key === 'T')) { e.preventDefault(); toggleTheme(); }
    if (e.altKey && e.key === 'ArrowLeft') { e.preventDefault(); history.back(); }
    if (e.altKey && (e.key === 'r' || e.key === 'R')) { e.preventDefault(); refreshPage(); }
    if (e.altKey && (e.key === 'n' || e.key === 'N')) { e.preventDefault(); toggleSidebar(); }
    if (e.altKey && (e.key === 'f' || e.key === 'F')) { e.preventDefault(); toggleFavorite(); }
  });

  // ========== CSS animations ==========
  var style = document.createElement('style');
  style.textContent =
    '@keyframes spin { from{transform:rotate(0)} to{transform:rotate(360deg)} }' +
    '@keyframes slideInUp { from{transform:translateY(20px);opacity:0} to{transform:translateY(0);opacity:1} }' +
    '@keyframes fadeIn { from{opacity:0} to{opacity:1} }' +
    '@keyframes fadeInUp { from{transform:translateY(10px);opacity:0} to{transform:translateY(0);opacity:1} }' +
    '.refresh-button.loading{opacity:.7;cursor:wait}' +
    '.refresh-button svg{transition:transform .3s ease}' +
    '.refresh-button:hover:not(.loading) svg{transform:rotate(45deg)}';
  document.head.appendChild(style);

})();

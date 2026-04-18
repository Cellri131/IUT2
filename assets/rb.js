// rb.js - Gestion du thème, toolbar, refresh API, sidebar navigation et améliorations UX
(function() {
  'use strict';

  var navigationData = null; // Stockage de l'arbre de navigation

  document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    setupToolbar();
    loadNavigationTree();
    enhanceImages();
    animateElements();
  });

  // ========== Gestion du thème ==========
  function initTheme() {
    var saved = localStorage.getItem('theme');
    var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setTheme(saved || (prefersDark ? 'dark' : 'light'));

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
      if (!localStorage.getItem('theme')) setTheme(e.matches ? 'dark' : 'light');
    });
  }

  function setTheme(theme) {
    var html = document.documentElement;
    var btn = document.querySelector('.theme-toggle');
    var sun = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
    var moon = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';

    if (theme === 'dark') {
      html.setAttribute('data-theme', 'dark');
      if (btn) btn.innerHTML = sun;
    } else {
      html.removeAttribute('data-theme');
      if (btn) btn.innerHTML = moon;
    }
    localStorage.setItem('theme', theme);
  }

  function toggleTheme() {
    setTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
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

    // Bouton thème
    var themeBtn = document.createElement('button');
    themeBtn.className = 'btn theme-toggle';
    themeBtn.title = 'Basculer thème (Alt+T)';
    themeBtn.onclick = toggleTheme;

    // Bouton rafraîchir
    var refreshBtn = document.createElement('button');
    refreshBtn.className = 'btn refresh-button';
    refreshBtn.innerHTML = '<svg class="refresh-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>';
    refreshBtn.title = 'Rafraîchir depuis le serveur (Alt+R)';
    refreshBtn.onclick = refreshPage;

    toolbar.appendChild(menuBtn);
    toolbar.appendChild(backBtn);
    toolbar.appendChild(themeBtn);
    toolbar.appendChild(refreshBtn);
    document.body.insertBefore(toolbar, document.body.firstChild);

    // Appliquer le thème au bouton
    setTheme(localStorage.getItem('theme') || 'light');
  }

  // ========== Navigation Sidebar ==========
  function loadNavigationTree() {
    // Déterminer le chemin vers navigation.json
    var basePath = getBasePath();
    var navPath = basePath + 'navigation.json';

    fetch(navPath)
      .then(function(resp) {
        if (!resp.ok) throw new Error('Navigation file not found');
        return resp.json();
      })
      .then(function(data) {
        navigationData = data;
        setupSidebar();
      })
      .catch(function(err) {
        console.warn('Navigation tree not loaded:', err);
      });
  }

  function getBasePath() {
    // Calculer le chemin relatif vers la racine pedago
    var path = window.location.pathname;
    var depth = (path.match(/\//g) || []).length - 1;
    if (path.endsWith('/')) depth--;
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

    // Contenu (arbre)
    var content = document.createElement('div');
    content.className = 'nav-content';
    content.appendChild(buildTree(navigationData));

    // Bouton fermer
    var closeBtn = document.createElement('button');
    closeBtn.className = 'nav-close';
    closeBtn.innerHTML = '×';
    closeBtn.onclick = toggleSidebar;

    sidebar.appendChild(closeBtn);
    sidebar.appendChild(header);
    sidebar.appendChild(content);

    // Overlay
    var overlay = document.createElement('div');
    overlay.className = 'nav-overlay';
    overlay.onclick = toggleSidebar;

    document.body.appendChild(sidebar);
    document.body.appendChild(overlay);

    // Highlight de la page active
    highlightActivePage();
  }

  function buildBreadcrumb() {
    var path = window.location.pathname;
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

    // Sauvegarder l'état expand/collapse dans localStorage
    var expandedKey = 'nav-expanded-' + node.path;
    var isExpanded = localStorage.getItem(expandedKey) !== 'false';

    if (node.children && node.children.length > 0) {
      node.children.forEach(function(child) {
        var li = document.createElement('li');
        li.className = 'nav-tree-item';
        li.dataset.path = child.path;

        if (child.type === 'folder') {
          var folderDiv = document.createElement('div');
          folderDiv.className = 'nav-folder';

          // Icône expand/collapse
          var toggle = document.createElement('span');
          toggle.className = 'nav-toggle';
          toggle.innerHTML = isExpanded ? '▼' : '▶';
          toggle.onclick = function(e) {
            e.stopPropagation();
            toggleFolder(li, child.path);
          };

          // Icône dossier
          var icon = document.createElement('span');
          icon.className = 'nav-icon';
          icon.innerHTML = '📁';

          // Nom
          var name = document.createElement('span');
          name.textContent = child.name;
          name.onclick = function() {
            // Si le dossier a un index.html, naviguer vers lui
            var indexPath = child.path + (child.path.endsWith('/') ? '' : '/') + 'index.html';
            window.location.href = indexPath;
          };

          folderDiv.appendChild(toggle);
          folderDiv.appendChild(icon);
          folderDiv.appendChild(name);
          li.appendChild(folderDiv);

          // Sous-arbre
          var subtree = buildTree(child, level + 1);
          subtree.style.display = isExpanded ? 'block' : 'none';
          li.appendChild(subtree);

          if (isExpanded) li.classList.add('expanded');

        } else if (child.type === 'file') {
          var fileDiv = document.createElement('div');
          fileDiv.className = 'nav-file';

          // Icône fichier
          var icon = document.createElement('span');
          icon.className = 'nav-icon';
          icon.innerHTML = '📄';

          // Nom (lien)
          var link = document.createElement('a');
          link.href = child.path;
          link.textContent = child.name;

          fileDiv.appendChild(icon);
          fileDiv.appendChild(link);
          li.appendChild(fileDiv);
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
    var overlay = document.querySelector('.nav-overlay');
    if (!sidebar || !overlay) return;

    var isOpen = sidebar.classList.contains('open');
    if (isOpen) {
      sidebar.classList.remove('open');
      overlay.classList.remove('open');
    } else {
      sidebar.classList.add('open');
      overlay.classList.add('open');
    }
  }

  function highlightActivePage() {
    var currentPath = window.location.pathname;
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

  // ========== Images ==========
  function enhanceImages() {
    document.querySelectorAll('img').forEach(function(img) {
      if (!img.complete) {
        img.style.opacity = '0';
        img.addEventListener('load', function() {
          this.style.transition = 'opacity 0.4s ease';
          this.style.opacity = '1';
        });
      }
      img.addEventListener('error', function() {
        this.style.opacity = '0.4';
        this.style.border = '2px dashed var(--border-color)';
        this.title = 'Image non disponible';
      });
      img.addEventListener('click', function() {
        if (this.title !== 'Image non disponible') openModal(this.src, this.alt);
      });
    });
  }

  // ========== Modal Image ==========
  function openModal(src, alt) {
    var modal = document.createElement('div');
    modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.95);' +
      'display:flex;align-items:center;justify-content:center;z-index:10000;cursor:pointer;padding:20px;';

    var img = document.createElement('img');
    img.src = src;
    img.alt = alt || '';
    img.style.cssText = 'max-width:90%;max-height:90%;object-fit:contain;border-radius:12px;box-shadow:0 0 40px rgba(255,255,255,.1);';

    var closeBtn = document.createElement('button');
    closeBtn.innerHTML = '\u2715';
    closeBtn.style.cssText = 'position:absolute;top:20px;right:20px;background:linear-gradient(135deg,#667eea,#764ba2);' +
      'color:#fff;border:none;font-size:24px;padding:12px 16px;cursor:pointer;border-radius:8px;';

    function close() { if (document.body.contains(modal)) document.body.removeChild(modal); }

    modal.appendChild(img);
    modal.appendChild(closeBtn);
    document.body.appendChild(modal);

    modal.onclick = function(e) { if (e.target === modal) close(); };
    closeBtn.onclick = close;
    document.addEventListener('keydown', function handler(e) {
      if (e.key === 'Escape') { close(); document.removeEventListener('keydown', handler); }
    });
  }

  // ========== Raccourcis clavier ==========
  document.addEventListener('keydown', function(e) {
    if (e.altKey && (e.key === 't' || e.key === 'T')) { e.preventDefault(); toggleTheme(); }
    if (e.altKey && e.key === 'ArrowLeft') { e.preventDefault(); history.back(); }
    if (e.altKey && (e.key === 'r' || e.key === 'R')) { e.preventDefault(); refreshPage(); }
    if (e.altKey && (e.key === 'n' || e.key === 'N')) { e.preventDefault(); toggleSidebar(); }
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

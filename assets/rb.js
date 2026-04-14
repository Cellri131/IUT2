// rb.js - Gestion du thème coloré et améliorations UX
(function() {
  'use strict';

  document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    setupToolbar();
    enhanceImages();
    animateElements();
  });

  // ========== Gestion du thème ==========
  function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = savedTheme || (prefersDark ? 'dark' : 'light');
    setTheme(theme);

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
      if (!localStorage.getItem('theme')) {
        setTheme(e.matches ? 'dark' : 'light');
      }
    });
  }

  function setTheme(theme) {
    const html = document.documentElement;
    const toggleBtn = document.querySelector('.theme-toggle');

    if (theme === 'dark') {
      html.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
      if (toggleBtn) toggleBtn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
    } else {
      html.removeAttribute('data-theme');
      localStorage.setItem('theme', 'light');
      if (toggleBtn) toggleBtn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    }
  }

  function toggleTheme() {
    const html = document.documentElement;
    const newTheme = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  }

  // ========== Barre d'outils ==========
  function setupToolbar() {
    const body = document.body;
    let toolbar = document.querySelector('.toolbar');

    if (!toolbar) {
      toolbar = document.createElement('div');
      toolbar.className = 'toolbar';

      // Bouton retour
      const backBtn = document.createElement('button');
      backBtn.className = 'btn back-button';
      backBtn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19 12H5M12 19l-7-7 7-7"/></svg> Retour';
      backBtn.onclick = () => history.back();

      // Bouton thème
      const themeBtn = document.createElement('button');
      themeBtn.className = 'btn theme-toggle';
      const currentTheme = document.documentElement.getAttribute('data-theme');
      themeBtn.innerHTML = currentTheme === 'dark'
        ? '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
        : '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
      themeBtn.title = 'Basculer thème (Alt+T)';
      themeBtn.onclick = toggleTheme;

      // Bouton rafraîchir
      const refreshBtn = document.createElement('button');
      refreshBtn.className = 'btn refresh-button';
      refreshBtn.innerHTML = '<svg class="refresh-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>';
      refreshBtn.title = 'Rafraîchir depuis le serveur (Alt+R)';
      refreshBtn.onclick = refreshPage;

      toolbar.appendChild(backBtn);
      toolbar.appendChild(themeBtn);
      toolbar.appendChild(refreshBtn);
      body.insertBefore(toolbar, body.firstChild);
    } else {
      // S'assurer que les boutons existent
      if (!document.querySelector('.theme-toggle')) {
        const themeBtn = document.createElement('button');
        themeBtn.className = 'btn theme-toggle';
        themeBtn.innerHTML = document.documentElement.getAttribute('data-theme') === 'dark'
          ? '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
          : '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
        themeBtn.onclick = toggleTheme;
        toolbar.appendChild(themeBtn);
      }

      if (!document.querySelector('.refresh-button')) {
        const refreshBtn = document.createElement('button');
        refreshBtn.className = 'btn refresh-button';
        refreshBtn.innerHTML = '<svg class="refresh-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>';
        refreshBtn.title = 'Rafraîchir depuis le serveur (Alt+R)';
        refreshBtn.onclick = refreshPage;
        toolbar.appendChild(refreshBtn);
      }
    }
  }

  // ========== Rafraîchissement de la page ==========
  function refreshPage() {
    const refreshBtn = document.querySelector('.refresh-button');
    const refreshIcon = refreshBtn.querySelector('.refresh-icon');

    // Obtenir le chemin du fichier actuel
    let filePath = '';

    // Si on est en file://, on peut récupérer le chemin
    if (window.location.protocol === 'file:') {
      // Convertir file:///C:/path/to/file.html en C:\path\to\file.html
      filePath = decodeURIComponent(window.location.pathname);
      // Supprimer le / initial sur Windows
      if (filePath.startsWith('/') && filePath.charAt(2) === ':') {
        filePath = filePath.substring(1);
      }
      // Convertir les / en \
      filePath = filePath.replace(/\//g, '\\');
    } else {
      // Si on est sur un serveur local, utiliser le pathname
      filePath = window.location.pathname;
    }

    // Animation de chargement
    refreshBtn.classList.add('loading');
    refreshIcon.style.animation = 'spin 1s linear infinite';

    // Essayer d'utiliser le protocole personnalisé
    const protocolUrl = 'iut-refresh://' + encodeURIComponent(filePath);

    // Créer un iframe caché pour déclencher le protocole
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    document.body.appendChild(iframe);

    // Timeout pour détecter si le protocole n'est pas enregistré
    let protocolHandled = false;

    // Listener pour détecter si on quitte la page (protocole fonctionne)
    window.addEventListener('blur', function onBlur() {
      protocolHandled = true;
      window.removeEventListener('blur', onBlur);
    });

    // Essayer le protocole
    try {
      iframe.contentWindow.location.href = protocolUrl;
    } catch (e) {
      // Le protocole n'est probablement pas enregistré
    }

    // Après un délai, vérifier si le protocole a fonctionné
    setTimeout(() => {
      document.body.removeChild(iframe);
      refreshBtn.classList.remove('loading');
      refreshIcon.style.animation = '';

      if (!protocolHandled) {
        // Afficher les instructions
        showRefreshInstructions(filePath);
      } else {
        // Le protocole a été déclenché, afficher un message
        showNotification('Script de rafraîchissement lancé. Rechargez la page (F5) après.', 'info');
      }
    }, 500);
  }

  // ========== Instructions de rafraîchissement ==========
  function showRefreshInstructions(filePath) {
    // Supprimer l'ancien modal s'il existe
    const oldModal = document.querySelector('.refresh-modal');
    if (oldModal) oldModal.remove();

    // Calculer le chemin vers refresh_page.py (dans le dossier css)
    let scriptPath = '';
    const currentPath = window.location.pathname;
    const pedagogIndex = currentPath.indexOf('/pedago/');

    if (pedagogIndex !== -1) {
      // Calculer le chemin relatif vers pedago/css/
      const pathAfterPedago = currentPath.substring(pedagogIndex + 8); // après "/pedago/"
      const depth = (pathAfterPedago.match(/\//g) || []).length;

      if (depth > 0) {
        scriptPath = '../'.repeat(depth) + 'css/refresh_page.py';
      } else {
        scriptPath = 'css/refresh_page.py';
      }
    } else {
      scriptPath = 'pedago/css/refresh_page.py';
    }

    // Construire la commande
    const command = `python "${scriptPath}" "${filePath}"`;

    // Chemin vers register_protocol.py (même dossier que refresh_page.py)
    const registerPath = scriptPath.replace('refresh_page.py', 'register_protocol.py');

    const modal = document.createElement('div');
    modal.className = 'refresh-modal';
    modal.innerHTML = `
      <div class="refresh-modal-content">
        <button class="refresh-modal-close">&times;</button>
        <h3>Rafraîchir la page</h3>
        <p>Pour télécharger la dernière version de cette page depuis le serveur, exécutez cette commande :</p>
        <div class="refresh-command">
          <code>${escapeHtml(command)}</code>
          <button class="copy-btn" title="Copier">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
            </svg>
          </button>
        </div>
        <p class="refresh-note">Puis rechargez cette page (F5) pour voir les modifications.</p>
        <div class="refresh-setup">
          <details>
            <summary>Configuration unique (optionnel)</summary>
            <p>Pour activer le bouton de rafraîchissement direct, exécutez une fois :</p>
            <code>python "${registerPath}"</code>
            <p>Cela enregistre le protocole <code>iut-refresh://</code> sur votre système.</p>
          </details>
        </div>
      </div>
    `;

    // Styles du modal
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.8);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
      animation: fadeIn 0.3s ease;
    `;

    document.body.appendChild(modal);

    // Style du contenu
    const content = modal.querySelector('.refresh-modal-content');
    content.style.cssText = `
      background: var(--bg-primary);
      padding: 24px;
      border-radius: 16px;
      max-width: 600px;
      width: 90%;
      box-shadow: var(--shadow-xl);
      position: relative;
    `;

    // Style du bouton fermer
    const closeBtn = modal.querySelector('.refresh-modal-close');
    closeBtn.style.cssText = `
      position: absolute;
      top: 12px;
      right: 12px;
      background: none;
      border: none;
      font-size: 24px;
      cursor: pointer;
      color: var(--text-secondary);
      padding: 4px 8px;
      border-radius: 4px;
    `;
    closeBtn.onclick = () => modal.remove();

    // Style du titre
    const title = modal.querySelector('h3');
    title.style.cssText = `
      margin: 0 0 16px 0;
      color: var(--text-primary);
      font-size: 20px;
    `;

    // Style des paragraphes
    modal.querySelectorAll('p').forEach(p => {
      p.style.cssText = `
        margin: 12px 0;
        color: var(--text-secondary);
        font-size: 14px;
      `;
    });

    // Style de la commande
    const commandDiv = modal.querySelector('.refresh-command');
    commandDiv.style.cssText = `
      display: flex;
      align-items: center;
      gap: 8px;
      background: var(--bg-tertiary);
      padding: 12px 16px;
      border-radius: 8px;
      margin: 16px 0;
      border: 1px solid var(--border-color);
    `;

    const code = commandDiv.querySelector('code');
    code.style.cssText = `
      flex: 1;
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      color: var(--color-green);
      word-break: break-all;
    `;

    // Bouton copier
    const copyBtn = modal.querySelector('.copy-btn');
    copyBtn.style.cssText = `
      background: var(--gradient-primary);
      border: none;
      padding: 8px;
      border-radius: 6px;
      cursor: pointer;
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
    `;
    copyBtn.onclick = () => {
      navigator.clipboard.writeText(command).then(() => {
        copyBtn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>';
        setTimeout(() => {
          copyBtn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>';
        }, 2000);
      });
    };

    // Note
    const note = modal.querySelector('.refresh-note');
    note.style.cssText = `
      margin: 16px 0;
      padding: 12px;
      background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(147, 51, 234, 0.1));
      border-radius: 8px;
      border-left: 3px solid var(--color-blue);
      color: var(--text-primary) !important;
      font-weight: 500;
    `;

    // Section setup
    const setup = modal.querySelector('.refresh-setup');
    setup.style.cssText = `
      margin-top: 20px;
      padding-top: 16px;
      border-top: 1px solid var(--border-color);
    `;

    const details = setup.querySelector('details');
    details.style.cssText = `
      font-size: 13px;
      color: var(--text-secondary);
    `;

    const summary = details.querySelector('summary');
    summary.style.cssText = `
      cursor: pointer;
      font-weight: 500;
      color: var(--text-primary);
      padding: 8px 0;
    `;

    setup.querySelectorAll('code').forEach(c => {
      c.style.cssText = `
        display: block;
        background: var(--bg-tertiary);
        padding: 8px 12px;
        border-radius: 6px;
        margin: 8px 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        color: var(--color-purple);
      `;
    });

    // Fermer avec Escape ou clic en dehors
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    document.addEventListener('keydown', function handler(e) {
      if (e.key === 'Escape') {
        modal.remove();
        document.removeEventListener('keydown', handler);
      }
    });
  }

  // ========== Utilitaires ==========
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // ========== Notifications ==========
  function showNotification(message, type = 'info') {
    const oldNotif = document.querySelector('.notification');
    if (oldNotif) oldNotif.remove();

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
      <span class="notification-icon">${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}</span>
      <span class="notification-message">${message}</span>
    `;

    notification.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 8px;
      background: ${type === 'success' ? 'linear-gradient(135deg, #10b981, #059669)' :
                   type === 'error' ? 'linear-gradient(135deg, #ef4444, #dc2626)' :
                   'linear-gradient(135deg, #3b82f6, #2563eb)'};
      color: white;
      font-weight: 500;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
      z-index: 10001;
      display: flex;
      align-items: center;
      gap: 10px;
      animation: slideInUp 0.3s ease;
      font-family: 'JetBrains Mono', monospace;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.style.animation = 'slideInUp 0.3s ease reverse';
      setTimeout(() => notification.remove(), 300);
    }, 4000);
  }

  // ========== Animation des éléments ==========
  function animateElements() {
    document.querySelectorAll('.cadre').forEach((el, i) => {
      el.style.opacity = '0';
      el.style.animation = 'fadeInUp 0.5s ease forwards';
      el.style.animationDelay = `${i * 0.1}s`;
    });

    document.querySelectorAll('tbody tr').forEach((el, i) => {
      el.style.opacity = '0';
      el.style.animation = 'fadeInUp 0.3s ease forwards';
      el.style.animationDelay = `${i * 0.05}s`;
    });
  }

  // ========== Images ==========
  function enhanceImages() {
    document.querySelectorAll('img').forEach(img => {
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
        this.style.cursor = 'not-allowed';
      });

      img.addEventListener('click', function(e) {
        if (!this.title || this.title !== 'Image non disponible') {
          openModal(this.src, this.alt);
        }
      });
    });
  }

  // ========== Modal Image ==========
  function openModal(src, alt) {
    const modal = document.createElement('div');
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.95);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
      cursor: pointer;
      padding: 20px;
      animation: fadeIn 0.3s ease;
    `;

    const img = document.createElement('img');
    img.src = src;
    img.alt = alt;
    img.style.cssText = `
      max-width: 90%;
      max-height: 90%;
      object-fit: contain;
      border-radius: 12px;
      box-shadow: 0 0 40px rgba(255, 255, 255, 0.1);
      animation: fadeInUp 0.4s ease;
    `;

    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '✕';
    closeBtn.style.cssText = `
      position: absolute;
      top: 20px;
      right: 20px;
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      border: none;
      font-size: 24px;
      padding: 12px 16px;
      cursor: pointer;
      border-radius: 8px;
      transition: all 0.2s ease;
    `;

    closeBtn.onmouseover = () => closeBtn.style.transform = 'scale(1.1)';
    closeBtn.onmouseout = () => closeBtn.style.transform = 'scale(1)';

    function close() {
      modal.style.animation = 'fadeIn 0.2s ease reverse';
      setTimeout(() => {
        if (document.body.contains(modal)) document.body.removeChild(modal);
      }, 200);
    }

    modal.appendChild(img);
    modal.appendChild(closeBtn);
    document.body.appendChild(modal);

    modal.onclick = (e) => { if (e.target === modal) close(); };
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
    if (e.altKey && (e.key === 't' || e.key === 'T')) {
      e.preventDefault();
      toggleTheme();
    }

    if (e.altKey && e.key === 'ArrowLeft') {
      e.preventDefault();
      history.back();
    }

    if (e.altKey && (e.key === 'r' || e.key === 'R')) {
      e.preventDefault();
      refreshPage();
    }
  });

  // ========== Styles CSS additionnels ==========
  const style = document.createElement('style');
  style.textContent = `
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }

    @keyframes slideInUp {
      from { transform: translateY(20px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    .refresh-button.loading {
      opacity: 0.7;
      cursor: wait;
    }

    .refresh-button svg {
      transition: transform 0.3s ease;
    }

    .refresh-button:hover:not(.loading) svg {
      transform: rotate(45deg);
    }
  `;
  document.head.appendChild(style);

})();

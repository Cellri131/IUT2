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
      if (toggleBtn) toggleBtn.innerHTML = '☀️';
    } else {
      html.removeAttribute('data-theme');
      localStorage.setItem('theme', 'light');
      if (toggleBtn) toggleBtn.innerHTML = '🌙';
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
      backBtn.innerHTML = '← Retour';
      backBtn.onclick = () => history.back();

      // Bouton thème
      const themeBtn = document.createElement('button');
      themeBtn.className = 'btn theme-toggle';
      const currentTheme = document.documentElement.getAttribute('data-theme');
      themeBtn.innerHTML = currentTheme === 'dark' ? '☀️' : '🌙';
      themeBtn.title = 'Basculer thème (Alt+T)';
      themeBtn.onclick = toggleTheme;

      toolbar.appendChild(backBtn);
      toolbar.appendChild(themeBtn);
      body.insertBefore(toolbar, body.firstChild);
    } else {
      // S'assurer que le bouton theme existe
      if (!document.querySelector('.theme-toggle')) {
        const themeBtn = document.createElement('button');
        themeBtn.className = 'btn theme-toggle';
        themeBtn.innerHTML = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙';
        themeBtn.onclick = toggleTheme;
        toolbar.appendChild(themeBtn);
      }
    }
  }

  // ========== Animation des éléments ==========
  function animateElements() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          entry.target.style.animationDelay = `${index * 0.1}s`;
          entry.target.classList.add('animate-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    // Observer les cadres
    document.querySelectorAll('.cadre').forEach((el, i) => {
      el.style.opacity = '0';
      el.style.animation = 'fadeInUp 0.5s ease forwards';
      el.style.animationDelay = `${i * 0.1}s`;
    });

    // Observer les lignes de tableau
    document.querySelectorAll('tbody tr').forEach((el, i) => {
      el.style.opacity = '0';
      el.style.animation = 'fadeInUp 0.3s ease forwards';
      el.style.animationDelay = `${i * 0.05}s`;
    });
  }

  // ========== Images ==========
  function enhanceImages() {
    document.querySelectorAll('img').forEach(img => {
      // Fade in au chargement
      if (!img.complete) {
        img.style.opacity = '0';
        img.addEventListener('load', function() {
          this.style.transition = 'opacity 0.4s ease';
          this.style.opacity = '1';
        });
      }

      // Gestion erreurs
      img.addEventListener('error', function() {
        this.style.opacity = '0.4';
        this.style.border = '2px dashed var(--border-color)';
        this.title = 'Image non disponible';
        this.style.cursor = 'not-allowed';
      });

      // Modal au clic
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

    closeBtn.onmouseover = () => {
      closeBtn.style.transform = 'scale(1.1)';
    };
    closeBtn.onmouseout = () => {
      closeBtn.style.transform = 'scale(1)';
    };

    function close() {
      modal.style.animation = 'fadeIn 0.2s ease reverse';
      setTimeout(() => {
        if (document.body.contains(modal)) {
          document.body.removeChild(modal);
        }
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
    // Alt + T : Toggle thème
    if (e.altKey && (e.key === 't' || e.key === 'T')) {
      e.preventDefault();
      toggleTheme();
    }

    // Alt + ← : Retour
    if (e.altKey && e.key === 'ArrowLeft') {
      e.preventDefault();
      history.back();
    }
  });

})();

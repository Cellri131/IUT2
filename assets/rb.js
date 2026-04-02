// rb.js - Scripts légers pour améliorer l'affichage du site IUT2
(function() {
  'use strict';

  document.addEventListener('DOMContentLoaded', function() {
    // Améliorer l'affichage des images
    enhanceImages();
  });

  // Amélioration des images
  function enhanceImages() {
    const images = document.querySelectorAll('img');

    images.forEach(function(img) {
      // Vérifier si l'image est chargée
      if (!img.complete) {
        img.addEventListener('load', function() {
          img.style.opacity = '1';
        });
        img.style.opacity = '0';
        img.style.transition = 'opacity 0.3s ease';
      }

      // Ajouter un clic pour agrandir l'image
      img.style.cursor = 'pointer';
      img.addEventListener('click', function() {
        openImageModal(img.src, img.alt);
      });

      // Gestion des erreurs de chargement
      img.addEventListener('error', function() {
        img.style.opacity = '0.3';
        img.style.border = '2px dashed #e5e7eb';
        img.title = 'Image non disponible';
      });
    });
  }

  // Modal pour afficher l'image en grand
  function openImageModal(src, alt) {
    // Créer le modal
    const modal = document.createElement('div');
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(0, 0, 0, 0.9);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
      cursor: pointer;
    `;

    const img = document.createElement('img');
    img.src = src;
    img.alt = alt;
    img.style.cssText = `
      max-width: 90%;
      max-height: 90%;
      object-fit: contain;
      box-shadow: 0 10px 50px rgba(0, 0, 0, 0.5);
    `;

    modal.appendChild(img);
    document.body.appendChild(modal);

    // Fermer en cliquant
    modal.addEventListener('click', function() {
      document.body.removeChild(modal);
    });

    // Fermer avec Échap
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && document.body.contains(modal)) {
        document.body.removeChild(modal);
      }
    });
  }

})();

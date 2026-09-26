(function () {
  'use strict';

   document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.bld-toast').forEach(function (t) {
      setTimeout(function () {
        t.style.transition = 'opacity 0.3s, transform 0.3s';
        t.style.opacity = '0';
        t.style.transform = 'translateX(100%)';
        setTimeout(function () { if (t.parentNode) t.remove(); }, 300);
      }, 5000);
    });
  });

   document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.bld-modal').forEach(function (m) {
        m.style.display = 'none';
      });
    }
  });

})();

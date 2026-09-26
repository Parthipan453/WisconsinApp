document.addEventListener('DOMContentLoaded', function() {
  // Animate stats on load
  document.querySelectorAll('.stat-card').forEach((card, index) => {
    setTimeout(() => {
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, index * 100);
  });

  // Resource card click feedback
  document.querySelectorAll('.resource-card').forEach(card => {
    card.addEventListener('click', function() {
      this.style.transform = 'scale(0.95)';
      setTimeout(() => {
        this.style.transform = '';
      }, 200);
    });
  });

  console.log(' Housing page loaded successfully!');
});
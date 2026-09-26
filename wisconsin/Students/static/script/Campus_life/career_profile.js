document.addEventListener('DOMContentLoaded', function() {
  // Animate skill bars on load
  document.querySelectorAll('.skill-fill').forEach(bar => {
    const width = bar.style.width;
    bar.style.width = '0%';
    setTimeout(() => {
      bar.style.width = width;
    }, 300);
  });

  console.log(' Career Profile loaded successfully!');
});
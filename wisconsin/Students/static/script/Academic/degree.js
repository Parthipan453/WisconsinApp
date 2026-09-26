document.addEventListener('DOMContentLoaded', function() {
  // Animate progress bars on load
  document.querySelectorAll('.req-fill').forEach(bar => {
    const width = bar.style.width;
    bar.style.width = '0%';
    setTimeout(() => {
      bar.style.width = width;
    }, 300);
  });

  // Click on course items
  document.querySelectorAll('.course-item').forEach(item => {
    item.addEventListener('click', function() {
      const code = this.querySelector('.course-code')?.textContent || 'Course';
      const name = this.querySelector('.course-name')?.textContent || '';
      const grade = this.querySelector('.course-grade')?.textContent || 'N/A';
      alert(`📚 ${code} - ${name}\nGrade: ${grade}`);
    });
    item.style.cursor = 'pointer';
  });

  // Click on semester boxes
  document.querySelectorAll('.semester-box').forEach(box => {
    box.addEventListener('click', function() {
      const title = this.querySelector('.semester-title')?.textContent || 'Semester';
      const stats = this.querySelector('.semester-stats')?.textContent || '';
      alert(`📅 ${title}\n${stats}`);
    });
  });

  console.log(' Degree Progress loaded successfully!');
});
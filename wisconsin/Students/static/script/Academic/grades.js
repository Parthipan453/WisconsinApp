document.addEventListener('DOMContentLoaded', function() {
  // Bar hover effect
  document.querySelectorAll('.chart-bar').forEach(bar => {
    bar.addEventListener('mouseenter', function() {
      const value = this.querySelector('.chart-bar-value');
      if (value) value.style.opacity = '1';
    });
    bar.addEventListener('mouseleave', function() {
      const value = this.querySelector('.chart-bar-value');
      if (value) value.style.opacity = '0.7';
    });
  });

  // Row click - show course details
  document.querySelectorAll('.grades-table tbody tr').forEach(row => {
    row.addEventListener('click', function() {
      const code = this.querySelector('.course-code')?.textContent || 'Course';
      const name = this.querySelector('td:nth-child(2)')?.textContent || '';
      const grade = this.querySelector('.grade-badge')?.textContent || '';
      alert(`📚 ${code} - ${name}\nGrade: ${grade}`);
    });
    row.style.cursor = 'pointer';
  });

  console.log(' Grades & GPA loaded successfully!');
});
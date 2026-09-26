function toggleTerm(element) {
  // Find the parent term-group
  const group = element.closest('.term-group');
  if (!group) return;
  
  // Toggle the active class
  group.classList.toggle('active');
  
  // Update arrow rotation
  const arrow = group.querySelector('.term-arrow');
  if (arrow) {
    arrow.style.transform = group.classList.contains('active') ? 'rotate(90deg)' : 'rotate(0deg)';
  }
  
  // Update courses visibility using !important
  const courses = group.querySelector('.term-courses');
  if (courses) {
    if (group.classList.contains('active')) {
      courses.style.display = 'block';
      courses.style.setProperty('display', 'block', 'important');
    } else {
      courses.style.display = 'none';
      courses.style.setProperty('display', 'none', 'important');
    }
  }
}

function toggleAllTerms() {
  const groups = document.querySelectorAll('.term-group');
  const allActive = Array.from(groups).every(g => g.classList.contains('active'));
  
  groups.forEach(group => {
    if (allActive) {
      group.classList.remove('active');
      const courses = group.querySelector('.term-courses');
      if (courses) {
        courses.style.display = 'none';
        courses.style.setProperty('display', 'none', 'important');
      }
      const arrow = group.querySelector('.term-arrow');
      if (arrow) {
        arrow.style.transform = 'rotate(0deg)';
      }
    } else {
      group.classList.add('active');
      const courses = group.querySelector('.term-courses');
      if (courses) {
        courses.style.display = 'block';
        courses.style.setProperty('display', 'block', 'important');
      }
      const arrow = group.querySelector('.term-arrow');
      if (arrow) {
        arrow.style.transform = 'rotate(90deg)';
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', function() {
  // Animate stats numbers
  animateStats();
  
  // Animate table rows on load
  animateTableRows();
  
  // Ensure all active terms are properly displayed on load
  document.querySelectorAll('.term-group.active').forEach(group => {
    const courses = group.querySelector('.term-courses');
    if (courses) {
      courses.style.display = 'block';
      courses.style.setProperty('display', 'block', 'important');
    }
    const arrow = group.querySelector('.term-arrow');
    if (arrow) {
      arrow.style.transform = 'rotate(90deg)';
    }
  });
  
  // Ensure all inactive terms are hidden on load
  document.querySelectorAll('.term-group:not(.active)').forEach(group => {
    const courses = group.querySelector('.term-courses');
    if (courses) {
      courses.style.display = 'none';
      courses.style.setProperty('display', 'none', 'important');
    }
    const arrow = group.querySelector('.term-arrow');
    if (arrow) {
      arrow.style.transform = 'rotate(0deg)';
    }
  });

  console.log(' Transcripts loaded successfully!');
});


function animateStats() {
  const stats = document.querySelectorAll('.stats-number');
  stats.forEach(stat => {
    const target = parseFloat(stat.textContent);
    const isDecimal = target % 1 !== 0;
    const duration = 1500;
    const startTime = performance.now();
    
    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = eased * target;
      
      if (isDecimal) {
        stat.textContent = current.toFixed(2);
      } else {
        stat.textContent = Math.floor(current);
      }
      
      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        if (isDecimal) {
          stat.textContent = target.toFixed(2);
        } else {
          stat.textContent = target;
        }
      }
    }
    requestAnimationFrame(update);
  });
}

// ============================================================
// ANIMATE TABLE ROWS ON LOAD
// ============================================================
function animateTableRows() {
  const rows = document.querySelectorAll('.transcript-table tbody tr');
  rows.forEach((row, index) => {
    row.style.opacity = '0';
    row.style.transform = 'translateX(-10px)';
    row.style.transition = 'all 0.3s ease';
    
    setTimeout(() => {
      row.style.opacity = '1';
      row.style.transform = 'translateX(0)';
    }, 100 + (index * 50));
  });
}


document.addEventListener('DOMContentLoaded', function() {
  const scrollWrappers = document.querySelectorAll('.term-scroll-wrapper');
  
  scrollWrappers.forEach(wrapper => {
    let isDown = false;
    let startX;
    let scrollLeft;
    
    wrapper.addEventListener('mousedown', (e) => {
      isDown = true;
      startX = e.pageX - wrapper.offsetLeft;
      scrollLeft = wrapper.scrollLeft;
      wrapper.style.cursor = 'grabbing';
    });
    
    wrapper.addEventListener('mouseleave', () => {
      isDown = false;
      wrapper.style.cursor = 'grab';
    });
    
    wrapper.addEventListener('mouseup', () => {
      isDown = false;
      wrapper.style.cursor = 'grab';
    });
    
    wrapper.addEventListener('mousemove', (e) => {
      if (!isDown) return;
      e.preventDefault();
      const x = e.pageX - wrapper.offsetLeft;
      const walk = (x - startX) * 1.5;
      wrapper.scrollLeft = scrollLeft - walk;
    });
  });
});


function handleResponsiveTable() {
  const width = window.innerWidth;
  const tables = document.querySelectorAll('.transcript-table');
  
  tables.forEach(table => {
    const rows = table.querySelectorAll('tr');
    rows.forEach(row => {
      const cells = row.querySelectorAll('th, td');
      
      // On very small screens, hide "Points" and "Status" columns
      if (width < 400) {
        if (cells.length > 4) {
          cells[4].style.display = 'none'; // Points
          cells[5].style.display = 'none'; // Status
        }
      } else if (width < 500) {
        if (cells.length > 4) {
          cells[4].style.display = 'none'; // Points
          cells[5].style.display = ''; // Status
        }
      } else {
        cells.forEach(cell => {
          cell.style.display = '';
        });
      }
    });
  });
}

// Run on load and resize
window.addEventListener('load', handleResponsiveTable);
window.addEventListener('resize', handleResponsiveTable);

function downloadFullTranscript() {
  const groups = document.querySelectorAll('.term-group');
  if (!groups.length) return;

  const studentInfo = document.querySelector('.page-sub')?.textContent.trim() || '';

  let sectionsHtml = '';
  groups.forEach(group => {
    const semesterName = group.querySelector('.term-name')?.textContent.trim() || 'Semester';
    const statusEl = group.querySelector('.term-status');
    const statusText = statusEl ? statusEl.textContent.trim() : '';
    const statusClass = statusEl && statusEl.classList.contains('completed') ? 'completed' : 'in-progress';
    const table = group.querySelector('.transcript-table');
    if (!table) return;

    sectionsHtml += `
      <div class="semester-section">
        <div class="semester-title-row">
          <h2>${semesterName}</h2>
          <span class="status-pill ${statusClass}">${statusText}</span>
        </div>
        ${table.outerHTML}
      </div>
    `;
  });

  const win = window.open('', '_blank', 'width=950,height=800');
  if (!win) {
    alert('Please allow pop-ups to download your transcript.');
    return;
  }

  win.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Transcript</title>
      <style>
        body { font-family: Arial, Helvetica, sans-serif; padding: 30px; color:#1a1a1a; }
        .header { border-bottom: 2px solid #c5050c; padding-bottom: 12px; margin-bottom: 24px; }
        .header h1 { margin:0; font-size: 20px; color:#c5050c; }
        .header p { margin:4px 0 0; font-size: 13px; color:#666; }

        .semester-section { margin-bottom: 34px; page-break-inside: avoid; }
        .semester-title-row {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 10px;
        }
        .semester-title-row h2 {
          margin: 0;
          font-size: 17px;
          color: #c5050c;
        }
        .status-pill {
          font-size: 11px;
          font-weight: 700;
          padding: 2px 10px;
          border-radius: 12px;
        }
        .status-pill.completed { background:#e6f4ea; color:#228b22; }
        .status-pill.in-progress { background:#fef3c7; color:#f59e0b; }

        table { width:100%; border-collapse: collapse; margin-top: 4px; }
        th, td { padding: 8px 12px; border: 1px solid #e0e0e0; text-align:left; font-size: 12.5px; }
        th { background:#fafafa; text-transform:uppercase; font-size: 11px; color:#888; }
        tfoot td { font-weight:700; background:#fafafa; }
        .grade-badge, .status-badge { padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>Transcript</h1>
        <p>${studentInfo}</p>
      </div>
      ${sectionsHtml}
    </body>
    </html>
  `);
  win.document.close();
  win.focus();
  setTimeout(() => { win.print(); }, 400);
}
function downloadSemester(event, btn) {
  event.stopPropagation(); // don't trigger toggleTerm on the parent header

  const group = btn.closest('.term-group');
  if (!group) return;

  const semesterName = btn.dataset.semester || group.querySelector('.term-name')?.textContent.trim() || 'Semester';
  const table = group.querySelector('.transcript-table');
  if (!table) return;

  const studentInfo = document.querySelector('.page-sub')?.textContent.trim() || '';

  const win = window.open('', '_blank', 'width=900,height=700');
  if (!win) {
    alert('Please allow pop-ups to download this semester\'s transcript.');
    return;
  }

  win.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>${semesterName} - Transcript</title>
      <style>
        body { font-family: Arial, Helvetica, sans-serif; padding: 30px; color:#1a1a1a; }
        .header { border-bottom: 2px solid #c5050c; padding-bottom: 12px; margin-bottom: 20px; }
        .header h1 { margin:0; font-size: 20px; color:#c5050c; }
        .header p { margin:4px 0 0; font-size: 13px; color:#666; }
        table { width:100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 8px 12px; border: 1px solid #e0e0e0; text-align:left; font-size: 12.5px; }
        th { background:#fafafa; text-transform:uppercase; font-size: 11px; color:#888; }
        tfoot td { font-weight:700; background:#fafafa; }
        .grade-badge, .status-badge { padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>${semesterName}</h1>
        <p>${studentInfo}</p>
      </div>
      ${table.outerHTML}
    </body>
    </html>
  `);
  win.document.close();
  win.focus();
  setTimeout(() => { win.print(); }, 400);
}
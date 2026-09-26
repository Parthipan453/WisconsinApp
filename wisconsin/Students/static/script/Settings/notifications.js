

/* *********************************************** Arun code ***************************************************  */

document.addEventListener('DOMContentLoaded', () => {
  AOS.init({ duration: 400, once: true });
});

function resetDefaults() {
  if (!confirm('Reset all notification preferences to defaults?')) return;

  const defaultOn = [
    'channel_email', 'channel_portal',
    'notif_grade', 'notif_enrollment', 'notif_standing',
    'notif_payment_due', 'notif_aid_status', 'notif_new_charge', 'notif_payment_confirm',
    'notif_docs',
  ];

  document.querySelectorAll('.notif-toggle input[type="checkbox"]').forEach(cb => {
    cb.checked = defaultOn.includes(cb.name);
  });

  showToast('Preferences reset to defaults. Save to apply.');
}

function showToast(message, type = 'info') {
  const existing = document.querySelector('.notif-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `notif-toast notif-toast-${type}`;
  toast.innerHTML = `<i class="ti ti-${type === 'success' ? 'circle-check' : 'info-circle'}"></i> ${message}`;
  toast.style.cssText = `
    position: fixed; bottom: 24px; right: 24px; z-index: 9999;
    display: flex; align-items: center; gap: 10px;
    padding: 14px 20px;
    background: ${type === 'success' ? '#059669' : '#4361ee'};
    color: #fff; border-radius: 12px;
    font-size: 13px; font-weight: 500;
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    animation: slideInRight 0.3s ease;
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

document.getElementById('notifForm')?.addEventListener('submit', function () {
  sessionStorage.setItem('notif_saved', '1');
});

if (sessionStorage.getItem('notif_saved')) {
  sessionStorage.removeItem('notif_saved');
  showToast('Notification preferences saved.', 'success');
}

const style = document.createElement('style');
style.textContent = `
  @keyframes slideInRight {
    from { opacity: 0; transform: translateX(20px); }
    to   { opacity: 1; transform: translateX(0); }
  }
`;
document.head.appendChild(style);


/* *********************************************** Arun code ***************************************************  */
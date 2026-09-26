

/* *********************************************** Arun code ***************************************************  */

document.addEventListener('DOMContentLoaded', () => {
  AOS.init({ duration: 400, once: true });
});

function openPayModal() {
  document.getElementById('payModal').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closePayModal() {
  document.getElementById('payModal').classList.remove('open');
  document.body.style.overflow = '';
}

document.getElementById('payModal').addEventListener('click', function (e) {
  if (e.target === this) closePayModal();
});

function downloadReceipt(id) {
  window.open(`/finance/payments/${id}/receipt/`, '_blank');
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}


/* *********************************************** Arun code ***************************************************  */
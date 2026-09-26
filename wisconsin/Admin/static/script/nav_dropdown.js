const userToggle = document.getElementById('userToggle');
const dropdown = document.getElementById('userDropdown');

userToggle.addEventListener('click', function(e) {
    e.stopPropagation();
    dropdown.classList.toggle('open');
    this.classList.toggle('active');
});

document.addEventListener('click', function(e) {
    if (!userToggle.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove('open');
        userToggle.classList.remove('active');
    }
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && dropdown.classList.contains('open')) {
        dropdown.classList.remove('open');
        userToggle.classList.remove('active');
    }
});

document.addEventListener('DOMContentLoaded', function() {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
});
 // kali code
document.addEventListener('DOMContentLoaded', function () {

   
    if (window.lucide) {
        lucide.createIcons();
    }

 
    const badge = document.getElementById('notifBadge');
    const countLabel = document.getElementById('notifCount');

    if (badge) {
        badge.style.display = 'none';
    }
    if (countLabel) {
        countLabel.hidden = true;
    }
});
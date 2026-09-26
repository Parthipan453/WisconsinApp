document.addEventListener('DOMContentLoaded', function () {

    document.querySelectorAll('.permission-app-group__head').forEach(function (head) {
        head.addEventListener('click', function () {
            var body = head.nextElementSibling;
            var toggle = head.querySelector('.permission-app-group__toggle');
            var isOpen = !body.hasAttribute('hidden');
            if (isOpen) {
                body.setAttribute('hidden', '');
                toggle && toggle.classList.remove('open');
            } else {
                body.removeAttribute('hidden');
                toggle && toggle.classList.add('open');
            }
        });
    });

    document.querySelectorAll('[data-select-all]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var group = btn.closest('.permission-app-group');
            var boxes = group.querySelectorAll('.permission-crud-checks input[type="checkbox"]:not(:disabled)');
            var allChecked = Array.prototype.every.call(boxes, function (b) { return b.checked; });
            boxes.forEach(function (b) {
                b.checked = !allChecked;
                b.dispatchEvent(new Event('change'));
            });
        });
    });

    var counter = document.getElementById('permission-count');
    var total = document.querySelectorAll('.permission-crud-checks input[type="checkbox"]').length;
    function updateCounter() {
        if (!counter) return;
        var checked = document.querySelectorAll('.permission-crud-checks input[type="checkbox"]:checked').length;
        counter.textContent = checked + ' / ' + total;
    }
    document.querySelectorAll('.permission-crud-checks input[type="checkbox"]').forEach(function (b) {
        b.addEventListener('change', updateCounter);
    });
});
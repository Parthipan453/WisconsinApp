(function () {
    const input = document.getElementById('schoolSearch');
    const reset = document.getElementById('resetSearch');
    let timer = null;

    function doSearch(q) {
        const url = new URL(window.location.href);
        if (q) { url.searchParams.set('q', q); }
        else    { url.searchParams.delete('q'); }
        url.searchParams.delete('page');
        window.location.href = url.toString();
    }

    input.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(() => doSearch(this.value.trim()), 450);
    });

    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') { clearTimeout(timer); doSearch(this.value.trim()); }
    });

    reset.addEventListener('click', () => doSearch(''));
})();


document.addEventListener('DOMContentLoaded', function () {

    const modalElement =
        document.getElementById('statusModal');

    const statusModal =
        new bootstrap.Modal(modalElement);

    document
        .querySelectorAll(
            '.activate-btn, .deactivate-btn'
        )
        .forEach(btn => {

            btn.addEventListener('click', function () {

                const action =
                    this.dataset.action;

                const name =
                    this.dataset.name;

                const url =
                    this.dataset.url;

                document
                    .getElementById(
                        'confirmStatusBtn'
                    )
                    .href = url;

                document
                    .getElementById(
                        'statusMessage'
                    )
                    .innerHTML =
                        action === 'activate'
                        ? `Are you sure you want to <strong>activate</strong><br><strong>${name}</strong>?`
                        : `Are you sure you want to <strong>deactivate</strong><br><strong>${name}</strong>?`;

                statusModal.show();

            });

        });

});




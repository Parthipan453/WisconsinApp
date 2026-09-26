// Steve code 
(function () {
    const input   = document.getElementById('universitySearch');
    const reset   = document.getElementById('resetSearch');
    let   timer   = null;

    function doSearch(q) {
        const url = new URL(window.location.href);
        if (q) {
            url.searchParams.set('q', q);
        } else {
            url.searchParams.delete('q');
        }
        url.searchParams.delete('page');   
        window.location.href = url.toString();
    }

    
    input.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(() => doSearch(this.value.trim()), 450);
    });

  
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            clearTimeout(timer);
            doSearch(this.value.trim());
        }
    });


    reset.addEventListener('click', function () {
        doSearch('');
    });
})();







document.addEventListener('DOMContentLoaded', function () {

    const modalElement = document.getElementById('statusModal');

    const statusModal = new bootstrap.Modal(modalElement, {
        backdrop: true,
        keyboard: true
    });

    document
        .querySelectorAll('.activate-btn, .deactivate-btn')
        .forEach(btn => {

            btn.addEventListener('click', function () {

                const action = this.dataset.action;
                const name   = this.dataset.name;
                const url    = this.dataset.url;

                document.getElementById('confirmStatusBtn').href = url;

                if (action === 'activate') {

                    document.getElementById('statusMessage').innerHTML = `
                        <p>
                            Are you sure you want to <strong>activate</strong>
                            <br><strong>${name}</strong>?
                        </p>

                        <div class="alert alert-info text-start mt-3 mb-0">

                            <strong>
                                This action will activate the entire university hierarchy:
                            </strong>

                            <ul class="mt-2 mb-2">
                                <li>University</li>
                                <li>All Schools / Colleges</li>
                                <li>All Departments</li>
                                <li>All Courses</li>
                                <li>All Academic Programs</li>
                                <li>All Program Curriculum</li>
                            </ul>

                            <hr>

                            <small>
                                Every child record belonging to this university
                                will automatically become <strong>Active</strong>.
                            </small>

                        </div>
                    `;

                } else {

                    document.getElementById('statusMessage').innerHTML = `
                        <p>
                            Are you sure you want to <strong>deactivate</strong>
                            <br><strong>${name}</strong>?
                        </p>

                        <div class="alert alert-warning text-start mt-3 mb-0">

                            <strong>
                                This action will deactivate the entire university hierarchy:
                            </strong>

                            <ul class="mt-2 mb-2">
                                <li>University</li>
                                <li>All Schools / Colleges</li>
                                <li>All Departments</li>
                                <li>All Courses</li>
                                <li>All Academic Programs</li>
                                <li>All Program Curriculum</li>
                            </ul>

                            <hr>

                            <small>
                                Every child record belonging to this university
                                will automatically become <strong>Inactive</strong>.
                            </small>

                        </div>
                    `;

                }

                statusModal.show();

            });

        });

});

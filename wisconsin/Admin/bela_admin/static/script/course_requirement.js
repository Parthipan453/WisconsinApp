 /* ── Tab filter ── */
  let activeTab = 'all';
  document.querySelectorAll('.crt-tab').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.crt-tab').forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      activeTab = this.dataset.tab;
      filterTable();
    });
  });

  function filterTable() {
    const search = document.getElementById('crtSearch').value.toLowerCase().trim();
    const rows   = document.querySelectorAll('#crtTbody tr[data-status]');
    let visible  = 0;
    rows.forEach(row => {
      const ok = (!search || row.dataset.name.includes(search)) &&
                 (activeTab === 'all' || row.dataset.status === activeTab);
      row.style.display = ok ? '' : 'none';
      if (ok) visible++;
    });
    document.getElementById('noResults').style.display = visible === 0 ? 'block' : 'none';
  }

  function resetFilters() {
    document.getElementById('crtSearch').value = '';
    activeTab = 'all';
    document.querySelectorAll('.crt-tab').forEach(t => t.classList.remove('active'));
    document.querySelector('[data-tab="all"]').classList.add('active');
    filterTable();
  }

  /* ── Edit modal — fill form from row data ── */
function openEditModal(btn) {

    const id = btn.dataset.id;
    const name = btn.dataset.name;
    const desc = btn.dataset.description;
    const status = btn.dataset.status;

    document.getElementById('id_name_edit').value = name;
    document.getElementById('id_description_edit').value = desc;

    // Choices.js
    const statusChoices = window.choicesMap["id_status_edit"];

    if (statusChoices) {
        statusChoices.setChoiceByValue(status);
    }

    document.getElementById('editForm').action =
        `/department/courses/requirement-types/${id}/edit/`;

    document.getElementById('err_edit_name').classList.remove('show');
    document.getElementById('id_name_edit').classList.remove('is-invalid');

    new bootstrap.Modal(document.getElementById('editModal')).show();
}

  /* ── Add form validation ── */
  document.getElementById('addForm').addEventListener('submit', function(e) {
    const name = document.getElementById('id_name_add').value.trim();
    if (!name) {
      e.preventDefault();
      document.getElementById('id_name_add').classList.add('is-invalid');
      document.getElementById('err_add_name').classList.add('show');
      document.getElementById('id_name_add').focus();
    }
  });
  document.getElementById('id_name_add').addEventListener('input', function() {
    if (this.value.trim()) {
      this.classList.remove('is-invalid');
      document.getElementById('err_add_name').classList.remove('show');
    }
  });

  /* ── Edit form validation ── */
  document.getElementById('editForm').addEventListener('submit', function(e) {
    const name = document.getElementById('id_name_edit').value.trim();
    if (!name) {
      e.preventDefault();
      document.getElementById('id_name_edit').classList.add('is-invalid');
      document.getElementById('err_edit_name').classList.add('show');
      document.getElementById('id_name_edit').focus();
    }
  });
  document.getElementById('id_name_edit').addEventListener('input', function() {
    if (this.value.trim()) {
      this.classList.remove('is-invalid');
      document.getElementById('err_edit_name').classList.remove('show');
    }
  });

  /* ── Inactive modal ── */
 function showInactiveModal(btn) {

    const id = btn.dataset.id;
    const name = btn.dataset.name;

    document.getElementById('inactiveTypeName').textContent = name;

    document.getElementById('inactiveForm').action =
        `/department/courses/requirement-types/${id}/inactivate/`;

    new bootstrap.Modal(document.getElementById('inactiveModal')).show();
}

function openViewModal(btn){

    document.getElementById("view_name").textContent =
        btn.dataset.name;

    document.getElementById("view_description").textContent =
        btn.dataset.description || "-";

    document.getElementById("view_created").textContent =
        btn.dataset.created;

    document.getElementById("view_updated").textContent =
        btn.dataset.updated;

    const status = document.getElementById("view_status");

    if(btn.dataset.status === "ACTIVE"){

        status.innerHTML =
        `<span class="status-pill active">
            Active
        </span>`;

    }else{

        status.innerHTML =
        `<span class="status-pill inactive">
            Inactive
        </span>`;

    }

    // Show loading while fetching linked courses
    document.getElementById("view_usage").innerHTML = "Loading...";

    fetch(`/department/courses/requirement-types/${btn.dataset.id}/view/`)
        .then(response => response.json())
        .then(data => {

            const usage = document.getElementById("view_usage");

            if (data.linked_courses.length === 0) {

                usage.innerHTML = "No linked courses";

            } else {

                usage.innerHTML = data.linked_courses
                    .map(course => `${course.code} - ${course.name}`)
                    .join("<br>");

            }

        });

    new bootstrap.Modal(
        document.getElementById("viewModal")
    ).show();

    lucide.createIcons();
}

  /* ── Init Lucide ── */
  document.addEventListener('DOMContentLoaded', () => {
    if (typeof lucide !== 'undefined') lucide.createIcons();
  });
  

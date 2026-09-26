document.addEventListener("DOMContentLoaded", function () {
    var categoryModalEl = document.getElementById("categoryModal");
    var categoryModal = categoryModalEl ? new bootstrap.Modal(categoryModalEl) : null;

    var nameInput = document.querySelector('[name="category_name"]');
    var descInput = document.querySelector('[name="description"]');
    var idInput = document.getElementById("categoryIdInput");
    var titleEl = document.getElementById("categoryModalTitle");
    var submitTextEl = document.getElementById("categorySubmitText");

    var listContainer = document.getElementById("categoriesListContainer");
    var searchInput = document.getElementById("filterSearch");
    var resultCountEl = document.getElementById("catResultCount");

    var searchDebounce = null;

    var addBtn = document.getElementById("btnAddCategory");
    if (addBtn) {
        addBtn.addEventListener("click", function () {
            resetCategoryForm();
            setCategoryModalMode(false);
            categoryModal.show();
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", function () {
            clearTimeout(searchDebounce);
            searchDebounce = setTimeout(function () {
                fetchCategories(1);
            }, 350);
        });
    }

    if (listContainer) {
        listContainer.addEventListener("click", function (e) {
            var editBtn = e.target.closest(".btn-edit-category");
            var deleteBtn = e.target.closest(".btn-delete-category");
            var pageBtn = e.target.closest(".page-btn");

            if (editBtn) {
                e.preventDefault();
                var row = editBtn.closest("tr");

                if (nameInput) nameInput.value = row.dataset.categoryName;
                if (descInput) descInput.value = row.dataset.categoryDescription;
                if (idInput) idInput.value = row.dataset.categoryId;

                setCategoryModalMode(true);
                categoryModal.show();
                return;
            }

            if (deleteBtn) {
                e.preventDefault();
                var row = deleteBtn.closest("tr");
                var categoryId = row.dataset.categoryId;
                var categoryName = row.dataset.categoryName;

                if (!confirm('Delete category "' + categoryName + '"? This cannot be undone.')) {
                    return;
                }

                var form = document.createElement("form");
                form.method = "post";
                form.action = "";

                var csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
                form.innerHTML =
                    '<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf + '">' +
                    '<input type="hidden" name="action" value="delete">' +
                    '<input type="hidden" name="category_id" value="' + categoryId + '">';

                document.body.appendChild(form);
                form.submit();
                return;
            }

            if (pageBtn) {
                e.preventDefault();
                fetchCategories(pageBtn.dataset.page);
            }
        });
    }

    function fetchCategories(page) {
        var params = new URLSearchParams();
        params.set("page", page);
        if (searchInput && searchInput.value.trim()) {
            params.set("search", searchInput.value.trim());
        }

        fetch(window.location.pathname + "?" + params.toString(), {
            headers: { "X-Requested-With": "XMLHttpRequest" },
        })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                listContainer.innerHTML = data.html;
                if (resultCountEl) resultCountEl.textContent = data.count_text;

                var newUrl = window.location.pathname + "?" + params.toString();
                window.history.replaceState({}, "", newUrl);
            })
            .catch(function (err) {
                console.error("Failed to load categories:", err);
            });
    }

    function resetCategoryForm() {
        if (nameInput) nameInput.value = "";
        if (descInput) descInput.value = "";
        if (idInput) idInput.value = "";
    }

    window.setCategoryModalMode = function (isEdit) {
        if (titleEl) titleEl.textContent = isEdit ? "Edit Event Category" : "Add Event Category";
        if (submitTextEl) submitTextEl.textContent = isEdit ? "Update Category" : "Save Category";
    };
});
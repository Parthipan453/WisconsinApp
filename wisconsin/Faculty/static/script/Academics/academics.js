// Gayathri G

const input = document.getElementById("searchInput");
const clearBtn = document.getElementById("clearSearchBtn");

const filterSelect = document.querySelector("[data-filter]");
const sortSelect = document.querySelector("[data-sort]");
const defaultSort = sortSelect.dataset.defaultSort;

function toggleClearButton() {
    clearBtn.style.display = input.value.trim() ? "flex" : "none";
}

toggleClearButton();

input.addEventListener("input", toggleClearButton);

function clearSearchBox() {
    input.value = "";

    if (filterSelect) {
        filterSelect.value = "";
    }

    if (sortSelect) {
        sortSelect.value = defaultSort;
    }

    input.form.submit();
}
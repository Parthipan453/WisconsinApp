document.addEventListener("DOMContentLoaded", function () {
    var dateInput = document.getElementById("attendanceDateInput");
    if (!dateInput) return;

    dateInput.addEventListener("change", function () {
        if (!this.value) return;
        var url = new URL(window.location.href);
        url.searchParams.set("date", this.value);
        window.location.href = url.toString();
    });
});

document.addEventListener("DOMContentLoaded", function () {
  const filterForm = document.querySelector(".filter-card form");
  if (!filterForm) return;

  const fromDateInput = document.getElementById("fromDateInput");
  const toDateInput = document.getElementById("toDateInput");
  const fromDateError = document.getElementById("fromDateError");
  const toDateError = document.getElementById("toDateError");

  function clearErrors() {
    fromDateError.textContent = "";
    toDateError.textContent = "";
    fromDateInput.classList.remove("filter-input-invalid");
    toDateInput.classList.remove("filter-input-invalid");
  }

  function showError(input, errorEl, message) {
    errorEl.textContent = message;
    input.classList.add("filter-input-invalid");
  }

  filterForm.addEventListener("submit", function (e) {
    clearErrors();

    const fromDate = fromDateInput.value;
    const toDate = toDateInput.value;
    let hasError = false;

    if (!fromDate) {
      showError(fromDateInput, fromDateError, "From Date is required.");
      hasError = true;
    }

    if (!toDate) {
      showError(toDateInput, toDateError, "To Date is required.");
      hasError = true;
    }

    if (fromDate && toDate && fromDate > toDate) {
      showError(toDateInput, toDateError, "To Date cannot be earlier than From Date.");
      hasError = true;
    }

    if (hasError) {
      e.preventDefault();
    }
  });

  // Clear a field's error as soon as the user fixes it
  [fromDateInput, toDateInput].forEach(input => {
    input.addEventListener("change", function () {
      this.classList.remove("filter-input-invalid");
      (this === fromDateInput ? fromDateError : toDateError).textContent = "";
    });
  });
});
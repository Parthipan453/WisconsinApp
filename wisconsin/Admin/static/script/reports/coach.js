const CO_PAGE_SIZE = 6;
let coCurrentPage = 1;

function coGetCards() {
  return Array.from(document.querySelectorAll("#coachGrid .co-card-col"));
}

function coPopulateDepartmentFilter() {
  const select = document.getElementById("filterDepartment");
  const departments = new Set(
    coGetCards().map((card) => card.dataset.department).filter(Boolean)
  );
  departments.forEach((dept) => {
    const opt = document.createElement("option");
    opt.value = dept;
    opt.textContent = dept;
    select.appendChild(opt);
  });
}

function filterCoaches() {

  const search = document.getElementById("coachSearch").value.trim().toLowerCase();
  const status = document.getElementById("filterStatus").value.toLowerCase();
  const gender = document.getElementById("filterGender").value.toLowerCase();
  const experience = document.getElementById("filterExperience").value;

  let visible = 0;

  coGetCards().forEach(card => {

    const name = card.dataset.name || "";
    const email = card.dataset.email || "";
    const phone = card.dataset.phone || "";
    const coachStatus = card.dataset.status || "";
    const coachGender = (card.dataset.gender || "").toLowerCase();
    const coachExperience = Number(card.dataset.experience || 0);

    let show = true;

    if (
      search &&
      !(
        name.includes(search) ||
        email.includes(search) ||
        phone.includes(search)
      )
    ) {
      show = false;
    }

    if (status && coachStatus !== status) {
      show = false;
    }

    if (gender && coachGender !== gender) {
      show = false;
    }
    // Experience

    if (experience === "0-5") {
      show = coachExperience >= 0 && coachExperience <= 5;
    }

    if (experience === "5-10") {
      show = coachExperience > 5 && coachExperience <= 10;
    }

    if (experience === "10+") {
      show = coachExperience > 10;
    }

    card.dataset.matches = show ? "1" : "0";

    if (show) visible++;
  });

  coCurrentPage = 1;
  coRenderPage();

  document.getElementById("coachEmptyState").style.display =
    visible ? "none" : "block";
}


function coRenderPage() {
  const matching = coGetCards().filter((card) => card.dataset.matches !== "0");
  const totalPages = Math.max(1, Math.ceil(matching.length / CO_PAGE_SIZE));
  coCurrentPage = Math.min(coCurrentPage, totalPages);

  coGetCards().forEach((card) => {
    card.style.display = "none";
  });

  const start = (coCurrentPage - 1) * CO_PAGE_SIZE;
  matching.slice(start, start + CO_PAGE_SIZE).forEach((card) => {
    card.style.display = "";
  });

  const info = document.getElementById("coachPaginationInfo");
  if (matching.length === 0) {
    info.textContent = "Showing 0 of 0";
  } else {
    info.textContent = `Showing ${start + 1}–${Math.min(
      start + CO_PAGE_SIZE,
      matching.length
    )} of ${matching.length}`;
  }

  const btnWrap = document.getElementById("coachPaginationBtns");
  btnWrap.innerHTML = "";

  const prev = document.createElement("button");
  prev.className = "sp-pag-btn";
  prev.innerHTML = '<i class="fas fa-chevron-left"></i>';
  prev.disabled = coCurrentPage === 1;
  prev.onclick = () => {
    coCurrentPage -= 1;
    coRenderPage();
  };
  btnWrap.appendChild(prev);

  for (let i = 1; i <= totalPages; i += 1) {
    const btn = document.createElement("button");
    btn.className = "sp-pag-btn" + (i === coCurrentPage ? " active" : "");
    btn.textContent = i;
    btn.onclick = () => {
      coCurrentPage = i;
      coRenderPage();
    };
    btnWrap.appendChild(btn);
  }

  const next = document.createElement("button");
  next.className = "sp-pag-btn";
  next.innerHTML = '<i class="fas fa-chevron-right"></i>';
  next.disabled = coCurrentPage === totalPages;
  next.onclick = () => {
    coCurrentPage += 1;
    coRenderPage();
  };
  btnWrap.appendChild(next);
}

let filterStatusChoice;
let filterExperienceChoice;
let filterGenderChoice;
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("assignCoachForm");

  const staff = document.getElementById("staff");
  const role = document.getElementById("role");
  const hireDate = document.getElementById("hire_date");
  const certification = document.getElementById("certification");

  const assignCoachModal = document.getElementById("assignCoachModal");
  const staffChoice = window.choicesMap.staff;
  const roleChoice = window.choicesMap.role;

flatpickr("#hire_date", {
    dateFormat: "Y-m-d",
    maxDate: "today",
    disableMobile: true,
    allowInput: false,
    static: true
});

   filterStatusChoice = new Choices("#filterStatus", {
    searchEnabled: false,
    shouldSort: false,
    itemSelectText: "",
    allowHTML: false,
  });

   filterExperienceChoice = new Choices("#filterExperience", {
    searchEnabled: false,
    shouldSort: false,
    itemSelectText: "",
    allowHTML: false,
  });

   filterGenderChoice = new Choices("#filterGender", {
    searchEnabled: false,
    shouldSort: false,
    itemSelectText: "",
    allowHTML: false,
  });

  coGetCards().forEach((card) => (card.dataset.matches = "1"));
  coPopulateDepartmentFilter();
  coRenderPage();
  function getChoice(field) {
    return field.parentElement.querySelector(".choices");
  }
  function showError(field, message) {

    const wrapper = field.closest(".mb-3");
    const feedback = wrapper.querySelector(".invalid-feedback");

    if (feedback) {
      feedback.textContent = message;
    }

    if (field.tagName === "SELECT") {
      wrapper.querySelector(".choices").classList.add("is-invalid");
    } else {
      field.classList.add("is-invalid");
    }
  }

  function clearError(field) {

    const wrapper = field.closest(".mb-3");
    if (!wrapper) return;
    const feedback = wrapper.querySelector(".invalid-feedback");
    if (feedback) {
      feedback.textContent = "";
    }
    field.classList.remove("is-invalid");
    const choice = wrapper.querySelector(".choices");
    if (choice) {
      choice.classList.remove("is-invalid");
    }
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    let valid = true;
    [staff, role, hireDate, certification].forEach(clearError);

    if (!staff.value) {
      showError(staff, "Please select a staff member.");
      valid = false;
    }

    if (!role.value) {
      showError(role, "Please select a role.");
      valid = false;
    }
    if (!hireDate.value) {
      showError(hireDate, "Please select hire date.");
      valid = false;

    } else {
      const today = new Date().toISOString().split("T")[0];
      if (hireDate.value > today) {
        showError(hireDate, "Hire date cannot be in the future.");
        valid = false;
      }
    }

    if (certification.value.trim().length > 500) {
      showError(certification, "Maximum 500 characters allowed.");
      valid = false;
    }

    if (valid) {
      form.submit();
    }
  });
  [staff, role].forEach(field => {
    field.addEventListener("change", () => clearError(field));
  });

  [hireDate, certification].forEach(field => {
    field.addEventListener("input", () => clearError(field));
  });
  let shouldReset = false;

  assignCoachModal.querySelector(".btn-close").addEventListener("click", () => {
    shouldReset = true;
  });

  assignCoachModal.querySelector(".btn-light").addEventListener("click", () => {
    shouldReset = true;
  });

  assignCoachModal.addEventListener("hidden.bs.modal", () => {
    if (!shouldReset) return;
    form.reset();
    staffChoice.removeActiveItems();
    roleChoice.removeActiveItems();
    clearError(staff);
    clearError(role);
    clearError(hireDate);
    clearError(certification);
    shouldReset = false;
  });


});

function toggleCoachMenu(button) {
  document.querySelectorAll(".co-menu-dropdown").forEach(menu => {
    if (menu !== button.nextElementSibling) {
      menu.classList.remove("show");
    }
  });
  button.nextElementSibling.classList.toggle("show");
}

document.addEventListener("click", function (e) {

  if (!e.target.closest(".co-card-menu")) {
    document.querySelectorAll(".co-menu-dropdown").forEach(menu => {
      menu.classList.remove("show");
    });
  }

});

cocurrentPage = 1;
coRenderPage();

function resetCoachFilters() {

  document.getElementById("coachSearch").value = "";

  filterStatusChoice.setChoiceByValue("");
  filterGenderChoice.setChoiceByValue("");
  filterExperienceChoice.setChoiceByValue("");

  filterCoaches();
}

// Steve code

document.addEventListener("DOMContentLoaded", () => {

    const programSelect   = document.querySelector('select[name="program"]');
    const studyYearSelect = document.querySelector('select[name="study_year"]');
    const termSelect      = document.querySelector('select[name="term"]');
    const statusRadios    = document.querySelectorAll('input[name="status"]');

    const courseGrid      = document.getElementById("courseGrid");
    const courseListEmpty = document.getElementById("courseListEmpty");
    const courseSearch    = document.getElementById("courseSearch");
    const selectAllBox    = document.getElementById("selectAllCourses");

    const prevAvatar  = document.getElementById("prevAvatar");
    const prevProgram = document.getElementById("prevProgram");
    const prevSem     = document.getElementById("prevSem");
    const prevCount   = document.getElementById("prevCount");
    const prevStatus  = document.getElementById("prevStatus");
    const selectedCountLabel = document.getElementById("selectedCountLabel");

    const form      = document.getElementById("programCourseForm");
    const submitBtn = document.getElementById("submitBtn");

    function selectedText(select) {
        const opt = select?.selectedOptions?.[0];
        return opt && opt.value ? opt.textContent.trim() : "";
    }

    function getStatus() {
        for (const r of statusRadios) {
            if (r.checked) return r.value;
        }
        return "";
    }

    function getSelectedCount() {
        return courseGrid.querySelectorAll('input[name="courses"]:checked').length;
    }

    function updatePreview() {
        const programText = selectedText(programSelect);
        const studyYear    = selectedText(studyYearSelect);
        const term         = selectedText(termSelect);
        const status       = getStatus();
        const count        = getSelectedCount();

        prevAvatar.textContent  = programText ? programText[0].toUpperCase() : "?";
        prevProgram.textContent = programText || "Program Name";
        prevSem.textContent     = `${studyYear || "Year -"} | ${term || "Term -"}`;

        prevCount.textContent = `${count} selected`;
        selectedCountLabel.textContent = count;

        prevStatus.textContent = status === "INACTIVE" ? "Inactive" : "Active";
        prevStatus.classList.toggle("is-active", status !== "INACTIVE");
        prevStatus.classList.toggle("is-inactive", status === "INACTIVE");
    }

    function showError(select, message) {
        if (!select) return;
        const field = select.closest(".df-field");
        field?.classList.add("has-error");
        let errEl = field?.querySelector(".df-error");
        if (!errEl) {
            errEl = document.createElement("div");
            errEl.className = "df-error";
            select.closest(".df-input-wrap")?.after(errEl);
        }
        errEl.innerHTML = `<svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> ${message}`;
    }

    function clearError(select) {
        if (!select) return;
        const field = select.closest(".df-field");
        field?.classList.remove("has-error");
        field?.querySelector(".df-error")?.remove();
    }

    function clearCourseGridError() {
        courseGrid.closest(".df-card-body")?.querySelector(".df-error")?.remove();
    }

    function buildCourseCard(course) {
        const wrap = document.createElement("label");
        wrap.className = "course-card";
        wrap.dataset.name = `${course.code || ""} ${course.name}`.toLowerCase();

        wrap.innerHTML = `
            <input type="checkbox" name="courses" value="${course.id}" class="course-card-check">
            <span class="course-card-body">
                <span class="course-card-name">${course.name}</span>
            </span>
            <span class="course-card-elective" title="Mark as elective">
                <input type="checkbox" name="elective_courses" value="${course.id}" class="course-elective-check">
                <span>Elective</span>
            </span>
        `;

        wrap.querySelector(".course-card-check").addEventListener("change", (e) => {
            wrap.classList.toggle("is-checked", e.target.checked);
            clearCourseGridError();
            updatePreview();
        });

        // stop the elective checkbox from toggling the outer course selection
        wrap.querySelector(".course-elective-check").addEventListener("click", (e) => {
            e.stopPropagation();
        });

        return wrap;
    }

    async function loadCourses() {
        const programId = programSelect.value;
        courseGrid.innerHTML = "";
        selectAllBox.checked = false;
        updatePreview();

        if (!programId) {
            courseListEmpty.style.display = "block";
            courseListEmpty.textContent = "Select a program above to load its courses.";
            return;
        }

        courseListEmpty.style.display = "block";
        courseListEmpty.textContent = "Loading courses…";
     
        // Rixie code start //
        try {
            const response = await fetch(`/colleges/ajax/program/${programId}/courses/?exclude_allocated=1`);
            if (!response.ok) throw new Error("Failed to load courses");
        // Rixie code end //
            const data = await response.json();
            courseGrid.innerHTML = "";

            if (!data.length) {
                courseListEmpty.style.display = "block";
                courseListEmpty.textContent = "No active courses found for this program.";
                return;
            }

            courseListEmpty.style.display = "none";
            data.forEach(course => courseGrid.appendChild(buildCourseCard(course)));
            updatePreview();

        } catch (err) {
            console.error(err);
            courseListEmpty.style.display = "block";
            courseListEmpty.textContent = "Could not load courses. Please try again.";
        }
    }

    programSelect?.addEventListener("change", () => {
        clearError(programSelect);
        loadCourses();
    });

    studyYearSelect?.addEventListener("change", () => { clearError(studyYearSelect); updatePreview(); });
    termSelect?.addEventListener("change", () => { clearError(termSelect); updatePreview(); });
    statusRadios.forEach(r => r.addEventListener("change", updatePreview));

    selectAllBox?.addEventListener("change", () => {
        courseGrid.querySelectorAll(".course-card").forEach(card => {
            const cb = card.querySelector(".course-card-check");
            cb.checked = selectAllBox.checked;
            card.classList.toggle("is-checked", selectAllBox.checked);
        });
        clearCourseGridError();
        updatePreview();
    });

    courseSearch?.addEventListener("input", () => {
        const term = courseSearch.value.trim().toLowerCase();
        courseGrid.querySelectorAll(".course-card").forEach(card => {
            card.style.display = card.dataset.name.includes(term) ? "" : "none";
        });
    });

    updatePreview();

    form?.addEventListener("submit", (e) => {
        let valid = true;

        clearError(programSelect);
        if (!programSelect?.value) {
            showError(programSelect, "Please select a program.");
            valid = false;
        }

        clearError(studyYearSelect);
        if (!studyYearSelect?.value) {
            showError(studyYearSelect, "Please select study year.");
            valid = false;
        }

        clearError(termSelect);
        if (!termSelect?.value) {
            showError(termSelect, "Please select term.");
            valid = false;
        }

        clearCourseGridError();
        if (getSelectedCount() === 0) {
            const body = courseGrid.closest(".df-card-body");
            const err = document.createElement("div");
            err.className = "df-error";
            err.innerHTML = `<svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> Please select at least one course.`;
            body?.insertBefore(err, courseListEmpty);
            valid = false;
        }

        if (!valid) {
            e.preventDefault();
            document.querySelector(".df-field.has-error, .df-error")
                ?.scrollIntoView({ behavior: "smooth", block: "center" });
        } else {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
                    <path d="M21 12a9 9 0 11-6.219-8.56"/>
                </svg>
                Saving…`;
        }
    });

});
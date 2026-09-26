// Steve code

document.addEventListener("DOMContentLoaded", () => {

    const programSelect   = document.querySelector('select[name="program"]');
    const courseSelect    = document.querySelector('select[name="course"]');
    const studyYearSelect = document.querySelector('select[name="study_year"]');
    const termSelect      = document.querySelector('select[name="term"]');
    const electiveCheckbox = document.getElementById("id_is_elective");
    const statusRadios    = document.querySelectorAll('input[name="status"]');
    const electiveText    = document.getElementById("electiveText");

    const prevAvatar  = document.getElementById("prevAvatar");
    const prevCourse  = document.getElementById("prevCourse");
    const prevProgram = document.getElementById("prevProgram");
    const prevSem     = document.getElementById("prevSem");
    const prevElective = document.getElementById("prevElective");
    const prevStatus  = document.getElementById("prevStatus");

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

    function updatePreview() {
        const courseText  = selectedText(courseSelect);
        const programText = selectedText(programSelect);
        const studyYear    = selectedText(studyYearSelect);
        const term         = selectedText(termSelect);
        const isElective   = !!electiveCheckbox?.checked;
        const status       = getStatus();

        prevAvatar.textContent  = courseText ? courseText[0].toUpperCase() : "?";
        prevCourse.textContent  = courseText || "Course Name";
        prevProgram.textContent = programText || "Program Name";

        if (prevSem) {
            prevSem.textContent = `${studyYear || "Year -"} | ${term || "Term -"}`;
        }

        prevElective.textContent = isElective ? "Elective" : "Core";
        prevElective.classList.toggle("is-elective", isElective);

        prevStatus.textContent = status === "INACTIVE" ? "Inactive" : "Active";
        prevStatus.classList.toggle("is-active", status !== "INACTIVE");
        prevStatus.classList.toggle("is-inactive", status === "INACTIVE");

        if (electiveText) {
            electiveText.textContent = isElective
                ? "This is an elective course"
                : "This is a core (required) course";
        }
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

    programSelect?.addEventListener("change", async function () {
        updatePreview();
        clearError(programSelect);

        const programId = this.value;
        courseSelect.value = "";
        updatePreview();
 // Rixie codde start //
        const currentProgramCourseId = document.getElementById("currentProgramCourseId")?.value || "";

        try {
            const response = await fetch(`/colleges/ajax/program/${programId}/courses/?exclude_allocated=1&current_program_course_id=${currentProgramCourseId}`);
 // Rixie code end //
            if (!response.ok) throw new Error("Failed to load courses");
            const data = await response.json();

            let courseChoices = window.choicesInstances?.["id_course"];

            if (courseChoices) {
                courseChoices.destroy();
                courseSelect.innerHTML = "";

                const defaultOption = document.createElement("option");
                defaultOption.value = "";
                defaultOption.textContent = "Select Course";
                courseSelect.appendChild(defaultOption);

                data.forEach(course => {
                    const option = document.createElement("option");
                    option.value = course.id;
                    option.textContent = course.name;
                    courseSelect.appendChild(option);
                });

                courseChoices = new Choices(courseSelect, {
                    searchEnabled: true,
                    shouldSort: false,
                    itemSelectText: "",
                    allowHTML: false,
                });

                window.choicesInstances["id_course"] = courseChoices;
            } else {
                courseSelect.innerHTML = '<option value="">Select Course</option>';
                data.forEach(course => {
                    courseSelect.innerHTML += `<option value="${course.id}">${course.name}</option>`;
                });
            }

            updatePreview();
        } catch (err) {
            console.error(err);
        }
    });

    courseSelect?.addEventListener("change", () => { updatePreview(); clearError(courseSelect); });
    studyYearSelect?.addEventListener("change", () => { updatePreview(); clearError(studyYearSelect); });
    termSelect?.addEventListener("change", () => { updatePreview(); clearError(termSelect); });
    statusRadios.forEach(r => r.addEventListener("change", updatePreview));
    electiveCheckbox?.addEventListener("change", updatePreview);

    updatePreview();

    form?.addEventListener("submit", (e) => {
        let valid = true;

        clearError(programSelect);
        if (!programSelect?.value) {
            showError(programSelect, "Please select a program.");
            valid = false;
        }

        clearError(courseSelect);
        if (!courseSelect?.value) {
            showError(courseSelect, "Please select a course.");
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

        if (!valid) {
            e.preventDefault();
            document.querySelector(".df-field.has-error")
                ?.scrollIntoView({ behavior: "smooth", block: "center" });
        } else {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
                    <path d="M21 12a9 9 0 11-6.219-8.56"/>
                </svg>
                Updating…`;
        }
    });


});
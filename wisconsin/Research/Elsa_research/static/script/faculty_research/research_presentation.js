document.addEventListener("DOMContentLoaded", function () {
    if (window.lucide) lucide.createIcons();
// ==============================================================================
    const presentationDateInput = document.getElementById("presentationDate");
    if (presentationDateInput) {
        const todayStr = new Date().toLocaleDateString("en-CA"); // "YYYY-MM-DD" in local time
        presentationDateInput.setAttribute("max", todayStr);
    }   
// ================================================================================
    const select = document.getElementById("progressResearchSelect");
    if (select) {
        new Choices(select, {
            searchEnabled: true,
            itemSelectText: "",
            shouldSort: false,
        });
    }

    const form = document.getElementById("presentationForm");
    if (form) {
        form.addEventListener("submit", function (e) {
            e.preventDefault();
            clearPresentationErrors();

            const btn = document.getElementById("savePresentationBtn");
            const originalHTML = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = "Saving...";

            fetch(form.action, {
                method: "POST",
                headers: { "X-Requested-With": "XMLHttpRequest" },
                body: new FormData(form),
            })
                .then(res => res.json().then(data => ({ status: res.status, data })))
                .then(({ status, data }) => {
                    if (status === 200 && data.success) {
                        window.location.reload();
                        return;
                    }
                    showPresentationErrors(data.errors || {});
                    btn.disabled = false;
                    btn.innerHTML = originalHTML;
                })
                .catch(err => {
                    console.error("Presentation save failed:", err);
                    btn.disabled = false;
                    btn.innerHTML = originalHTML;
                    alert("Something went wrong. Please try again.");
                });
        });
    }
});

function clearPresentationErrors() {
    document.querySelectorAll("#presentationForm .rp-error").forEach(el => el.textContent = "");
    document.querySelectorAll("#presentationForm .input-error").forEach(el => el.classList.remove("input-error"));
}

function showPresentationErrors(errors) {
    const fieldToInput = {
        event_name: "presentationEvent",
        presentation_date: "presentationDate",
        award: "presentationAward",
    };
    Object.keys(errors).forEach(function (field) {
        const errEl = document.getElementById("err-" + field);
        if (errEl) errEl.textContent = errors[field];
        const inputEl = document.getElementById(fieldToInput[field]);
        if (inputEl) inputEl.classList.add("input-error");
    });
}

window.openPresentationModal = function () {
    document.getElementById("presentationForm").reset();
    document.getElementById("presentationId").value = "";
    clearPresentationErrors();
    document.getElementById("presentationModalTitle").innerHTML = '<i data-lucide="presentation"></i> Add Presentation';
    document.getElementById("savePresentationBtn").innerHTML = '<i data-lucide="save"></i> Save Presentation';
    document.getElementById("presentationModal").classList.add("active");
    if (window.lucide) lucide.createIcons();
};

window.editPresentation = function (btn) {
    clearPresentationErrors();
    document.getElementById("presentationId").value = btn.dataset.id;
    document.getElementById("presentationEvent").value = btn.dataset.event;
    document.getElementById("presentationDate").value = btn.dataset.date;
    document.getElementById("presentationAward").value = btn.dataset.award;
    document.getElementById("presentationModalTitle").innerHTML = '<i data-lucide="edit"></i> Edit Presentation';
    document.getElementById("savePresentationBtn").innerHTML = '<i data-lucide="save"></i> Update Presentation';
    document.getElementById("presentationModal").classList.add("active");
    if (window.lucide) lucide.createIcons();
};

window.closePresentationModal = function () {
    document.getElementById("presentationForm").reset();
    clearPresentationErrors();
    document.getElementById("presentationModal").classList.remove("active");
};

window.addEventListener("click", function (event) {
    const modal = document.getElementById("presentationModal");
    if (event.target === modal) closePresentationModal();
});
window.openPresentationDetailModal = function (data) {
    document.getElementById("detailEventName").textContent = data.event;
    document.getElementById("detailDate").textContent = data.date;

    const awardBox = document.getElementById("detailAwardBox");
    if (data.award) {
        awardBox.style.display = "block";
        document.getElementById("detailAward").textContent = data.award;
    } else {
        awardBox.style.display = "none";
    }

    const certBlock = document.getElementById("detailCertBlock");
    if (data.certificateUrl) {
        certBlock.style.display = "block";
        document.getElementById("detailCertLink").href = data.certificateUrl;
    } else {
        certBlock.style.display = "none";
    }

    const docsBlock = document.getElementById("detailDocsBlock");
    const docsList = document.getElementById("detailDocsList");
    if (data.documents && data.documents.length) {
        docsBlock.style.display = "block";
        docsList.innerHTML = data.documents.map(d =>
            `<div class="rp-uploaded-file-row">
                <a href="${d.url}" target="_blank" class="rp-file-link" style="margin:0;">
                    <i data-lucide="file-text"></i> ${d.name}
                </a>
            </div>`
        ).join("");
    } else {
        docsBlock.style.display = "none";
    }

    document.getElementById("presentationDetailModal").classList.add("active");
    if (window.lucide) lucide.createIcons();
};

window.closePresentationDetailModal = function () {
    document.getElementById("presentationDetailModal").classList.remove("active");
};

window.addEventListener("click", function (event) {
    const modal = document.getElementById("presentationDetailModal");
    if (event.target === modal) closePresentationDetailModal();
});
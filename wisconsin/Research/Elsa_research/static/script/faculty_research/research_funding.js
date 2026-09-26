document.addEventListener("DOMContentLoaded", function () {
    lucide.createIcons();   

// ==============================================================================
    const awardDateInput = document.getElementById("awardDate");
    if (awardDateInput) {
        const todayStr = new Date().toLocaleDateString("en-CA"); // "YYYY-MM-DD" in local time
        awardDateInput.setAttribute("max", todayStr);
    }    
// ================================================================================
    document.querySelectorAll(".rf-choice").forEach(function (el) {
        if (el.id === "researchFilter") return;
        new Choices(el, {
            searchEnabled: false,
            itemSelectText: "",
            shouldSort: false,
        });
    });
    const researchFilter = document.getElementById("researchFilter");
    if (researchFilter) {
        new Choices(researchFilter, {
            searchEnabled: true,
            searchPlaceholderValue: "Search project...",
            itemSelectText: "",
            shouldSort: false,
            noResultsText: "No project found",
        });
    }
    const researchSelect = document.getElementById("researchSelect");
    if (researchSelect) {
        window.researchChoices = new Choices(researchSelect, {
            searchEnabled: true,
            itemSelectText: "",
            shouldSort: false,
        });
    }
    const cancelBtn = document.getElementById("cancelFundingBtn");
    if(cancelBtn){
        cancelBtn.addEventListener(
            "click",
            window.closeFundingModal
        );
    }

});


// ADD MODE
window.openFundingModal = function(){
    document.getElementById("fundingForm").reset();
    document.getElementById("fundingId").value = "";
    clearFormErrors();
    document.getElementById("fundingModalTitle").innerHTML =
    '<i data-lucide="hand-coins"></i> Add New Funding';
    document.getElementById("saveFundingBtn").innerHTML =
    '<i data-lucide="save"></i> Save Funding';
    document
    .getElementById("fundingModal")
    .classList.add("active");
    lucide.createIcons();
};

// CLOSE MODAL
window.closeFundingModal = function () {
    document.getElementById("fundingForm").reset();
    clearFormErrors();
    document.getElementById("fundingModal").classList.remove("active");
};

// EDIT MODE
window.editFunding = function(btn){
    console.log("Edit clicked", btn.dataset);
    document.getElementById("fundingId").value =
        btn.dataset.id;
    // update Choices dropdown
    if(window.researchChoices){
        window.researchChoices.setChoiceByValue(
            btn.dataset.research
        );
    }
    document.getElementById("fundingSource").value =
        btn.dataset.source;
    document.getElementById("fundingAmount").value =
        btn.dataset.amount;
    document.getElementById("awardDate").value =
        btn.dataset.date;
    document.getElementById("sponsor").value =
        btn.dataset.sponsor;
    document.getElementById("fundingModalTitle").innerHTML =
    '<i data-lucide="pencil"></i> Edit Funding';
    document.getElementById("saveFundingBtn").innerHTML =
    '<i data-lucide="save"></i> Update Funding';
    document
    .getElementById("fundingModal")
    .classList.add("active");
    lucide.createIcons();
};

// CLICK OUTSIDE CLOSE
window.onclick = function(event){
    const modal =
    document.getElementById("fundingModal");
    if(event.target === modal){
        window.closeFundingModal();
    }
};

function clearFormErrors() {
    document.querySelectorAll("#fundingForm .text-danger")
        .forEach(el => el.textContent = "");
    document.querySelectorAll("#fundingForm .input-error")
        .forEach(el => el.classList.remove("input-error"));
}

function showFormErrors(errors) {
    const fieldToInput = {
        research: "researchSelect",
        funding_source: "fundingSource",
        amount: "fundingAmount",
        award_date: "awardDate",
        sponsor: "sponsor",
    };
    Object.keys(errors).forEach(function (field) {
        const errEl = document.getElementById("err-" + field);
       if (errEl) { errEl.textContent = "⚠ " + errors[field]; }
        const inputEl = document.getElementById(fieldToInput[field]);
        if (inputEl) inputEl.classList.add("input-error");
    });
}

const fundingForm = document.getElementById("fundingForm");
if (fundingForm) {
    fundingForm.addEventListener("submit", function (e) {
        e.preventDefault();
        clearFormErrors();
        const saveBtn = document.getElementById("saveFundingBtn");
        const originalHTML = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = "Saving...";
        fetch(window.location.pathname + window.location.search, {
            method: "POST",
            headers: { "X-Requested-With": "XMLHttpRequest" },
            body: new FormData(fundingForm),
        })
            .then(res => res.json().then(data => ({ status: res.status, data })))
            .then(({ status, data }) => {
                if (status === 200 && data.success) {
                    window.location.reload();
                    return;
                }
                showFormErrors(data.errors || {});
                saveBtn.disabled = false;
                saveBtn.innerHTML = originalHTML;
            })
            .catch(err => {
                console.error("Funding save failed:", err);
                saveBtn.disabled = false;
                saveBtn.innerHTML = originalHTML;
                alert("Something went wrong. Please try again.");
            });
    });
}
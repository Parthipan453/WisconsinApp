// // =======================
// // TOAST
// // =======================
// const toastEl = document.getElementById("liveToast");
// const toastMsg = document.getElementById("toastMessage");
// const toast = toastEl ? new bootstrap.Toast(toastEl, { delay: 2000 }) : null;

// function showToast(message, type) {
//     if (!toastEl || !toastMsg || !toast) {
//         console.warn("Toast elements (#liveToast / #toastMessage) not found in DOM. Message was:", message);
//         return;
//     }
//     toastMsg.innerText = message;
//     toastEl.classList.remove(
//         "text-bg-success",
//         "text-bg-danger",
//         "text-bg-warning",
//         "text-bg-info"
//     );
//     toastEl.classList.add(`text-bg-${type}`);
//     toast.show();
// }

// =======================
// CSRF TOKEN
// =======================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// =======================
// DOM READY
// =======================
document.addEventListener("DOMContentLoaded", function () {

    // =======================
    // CHART
    // =======================
    const ctx = document.getElementById("gradeChart");

    if (ctx && typeof Chart !== "undefined") {
        const chartData = window.GRADE_CHART_DATA || { labels: [], points: [], colors: [] };

        if (!chartData.labels || chartData.labels.length === 0) {
            const wrapper = ctx.closest(".chart-wrapper") || ctx.parentElement;
            if (wrapper) {
                wrapper.innerHTML = `
                    <div class="chart-empty-state">
                        <i data-lucide="pie-chart"></i>
                        <p>No grades added yet</p>
                        <span>Add a grade to see the distribution here</span>
                    </div>
                `;
                if (typeof lucide !== "undefined") lucide.createIcons();
            }
        } else {
            new Chart(ctx, {
                type: "doughnut",
                data: {
                    labels: chartData.labels,
                    datasets: [{
                        data: chartData.points,
                        backgroundColor: chartData.colors,
                        borderColor: "#ffffff",
                        borderWidth: 3,
                        hoverOffset: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: "68%",
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: { usePointStyle: true, pointStyle: "circle", padding: 18, font: { size: 13 } }
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    const idx = context.dataIndex;
                                    const pts = chartData.points[idx];
                                    const min = chartData.min[idx];
                                    const max = chartData.max[idx];
                                    return `${context.label} : ${min}% - ${max}%    (${pts} pts)`;
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    // ============ DELETE MODAL BLOCK (no Bootstrap) ============
    const deleteModalEl = document.getElementById("deleteConfirmModal");

    if (deleteModalEl) {
        const gradeNameSpan = document.getElementById("deleteGradeName");
        const confirmBtn = document.getElementById("confirmDeleteBtn");
        const cancelBtn = document.getElementById("deleteModalCancelBtn");
        const closeBtn = document.getElementById("deleteModalCloseBtn");

        let pendingUrl = null;
        let pendingRow = null;

        function openDeleteModal(url, row, name) {
            pendingUrl = url;
            pendingRow = row;
            gradeNameSpan.textContent = name || "";
            deleteModalEl.classList.add("show");
            document.body.classList.add("custom-modal-open");
        }

        function closeDeleteModal() {
            deleteModalEl.classList.remove("show");
            document.body.classList.remove("custom-modal-open");
            pendingUrl = null;
            pendingRow = null;
        }

        function resetDeleteButton() {
            confirmBtn.disabled = false;
            confirmBtn.innerText = "Delete";
        }

        document.querySelectorAll(".delete-btn").forEach(function (btn) {
            btn.addEventListener("click", function () {
                openDeleteModal(
                    btn.getAttribute("data-url"),
                    btn.closest("tr"),
                    btn.getAttribute("data-name")
                );
            });
        });
        cancelBtn.addEventListener("click", closeDeleteModal);
        closeBtn.addEventListener("click", closeDeleteModal);
        deleteModalEl.addEventListener("click", function (e) {
            if (e.target === deleteModalEl) closeDeleteModal();
        });

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && deleteModalEl.classList.contains("show")) {
                closeDeleteModal();
            }
        });

        confirmBtn.addEventListener("click", async function () {
            if (!pendingUrl) return;
            confirmBtn.disabled = true;
            confirmBtn.innerText = "Deleting...";
            // Safety net: never let the button stay stuck longer than 8 seconds
            const failSafeTimer = setTimeout(() => {
                console.error("Delete request took too long / did not resolve.");
                resetDeleteButton();
                showToast("error", "Request timed out. Please try again.");
            }, 8000);

            try {
                const csrftoken = getCookie("csrftoken");

                let response = await fetch(pendingUrl, {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "X-CSRFToken": csrftoken
                    }
                });

                clearTimeout(failSafeTimer);
                const rawText = await response.text();
                let data;
                try {
                    data = JSON.parse(rawText);
                } catch (parseErr) {
                    console.error("Delete response was not JSON. Status:", response.status);
                    console.error("Raw response:", rawText.substring(0, 500));
                    closeDeleteModal();
                    showToast("danger",`Server error (${response.status}). Please try again.`);
                    resetDeleteButton();
                    return;
                }
                if (data.success) {
                    showToast("success", data.message || "Grade deleted successfully");
                    setTimeout(() => {
                        window.location.reload();
                    }, 800);
                } else {
                    closeDeleteModal();
                    showToast("error", data.message || "Could not delete grade");
                    resetDeleteButton();
                }
            } catch (err) {
                clearTimeout(failSafeTimer);
                console.error("Delete request failed:", err);
                closeDeleteModal();
                showToast("error", "Network error. Please try again later.");
                resetDeleteButton();
            }
        });
    } else {
        console.warn("deleteConfirmModal not found in DOM — delete button won't work.");
    }

    // =======================
    // ADD / EDIT FORM AJAX
    // =======================
    const gradeForm = document.getElementById("gradeForm");
    if (gradeForm) {
        gradeForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            document.querySelectorAll(".text-danger").forEach(el => {
                el.innerText = "";
            });
            let formData = new FormData(this);
            let response = await fetch("", {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            });
            let data = await response.json();
            if (data.success) {
                showToast("success", data.message);
                let formType = document.getElementById("formType")?.value;
                setTimeout(() => {
                    if (formType === "edit") {
                        window.location.href = "/dashboard/grade_scale/";
                    } else {
                        showToast("success", "Grade added successfully");
                        window.location.reload();
                    }
                }, 800);
            } else {
               showToast("error", data.message || "Please fix the errors and try again.");

                for (let field in data.errors) {
                    let errorDiv = document.getElementById(field + "_error");
                    if (errorDiv) {
                        errorDiv.innerText = data.errors[field];
                    }
                }
            }
        });
    }

    // =======================
    // HISTORY MODAL
    // =======================
    const buttons = document.querySelectorAll(".history-btn");
    buttons.forEach(function (button) {
        button.onclick = function (e) {
            e.preventDefault();
            let url = button.getAttribute("data-url");
            console.log("Calling:", url);
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    let body = document.getElementById("historyBody");
                    body.innerHTML = "";

                    if (data.history.length === 0) {

                        body.innerHTML = `
                        <tr>
                            <td colspan="6" class="text-center">
                                No history available
                            </td>
                        </tr>`;
                    } else {
                        data.history.forEach(row => {
                            body.innerHTML += `
                            <tr>
                                <td>${row.field}</td>
                                <td>${row.old}</td>
                                <td>${row.new}</td>
                                <td>${row.user}</td>
                                <td>${row.date}</td>
                                <td>${row.reason}</td>
                            </tr>`;
                        });
                    }
                    let modal = new bootstrap.Modal(
                        document.getElementById("historyModal")
                    );
                    modal.show();
                })
                .catch(error => {
                    console.log(error);
                });
        };
    });
});

// =======================
// LETTER GRADE INPUT FILTER
// =======================
const gradeInput = document.getElementById("letter_grade");
if (gradeInput) {
    gradeInput.addEventListener("input", function () {
        let value = this.value.toUpperCase();
        // Allow only alphabets and + -
        value = value.replace(/[^A-Z+-]/g, "");
        // + or - only once and only at the end
        value = value.replace(/([+-]).*[+-]/, "$1");
        // remove + or - if typed first
        value = value.replace(/^[+-]/, "");
        this.value = value;
    });
}

// =======================
// DESCRIPTION INPUT FILTER
// =======================
const descriptionInput = document.getElementById("description");
if (descriptionInput) {
    descriptionInput.addEventListener("input", function () {
        this.value = this.value.replace(/[^a-zA-Z ]/g, "");
    });
}
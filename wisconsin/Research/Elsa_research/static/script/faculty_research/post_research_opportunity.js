
console.log("post_research_opportunity.js loaded");

document.addEventListener("DOMContentLoaded", function () {

    const todayStr = new Date().toLocaleDateString("en-CA"); // "YYYY-MM-DD" in local time

    document.querySelectorAll('input[type="date"]').forEach(function (input) {
        if (input.value && input.value < todayStr) {
            return;
        }
        input.setAttribute("min", todayStr);
    });

    // ===============================
    // Add / Remove file rows
    // ===============================
    const addFileBtn = document.getElementById("add-file");
    const fileContainer = document.getElementById("file-container");

    if (!addFileBtn || !fileContainer) {
        console.log("File elements not found");
        return;
    }

    addFileBtn.addEventListener("click", function () {

        const row = document.createElement("div");
        row.className = "file-row";

        row.innerHTML = `
            <input 
                type="file"
                name="supporting_documents"
                accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.mp4,.mov,.avi">

            <button type="button" class="remove-file">
                ✕
            </button>
        `;

        fileContainer.appendChild(row);

        row.querySelector(".remove-file").addEventListener(
            "click",
            function () {
                row.remove();
            }
        );

    });

});
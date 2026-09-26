/* *********************************************** Arun code *************************************************** */

document.addEventListener("DOMContentLoaded", function () {
    AOS.init({ once: true });
});

/* ===== FILTER ===== */
function filterDocs(btn, type) {
    document.querySelectorAll(".doc-tab").forEach((t) => t.classList.remove("active"));
    btn.classList.add("active");

    document.querySelectorAll("#docTableBody tr").forEach((row) => {
        if (type === "all" || row.dataset.type === type) {
            row.classList.remove("hidden-row");
        } else {
            row.classList.add("hidden-row");
        }
    });
}

/* ===== UPLOAD MODAL ===== */
function openUploadModal() {
    document.getElementById("uploadModal").style.display = "flex";
    document.getElementById("document_id").value = "";
    document.getElementById("uploadType").value = "";
    clearFile();
}

function closeUploadModal(event) {
    if (!event || event.target === document.getElementById("uploadModal")) {
        document.getElementById("uploadModal").style.display = "none";
        clearFile();
        document.getElementById("uploadType").value = "";
        document.getElementById("document_id").value = "";
    }
}

/* ===== FILE HANDLING ===== */
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) showSelectedFile(file.name);
}

function handleDrop(event) {
    event.preventDefault();
    document.getElementById("dropZone").classList.remove("drag-over");
    const file = event.dataTransfer.files[0];
    if (file) {
        // Update file input
        const fileInput = document.getElementById("fileInput");
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
        showSelectedFile(file.name);
    }
}

function showSelectedFile(name) {
    document.getElementById("dropZone").style.display = "none";
    document.getElementById("selectedFile").style.display = "flex";
    document.getElementById("selectedFileName").textContent = name;
}

function clearFile() {
    document.getElementById("fileInput").value = "";
    document.getElementById("dropZone").style.display = "";
    document.getElementById("selectedFile").style.display = "none";
    document.getElementById("selectedFileName").textContent = "";
}

/* *********************************************** Parthi Code - Toast Notifications - 2026-07-20 *************************************************** */

// ✅ Toast functions using common toast from student_base.html
function showDocumentUploaded() {
    toastSuccess("Document uploaded successfully!");
}

function showDocumentDeleted() {
    toastSuccess("Document deleted successfully!");
}

function showDocumentError(message) {
    toastError(message || "Something went wrong. Please try again.");
}

function showDocumentWarning(message) {
    toastWarning(message || "Please check your input.");
}

function showDocumentInfo(message) {
    toastInfo(message || "Processing...");
}

/* *********************************************** Parthi Code - AJAX Submit - 2026-07-20 *************************************************** */

// ✅ Form Submit with AJAX
document.addEventListener("DOMContentLoaded", function() {
    const form = document.querySelector("#uploadForm");
    if (form) {
        form.addEventListener("submit", function(e) {
            e.preventDefault();
            
            // Validate
            const docType = document.getElementById("uploadType").value;
            const fileInput = document.getElementById("fileInput");
            const file = fileInput.files[0];
            
            if (!docType) {
                toastError("Please select a document type.");
                document.getElementById("uploadType").focus();
                document.getElementById("uploadType").style.borderColor = "#ef4444";
                return false;
            }
            
            if (!file) {
                toastError("Please select a file to upload.");
                document.getElementById("dropZone").style.borderColor = "#ef4444";
                return false;
            }
            
            // Validate file size (10MB max)
            if (file.size > 10 * 1024 * 1024) {
                toastError("File size must be less than 10MB.");
                return false;
            }
            
            // Clear error styles
            document.querySelectorAll("#uploadModal .mfield-input, #uploadModal .upload-drop-zone").forEach(function(input) {
                input.style.borderColor = "";
            });

            const formData = new FormData(form);
            
            toastInfo("Uploading document...");
            
            fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    toastSuccess(data.message || "Document uploaded successfully!");
                    closeUploadModal();
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                } else {
                    toastError(data.message || "Something went wrong!");
                }
            })
            .catch(error => {
                toastError("Network error. Please try again.");
                console.error("Error:", error);
            });
            
            return false;
        });
    }
});

// ✅ Clear error styles on focus
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll("#uploadModal .mfield-input, #uploadModal .upload-drop-zone").forEach(function(input) {
        input.addEventListener("focus", function() {
            this.style.borderColor = "";
        });
    });
});

// ✅ Keyboard shortcuts
document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") {
        const modal = document.getElementById("uploadModal");
        if (modal && modal.style.display === "flex") {
            closeUploadModal();
        }
    }
    
    if (e.ctrlKey && e.key === "Enter") {
        const form = document.querySelector("#uploadForm");
        if (form) {
            form.dispatchEvent(new Event("submit"));
        }
    }
});

/* *********************************************** Parthi Code - AJAX Delete - 2026-07-20 *************************************************** */

// ✅ Delete Document with AJAX
function deleteDocument(docId, docName) {
    if (!confirm(`Are you sure you want to delete "${docName}"?`)) {
        return;
    }
    
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
    if (!csrfToken) {
        toastError("Security token not found. Please refresh the page.");
        return;
    }
    
    toastInfo("Deleting document...");
    
    const formData = new FormData();
    formData.append('delete_document_id', docId);
    formData.append('csrfmiddlewaretoken', csrfToken.value);
    
    fetch(window.location.href, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastSuccess(data.message || "Document deleted successfully!");
            
            // Remove row from table
            const row = document.querySelector(`[data-doc-id="${docId}"]`);
            if (row) {
                row.style.transition = "opacity 0.3s";
                row.style.opacity = "0";
                setTimeout(() => {
                    row.remove();
                    const tbody = document.querySelector("#docTableBody");
                    if (tbody && tbody.children.length === 0) {
                        location.reload();
                    }
                }, 300);
            }
            
            // Remove from card list
            const card = document.querySelector(`[data-doc-id="${docId}"]`);
            if (card) {
                card.style.transition = "opacity 0.3s";
                card.style.opacity = "0";
                setTimeout(() => {
                    card.remove();
                }, 300);
            }
        } else {
            toastError(data.message || "Error deleting document!");
        }
    })
    .catch(error => {
        toastError("Network error. Please try again.");
        console.error("Error:", error);
    });
}

/* *********************************************** Parthi Code End - 2026-07-20 *************************************************** */

// ✅ EXPOSE FUNCTIONS GLOBALLY
window.openUploadModal = openUploadModal;
window.closeUploadModal = closeUploadModal;
window.filterDocs = filterDocs;
window.handleFileSelect = handleFileSelect;
window.handleDrop = handleDrop;
window.showSelectedFile = showSelectedFile;
window.clearFile = clearFile;
window.showDocumentUploaded = showDocumentUploaded;
window.showDocumentDeleted = showDocumentDeleted;
window.showDocumentError = showDocumentError;
window.showDocumentWarning = showDocumentWarning;
window.showDocumentInfo = showDocumentInfo;
window.deleteDocument = deleteDocument;

console.log("✅ Documents page loaded successfully! (Parthi Code - 2026-07-20)");

/* *********************************************** Arun code *************************************************** */
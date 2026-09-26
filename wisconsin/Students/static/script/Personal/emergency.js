/* *********************************************** Arun code *************************************************** */

document.addEventListener("DOMContentLoaded", function () {
    AOS.init({ once: true });
});

function openContactModal() {
    document.getElementById("contactModalTitle").textContent = "Add Emergency Contact";
    document.getElementById("contact_id").value = "";
    clearContactFields();
    document.getElementById("contactModal").style.display = "flex";
}

function openEditContactModal(id, name, relationship, phone, email, priority) {
    document.getElementById("contactModalTitle").textContent = "Edit Emergency Contact";
    document.getElementById("contact_id").value = id;
    document.getElementById("ecName").value = name;
    document.getElementById("ecRelation").value = relationship;
    document.getElementById("ecPhone").value = phone;
    document.getElementById("ecEmail").value = email;
    document.getElementById("ecPriority").value = priority;
    document.getElementById("contactModal").style.display = "flex";
}

function closeContactModal(event) {
    if (!event || event.target === document.getElementById("contactModal")) {
        document.getElementById("contactModal").style.display = "none";
        clearContactFields();
        document.getElementById("contact_id").value = "";
    }
}

function clearContactFields() {
    document.getElementById("ecName").value = "";
    document.getElementById("ecRelation").value = "";
    document.getElementById("ecPhone").value = "";
    document.getElementById("ecEmail").value = "";
    document.getElementById("ecPriority").value = "1";
}

/* *********************************************** Parthi Code - Toast - 2026-07-20 *************************************************** */


function showContactAdded() {
    toastSuccess("Emergency contact added successfully!");
}

function showContactUpdated() {
    toastSuccess("Emergency contact updated successfully!");
}

function showContactDeleted() {
    toastSuccess("Emergency contact deleted successfully!");
}

function showContactError(message) {
    toastError(message || "Something went wrong. Please try again.");
}

/* *********************************************** Parthi Code - AJAX Submit - 2026-07-20 *************************************************** */

document.addEventListener("DOMContentLoaded", function() {
    const form = document.querySelector("#contactForm");
    if (form) {
        form.addEventListener("submit", function(e) {
            e.preventDefault();
            
            
            const name = document.getElementById("ecName").value.trim();
            const relationship = document.getElementById("ecRelation").value.trim();
            const phone = document.getElementById("ecPhone").value.trim();
            const email = document.getElementById("ecEmail").value.trim();
            
            if (!name) {
                toastError("Contact name is required.");
                document.getElementById("ecName").focus();
                document.getElementById("ecName").style.borderColor = "#ef4444";
                return false;
            }
            
            if (!relationship) {
                toastError("Relationship is required.");
                document.getElementById("ecRelation").focus();
                document.getElementById("ecRelation").style.borderColor = "#ef4444";
                return false;
            }
            
            if (!phone) {
                toastError("Phone number is required.");
                document.getElementById("ecPhone").focus();
                document.getElementById("ecPhone").style.borderColor = "#ef4444";
                return false;
            }
            
            // Validate phone number (10 digits)
            if (phone && !/^[0-9]{10}$/.test(phone)) {
                toastError("Please enter a valid 10-digit phone number.");
                document.getElementById("ecPhone").focus();
                document.getElementById("ecPhone").style.borderColor = "#ef4444";
                return false;
            }
            
            // Validate email (optional)
            if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                toastError("Please enter a valid email address.");
                document.getElementById("ecEmail").focus();
                document.getElementById("ecEmail").style.borderColor = "#ef4444";
                return false;
            }
            
            // Clear error styles
            document.querySelectorAll("#contactModal .mfield-input").forEach(function(input) {
                input.style.borderColor = "";
            });

            const formData = new FormData(form);
            
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
                    toastSuccess(data.message || "Emergency contact saved successfully!");
                    closeContactModal();
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


document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll("#contactModal .mfield-input").forEach(function(input) {
        input.addEventListener("focus", function() {
            this.style.borderColor = "";
        });
    });
});


document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") {
        const modal = document.getElementById("contactModal");
        if (modal && modal.style.display === "flex") {
            closeContactModal();
        }
    }
    
    if (e.ctrlKey && e.key === "Enter") {
        const form = document.querySelector("#contactForm");
        if (form) {
            form.dispatchEvent(new Event("submit"));
        }
    }
});

/* *********************************************** Parthi Code - AJAX Delete - 2026-07-20 *************************************************** */

function deleteContact(contactId, contactName) {
    if (!confirm(`Are you sure you want to delete ${contactName} as emergency contact?`)) {
        return;
    }
    
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
    if (!csrfToken) {
        toastError("Security token not found. Please refresh the page.");
        return;
    }
    
    toastInfo("Deleting contact...");
    
    const formData = new FormData();
    formData.append('delete_contact_id', contactId);
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
            toastSuccess(data.message || "Emergency contact deleted successfully!");
            
            const card = document.querySelector(`[data-contact-id="${contactId}"]`);
            if (card) {
                card.style.transition = "opacity 0.3s";
                card.style.opacity = "0";
                setTimeout(() => {
                    card.remove();
                    const grid = document.querySelector(".ec-list");
                    if (grid && grid.children.length === 0) {
                        location.reload();
                    }
                }, 300);
            }
        } else {
            toastError(data.message || "Error deleting contact!");
        }
    })
    .catch(error => {
        toastError("Network error. Please try again.");
        console.error("Error:", error);
    });
}

/* *********************************************** Parthi Code End - 2026-07-20 *************************************************** */

// EXPOSE FUNCTIONS GLOBALLY
window.openContactModal = openContactModal;
window.openEditContactModal = openEditContactModal;
window.closeContactModal = closeContactModal;
window.clearContactFields = clearContactFields;
window.showContactAdded = showContactAdded;
window.showContactUpdated = showContactUpdated;
window.showContactDeleted = showContactDeleted;
window.showContactError = showContactError;
window.deleteContact = deleteContact;

console.log("Emergency Contacts page loaded successfully!");

/* *********************************************** Arun code *************************************************** */
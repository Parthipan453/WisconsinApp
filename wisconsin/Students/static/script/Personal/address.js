/* *********************************************** Arun code *************************************************** */

document.addEventListener("DOMContentLoaded", function () {
    AOS.init({ once: true });
});

function openAddModal() {
    document.getElementById("modalTitle").textContent = "Add Address";
    document.getElementById("address_id").value = "";
    clearModalFields();
    document.getElementById("addrModal").style.display = "flex";
}

function openEditModal(id, type, line1, line2, city, state, zip, country) {
    document.getElementById("modalTitle").textContent = "Edit Address";
    document.getElementById("address_id").value = id;
    document.getElementById("addrType").value = type;
    document.getElementById("addrLine1").value = line1;
    document.getElementById("addrLine2").value = line2;
    document.getElementById("addrCity").value = city;
    document.getElementById("addrState").value = state;
    document.getElementById("addrZip").value = zip;
    document.getElementById("addrCountry").value = country;
    document.getElementById("addrModal").style.display = "flex";
}

function closeAddrModal(event) {
    if (!event || event.target === document.getElementById("addrModal")) {
        document.getElementById("addrModal").style.display = "none";
        clearModalFields();
        document.getElementById("address_id").value = "";
    }
}

function clearModalFields() {
    document.getElementById("addrType").value = "PERMANENT";
    document.getElementById("addrLine1").value = "";
    document.getElementById("addrLine2").value = "";
    document.getElementById("addrCity").value = "";
    document.getElementById("addrState").value = "";
    document.getElementById("addrZip").value = "";
    document.getElementById("addrCountry").value = "United States";
}

/* *********************************************** Parthi Code - Toast Notifications - 2026-07-20 *************************************************** */

function showAddressAdded() {
    toastSuccess("Address added successfully!");
}

function showAddressUpdated() {
    toastSuccess("Address updated successfully!");
}

function showAddressDeleted() {
    toastSuccess("Address deleted successfully!");
}

function showAddressError(message) {
    toastError(message || "Something went wrong. Please try again.");
}

function showAddressWarning(message) {
    toastWarning(message || "Please check your input.");
}

function showAddressInfo(message) {
    toastInfo(message || "Processing...");
}

/* *********************************************** Parthi Code - AJAX Submit - 2026-07-20 *************************************************** */

document.addEventListener("DOMContentLoaded", function() {
    const form = document.querySelector("#addressForm");
    if (form) {
        form.addEventListener("submit", function(e) {
            e.preventDefault();
            
            // Validate
            const line1 = document.getElementById("addrLine1").value.trim();
            const city = document.getElementById("addrCity").value.trim();
            const state = document.getElementById("addrState").value.trim();
            const zip = document.getElementById("addrZip").value.trim();
            
            if (!line1) {
                toastError("Address Line 1 is required.");
                document.getElementById("addrLine1").focus();
                document.getElementById("addrLine1").style.borderColor = "#ef4444";
                return false;
            }
            
            if (!city) {
                toastError("City is required.");
                document.getElementById("addrCity").focus();
                document.getElementById("addrCity").style.borderColor = "#ef4444";
                return false;
            }
            
            if (!state) {
                toastError("State is required.");
                document.getElementById("addrState").focus();
                document.getElementById("addrState").style.borderColor = "#ef4444";
                return false;
            }
            
            if (!zip) {
                toastError("Postal code is required.");
                document.getElementById("addrZip").focus();
                document.getElementById("addrZip").style.borderColor = "#ef4444";
                return false;
            }
            
            // Clear error styles
            document.querySelectorAll("#addrModal .mfield-input").forEach(function(input) {
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
                    toastSuccess(data.message || "Address saved successfully!");
                    closeAddrModal();
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
    document.querySelectorAll("#addrModal .mfield-input").forEach(function(input) {
        input.addEventListener("focus", function() {
            this.style.borderColor = "";
        });
    });
});


document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") {
        const modal = document.getElementById("addrModal");
        if (modal && modal.style.display === "flex") {
            closeAddrModal();
        }
    }
    
    if (e.ctrlKey && e.key === "Enter") {
        const form = document.querySelector("#addressForm");
        if (form) {
            form.dispatchEvent(new Event("submit"));
        }
    }
});

/* *********************************************** Parthi Code - AJAX Delete - 2026-07-20 *************************************************** */

function deleteAddress(addressId, addressType) {
    if (!confirm(`Are you sure you want to delete this ${addressType} address?`)) {
        return;
    }
    
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
    if (!csrfToken) {
        toastError("Security token not found. Please refresh the page.");
        return;
    }
    
    toastInfo("Deleting address...");
    
    const formData = new FormData();
    formData.append('delete_address_id', addressId);
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
            toastSuccess(data.message || "Address deleted successfully!");
            
            const card = document.querySelector(`[data-address-id="${addressId}"]`);
            if (card) {
                card.style.transition = "opacity 0.3s";
                card.style.opacity = "0";
                setTimeout(() => {
                    card.remove();
                    const grid = document.querySelector(".address-grid");
                    if (grid && grid.children.length === 0) {
                        location.reload();
                    }
                }, 300);
            }
        } else {
            toastError(data.message || "Error deleting address!");
        }
    })
    .catch(error => {
        toastError("Network error. Please try again.");
        console.error("Error:", error);
    });
}

/* *********************************************** Parthi Code End - 2026-07-20 *************************************************** */


window.openAddModal = openAddModal;
window.openEditModal = openEditModal;
window.closeAddrModal = closeAddrModal;
window.clearModalFields = clearModalFields;
window.showAddressAdded = showAddressAdded;
window.showAddressUpdated = showAddressUpdated;
window.showAddressDeleted = showAddressDeleted;
window.showAddressError = showAddressError;
window.showAddressWarning = showAddressWarning;
window.showAddressInfo = showAddressInfo;
window.deleteAddress = deleteAddress;

console.log("Address page loaded successfully! (Parthi Code - 2026-07-20)");

/* *********************************************** Arun code *************************************************** */
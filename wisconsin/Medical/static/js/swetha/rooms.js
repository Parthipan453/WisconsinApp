document.addEventListener("DOMContentLoaded", function () {

    if (window.AOS) {
        AOS.init({
            duration: 500,
            once: true,
            offset: 40,
        });
    }

    var floors = document.querySelectorAll(".med-rooms__floor");

    floors.forEach(function (floor, index) {

        var head = floor.querySelector(".med-rooms__floor-head");
        var body = floor.querySelector(".med-rooms__floor-body");

        if (!head || !body) {
            return;
        }

        head.addEventListener("click", function () {
            var isOpen = floor.classList.contains("is-open");

            if (isOpen) {
                floor.classList.remove("is-open");
                body.style.maxHeight = null;
            } else {
                floor.classList.add("is-open");
                body.style.maxHeight = body.scrollHeight + "px";
            }
        });

        
        if (index === 0) {
            floor.classList.add("is-open");
            body.style.maxHeight = body.scrollHeight + "px";
        }
    });

    window.addEventListener("resize", function () {
        document.querySelectorAll(".med-rooms__floor.is-open").forEach(function (floor) {
            var body = floor.querySelector(".med-rooms__floor-body");
            if (body) {
                body.style.maxHeight = body.scrollHeight + "px";
            }
        });
    });



    var root = document.querySelector(".med-rooms");

    if (!root) {
        return;
    }

    var ADMISSION_REQUESTS_URL = root.dataset.admissionRequestsUrl;
    var ADMIT_URL = root.dataset.admitUrl;
    var ROOM_OCCUPANT_URL_BASE = root.dataset.roomOccupantUrlBase;

    var admissionList = document.getElementById("admissionRequestsList");
    var admissionEmpty = document.getElementById("admissionRequestsEmpty");
    var admissionCountPill = document.getElementById("admissionRequestsCount");

    var admissionModal = document.getElementById("admissionRequestModal");
    var admissionModalPatientName = document.getElementById("admissionModalPatientName");
    var admissionModalDetails = document.getElementById("admissionModalDetails");
    var roomPickerList = document.getElementById("roomPickerList");
    var roomPickerEmpty = document.getElementById("roomPickerEmpty");
    var confirmAdmitBtn = document.getElementById("confirmAdmitBtn");

    var occupantModal = document.getElementById("roomOccupantModal");
    var occupantModalRoomName = document.getElementById("occupantModalRoomName");
    var occupantModalDetails = document.getElementById("occupantModalDetails");

    var selectedRegistrationId = null;
    var selectedRoomId = null;
    var checkupNoteInput = document.getElementById("checkupNoteInput");
    var saveCheckupBtn = document.getElementById("saveCheckupBtn");
    var checkupNotesList = document.getElementById("checkupNotesList");
    var checkupNotesEmpty = document.getElementById("checkupNotesEmpty");
    var ROOM_CHECKUP_URL_BASE = ROOM_OCCUPANT_URL_BASE;
    var currentOccupantRegistrationId = null;



    function getCookie(name) {
        var value = null;

        if (!document.cookie) {
            return value;
        }

        document.cookie.split(";").forEach(function (cookie) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                value = decodeURIComponent(cookie.substring(name.length + 1));
            }
        });

        return value;
    }

    var csrftoken = getCookie("csrftoken");

    function escapeHTML(value) {
        if (value === null || value === undefined) {
            return "";
        }
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    async function parseJsonResponse(response) {
        var contentType = response.headers.get("content-type") || "";
        var text = await response.text();

        if (!text) {
            return { success: false, message: "Server returned HTTP " + response.status };
        }

        if (!contentType.includes("application/json")) {
            return { success: false, message: "Server returned HTTP " + response.status };
        }

        try {
            return JSON.parse(text);
        } catch (error) {
            return { success: false, message: "Invalid JSON response from server." };
        }
    }

    async function apiRequest(url, method, payload) {
        var options = {
            method: method || "GET",
            credentials: "same-origin",
            headers: {
                Accept: "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": csrftoken || "",
            },
        };

        if (payload) {
            options.headers["Content-Type"] = "application/json";
            options.body = JSON.stringify(payload);
        }

        var response = await fetch(url, options);
        var data = await parseJsonResponse(response);

        if (!response.ok || !data.success) {
            throw new Error(data.message || "HTTP " + response.status);
        }

        return data;
    }

    function showToast(message, type) {
        var container = document.getElementById("med-rooms-toast-container");
        if (!container) {
            return;
        }

        var toast = document.createElement("div");
        toast.className = "med-rooms__toast" + (type === "error" ? " med-rooms__toast--error" : "");
        var icon = type === "error" ? "fa-circle-exclamation" : "fa-circle-check";

        toast.innerHTML = '<i class="fas ' + icon + '"></i><span>' + escapeHTML(message) + "</span>";
        container.appendChild(toast);

        setTimeout(function () { toast.classList.add("show"); }, 30);
        setTimeout(function () {
            toast.classList.remove("show");
            setTimeout(function () { toast.remove(); }, 250);
        }, 3200);
    }

    function openModal(modal) {
        if (modal) {
            modal.style.display = "flex";
        }
    }

    function closeModal(modal) {
        if (modal) {
            modal.style.display = "none";
        }
    }

    document.querySelectorAll("[data-close-modal]").forEach(function (el) {
        el.addEventListener("click", function () {
            closeModal(document.getElementById(this.dataset.closeModal));
        });
    });

    function detailItem(label, value, full) {
        return (
            '<div class="med-rooms__detail-item' + (full ? " med-rooms__detail-item--full" : "") + '">' +
            '<span class="med-rooms__detail-label">' + escapeHTML(label) + "</span>" +
            '<span class="med-rooms__detail-value">' + escapeHTML(value || "-") + "</span>" +
            "</div>"
        );
    }

    function admissionRemarkItem(value) {
        return (
            '<div class="med-rooms__detail-item med-rooms__detail-item--full med-rooms__detail-item--remark">' +
            '<span class="med-rooms__detail-label"><i class="fas fa-triangle-exclamation"></i> Admission Reason</span>' +
            '<span class="med-rooms__detail-value">' + escapeHTML(value || "No remark provided.") + "</span>" +
            "</div>"
        );
    }

  

    function renderAdmissionCard(req) {
        var card = document.createElement("div");
        card.className = "med-rooms__admission-card med-rooms__admission-card--" + req.priority;
        card.dataset.id = req.id;
        card.dataset.patientName = req.patient_name;
        card.dataset.patientNumber = req.patient_number;
        card.dataset.number = req.number;
        card.dataset.remark = req.remark;
        card.dataset.requestedBy = req.requested_by;
        card.dataset.requestedAt = req.requested_at;
        card.dataset.priority = req.priority;

        card.innerHTML =
            '<div class="med-rooms__admission-top">' +
            '<div class="med-rooms__admission-patient">' +
            '<span class="med-rooms__admission-avatar">' + escapeHTML((req.patient_name || "?").slice(0, 1)) + "</span>" +
            "<div>" +
            '<div class="med-rooms__admission-name">' + escapeHTML(req.patient_name) + "</div>" +
            '<div class="med-rooms__admission-id">' + escapeHTML(req.number) + "</div>" +
            "</div></div>" +
            '<span class="med-rooms__priority-badge med-rooms__priority-badge--' + req.priority + '">' +
            escapeHTML(req.priority.charAt(0).toUpperCase() + req.priority.slice(1)) +
            "</span></div>" +
            '<div class="med-rooms__admission-reason">' + escapeHTML(req.remark || "No remark provided.") + "</div>" +
            '<div class="med-rooms__admission-meta">' +
            '<span><i class="fas fa-user-doctor"></i> ' + escapeHTML(req.requested_by) + "</span>" +
            '<span><i class="fas fa-clock"></i> ' + escapeHTML(req.requested_at) + "</span>" +
            "</div>";

        card.addEventListener("click", function () {
            openAdmissionModal(card.dataset);
        });

        return card;
    }

    function refreshAdmissionRequestsUI(requests) {
        if (!admissionList) {
            return;
        }

        admissionList.innerHTML = "";

        requests.forEach(function (req) {
            admissionList.appendChild(renderAdmissionCard(req));
        });

        if (admissionCountPill) {
            admissionCountPill.textContent = requests.length + " pending";
        }

        if (admissionEmpty) {
            admissionEmpty.style.display = requests.length ? "none" : "block";
        }
    }

    async function pollAdmissionRequests() {
        if (!ADMISSION_REQUESTS_URL) {
            return;
        }

        try {
            var data = await apiRequest(ADMISSION_REQUESTS_URL, "GET");
            refreshAdmissionRequestsUI(data.requests || []);
        } catch (error) {
            console.error("Admission requests poll failed:", error);
        }
    }

    if (ADMISSION_REQUESTS_URL) {
        setInterval(pollAdmissionRequests, 8000);
    }

   

    function getAvailableRoomCards() {
        return Array.from(document.querySelectorAll('.med-rooms__room-card[data-status="AVAILABLE"]'));
    }

    function buildRoomPicker() {
        var availableRooms = getAvailableRoomCards();

        roomPickerList.innerHTML = "";
        selectedRoomId = null;
        confirmAdmitBtn.disabled = true;

        if (!availableRooms.length) {
            roomPickerEmpty.style.display = "block";
            return;
        }

        roomPickerEmpty.style.display = "none";

        var byFloor = {};

        availableRooms.forEach(function (roomEl) {
            var floorId = roomEl.dataset.floorId;
            if (!byFloor[floorId]) {
                byFloor[floorId] = [];
            }
            byFloor[floorId].push(roomEl);
        });

        Object.keys(byFloor).forEach(function (floorId) {
            var floorEl = document.querySelector('.med-rooms__floor[data-floor-id="' + floorId + '"]');
            var floorName = floorEl
                ? floorEl.querySelector(".med-rooms__floor-name").textContent.trim().replace(/\s+/g, " ")
                : "Floor";

            var wrapper = document.createElement("div");

            var heading = document.createElement("div");
            heading.className = "med-rooms__room-picker-floor";
            heading.textContent = floorName;
            wrapper.appendChild(heading);

            var grid = document.createElement("div");
            grid.className = "med-rooms__room-picker-grid";

            byFloor[floorId].forEach(function (roomEl) {
                var option = document.createElement("label");
                option.className = "med-rooms__room-option";
                option.dataset.roomId = roomEl.dataset.roomId;

                option.innerHTML =
                    '<input type="radio" name="roomPick" value="' + roomEl.dataset.roomId + '">' +
                    '<span class="med-rooms__room-option-text">' +
                    '<span class="med-rooms__room-option-number">' + escapeHTML(roomEl.dataset.roomNumber) + "</span>" +
                    '<span class="med-rooms__room-option-name">' + escapeHTML(roomEl.dataset.roomName) + "</span>" +
                    "</span>";

                option.querySelector("input").addEventListener("change", function () {
                    document.querySelectorAll(".med-rooms__room-option").forEach(function (el) {
                        el.classList.remove("is-selected");
                    });
                    option.classList.add("is-selected");
                    selectedRoomId = roomEl.dataset.roomId;
                    confirmAdmitBtn.disabled = false;
                });

                grid.appendChild(option);
            });

            wrapper.appendChild(grid);
            roomPickerList.appendChild(wrapper);
        });
    }

    function openAdmissionModal(data) {
        selectedRegistrationId = data.id;

        admissionModalPatientName.textContent = data.patientName || "Patient";

        admissionModalDetails.innerHTML =
            detailItem("Patient", data.patientName) +
            detailItem("Patient Number", data.patientNumber) +
            detailItem("Appointment / Token", data.number) +
            detailItem("Priority", data.priority) +
            detailItem("Requested By", data.requestedBy) +
            detailItem("Requested At", data.requestedAt) +
            detailItem("Admission Remark", data.remark || "No remark provided.", true);

        buildRoomPicker();
        openModal(admissionModal);
    }

    confirmAdmitBtn.addEventListener("click", async function () {
        if (!selectedRegistrationId || !selectedRoomId || !ADMIT_URL) {
            return;
        }

        var originalHTML = confirmAdmitBtn.innerHTML;
        confirmAdmitBtn.disabled = true;
        confirmAdmitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Admitting...';

        try {
            var data = await apiRequest(ADMIT_URL, "POST", {
                registration_id: selectedRegistrationId,
                room_id: selectedRoomId,
            });

            applyRoomOccupied(data.room_id);
            removeAdmissionCard(selectedRegistrationId);
            applyStats(data.status_counts, data.total_rooms);

            closeModal(admissionModal);
            showToast("Patient admitted successfully.", "success");
        } catch (error) {
            console.error("Admit patient error:", error);
            showToast(error.message || "Unable to admit patient.", "error");
        } finally {
            confirmAdmitBtn.disabled = false;
            confirmAdmitBtn.innerHTML = originalHTML;
        }
    });

    function removeAdmissionCard(registrationId) {
        var card = admissionList.querySelector('[data-id="' + registrationId + '"]');
        if (!card) {
            return;
        }
        card.classList.add("is-removing");
        setTimeout(function () {
            card.remove();
            var remaining = admissionList.querySelectorAll(".med-rooms__admission-card").length;
            if (admissionCountPill) {
                admissionCountPill.textContent = remaining + " pending";
            }
            if (admissionEmpty) {
                admissionEmpty.style.display = remaining ? "none" : "block";
            }
        }, 200);
    }

    function applyRoomOccupied(roomId) {
        var roomEl = document.querySelector('.med-rooms__room-card[data-room-id="' + roomId + '"]');
        if (!roomEl) {
            return;
        }

        roomEl.dataset.status = "OCCUPIED";

        var badge = roomEl.querySelector(".med-rooms__status-badge");
        if (badge) {
            badge.textContent = "Occupied";
            badge.className = "med-rooms__status-badge med-rooms__status-badge--occupied";
        }
    }

    function applyStats(statusCounts, totalRooms) {
        if (!statusCounts) {
            return;
        }

        var available = document.getElementById("statAvailable");
        var occupied = document.getElementById("statOccupied");
        var maintenance = document.getElementById("statMaintenance");
        var blocked = document.getElementById("statBlocked");
        var totalRoomsEl = document.getElementById("statTotalRooms");

        if (available) available.textContent = statusCounts.available;
        if (occupied) occupied.textContent = statusCounts.occupied;
        if (maintenance) maintenance.textContent = statusCounts.maintenance;
        if (blocked) blocked.textContent = statusCounts.blocked;
        if (totalRoomsEl && totalRooms !== undefined) totalRoomsEl.textContent = totalRooms;
    }


    function renderCheckupItem(note) {
        var item = document.createElement("div");
        item.className = "med-rooms__checkup-item";
        item.innerHTML =
            '<div class="med-rooms__checkup-item-meta">' +
            "<span>" + escapeHTML(note.created_by) + "</span>" +
            "<span>" + escapeHTML(note.created_at) + "</span>" +
            "</div>" +
            '<div class="med-rooms__checkup-item-text">' + escapeHTML(note.note) + "</div>";
        return item;
    }

    function renderCheckupNotes(notes) {
        checkupNotesList.innerHTML = "";

        if (!notes || !notes.length) {
            checkupNotesEmpty.style.display = "block";
            return;
        }

        checkupNotesEmpty.style.display = "none";

        notes.forEach(function (note) {
            checkupNotesList.appendChild(renderCheckupItem(note));
        });
    }

    document.querySelectorAll(".med-rooms__room-card").forEach(function (roomEl) {
        roomEl.addEventListener("click", async function () {
            if (roomEl.dataset.status !== "OCCUPIED" || !ROOM_OCCUPANT_URL_BASE) {
                return;
            }

            roomEl.classList.add("is-updating");

            try {
                var url = ROOM_OCCUPANT_URL_BASE + roomEl.dataset.roomId + "/occupant/";
                var data = await apiRequest(url, "GET");
                var occupant = data.occupant;

                
                occupantModalRoomName.textContent = occupant.room_number + " · " + occupant.room_name;

                occupantModalDetails.innerHTML =
                    detailItem("Patient", occupant.patient_name) +
                    detailItem("Patient Number", occupant.patient_number) +
                    detailItem("Appointment / Token", occupant.number) +
                    detailItem("Floor", occupant.floor_name) +
                    detailItem("Admitted By", occupant.admitted_by) +
                    detailItem("Admitted At", occupant.admitted_at) +
                    admissionRemarkItem(occupant.remark);

                currentOccupantRegistrationId = occupant.registration_id;
                checkupNoteInput.value = "";
                checkupNoteInput.classList.remove("is-invalid");
                renderCheckupNotes(occupant.checkup_notes);

                openModal(occupantModal);
            } catch (error) {
                console.error("Room occupant fetch failed:", error);
                showToast(error.message || "Unable to load room occupant.", "error");
            } finally {
                roomEl.classList.remove("is-updating");
            }
        });
    });

    checkupNoteInput.addEventListener("input", function () {
        checkupNoteInput.classList.remove("is-invalid");
    });

    saveCheckupBtn.addEventListener("click", async function () {
        var noteText = (checkupNoteInput.value || "").trim();

        if (!noteText) {
            checkupNoteInput.classList.add("is-invalid");
            checkupNoteInput.focus();
            showToast("Please give a remark.", "error");
            return;
        }

        checkupNoteInput.classList.remove("is-invalid");

        if (!currentOccupantRegistrationId || !ROOM_CHECKUP_URL_BASE) {
            showToast("Unable to identify this patient's room record. Please reopen the room.", "error");
            return;
        }

        var originalHTML = saveCheckupBtn.innerHTML;
        saveCheckupBtn.disabled = true;
        saveCheckupBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            var url = ROOM_CHECKUP_URL_BASE + currentOccupantRegistrationId + "/checkup/save/";
            var data = await apiRequest(url, "POST", { note: noteText });

            checkupNoteInput.value = "";
            checkupNotesList.insertBefore(renderCheckupItem(data.note), checkupNotesList.firstChild);
            checkupNotesEmpty.style.display = "none";

            showToast("Remarked successfully.", "success");
        } catch (error) {
            console.error("Save checkup error:", error);
            showToast(error.message || "Unable to save checkup remark.", "error");
        } finally {
            saveCheckupBtn.disabled = false;
            saveCheckupBtn.innerHTML = originalHTML;
        }
    });

});
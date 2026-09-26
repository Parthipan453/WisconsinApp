/* ==========================================================================
   ROOM PURPOSE LIST — temporary, to be replaced by backend-provided values
   ========================================================================== */


function getCookie(name) {
  let cookieValue = null;

  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");

    for (let cookie of cookies) {
      cookie = cookie.trim();

      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(
          cookie.substring(name.length + 1)
        );
        break;
      }
    }
  }

  return cookieValue;
}


function resetPurposeSelect(selectId) {
  const select = document.getElementById(selectId);

  if (!select) return;

  select.selectedIndex = 0;
  select.value = "";

  // Make sure the placeholder option is selected
  const firstOption = select.options[0];

  if (firstOption) {
    firstOption.selected = true;
  }
}




const roomPurposes = [
  "Patient Room",
  "Consultation Room",
  "Examination Room",
  "Treatment Room",
  "Procedure Room",
  "Operating Room",
  "Pre-Operative Room",
  "Post-Operative Recovery Room",
  "Emergency Room",
  "Trauma Room",
  "Isolation Room",
  "Negative Pressure Room",
  "Infusion Room",
  "Laboratory",
  "Pharmacy",
  "Nursing Station",
  "Doctor's Office",
  "Staff Room",
  "Waiting Room",
  "Patient Registration",
  "Medical Records Room",
  "Clean Utility Room",
  "Soiled Utility Room",
  "Sterilization Room",
  "Storage Room",
  "Housekeeping Room",
  "Administrative Office",
  "Conference Room",
  "Other"
];

/* ==========================================================================
    TEMPORARY ROOM DATA — represents rooms already created under a
    Hospital → Building → Floor structure on the backend
   ========================================================================== */


let purposeChoices = null;
let statusChoices = null;

/* ==========================================================================
   STATE
   ========================================================================== */
const state = {
  selected: new Set(),
  filters: { search: "", purpose: "all", status: "all" },
  openFloors: new Set(), // floors currently expanded
  singleModalRoomId: null, // room currently being edited in single modal
};

let floors = floorData;
let rooms = [];
let floorOrder = [];

function prepareRoomData() {
  rooms = [];

  floors.forEach((floor) => {
    floor.rooms.forEach((room) => {
      rooms.push({
        ...room,
        floor: floor.name,
        purpose: room.purpose || null,
        facilityName: room.facilityName || null,
        hasFacility: !!room.facilityName,
      });
    });
  });

  floorOrder = floors.map((floor) => floor.name);

  if (floorOrder.length) {
    state.openFloors.add(floorOrder[0]);
  }
}

const singleModal = new bootstrap.Modal(document.getElementById("singleModal"));
const bulkModal = new bootstrap.Modal(document.getElementById("bulkModal"));

/* ==========================================================================
   INIT
   ========================================================================== */
function init() {
  prepareRoomData();

  populatePurposeFilter();
  populatePurposeSelects();
  initializeStatusFilter();

  renderFloors();
  updateStatistics();
  bindGlobalEvents();
}

function populatePurposeFilter() {
  const sel = document.getElementById("purposeFilter");

  roomPurposes.forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p;
    opt.textContent = p;
    sel.appendChild(opt);
  });

  purposeChoices = new Choices(sel, {
  searchEnabled: true,
  searchPlaceholderValue: "Search purpose...",
  shouldSort: false,
  itemSelectText: "",
  allowHTML: false,
  noResultsText: "No purpose found",
  noChoicesText: "No purposes available",
});
}


function initializeStatusFilter() {
  const sel = document.getElementById("statusFilter");

  if (!sel) return;

  new Choices(sel, {
    searchEnabled: false,
    shouldSort: false,
    itemSelectText: "",
    allowHTML: false,
    allowSearch: false,
  });
}

function populatePurposeSelects() {
  [
    document.getElementById("singleModalPurposeSelect"),
    document.getElementById("bulkModalPurposeSelect"),
  ].forEach((sel) => {
    roomPurposes.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p;
      opt.textContent = p;
      sel.appendChild(opt);
    });
  });
}

/* ==========================================================================
   FILTERING
   ========================================================================== */
function filterRooms(list) {
  const { search, purpose, status } = state.filters;
  const q = search.trim().toLowerCase();

  return list.filter((r) => {
    if (q) {
      const hay =
        `${r.roomNumber} ${r.roomName} ${r.purpose || ""}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }

    if (purpose !== "all" && r.purpose !== purpose) return false;

    if (status === "assigned" && !r.hasFacility && !r.purpose) return false;

    if (status === "unassigned" && (r.hasFacility || r.purpose)) return false;

    return true;
  });
}

/* ==========================================================================
   RENDER: FLOORS
   ========================================================================== */
function renderFloors() {
  const container = document.getElementById("floorsContainer");
  container.innerHTML = "";

  floorOrder.forEach((floorName) => {
    const floorRooms = rooms.filter((r) => r.floor === floorName);
    const assignedCount = floorRooms.filter(
      (r) => r.hasFacility || r.purpose,
    ).length;
    const unassignedCount = floorRooms.length - assignedCount;
    const isOpen = state.openFloors.has(floorName);

    const floorEl = document.createElement("div");
    floorEl.className = `raa-floor${isOpen ? " is-open" : ""}`;
    floorEl.dataset.floor = floorName;

    floorEl.innerHTML = `
      <button class="raa-floor-header" data-floor-toggle="${floorName}" aria-expanded="${isOpen}">
        <span class="raa-floor-badge">${floorInitial(floorName)}</span>
        <span class="raa-floor-meta">
          <span class="raa-floor-name">${floorName}</span>
          <span class="raa-floor-sub">
            <span>${floorRooms.length} Rooms</span>
            <span>·</span>
            <span class="raa-dot">${assignedCount} Assigned</span>
            <span>·</span>
            <span class="raa-dot unassigned">${unassignedCount} Unassigned</span>
          </span>
        </span>
        <span class="raa-floor-chevron"><i class="bi bi-chevron-down"></i></span>
      </button>
      <div class="raa-floor-body">
        <div class="raa-floor-body-inner">
          <div class="raa-room-grid" id="grid-${cssSafe(floorName)}"></div>
        </div>
      </div>
    `;
    container.appendChild(floorEl);
    renderRooms(floorName);
  });
}

function floorInitial(name) {
  if (/ground/i.test(name)) return "G";
  const m = name.match(/(\d+)/);
  return m ? m[1] : name.charAt(0);
}
function cssSafe(str) {
  return str.replace(/[^a-z0-9]/gi, "-");
}

/* ==========================================================================
   RENDER: ROOMS (per floor)
   ========================================================================== */
function renderRooms(floorName) {
  const grid = document.getElementById(`grid-${cssSafe(floorName)}`);
  if (!grid) return;

  const floorRooms = rooms.filter((r) => r.floor === floorName);
  const visibleRooms = filterRooms(floorRooms);

  grid.innerHTML = "";

  if (visibleRooms.length === 0) {
    grid.innerHTML = `<div class="raa-empty-floor">No rooms match the current filters on this floor.</div>`;
    return;
  }

  visibleRooms.forEach((room, i) => {
    const card = renderRoomCard(room);
    card.style.animationDelay = `${Math.min(i * 0.035, 0.4)}s`;
    grid.appendChild(card);
  });
}

/* ==========================================================================
   RENDER: SINGLE ROOM CARD
   ========================================================================== */
function renderRoomCard(room) {
  const hasFacility = !!room.facilityAllocated;
  const hasPurpose = !!room.purpose;

  const isAssigned = hasFacility || hasPurpose;

  const card = document.createElement("div");
  card.className = `raa-card ${isAssigned ? "is-assigned" : "is-unassigned"}${state.selected.has(room.id) ? " is-selected" : ""}`;
  card.dataset.roomId = room.id;

  card.innerHTML = `
    <div class="raa-card-top">

      ${
        !hasFacility
          ? `
        <input
          type="checkbox"
          class="raa-check"
          data-room-checkbox="${room.id}"
          ${state.selected.has(room.id) ? "checked" : ""}
          aria-label="Select ${room.roomName}"
        >
      `
          : ""
      }

      <span class="raa-status-pill ${isAssigned ? "assigned" : "unassigned"}">
        <i class="bi bi-circle-fill"></i>${isAssigned ? "ASSIGNED" : "UNASSIGNED"}
      </span>

    </div>

    <div>
      <div class="raa-room-number">RM · ${room.roomNumber}</div>
    </div>

    <div class="raa-purpose-block">

      <div class="raa-purpose-label">
        ${hasFacility ? "Facility" : "Purpose"}
      </div>

      <div class="raa-purpose-value ${isAssigned ? "" : "empty"}">
        ${
          hasFacility
            ? room.facilityName
            : hasPurpose
              ? room.purpose
              : "No purpose assigned"
        }
      </div>

    </div>

    <div class="raa-card-action-row">
      <button class="raa-card-action" data-open-single="${room.id}">
        ${isAssigned ? "Change Purpose" : "Assign Purpose"}
        <i class="bi bi-arrow-right"></i>
      </button>

      ${
        hasPurpose && !hasFacility
          ? `
      <button class="raa-card-empty" data-empty-room="${room.id}" title="Empty Room">
        <i class="bi bi-eraser"></i>Empty Room
      </button>`
          : ""
      }
          </div>
        `;

  return card;
}

/* ==========================================================================
   STATISTICS
   ========================================================================== */
function updateStatistics() {
  const total = rooms.length;
  const assigned = rooms.filter((r) => r.hasFacility || r.purpose).length;
  const unassigned = total - assigned;
  const floors = floorOrder.length;

  animateNumber("statTotal", total);
  animateNumber("statAssigned", assigned);
  animateNumber("statUnassigned", unassigned);
  animateNumber("statFloors", floors);
}

function animateNumber(elId, target) {
  const el = document.getElementById(elId);
  const start = parseInt(el.textContent, 10) || 0;
  if (start === target) {
    el.textContent = target;
    return;
  }
  const duration = 500;
  const startTime = performance.now();
  function tick(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = Math.round(start + (target - start) * eased);
    el.textContent = value;
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function updateFloorCounts() {
  // Counts are recomputed on full re-render; this keeps a dedicated hook
  // per the requested architecture for cases where only counts need a refresh.
  renderFloors();
}

/* ==========================================================================
   SELECTION
   ========================================================================== */
function handleRoomSelection(roomId, checked) {
  if (checked) state.selected.add(roomId);
  else state.selected.delete(roomId);
  refreshSelectionUI();
}

function selectAllRooms() {
  state.selected = new Set(
    rooms.filter((r) => !r.hasFacility).map((r) => r.id),
  );

  refreshSelectionUI(true);
}

function selectUnassignedRooms() {
  filterRooms(rooms)
    .filter((r) => !r.hasFacility && !r.purpose)
    .forEach((r) => state.selected.add(r.id));

  refreshSelectionUI(true);
}

function clearSelection() {
  // 1. Clear selected rooms
  state.selected.clear();

  // 2. Reset all filters
  state.filters.search = "";
  state.filters.purpose = "all";
  state.filters.status = "all";

  // 3. Reset search input
  const searchInput = document.getElementById("searchInput");

  if (searchInput) {
    searchInput.value = "";
  }

  // 4. Reset purpose Choices
  const purposeFilter = document.getElementById("purposeFilter");

  if (purposeFilter) {
    purposeFilter.value = "all";
  }

  // 5. Reset status Choices
  const statusFilter = document.getElementById("statusFilter");

  if (statusFilter) {
    statusFilter.value = "all";
  }

  // 6. Remove selected visual state
  document.querySelectorAll(".raa-card.is-selected").forEach((card) => {
    card.classList.remove("is-selected");
  });

  // 7. Uncheck room checkboxes
  document.querySelectorAll("[data-room-checkbox]").forEach((checkbox) => {
    checkbox.checked = false;
  });

  // 8. Re-render ALL rooms using reset filters
  floorOrder.forEach((floorName) => {
    renderRooms(floorName);
  });

  // 9. Update selection UI
  refreshSelectionUI(false);
}

function refreshSelectionUI(rerenderCards) {
  const count = state.selected.size;
  const bulkBar = document.getElementById("bulkBar");
  bulkBar.classList.toggle("is-visible", count > 0);
  document.getElementById("bulkCount").textContent = count;
  document.getElementById("btnBulkAssignTop").disabled = count === 0;

  if (rerenderCards) {
    // Re-render room grids so checkbox / highlight states reflect selection
    floorOrder.forEach(renderRooms);
  } else {
    document.querySelectorAll(".raa-card").forEach((card) => {
      const id = Number(card.dataset.roomId);
      card.classList.toggle("is-selected", state.selected.has(id));
    });
  }
}

/* ==========================================================================
   MODALS: SINGLE ASSIGN / CHANGE
   ========================================================================== */
function openRoomPurposeModal(roomId) {

  const room = rooms.find((r) => r.id === roomId);

  if (!room) return;

  state.singleModalRoomId = roomId;

  const isAssigned = !!room.purpose;

  document.getElementById("singleModalTitle").textContent =
    isAssigned
      ? "Change Room Purpose"
      : "Assign Room Purpose";

  document.getElementById("singleModalRoom").textContent =
    room.roomNumber;

  document.getElementById("singleModalFloor").textContent =
    room.floor;

  document.getElementById("singleModalPurposeLabel").textContent =
    isAssigned
      ? "New Purpose"
      : "Purpose";

  const currentWrap =
    document.getElementById("singleModalCurrentWrap");

  if (isAssigned) {

    currentWrap.style.display = "block";

    document.getElementById("singleModalCurrent").textContent =
      room.purpose;

  } else {

    currentWrap.style.display = "none";

    document.getElementById("singleModalCurrent").textContent =
      "—";
  }

  // IMPORTANT:
  // Always reset the purpose selector when modal opens
  resetPurposeSelect("singleModalPurposeSelect");

  const saveBtn =
    document.getElementById("singleModalSaveBtn");

  saveBtn.textContent =
    isAssigned
      ? "Update Purpose"
      : "Save Purpose";

  singleModal.show();
}

async function assignRoomPurpose() {

  const select = document.getElementById("singleModalPurposeSelect");
  const purpose = select.value;

  if (!purpose) {
    Swal.fire({
      icon: "warning",
      title: "Select a purpose",
      text: "Please choose a room purpose before saving.",
      confirmButtonColor: "#8A0F22",
    });
    return;
  }

  const room = rooms.find(
    (r) => r.id === state.singleModalRoomId
  );

  if (!room) return;

  const formData = new FormData();

  formData.append("room_ids[]", room.id);
  formData.append("purpose", purpose);

  try {

    const response = await fetch(
      ROOM_PURPOSE_SAVE_URL,
      {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
      }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(
        data.message || "Failed to save room purpose."
      );
    }

    // Update local state only after DB success
    room.purpose = purpose;

    singleModal.hide();

    renderFloors();
    updateStatistics();
    refreshSelectionUI();

    Swal.fire({
      icon: "success",
      title: "Purpose saved",
      text: `${room.roomName} is now set to "${purpose}".`,
      confirmButtonColor: "#8A0F22",
      timer: 2200,
      timerProgressBar: true,
    });

  } catch (error) {

    console.error("Room purpose save error:", error);

    Swal.fire({
      icon: "error",
      title: "Save failed",
      text: error.message || "Unable to save room purpose.",
      confirmButtonColor: "#8A0F22",
    });
  }
}

/* ==========================================================================
   EMPTY ROOM — resets an assigned room back to unassigned
   ========================================================================== */
async function emptyRoom(roomId) {

  const room = rooms.find((r) => r.id === roomId);

  if (!room) return;

  const result = await Swal.fire({
    icon: "warning",
    title: "Empty Room?",
    text: `Remove the purpose assigned to ${room.roomName}?`,
    showCancelButton: true,
    confirmButtonText: "Yes, Empty Room",
    cancelButtonText: "Cancel",
    confirmButtonColor: "#8A0F22",
    reverseButtons: true,
  });

  if (!result.isConfirmed) return;

  const formData = new FormData();

  formData.append("room_id", room.id);

  try {

    const response = await fetch(
      ROOM_PURPOSE_EMPTY_URL,
      {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
      }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(
        data.message || "Failed to empty room."
      );
    }

    // DB success only after this
    room.purpose = null;

    state.selected.delete(room.id);

    renderFloors();
    updateStatistics();
    refreshSelectionUI();

    Swal.fire({
      toast: true,
      position: "top-end",

      icon: "success",
      title: "Room emptied",
      text: `${room.roomName} is now unassigned.`,

      showConfirmButton: false,

      timer: 2200,
      timerProgressBar: true,

      background: "#ffffff",
      color: "#3f302b",

      iconColor: "#198754",

      customClass: {
        popup: "raa-toast"
      }
    });

  } catch (error) {

    console.error("Empty room error:", error);

    Swal.fire({
      toast: true,
      position: "top-end",

      icon: "error",
      title: "Action failed",
      text: error.message || "Unable to empty the room.",

      showConfirmButton: false,

      timer: 3000,
      timerProgressBar: true,

      background: "#ffffff",
      color: "#3f302b",

      iconColor: "#dc3545",

      customClass: {
        popup: "raa-toast"
      }
    });
  }
}

/* ==========================================================================
   MODALS: BULK ASSIGN
   ========================================================================== */
function openBulkAssignModal() {
  const selectedRooms = rooms.filter((r) => state.selected.has(r.id));

  if (selectedRooms.length === 0) return;

  const facilityRoom = selectedRooms.find((r) => r.hasFacility);

  if (facilityRoom) {
    Swal.fire({
      toast: true,
      position: "top-end",
      icon: "info",
      title: `Room already assigned to ${facilityRoom.facilityName}`,
      text: "Please go to Facility Allocation.",
      showConfirmButton: false,
      timer: 3000,
      timerProgressBar: true,
    });

    return;
  }

  const listEl = document.getElementById("bulkModalRoomList");

  listEl.innerHTML = selectedRooms
    .sort((a, b) => a.roomNumber.localeCompare(b.roomNumber))
    .map(
      (r) =>
        `<span class="raa-selected-chip">
        <i class="bi bi-check-circle-fill"></i>
        ${r.roomNumber}
      </span>`,
    )
    .join("");

  resetPurposeSelect("bulkModalPurposeSelect");

  bulkModal.show();
}

async function assignBulkPurpose() {

  const select = document.getElementById(
    "bulkModalPurposeSelect"
  );

  const purpose = select.value;

  if (!purpose) {
    Swal.fire({
      icon: "warning",
      title: "Select a purpose",
      text: "Please choose a purpose to apply to the selected rooms.",
      confirmButtonColor: "#8A0F22",
    });
    return;
  }

  const selectedRooms = rooms.filter(
    (r) => state.selected.has(r.id)
  );

  if (!selectedRooms.length) return;

  const formData = new FormData();

  selectedRooms.forEach((room) => {
    formData.append("room_ids[]", room.id);
  });

  formData.append("purpose", purpose);

  try {

    const response = await fetch(
      ROOM_PURPOSE_SAVE_URL,
      {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
      }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(
        data.message || "Failed to update rooms."
      );
    }

    // Update local state only after DB success
    selectedRooms.forEach((room) => {
      room.purpose = purpose;
    });

    const count = selectedRooms.length;

    bulkModal.hide();

    clearSelection();
    renderFloors();
    updateStatistics();

    Swal.fire({
      icon: "success",
      title: "Rooms updated",
      text: `${count} room${count > 1 ? "s" : ""} assigned to "${purpose}".`,
      confirmButtonColor: "#8A0F22",
      timer: 2400,
      timerProgressBar: true,
    });

  } catch (error) {

    console.error("Bulk room purpose error:", error);

    Swal.fire({
      icon: "error",
      title: "Update failed",
      text: error.message || "Unable to update rooms.",
      confirmButtonColor: "#8A0F22",
    });
  }
}

/* ==========================================================================
   EVENT BINDING (delegated for dynamically rendered content)
   ========================================================================== */
function bindGlobalEvents() {
  // Search & filters
  document.getElementById("searchInput").addEventListener("input", (e) => {
    state.filters.search = e.target.value;
    floorOrder.forEach(renderRooms);
  });
  document.getElementById("purposeFilter").addEventListener("change", (e) => {
    state.filters.purpose = e.target.value;
    floorOrder.forEach(renderRooms);
  });
  document.getElementById("statusFilter").addEventListener("change", (e) => {
    state.filters.status = e.target.value;
    floorOrder.forEach(renderRooms);
  });

  // Global action buttons
  document
    .getElementById("btnSelectAll")
    .addEventListener("click", selectAllRooms);
  document
    .getElementById("btnSelectUnassigned")
    .addEventListener("click", selectUnassignedRooms);
  document
  .getElementById("btnClearSelection")
  .addEventListener("click", (e) => {
    e.preventDefault();
    clearSelection();
  });
  document
    .getElementById("btnBulkAssignTop")
    .addEventListener("click", openBulkAssignModal);

  // Bulk bar
  document
  .getElementById("bulkClearBtn")
  .addEventListener("click", (e) => {
    e.preventDefault();
    clearSelection();
  });
  document
    .getElementById("bulkAssignBtn")
    .addEventListener("click", openBulkAssignModal);

  // Modal save buttons
  document
    .getElementById("singleModalSaveBtn")
    .addEventListener("click", assignRoomPurpose);
  document
    .getElementById("bulkModalSaveBtn")
    .addEventListener("click", assignBulkPurpose);

  // Delegated: floor toggle, checkbox, card action
  document.getElementById("floorsContainer").addEventListener("click", (e) => {
    const toggleBtn = e.target.closest("[data-floor-toggle]");
    if (toggleBtn) {
      const floorName = toggleBtn.dataset.floorToggle;
      if (state.openFloors.has(floorName)) state.openFloors.delete(floorName);
      else state.openFloors.add(floorName);
      const floorEl = toggleBtn.closest(".raa-floor");
      floorEl.classList.toggle("is-open");
      toggleBtn.setAttribute(
        "aria-expanded",
        floorEl.classList.contains("is-open"),
      );
      return;
    }

    const actionBtn = e.target.closest("[data-open-single]");

    if (actionBtn) {
      const roomId = Number(actionBtn.dataset.openSingle);
      const room = rooms.find((r) => r.id === roomId);

      if (!room) return;

      if (room.hasFacility) {
        Swal.fire({
          toast: true,
          position: "top-end",
          icon: "info",
          title: `Room already assigned to ${room.facilityName}`,
          text: "Please go to Facility Allocation.",
          showConfirmButton: false,
          timer: 3000,
          timerProgressBar: true,
        });

        return;
      }

      openRoomPurposeModal(roomId);
      return;
    }

    const emptyBtn = e.target.closest("[data-empty-room]");
    if (emptyBtn) {
      emptyRoom(Number(emptyBtn.dataset.emptyRoom));
      return;
    }
  });

  document.getElementById("floorsContainer").addEventListener("change", (e) => {
    const checkbox = e.target.closest("[data-room-checkbox]");
    if (checkbox) {
      handleRoomSelection(
        Number(checkbox.dataset.roomCheckbox),
        checkbox.checked,
      );
    }
  });
}

init();

function getCookie(name) {
  let cookieValue = null;

  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");

    for (let cookie of cookies) {
      cookie = cookie.trim();

      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));

        break;
      }
    }
  }

  return cookieValue;
}
(function () {
  "use strict";

  /* ---------------- MOCK DATA ---------------- */

  /* ---------------- STATE ---------------- */
  var afmState = {
    facility: null,
    floorId: null,
    roomId: null,

    editingAllocationId: null,
    editingRoomId: null,
    editingFloorId: null,
    editingRoomNumber: null,
    editingRoomName: null,
  };
  var afmLastFocused = null;
  var afmModalInstance = null;

  /* ---------------- ELEMENTS ---------------- */
  var afmFacilityGrid = document.getElementById("afmFacilityGrid");
  var afmModalEl = document.getElementById("afmModal");
  var afmModalBody = document.getElementById("afmModalBody");
  var afmMainView = document.getElementById("afmMainView");
  var afmSuccessView = document.getElementById("afmSuccessView");

  var afmSelFacIcon = document.getElementById("afmSelFacIcon");
  var afmSelFacName = document.getElementById("afmSelFacName");
  var afmHeaderIcon = document.getElementById("afmHeaderIcon");
  var afmSumFacility = document.getElementById("afmSumFacility");

  var afmFloorSelect = document.getElementById("afmFloorSelect");
  var afmFloorTrigger = document.getElementById("afmFloorTrigger");
  var afmFloorTriggerLabel = document.getElementById("afmFloorTriggerLabel");
  var afmFloorPanel = document.getElementById("afmFloorPanel");

  var afmRoomContent = document.getElementById("afmRoomContent");
  var afmLocationPreview = document.getElementById("afmLocationPreview");
  var afmSummaryCard = document.getElementById("afmSummaryCard");

  var afmAllocateBtn = document.getElementById("afmAllocateBtn");
  var afmCancelBtn = document.getElementById("afmCancelBtn");
  var afmDoneBtn = document.getElementById("afmDoneBtn");

  var afmLpFloorIcon = document.getElementById("afmLpFloorIcon");
  var afmLpFloorName = document.getElementById("afmLpFloorName");
  var afmLpRoomName = document.getElementById("afmLpRoomName");
  var afmLpRoomSub = document.getElementById("afmLpRoomSub");
  var afmSumChain = document.getElementById("afmSumChain");
  var afmSuccessFacility = document.getElementById("afmSuccessFacility");
  var afmSuccessChain = document.getElementById("afmSuccessChain");

  /* ---------------- INITIALIZE MODAL ---------------- */
  function initModal() {
    if (typeof bootstrap !== "undefined" && bootstrap.Modal) {
      afmModalInstance = new bootstrap.Modal(afmModalEl, {
        backdrop: true,
        keyboard: true,
        focus: true,
      });
    } else {
      // Fallback: manual show/hide
      afmModalInstance = {
        show: function () {
          afmModalEl.style.display = "block";
          afmModalEl.classList.add("show");
          document.body.classList.add("modal-open");
          var backdrop = document.createElement("div");
          backdrop.className = "modal-backdrop fade show";
          document.body.appendChild(backdrop);
        },
        hide: function () {
          afmModalEl.style.display = "none";
          afmModalEl.classList.remove("show");
          document.body.classList.remove("modal-open");
          var backdrops = document.querySelectorAll(".modal-backdrop");
          backdrops.forEach(function (el) {
            el.remove();
          });
        },
      };
    }
  }

  // Initialize after DOM is ready and Bootstrap is loaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initModal);
  } else {
    initModal();
  }

  /* ---------------- RENDER FLOOR OPTIONS ---------------- */
  afmFloorPanel.innerHTML = AFM_FLOORS.map(function (fl) {
    return `
        <div
            class="afm-select-option"
            data-floor="${fl.id}"
            role="option"
            tabindex="0"
        >
            <span class="afm-oicon">🪜</span>

            <span class="afm-otext">
                <div class="afm-oname">
                    ${fl.name}
                </div>

                <div class="afm-onum">
                    Level ${fl.number}
                </div>
            </span>

            <svg
                class="afm-ocheck"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="3"
                stroke-linecap="round"
                stroke-linejoin="round"
            >
                <path d="M20 6 9 17l-5-5"/>
            </svg>
        </div>
    `;
  }).join("");

  /* ---------------- OPEN MODAL ---------------- */
  function afmOpenModal(facility, triggerEl) {
    afmLastFocused = triggerEl || document.activeElement;

    afmState = {
      facility: facility,
      floorId: null,
      roomId: null,
    };

    // Facility name
    afmSelFacName.textContent = facility.name;

    // Facility icon
    afmSelFacIcon.innerHTML = `<i class="${facility.icon}"></i>`;

    // Header icon
    afmHeaderIcon.innerHTML = `<i class="${facility.icon}"></i>`;

    // Summary
    afmSumFacility.textContent = facility.name;

    afmResetFloorUI();
    afmRenderRoomPlaceholder();
    afmUpdateLocationPreview();
    afmUpdateAllocateState();

    afmMainView.style.display = "flex";
    afmSuccessView.classList.remove("afm-show");

    if (afmModalInstance) {
      afmModalInstance.show();
    }

    setTimeout(function () {
      const closeBtn = afmModalEl.querySelector(".btn-close");

      if (closeBtn) {
        closeBtn.focus();
      }
    }, 300);
  }

  /* ---------------- EDIT ALLOCATION ---------------- */

  var allocationEditBtn = document.getElementById("allocationEditBtn");

  allocationEditBtn.addEventListener("click", function () {
    const allocationId = this.dataset.allocationId;
    const roomId = this.dataset.roomId;

    const card = document.querySelector(
      `.smh-facility-card[data-allocation-id="${allocationId}"]`,
    );

    if (!card) {
      console.error("Allocation card not found.");
      return;
    }

    const facility = {
      id: card.dataset.facilityId,
      name: card.querySelector(".smh-fn")?.textContent.trim(),
      icon: card.querySelector(".smh-fi i")?.className || "bi bi-hospital",
      type: card.dataset.facilityType,
    };

    // Close allocation details modal
    allocationDetailsModal.hide();

    // Open existing allocation modal
    afmOpenModal(facility, card);

    // Set edit state AFTER afmOpenModal()
    // because afmOpenModal resets afmState
    afmState.editingAllocationId = allocationId;

    afmAllocateBtn.querySelector(".afm-btn-label").textContent =
      "Update Allocation";
    afmState.editingRoomId = roomId;

    afmState.editingFloorId = card.dataset.allocationFloorId;

    afmState.editingRoomNumber = card.dataset.allocationRoomNumber;

    afmState.editingRoomName = card.dataset.allocationRoomName;

    // Automatically select current floor
    afmSelectFloor(afmState.editingFloorId);
  });

  /* ---------------- CLOSE MODAL ---------------- */
  function afmCloseModal() {
    if (afmModalInstance) {
      afmModalInstance.hide();
    }
    if (afmLastFocused) {
      setTimeout(function () {
        afmLastFocused.focus();
      }, 200);
    }
  }

  /* ---------------- FLOOR DROPDOWN ---------------- */
  function afmResetFloorUI() {
    afmFloorTriggerLabel.textContent = "Choose a floor";
    afmFloorTriggerLabel.classList.add("afm-placeholder");
    var opts = afmFloorPanel.querySelectorAll(".afm-select-option");
    opts.forEach(function (o) {
      o.classList.remove("afm-selected");
    });
    afmCloseFloorPanel();
  }

  function afmOpenFloorPanel() {
    afmFloorSelect.classList.add("afm-open");
    afmFloorTrigger.setAttribute("aria-expanded", "true");
  }

  function afmCloseFloorPanel() {
    afmFloorSelect.classList.remove("afm-open");
    afmFloorTrigger.setAttribute("aria-expanded", "false");
  }

  afmFloorTrigger.addEventListener("click", function (e) {
    e.stopPropagation();
    if (afmFloorSelect.classList.contains("afm-open")) {
      afmCloseFloorPanel();
    } else {
      afmOpenFloorPanel();
    }
  });

  document.addEventListener("click", function (e) {
    if (!afmFloorSelect.contains(e.target)) afmCloseFloorPanel();
  });

  afmFloorPanel.addEventListener("click", function (e) {
    var opt = e.target.closest(".afm-select-option");
    if (!opt) return;
    afmSelectFloor(opt.dataset.floor);
  });

  afmFloorPanel.addEventListener("keydown", function (e) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      var opt = e.target.closest(".afm-select-option");
      if (opt) afmSelectFloor(opt.dataset.floor);
    }
  });

  function afmSelectFloor(floorId) {

    afmCloseFloorPanel();

    afmState.floorId = floorId;

    const floor = AFM_FLOORS.find(function (f) {
        return String(f.id) === String(floorId);
    });

    if (!floor) return;

    // -----------------------------------------
    // UPDATE SELECTED FLOOR UI
    // -----------------------------------------

    afmFloorTriggerLabel.textContent = floor.name;
    afmFloorTriggerLabel.classList.remove("afm-placeholder");

    afmFloorPanel
        .querySelectorAll(".afm-select-option")
        .forEach(function (option) {
            option.classList.toggle(
                "afm-selected",
                String(option.dataset.floor) === String(floorId)
            );
        });


    // -----------------------------------------
    // GET ALREADY ALLOCATED ROOMS
    // -----------------------------------------

    const allocatedRoomIds = new Set(
        Array.from(
            document.querySelectorAll(
                '.smh-facility-card[data-allocated="true"]'
            )
        )
        .filter(function (card) {

            // EDIT MODE:
            // current facility allocation-a exclude pannunga
            if (afmState.editingAllocationId) {
                return (
                    String(card.dataset.allocationId) !==
                    String(afmState.editingAllocationId)
                );
            }

            return true;
        })
        .map(function (card) {
            return String(card.dataset.allocationRoomId);
        })
    );


    // -----------------------------------------
    // SHOW ONLY AVAILABLE ROOMS
    // -----------------------------------------

    let rooms = floor.rooms.filter(function (room) {
        return !allocatedRoomIds.has(String(room.id));
    });


    // -----------------------------------------
    // EDIT MODE
    // CURRENT ROOM ONLY
    // -----------------------------------------

    if (
        afmState.editingAllocationId &&
        afmState.editingRoomId &&
        String(floor.id) === String(afmState.editingFloorId)
    ) {

        const currentRoomExists = rooms.some(function (room) {
            return String(room.id) === String(afmState.editingRoomId);
        });

        if (!currentRoomExists) {

            rooms.unshift({
                id: afmState.editingRoomId,
                num: afmState.editingRoomNumber,
                name: afmState.editingRoomName,
                type: "",
                status: "ALLOCATED"
            });
        }
    }


    // -----------------------------------------
    // RENDER
    // -----------------------------------------

    const renderFloor = {
        ...floor,
        rooms: rooms
    };

    afmRenderRooms(renderFloor);


    // -----------------------------------------
    // AUTO SELECT CURRENT ROOM IN EDIT
    // -----------------------------------------

    if (
        afmState.editingAllocationId &&
        afmState.editingRoomId &&
        String(floor.id) === String(afmState.editingFloorId)
    ) {

        afmState.roomId = afmState.editingRoomId;

        const currentRoomCard =
            afmRoomContent.querySelector(
                `.afm-room-card[data-room="${afmState.editingRoomId}"]`
            );

        if (currentRoomCard) {
            currentRoomCard.classList.add("afm-selected");
        }

        afmUpdateLocationPreview();
        afmUpdateAllocateState();
    }
}

  /* ---------------- ROOM SECTION ---------------- */
  function afmRenderRoomPlaceholder() {
    afmRoomContent.innerHTML =
      '<div class="afm-room-placeholder">' +
      '<div class="afm-picon">🚪</div>' +
      "<p>Select a floor to view available rooms</p>" +
      "</div>";
  }

  function afmRenderRooms(floor) {
    if (!floor.rooms.length) {
      afmRoomContent.innerHTML =
        '<div class="afm-room-empty">' +
        '<div class="afm-eicon">🚪</div>' +
        "<h4>No Rooms Available</h4>" +
        "<p>There are currently no rooms configured on this floor.</p>" +
        "</div>";
      return;
    }

    var html = '<div class="afm-room-grid">';
    floor.rooms.forEach(function (r, i) {
      html +=
        '<button type="button" class="afm-room-card" data-room="' +
        r.id +
        '" style="animation-delay:' +
        i * 55 +
        'ms">' +
        '<span class="afm-ricon">🚪</span>' +
        '<span class="afm-rtext">' +
        '<div class="afm-rnum">' +
        r.num +
        "</div>" +
        '<div class="afm-rname">' +
        r.name +
        "</div>" +
        "</span>" +
        '<span class="afm-rcheck">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>' +
        "</span>" +
        "</button>";
    });
    html += "</div>";
    afmRoomContent.innerHTML = html;

    var cards = afmRoomContent.querySelectorAll(".afm-room-card");
    cards.forEach(function (card) {
      card.addEventListener("click", function () {
        afmSelectRoom(this.dataset.room);
      });
    });
  }

  function afmSelectRoom(roomId) {
    afmState.roomId = roomId;
    var cards = afmRoomContent.querySelectorAll(".afm-room-card");
    cards.forEach(function (c) {
      c.classList.toggle("afm-selected", c.dataset.room === roomId);
    });
    afmUpdateLocationPreview();
    afmUpdateAllocateState();

    setTimeout(function () {
      afmModalBody.scrollTo({
        top: afmModalBody.scrollHeight,
        behavior: "smooth",
      });
    }, 260);
  }

  /* ---------------- LOCATION PREVIEW + SUMMARY ---------------- */
  function afmUpdateLocationPreview() {
    var floor = AFM_FLOORS.find(function (f) {
      return f.id === afmState.floorId;
    });

    var room = floor
        ? floor.rooms.find(function (r) {
            return String(r.id) === String(afmState.roomId);
        })
        : null;

    if (!room && afmState.editingAllocationId) {
        room = {
            num: afmState.editingRoomNumber,
            name: afmState.editingRoomName
        };
    }

    if (floor && room) {
      afmLpFloorIcon.textContent = floor.icon;
      afmLpFloorName.textContent = floor.name;
      afmLpRoomName.textContent = "Room " + room.num;
      afmLpRoomSub.textContent = room.name;
      afmSumChain.textContent = "→ " + floor.name + " → Room " + room.num;

      afmLocationPreview.classList.add("afm-show");
      afmSummaryCard.classList.add("afm-show");
    } else {
      afmLocationPreview.classList.remove("afm-show");
      afmSummaryCard.classList.remove("afm-show");
    }
  }

  function afmUpdateAllocateState() {
    afmAllocateBtn.disabled = !(afmState.floorId && afmState.roomId);
  }

  /* ---------------- ALLOCATE + SUCCESS ---------------- */
  afmAllocateBtn.addEventListener("click", async function () {
    if (this.disabled) return;

    const facilityId = afmState.facility.id;
    const roomId = afmState.roomId;

    const oldRoomId = afmState.editingRoomId;
    const oldRoomNumber = afmState.editingRoomNumber;
    const oldRoomName = afmState.editingRoomName;

    if (!facilityId || !roomId) {
      return;
    }

    this.classList.add("afm-loading");
    this.disabled = true;

    try {
      const response = await fetch(facilityAllocationUrl, {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },

        body: JSON.stringify({
          facility_id: facilityId,
          room_id: roomId,
          allocation_id: afmState.editingAllocationId || null,
        }),
      });

      const data = await response.json();

      console.log("Allocation response:", data);

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Allocation failed.");
      }

      // EDIT MODE → release old room
        if (
            afmState.editingAllocationId &&
            oldRoomId &&
            String(oldRoomId) !== String(roomId)
        ) {
            const oldFloor = AFM_FLOORS.find(function (floor) {
                return String(floor.id) === String(afmState.editingFloorId);
            });

            if (oldFloor) {
                const exists = oldFloor.rooms.some(function (room) {
                    return String(room.id) === String(oldRoomId);
                });

                if (!exists) {
                    oldFloor.rooms.push({
                        id: oldRoomId,
                        num: oldRoomNumber,
                        name: oldRoomName,
                        type: "",
                        status: "AVAILABLE"
                    });
                }
            }
        }

      // Update current card immediately
      if (afmLastFocused) {
        const card = afmLastFocused.closest(".smh-facility-card");

        if (card) {
          card.dataset.allocated = "true";

          card.dataset.allocationId = data.allocation_id;

          card.dataset.allocationRoomId = afmState.roomId;

          const selectedRoom = document.querySelector(
            `.afm-room-card[data-room="${afmState.roomId}"]`,
          );

          if (selectedRoom) {
            card.dataset.allocationRoomNumber =
              selectedRoom.querySelector(".afm-rnum")?.textContent.trim() || "";

            card.dataset.allocationRoomName =
              selectedRoom.querySelector(".afm-rname")?.textContent.trim() ||
              "";
          }

          const floor = AFM_FLOORS.find(function (f) {
            return String(f.id) === String(afmState.floorId);
          });

          if (floor) {
            card.dataset.allocationFloorId = floor.id;
            card.dataset.allocationFloorName = floor.name;
          }

          card.dataset.allocationBuildingName =
            document.querySelector(".afm-lp-name")?.textContent.trim() || "";
        }
      }

      afmShowSuccess();
    } catch (error) {
      console.error("Allocation error:", error);

      alert(error.message);

      this.disabled = false;
    } finally {
      this.classList.remove("afm-loading");
    }
  });

    function afmShowSuccess() {

        var floor = AFM_FLOORS.find(function (f) {
            return String(f.id) === String(afmState.floorId);
        });

        if (!floor) return;

        var room = floor.rooms.find(function (r) {
            return String(r.id) === String(afmState.roomId);
        });

        // EDIT MODE:
        // Current allocated room is temporarily rendered,
        // so it may not exist inside AFM_FLOORS.
        if (!room && afmState.editingAllocationId) {
            room = {
                num: afmState.editingRoomNumber,
                name: afmState.editingRoomName
            };
        }

        if (!room) return;

        afmSuccessFacility.textContent =
            afmState.facility.name;

        afmSuccessChain.textContent =
            "→ " +
            floor.name +
            " → Room " +
            room.num;

        
        // Hide footer buttons
        afmCancelBtn.style.display = "none";
        afmAllocateBtn.style.display = "none";

        afmMainView.style.display = "none";

        afmSuccessView.classList.add("afm-show");

        setTimeout(function () {
            afmDoneBtn.focus();
        }, 200);
    }

  /* ---------------- CLOSE HANDLERS ---------------- */
  afmCancelBtn.addEventListener("click", afmCloseModal);
  afmDoneBtn.addEventListener("click", afmCloseModal);

  afmModalEl.addEventListener("hidden.bs.modal", function () {
    afmSuccessView.classList.remove("afm-show");
    afmMainView.style.display = "flex";
    afmAllocateBtn.classList.remove("afm-loading");
    afmAllocateBtn.disabled = true;
    afmResetFloorUI();
    afmRenderRoomPlaceholder();
    afmUpdateLocationPreview();
    afmUpdateAllocateState();
  });

  /* ---------------- CLICK ON STATIC FACILITY CARDS ---------------- */

  document.addEventListener("click", function (e) {
    const card = e.target.closest(".smh-facility-card");

    if (!card) return;

    // Edit button click
    if (e.target.closest(".edit-facility-btn")) {
      return;
    }

    const iconElement = card.querySelector(".smh-fi i");

    const facility = {
      id: card.dataset.facilityId,
      name: card.querySelector(".smh-fn")?.textContent.trim(),
      icon: iconElement ? iconElement.className : "bi bi-hospital",
      type: card.dataset.facilityType,
    };

    const buildingId = card.dataset.buildingId;

    // Check allocation
    const isAllocated = card.dataset.allocated === "true";

    if (isAllocated) {
      afmOpenAllocationDetails(card, facility);
    } else {
      afmOpenModal(facility, card, buildingId);
    }
  });

  function afmOpenAllocationDetails(card, facility) {
    const roomNumber = card.dataset.allocationRoomNumber || "—";

    const roomName = card.dataset.allocationRoomName || "";

    const floorName = card.dataset.allocationFloorName || "—";

    const buildingName = card.dataset.allocationBuildingName || "—";

    // Facility
    allocationDetailFacility.textContent = facility.name;

    // Icon
    allocationDetailIcon.innerHTML = `<i class="${facility.icon}"></i>`;

    // Location
    allocationDetailBuilding.textContent = buildingName;

    allocationDetailFloor.textContent = floorName;

    allocationDetailRoom.textContent = roomNumber;

    allocationDetailRoomName.textContent = roomName;

    // Keep current card for edit
    allocationEditBtn.dataset.facilityId = facility.id;

    allocationEditBtn.dataset.allocationId = card.dataset.allocationId;

    allocationEditBtn.dataset.roomId = card.dataset.allocationRoomId;

    allocationDetailsModal.show();
  }

  /* ---------------- KEYBOARD: ESC closes floor dropdown ---------------- */
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      if (afmFloorSelect.classList.contains("afm-open")) {
        afmCloseFloorPanel();
        e.preventDefault();
        e.stopPropagation();
      }
    }
  });

  /* ---------------- PREVENT modal close on floor panel clicks ---------------- */
  afmFloorPanel.addEventListener("mousedown", function (e) {
    e.stopPropagation();
  });
})();

// ALLOCATED ROOM FUNCTIONS

// ── Dynamic Sparkle Particles ──
document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("allocationDetailsModal");
  const sparkleContainer = modal.querySelector(".sparkle-container");

  const createSparkles = () => {
    sparkleContainer.innerHTML = "";
    const count = 18;
    for (let i = 0; i < count; i++) {
      const sparkle = document.createElement("span");
      const size = Math.random() * 5 + 2;
      sparkle.style.cssText = `
                        position: absolute;
                        width: ${size}px;
                        height: ${size}px;
                        background: ${
                          Math.random() > 0.5
                            ? "rgba(220,180,140,0.7)"
                            : "rgba(255,200,200,0.6)"
                        };
                        border-radius: 50%;
                        top: ${Math.random() * 85}%;
                        left: ${Math.random() * 88}%;
                        pointer-events: none;
                        animation: sparkleFloat ${Math.random() * 3 + 2.5}s ease-in-out infinite;
                        animation-delay: ${Math.random() * 3}s;
                        box-shadow: 0 0 ${size + 2}px rgba(220,160,140,0.5);
                    `;
      sparkleContainer.appendChild(sparkle);
    }
  };

  const styleSheet = document.createElement("style");
  styleSheet.textContent = `
                @keyframes sparkleFloat {
                    0%, 100% { transform: translateY(0) scale(1); opacity: 0.3; }
                    30% { transform: translateY(-12px) scale(1.6); opacity: 0.9; }
                    60% { transform: translateY(-4px) scale(1); opacity: 0.5; }
                }
            `;
  document.head.appendChild(styleSheet);

  modal.addEventListener("show.bs.modal", () => {
    createSparkles();
  });

  createSparkles();
});

const allocationDetailsModalEl = document.getElementById(
  "allocationDetailsModal",
);

const allocationDetailFacility = document.getElementById(
  "allocationDetailFacility",
);

const allocationDetailIcon = document.getElementById("allocationDetailIcon");

const allocationDetailBuilding = document.getElementById(
  "allocationDetailBuilding",
);

const allocationDetailFloor = document.getElementById("allocationDetailFloor");

const allocationDetailRoom = document.getElementById("allocationDetailRoom");

const allocationDetailRoomName = document.getElementById(
  "allocationDetailRoomName",
);

const allocationEditBtn = document.getElementById("allocationEditBtn");

const allocationDetailsModal = new bootstrap.Modal(allocationDetailsModalEl);

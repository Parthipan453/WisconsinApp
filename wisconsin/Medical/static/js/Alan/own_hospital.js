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

document.addEventListener("DOMContentLoaded", function () {
  // ---------- DATA ----------

window.maintenanceData = JSON.parse(
    document.getElementById("maintenance-data").textContent
);
  const emergencyFacilities = [
    ["ICU", "bi-heart-pulse-fill", "avail", "6 beds free"],
    ["NICU", "bi-emoji-smile", "avail", "3 beds free"],
    ["PICU", "bi-person-hearts", "limited", "1 bed free"],
    ["Ventilator", "bi-wind", "avail", "9 units ready"],
    ["Ambulance", "bi-truck-front-fill", "avail", "4 on standby"],
    ["Blood Bank", "bi-droplet-fill", "avail", "All groups stocked"],
  ];
  const galleryCategories = [
    "All",
    "Banner",
    "Building",
    "Reception",
    "Waiting Area",
    "Rooms",
    "Emergency Ward",
    "Operation Theatre",
    "Laboratory",
    "MRI Room",
    "CT Scan Room",
    "Parking",
  ];
  const galleryImages = [
    ["Building", "Front facade at dusk", "1587351021355-a479a299d2f9"],
    ["Reception", "Main reception desk", "1666214280557-f1b5022eb634"],
    ["Waiting Area", "Family waiting lounge", "1519494026892-80bbd2d6fd0d"],
    ["Rooms", "Deluxe private room", "1586773860418-d37222d8fce3"],
    ["Emergency Ward", "24x7 emergency bay", "1512678080530-7760d81faba6"],
    ["Operation Theatre", "OT Suite 3", "1551076805-e1869033e561"],
    ["Laboratory", "Central diagnostic lab", "1579154204601-01588f351e67"],
    ["MRI Room", "MRI Suite", "1516549655169-df83a0774514"],
    ["CT Scan Room", "CT imaging suite", "1584982751601-97dcc096659c"],
    ["Parking", "Visitor parking bay", "1470224114660-3f6686c562eb"],
    ["Banner", "Hospital campus banner", "1519494140681-8b17d830a3e9"],
    ["Building", "Aerial hospital view", "1551190822-a9333d879b1f"],
  ];
  const activities = [
    {
      t: "Maintenance Completed",
      d: "Generator Backup annual servicing marked completed",
      when: "18 min ago",
      icon: "bi-check-circle-fill",
      color: "linear-gradient(135deg,#22c55e,#86efac)",
    },
    {
      t: "Maintenance Created",
      d: "Emergency ticket raised for Block C elevator fault",
      when: "2 hr ago",
      icon: "bi-exclamation-triangle-fill",
      color: "linear-gradient(135deg,#dc2626,#f97316)",
    },
    {
      t: "Gallery Updated",
      d: "6 new photos uploaded to Operation Theatre category",
      when: "5 hr ago",
      icon: "bi-images",
      color: "linear-gradient(135deg,var(--smh-violet),#c084fc)",
    },
    {
      t: "Medical Facility Added",
      d: "DEXA Scan facility added to hospital profile",
      when: "Yesterday",
      icon: "bi-plus-circle-fill",
      color: "linear-gradient(135deg,var(--smh-rose-600),var(--smh-coral))",
    },
    {
      t: "Other Facility Removed",
      d: "Old cafeteria vendor kiosk entry removed",
      when: "2 days ago",
      icon: "bi-dash-circle-fill",
      color: "linear-gradient(135deg,#94a3b8,#cbd5e1)",
    },
    {
      t: "Hospital Updated",
      d: "Working hours revised for Saturday OPD",
      when: "3 days ago",
      icon: "bi-pencil-fill",
      color: "linear-gradient(135deg,var(--smh-sky),#7cc8ff)",
    },
    {
      t: "Medical Facility Added",
      d: "TMT diagnostic facility marked available",
      when: "4 days ago",
      icon: "bi-plus-circle-fill",
      color: "linear-gradient(135deg,var(--smh-teal),#34d1c8)",
    },
  ];

  /* ---------- RENDER: maintenance ---------- */
  const maintGrid = document.getElementById("smh-maintGrid");
  function renderMaint(filter = "all") {
    maintGrid.innerHTML = "";
    const list = window.maintenanceData.filter(
      (m) => filter === "all" || m.status === filter,
    );
    if (list.length === 0) {
      maintGrid.innerHTML = `<div class="smh-gcard smh-empty-state" style="grid-column:1/-1;">
                <div class="smh-ei"><i class="bi bi-tools"></i></div>
                <h3>No maintenance in this category</h3>
                <p>
                    There are currently no maintenance requests for this hospital.
                    All facilities are operating normally.
                </p>
            </div>`;
      return;
    }
    list.forEach((m) => {
      const priorityClass = m.priority;
      const el = document.createElement("div");
      el.className = "smh-gcard smh-maint-card " + m.status;
      el.innerHTML = `
                <div class="smh-mc-top">
                    <div class="smh-mc-id"><div class="smh-mc-icon"><i class="bi ${m.icon}"></i></div><div><div class="smh-mc-name">${m.name}</div></div></div>
                    <div class="smh-mc-priority smh-${priorityClass}">${m.priority}</div>
                </div>
                <div class="smh-mc-status smh-${m.status}"><i class="bi bi-circle-fill" style="font-size:6px;"></i> ${m.status.charAt(0).toUpperCase() + m.status.slice(1)}</div>
                <div class="smh-mc-grid">
                    <div><div class="smh-l">Start Date</div><div class="smh-v">${m.start}</div></div>
                    <div><div class="smh-l">Expected Completion</div><div class="smh-v">${m.eta}</div></div>
                    <div style="grid-column:span 2"><div class="smh-l">Assigned Engineer</div><div class="smh-v">${m.eng}</div></div>
                </div>
                <div class="smh-mc-remarks"><i class="bi bi-chat-left-text"></i> ${m.description}</div>
                <div class="smh-mc-actions">

                  <button
                      class="smh-btn smh-btn-soft smh-btn-sm view-maintenance-btn"
                      data-maintenance-id="${m.id}">
                      <i class="bi bi-eye"></i> View
                  </button>

                  ${m.status !== "completed" ? `
                      <button
                          class="smh-btn smh-btn-soft smh-btn-sm edit-maintenance-btn"
                          data-maintenance-id="${m.id}">
                          <i class="bi bi-pencil"></i> Edit
                      </button>

                      <button
                          class="smh-btn smh-btn-outline smh-btn-sm complete-maintenance-btn"
                          data-maintenance-id="${m.id}">
                          <i class="bi bi-check2"></i> Mark Completed
                      </button>
                  ` : ""}

                  

                </div>`;
      maintGrid.appendChild(el);
    });
  }

  window.renderMaint = renderMaint;
  
  renderMaint();
  document.querySelectorAll(".smh-mtab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document
        .querySelectorAll(".smh-mtab")
        .forEach((t) => t.classList.remove("smh-active"));
      tab.classList.add("smh-active");
      renderMaint(tab.dataset.smhFilter);
    });
  });


  /* ---------- Animated Counters ---------- */
  const counters = document.querySelectorAll(".smh-sv[data-smh-count]");
  const counterObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const rawValue = el.dataset.smhCount;

            // Empty / null / undefined / invalid value
            if (
                rawValue === "" ||
                rawValue === "null" ||
                rawValue === "None" ||
                rawValue === "undefined" ||
                isNaN(Number(rawValue))
            ) {
                el.textContent = "-";
                counterObserver.unobserve(el);
                return;
            }

            const target = Number(rawValue);
            let cur = 0;

            const step = Math.max(1, Math.ceil(target / 40));

            const timer = setInterval(() => {
                cur += step;

                if (cur >= target) {
                    cur = target;
                    clearInterval(timer);
                }

                el.textContent = cur;
            }, 25);
          counterObserver.unobserve(el);
        }
      });
    },
    { threshold: 0.4 },
  );
  counters.forEach((c) => counterObserver.observe(c));

  /* ---------- Reveal on scroll ---------- */
/* ---------- Reveal on scroll ---------- */

const revealObserver = new IntersectionObserver(
    (entries) => {

        entries.forEach((entry, i) => {

            if (entry.isIntersecting) {

                setTimeout(() => {

                    entry.target.classList.add("smh-show");

                }, i * 40);

                revealObserver.unobserve(entry.target);
            }

        });

    },
    {
        threshold: 0.15
    }
);


function observeRevealElements(container = document) {

    container
        .querySelectorAll(".smh-reveal")
        .forEach((element) => {

            revealObserver.observe(element);

        });

}


// IMPORTANT: observe elements already present on page load
observeRevealElements();

  /* ---------- Quick-jump active chip on scroll ---------- */
  const chips = document.querySelectorAll(".smh-chip[data-smh-target]");
  chips.forEach((chip) => {
    chip.addEventListener("click", (e) => {
      e.preventDefault();
      document
        .querySelector(chip.dataset.smhTarget)
        .scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  const sections = [...chips]
    .map((c) => document.querySelector(c.dataset.smhTarget))
    .filter(Boolean);
  const navObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = "#" + entry.target.id;
          chips.forEach((c) =>
            c.classList.toggle("smh-active", c.dataset.smhTarget === id),
          );
        }
      });
    },
    { rootMargin: "-40% 0px -50% 0px" },
  );
  sections.forEach((s) => navObserver.observe(s));



  const hero = document.querySelector(".smh-hero");
  const quickNav = document.querySelector(".smh-quicknav");
});

// VIEW MAINTENANCE

document.addEventListener("click", function (e) {

    const btn = e.target.closest(".view-maintenance-btn");

    if (!btn) return;

    const maintenanceId = btn.dataset.maintenanceId;

    const url = maintenanceDetailUrl.replace(
        "0",
        maintenanceId
    );
    fetch(url, {
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    })
    .then(response => response.json())
    .then(data => {

        const m = data.maintenance;

        document.getElementById("viewFacility").textContent = m.facility;
        document.getElementById("viewTitle").textContent = m.title;
        document.getElementById("viewStart").textContent = m.start_date;
        document.getElementById("viewETA").textContent = m.expected_completion;
        document.getElementById("viewEngineer").textContent = m.engineer;
        document.getElementById("viewContact").textContent = m.contact;
        document.getElementById("viewDescription").textContent = m.description;
        document.getElementById("viewRemarks").textContent = m.remarks;

        // status badge

        const status = document.getElementById("viewStatus");

                status.textContent =
                    m.status.charAt(0).toUpperCase() + m.status.slice(1);

                status.className = "smh-status-badge status-" + m.status;

                // priority badge

                const priority = document.getElementById("viewPriority");

        priority.textContent =
            m.priority.charAt(0).toUpperCase() + m.priority.slice(1);

        priority.className =
            "smh-priority-badge priority-" + m.priority;

        // open modal

        const modal = new bootstrap.Modal(
            document.getElementById("viewMaintenanceModal")
        );

        modal.show();

    })
    .catch(error => {

        console.error(error);

    });

});



// EDIT MAINTENANCE

document.addEventListener("click", function (e) {

    const btn = e.target.closest(".edit-maintenance-btn");
    if (!btn) return;

    const maintenanceId = btn.dataset.maintenanceId;

    const url = maintenanceDetailUrl.replace("0", maintenanceId);

    fetch(url, {
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    })
    .then(response => response.json())
    .then(data => {

        if (!data.success) return;

        const m = data.maintenance;

        document.getElementById("maintenance_id").value = m.id;

        document.getElementById("id_facility").value = m.facility;
        document.getElementById("facility_id").value = m.facility_id;
        document.getElementById("facility_type").value = m.facility_type;
        document.getElementById("id_title").value = m.title;
        document.getElementById("id_engineer").value = m.engineer;
        document.getElementById("id_description").value = m.description;
        document.getElementById("id_contact_number").value = m.contact;
        document.getElementById("id_remarks").value =
            m.remarks === "-" ? "" : m.remarks;

        document.getElementById("id_start_date").value = m.start_date;

        document.getElementById("id_expected_completion").value =
            m.expected_completion === "-" ? "" : m.expected_completion;

        document.getElementById("id_status").value = m.status;
        document.getElementById("id_priority").value = m.priority;

        document.getElementById("facilityMaintenanceModalLabel").textContent =
            "Edit Maintenance";

        document.getElementById("maintenanceSubmitBtn").innerHTML =
            '<i class="bi bi-check-circle"></i> Update Maintenance';

        bootstrap.Modal.getOrCreateInstance(
            document.getElementById("facilityMaintenanceModal")
        ).show();

    })
    .catch(console.error);

});

// MARK COMPLETED - MAINTENANCE

document.addEventListener("click", function (e) {

    const btn = e.target.closest(".complete-maintenance-btn");

    if (!btn) return;

    const maintenanceId = btn.dataset.maintenanceId;

    const url = completeMaintenanceUrl.replace("0", maintenanceId);

    fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest"
        }
    })
    .then(response => response.json())
    .then(data => {

        if (!data.success) {

            return;
          }


        // completed maintenance
        const maintenance = window.maintenanceData.find(
            m => m.id == data.maintenance_id
        );

        if (maintenance) {

            maintenance.status = "completed";

        }


        // Re-render maintenance cards
        window.renderMaint();

        // Update Recent Activities
        window.refreshRecentActivities(1);

        // Update facility card
      const card = document.querySelector(
            `[data-facility-id="${data.facility_id}"][data-facility-type="${data.facility_type}"]`
);

        if (card) {

            card.classList.remove("under-maintenance");

            const badge = card.querySelector(".maintenance-badge");
            const maintenanceBtn =
                card.querySelector(".edit-facility-btn") ||
                card.querySelector(".maintenance-btn");

            if (badge) {
                badge.textContent = "Available";
                badge.classList.remove("smh-unavail");
                badge.classList.add("smh-avail");
            }

            if (maintenanceBtn) {
                maintenanceBtn.style.display = "";
            }
        }

        Swal.fire({

            icon: "success",

            title: data.message,

        });

    })
    .catch(error => console.error(error));

});


// RECENT ACTIVITIES AJAX AND PAGINATION FUNCTIONS

window.refreshRecentActivities = async function (page = 1) {

    const timeline =
        document.getElementById("smh-timelineList");

    if (!timeline) {
        console.error("Timeline container not found");
        return;
    }

    const hospitalId =
        timeline.dataset.hospitalId;

    console.log("Hospital ID:", hospitalId);
    console.log("Requested Page:", page);

    if (!hospitalId) {
        console.error("Hospital UUID not found");
        return;
    }

    try {

        const url =
            `/medical/own_hospital/${hospitalId}/?activity_page=${page}`;

        console.log("Fetching:", url);

        const response = await fetch(url, {
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        });

        console.log("Response status:", response.status);

        const data = await response.json();

        console.log("AJAX response:", data);
        console.log("Timeline HTML:", data.timeline_html);

        if (!data.success) {
            console.error("Recent activities request failed");
            return;
        }

        if (!data.timeline_html) {
            console.error("timeline_html is empty");
            return;
        }

        timeline.innerHTML = data.timeline_html;
        
        // Make newly loaded activities visible
        timeline
            .querySelectorAll(".smh-reveal")
            .forEach((el) => {
                el.classList.add("smh-show");
            });

    } catch (error) {

        console.error(
            "Recent activities refresh error:",
            error
        );

    }
};


// =====================================================
// RECENT ACTIVITIES PAGINATION
// =====================================================

document.addEventListener("click", function (e) {

    const link = e.target.closest(
        "#smh-timelineList .activity-page-link"
    );

    if (!link) return;

    e.preventDefault();

    const url = new URL(
        link.href,
        window.location.origin
    );

    const page =
        url.searchParams.get("activity_page") || 1;

    window.refreshRecentActivities(page);

});


// HOSPITAL EDIT

document.addEventListener("click", function (e) {

    const btn = e.target.closest(".edit-hospital-btn");

    if (!btn) return;

    const hospitalId = btn.dataset.hospitalId;

    window.location.href =
        `/medical/create_hospital/?hospital=${hospitalId}`;

});

document.addEventListener("click", function (e) {

    console.log("button called")

    const btn = e.target.closest(".section-edit-btn");

    if (!btn) return;

    const hospitalId = btn.dataset.hospitalId;
    const section = btn.dataset.section;

    window.location.href =
        `/medical/create_hospital/?hospital=${hospitalId}#${section}`;
});


// HOSPITAL DELETE FUCNTION

document.addEventListener("click", function (e) {

    const btn = e.target.closest(".gallery-delete-btn");

    if (!btn) return;

    const galleryId = btn.dataset.id;

    Swal.fire({

        title: "Delete Gallery Image",

        html: `
            <div style="font-size:14px;color:#6c757d;">
                This action cannot be undone.
            </div>
        `,

        icon: "warning",

        width: "360px",

        padding: "1.5rem",

        showCancelButton: true,

        reverseButtons: true,

        focusCancel: true,

        confirmButtonText:
            '<i class="bi bi-trash3 me-1"></i> Delete',

        cancelButtonText:
            '<i class="bi bi-x-lg me-1"></i> Cancel',

        confirmButtonColor: "#dc3545",

        cancelButtonColor: "#6c757d",

        customClass: {

            popup: "gallery-delete-popup",

            title: "gallery-delete-title",

            confirmButton: "gallery-delete-confirm",

            cancelButton: "gallery-delete-cancel",

        }

    }).then((result) => {

        if (!result.isConfirmed) return;

        const deleteUrl = document.getElementById("smh-galleryGrid").dataset.deleteUrl.replace("0", galleryId);

        fetch(deleteUrl, {

            method: "POST",

            headers: {

                "X-CSRFToken": document.querySelector(
                    "[name=csrfmiddlewaretoken]"
                ).value,

            },

        })
        .then(res => res.json())
        .then(data => {

            if (data.success) {

                document.getElementById(
                    "smh-galleryGrid"
                ).innerHTML = data.html;

                Swal.fire({

                    toast: true,

                    position: "top-end",

                    icon: "success",

                    title: "Gallery image deleted",

                    showConfirmButton: false,

                    timer: 1800,

                    timerProgressBar: true,

                    width: "320px",

                    padding: "0.75rem 1rem",

                    customClass: {

                        popup: "gallery-toast",

                        title: "gallery-toast-title"

                    }

                });

            }

        });

    });

});
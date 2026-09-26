
        // ─── AOS Init ───
        AOS.init({
            duration: 700,
            once: true,
            offset: 40,
            easing: 'ease-out-quad'
        });

        // ─── Swiper ───
        const swiper = new Swiper('.mySwiper', {
            slidesPerView: 1,
            spaceBetween: 20,
            loop: true,
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
            },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
            },
            breakpoints: {
                576: { slidesPerView: 2, spaceBetween: 20 },
                992: { slidesPerView: 3, spaceBetween: 24 },
                1200: { slidesPerView: 4, spaceBetween: 24 }
            }
        });

        // ─── Animated Counters ───
        function animateCounter(element, target, duration = 1200) {
            let start = 0;
            const step = target / (duration / 16);
            const timer = setInterval(() => {
                start += step;
                if (start >= target) {
                    start = target;
                    clearInterval(timer);
                }
                element.textContent = Math.floor(start).toLocaleString();
            }, 16);
        }

        document.querySelectorAll('.kpi-value[data-count]').forEach(el => {
            const target = parseInt(el.getAttribute('data-count'), 10);
            animateCounter(el, target);
        });



// MAINTENANCE MODAL JS FUNCTIONS

const maintenanceModal = new bootstrap.Modal(
    document.getElementById("facilityMaintenanceModal")
);

document.addEventListener("click", function (e) {

    const btn = e.target.closest(".maintenance-view-btn");

    if (!btn) return;

    const facilityId = btn.dataset.facilityId;

    const url = btn.dataset.url.replace("0", facilityId);

    fetch(url)
        .then(res => res.json())
        .then(data => {

            populateFacilityModal(data);

            maintenanceModal.show();

        });

});


function populateFacilityModal(data){

    document.getElementById("modalFacilityIcon").className =
        data.facility.icon;

    document.getElementById("modalFacilityName").textContent =
        data.facility.name;

    document.getElementById("modalFacilityType").innerHTML =
        `<i class="bi bi-crosshair me-1"></i>${data.facility.type}`;

    document.getElementById("modalTotalHospitals").textContent =
        data.summary.total_hospitals;

    document.getElementById("modalAvailableHospitals").textContent =
        data.summary.available;

    document.getElementById("modalMaintenanceHospitals").textContent =
        data.summary.maintenance;

    renderAvailableHospitals(data.available_hospitals);

    renderMaintenanceHospitals(data.maintenance_hospitals);

}


function renderAvailableHospitals(hospitals){

    const container = document.getElementById(
        "availableHospitalContainer"
    );

    container.innerHTML = "";

    hospitals.forEach(hospital=>{

        container.insertAdjacentHTML("beforeend",`

<div class="col-sm-6 col-12">

<div class="hospital-card-available d-flex align-items-center gap-3">

<div class="hospital-icon">
<i class="bi bi-hospital-fill"></i>
</div>

<div class="flex-grow-1">

<div class="d-flex justify-content-between">

<span class="hospital-name">
${hospital.hospital}
</span>

<span class="status-badge-available">
<i class="bi bi-check-circle-fill"></i>
Available
</span>

</div>

</div>

</div>

</div>

`);

    });

}



function renderMaintenanceHospitals(records) {

    const container = document.getElementById(
        "maintenanceHospitalContainer"
    );

    container.innerHTML = "";

    if (!records.length) {

        container.innerHTML = `
            <div class="col-12">
                <div class="text-center py-4 text-muted">
                    No maintenance records found.
                </div>
            </div>
        `;

        return;
    }

    records.forEach(record => {

        const statusClass =
            record.status === "running"
                ? "running"
                : "pending";

        const statusIcon =
            record.status === "running"
                ? "bi-arrow-repeat"
                : "bi-clock-history";

        const priorityClass =
            record.priority.toLowerCase();

        container.insertAdjacentHTML("beforeend", `

<div class="col-12">

    <div class="hospital-card-maintenance">

        <div class="d-flex align-items-center gap-3 mb-3">

            <div class="hospital-icon">
                <i class="bi bi-hospital-fill"></i>
            </div>

            <div class="flex-grow-1">

                <span class="hospital-name">
                    ${record.hospital}
                </span>

            </div>

            <span class="status-badge-maintenance ${statusClass}">
                <i class="bi ${statusIcon}"></i>
                ${capitalize(record.status)}
            </span>

        </div>

        <div class="row g-2 g-sm-3 maintenance-demodal">

            <div class="col-12">

                <div class="maintenance-title">
                    ${record.title}
                </div>

                <div class="maintenance-desc mt-1">
                    ${record.description}
                </div>

            </div>

            <div class="col-6 col-sm-4 col-md-3">

                <div class="detail-label">
                    Priority
                </div>

                <div class="priority-badge ${priorityClass} mt-1">
                    <i class="bi bi-flag-fill"></i>
                    ${capitalize(record.priority)}
                </div>

            </div>

            <div class="col-6 col-sm-4 col-md-3">

                <div class="detail-label">
                    Engineer
                </div>

                <div class="detail-value engineer">
                    ${record.engineer || "-"}
                </div>

            </div>

            <div class="col-6 col-sm-4 col-md-3">

                <div class="detail-label">
                    Contact
                </div>

                <div class="detail-value contact">
                    ${record.contact || "-"}
                </div>

            </div>

            <div class="col-6 col-sm-4 col-md-3">

                <div class="detail-label">
                    Started
                </div>

                <div class="detail-value">
                    ${record.start_date}
                </div>

            </div>

            <div class="col-6 col-sm-4 col-md-3">

                <div class="detail-label">
                    Expected Completion
                </div>

                <div class="detail-value">
                    ${record.expected_completion}
                </div>

            </div>

            <div class="col-12">

                <div class="detail-label">
                    Remarks
                </div>

                <div class="detail-value">
                    ${record.remarks || "-"}
                </div>

            </div>

        </div>

    </div>

</div>

`);

    });

}

function capitalize(text) {

    if (!text) return "";

    return text.charAt(0).toUpperCase() + text.slice(1);

}
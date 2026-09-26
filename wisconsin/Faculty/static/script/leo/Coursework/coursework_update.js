document.addEventListener("DOMContentLoaded", function () {

    console.log("Coursework JS Loaded");

    const isSmallScreen = window.innerWidth < 320;

    const commonConfig = {
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d-m-Y",
        allowInput: false,
        clickOpens: true,
        disableMobile: true,
        animate: true,
        showMonths: 1,
        monthSelectorType: "dropdown",
        appendTo: isSmallScreen ? document.body : undefined,
        static: false,
        position: isSmallScreen ? "auto center" : "auto",
        onReady: function (selectedDates, dateStr, instance) {
            instance.altInput.setAttribute("readonly", true);
        }
    };

    // Start Date - Only past dates and today allowed
    flatpickr("#id_start_date", {
        ...commonConfig,
        maxDate: "today",
        onDayCreate: function (dObj, dStr, fp, dayElem) {
            const date = new Date(dayElem.dateObj);
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            dayElem.style.color = "#1e1e1e";
            dayElem.style.opacity = "1";
            dayElem.style.pointerEvents = "auto";
            dayElem.style.background = "transparent";

            if (date > today) {
                dayElem.style.opacity = "0.4";
                dayElem.style.pointerEvents = "none";
                dayElem.style.color = "#b0b0b0";
                dayElem.style.background = "#f5f5f5";
            }
        }
    });

    // Expected Completion Date - Only today and future dates allowed
    flatpickr("#id_expected_completion_date", {
        ...commonConfig,
        minDate: "today",
        onDayCreate: function (dObj, dStr, fp, dayElem) {
            const date = new Date(dayElem.dateObj);
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            dayElem.style.color = "#1e1e1e";
            dayElem.style.opacity = "1";
            dayElem.style.pointerEvents = "auto";
            dayElem.style.background = "transparent";

            if (date < today) {
                dayElem.style.opacity = "0.4";
                dayElem.style.pointerEvents = "none";
                dayElem.style.color = "#b0b0b0";
                dayElem.style.background = "#f5f5f5";
            }
        }
    });

    // Completion Date - Only past dates and today allowed
    flatpickr("#id_completion_date", {
        ...commonConfig,
        maxDate: "today",
        onDayCreate: function (dObj, dStr, fp, dayElem) {
            const date = new Date(dayElem.dateObj);
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            dayElem.style.color = "#1e1e1e";
            dayElem.style.opacity = "1";
            dayElem.style.pointerEvents = "auto";
            dayElem.style.background = "transparent";

            if (date > today) {
                dayElem.style.opacity = "0.4";
                dayElem.style.pointerEvents = "none";
                dayElem.style.color = "#b0b0b0";
                dayElem.style.background = "#f5f5f5";
            }
        }
    });

});
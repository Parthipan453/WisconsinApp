document.addEventListener("DOMContentLoaded", function () {
  AOS.init({ duration: 600, once: true, easing: "ease-out-cubic" });

  document.querySelectorAll('.ss-form-select').forEach(select => {
        new SlimSelect({
            select: select,
            settings: {
                placeholderText: select.options[0].text,
                showSearch: false
            }
        });
  });
});

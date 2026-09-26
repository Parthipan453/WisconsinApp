// ############################ Steve code start ##############################

document.addEventListener("DOMContentLoaded", () => {

    const observer = new IntersectionObserver((entries, observer) => {

        entries.forEach(entry => {

            if (entry.isIntersecting) {

                entry.target.classList.add("show");

                observer.unobserve(entry.target); // animate only once
            }

        });

    }, {
        threshold: 0.3,
        rootMargin: "0px 0px -100px 0px"
    });

    document.querySelectorAll(
        ".reveal-up, .reveal-left, .reveal-right"
    ).forEach(el => {
        observer.observe(el);
    });

});

// ############################ Steve code end ##############################
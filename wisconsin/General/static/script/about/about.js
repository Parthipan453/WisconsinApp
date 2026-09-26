
const counters = document.querySelectorAll(".counter");

const observer = new IntersectionObserver(entries => {

    entries.forEach(entry => {

        if(entry.isIntersecting){

            const counter = entry.target;

            const target = parseInt(
                counter.getAttribute("data-target")
            );

            let current = 0;

            const duration = 2000;

            const increment = target / (duration / 16);

            const updateCounter = () => {

                current += increment;

                if(current < target){

                    counter.innerText =
                    Math.floor(current);

                    requestAnimationFrame(updateCounter);

                }else{

                    counter.innerText = target;
                }
            };

            updateCounter();

            observer.unobserve(counter);
        }

    });

},{
    threshold:0.5
});

counters.forEach(counter => {
    observer.observe(counter);
});

// Word changing

const words = [
    "regionally",
    "nationally",
    "globally",
    "locally"
];

let index = 0;

const changingWord =
document.getElementById("changing-word");

setInterval(() => {

    changingWord.style.opacity = 0;

    setTimeout(() => {

        index = (index + 1) % words.length;

        changingWord.textContent =
        words[index];

        changingWord.style.opacity = 1;

    }, 300);

}, 3000); // 1 minute



const counters = document.querySelectorAll('.counter');

const observer = new IntersectionObserver(entries => {

    entries.forEach(entry => {

        if(entry.isIntersecting){

            const counter = entry.target;
            const target = +counter.dataset.target;

            let count = 0;

            const speed = target / 150;

            const updateCounter = () => {

                if(count < target){

                    count += speed;

                    counter.innerText =
                    Math.ceil(count).toLocaleString();

                    requestAnimationFrame(updateCounter);

                }else{

                    counter.innerText =
                    target.toLocaleString();
                }
            }

            updateCounter();

            observer.unobserve(counter);
        }
    });

},{threshold:0.5});

counters.forEach(counter => {

    observer.observe(counter);

});


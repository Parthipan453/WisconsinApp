// ############################ Steve code start ##############################

document.addEventListener("DOMContentLoaded", function(){

    const elements = document.querySelectorAll(
        ".animate-up, .animate-left, .animate-right, .animate-zoom"
    );

    const observer = new IntersectionObserver(

        (entries)=>{

            entries.forEach(entry=>{

                if(entry.isIntersecting){

                    entry.target.classList.add("show-animation");

                }

            });

        },

        {
            threshold:0.2
        }

    );

    elements.forEach(el=>observer.observe(el));

});

// ############################ Steve code end ##############################
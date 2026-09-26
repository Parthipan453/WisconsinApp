const menuToggle = document.querySelector(".menu-toggle");
const searchMenu = document.querySelector(".search-menu");

if (menuToggle && searchMenu) {

    menuToggle.addEventListener("click", function (e) {
        e.stopPropagation();
        searchMenu.classList.toggle("active");
    });

    searchMenu.addEventListener("click", function (e) {
        e.stopPropagation();
    });

    document.addEventListener("click", function () {
        searchMenu.classList.remove("active");
    });

}

const searchModal = document.getElementById("searchModal");
const openSearch = document.getElementById("openSearch");
const closeSearch = document.getElementById("closeSearch");

openSearch.addEventListener("click", function(e){
    e.preventDefault();
    searchModal.classList.add("show");
});

closeSearch.addEventListener("click", function(){
    searchModal.classList.remove("show");
});

searchModal.addEventListener("click", function(e){

    if(e.target === searchModal){
        searchModal.classList.remove("show");
    }

});

document.addEventListener("keydown", function(e){

    if(e.key === "Escape"){
        searchModal.classList.remove("show");
    }

});

document.addEventListener("DOMContentLoaded", function () {

    const selects = document.querySelectorAll(".choices-select");

    selects.forEach(function (select) {

        if (!select.dataset.choicesInitialized) {

            new Choices(select, {
                searchEnabled: false,
                itemSelectText: "",
                shouldSort: false,
                allowHTML: false,
                position: "bottom"
            });

            select.dataset.choicesInitialized = "true";
        }

    });

});

document.addEventListener("DOMContentLoaded", function () {

    const headers = document.querySelectorAll(".accordion-header");

    headers.forEach(function(header){

        header.addEventListener("click", function(){

            const body = header.nextElementSibling;

            const icon = header.querySelector("i");

            body.classList.toggle("open");

            header.classList.toggle("active");

            if(body.classList.contains("open")){

                icon.classList.remove("fa-chevron-down");

                icon.classList.add("fa-chevron-up");

            }

            else{

                icon.classList.remove("fa-chevron-up");

                icon.classList.add("fa-chevron-down");

            }

        });

    });

});

const swiper = new Swiper(".relatedSwiper",{

    slidesPerView:5,

    spaceBetween:16,

    navigation:{
        nextEl:".swiper-button-next",
        prevEl:".swiper-button-prev",
    },

    breakpoints:{

        1400:{
            slidesPerView:5
        },

        1200:{
            slidesPerView:4
        },

        992:{
            slidesPerView:3
        },

        768:{
            slidesPerView:2
        },

        0:{
            slidesPerView:1
        }

    }

});
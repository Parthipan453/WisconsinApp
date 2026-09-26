const menuToggle = document.querySelector(".menu-toggle");
const navbarMenu = document.querySelector(".navbar-menu");

if (menuToggle && navbarMenu) {

    menuToggle.addEventListener("click", function (e) {
        e.stopPropagation();
        navbarMenu.classList.toggle("active");
    });

    navbarMenu.addEventListener("click", function (e) {
        e.stopPropagation();
    });

    document.addEventListener("click", function () {
        navbarMenu.classList.remove("active");
    });

    document.querySelectorAll(".navbar-menu a").forEach(link => {
        link.addEventListener("click", () => {
            navbarMenu.classList.remove("active");
        });
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
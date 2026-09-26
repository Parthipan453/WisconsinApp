document.addEventListener("click", function(e){

    const link = e.target.closest(".ajax-page");

    if(!link) return;

    e.preventDefault();

    fetch(link.href,{
        headers:{
            "X-Requested-With":"XMLHttpRequest"
        }
    })
    .then(res=>res.json())
    .then(data=>{
        document.getElementById("latest-news-container").innerHTML = data.html;
    });

});
// CSRF
function getCookie(name) {
  let cookieValue = null;

  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");

    for (let cookie of cookies) {
      cookie = cookie.trim();

      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }

  return cookieValue;
}
const newsList = document.getElementById("newsList");
// LIVE DATE TIME UPDATE FUNCTION
function updateMasthead() {
  const now = new Date();

  const date = now.toLocaleDateString("en-GB", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  const time = now.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });

  document.querySelector(".masthead-date").innerHTML = `
        <i class="bi bi-calendar-week me-1"></i>${date} &middot; ${time}
    `;
}

updateMasthead();
setInterval(updateMasthead, 1000);

// REMOVE NEWS

let removeUrl = "";

const removeNewsModal = new bootstrap.Modal(document.getElementById("removeNewsModal"))


document.addEventListener("click", function (e) {

    const btn = e.target.closest(".btn-remove");

    if (!btn) return;

    removeUrl = btn.dataset.url;

    removeNewsModal.show();

});
// CONFIRM REMOVE

document.getElementById("confirmRemoveBtn").addEventListener("click", function() {

  fetch(removeUrl, {

    method: "POST",

    headers: {"X-CSRFToken": getCookie("csrftoken"), }

  })

  .then(response => response.json())
  .then(data => {

    

      if (data.success) {

        removeNewsModal.hide();

        location.reload();
      } else {
        alert(data.message);
      }
    
  })

  .catch(error => {
    console.error(error);
  });
});


// DRAFT TO PUBLISH NEWS

// PUBLISH NEWS

let publishUrl = "";

const publishNewsModal = new bootstrap.Modal(
    document.getElementById("publishNewsModal")
);

document.addEventListener("click", function (e) {

    const btn = e.target.closest(".publish-news");

    if (!btn) return;

    publishUrl = btn.dataset.url;

    publishNewsModal.show();

});


// CONFIRM PUBLISH

document.getElementById("confirmPublishBtn").addEventListener("click", function () {

    fetch(publishUrl, {

        method: "POST",

        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
        }

    })
    .then(response => response.json())
    .then(data => {

        if (data.success) {

            publishNewsModal.hide();

            location.reload();

        } else {

            alert(data.message);

        }

    })
    .catch(error => {
        console.error(error);
    });

});

// FILTER DATE FUNCTIONS

const filterDate = document.getElementById("filterDate");

filterDate.max = new Date().toISOString().split("T")[0];

filterDate.addEventListener("change", function () {

    if (!this.value) return;

    const [year, month, day] = this.value.split("-");

    console.log(`${day}/${month}/${year}`);

});

filterDate.addEventListener("keydown", function (e) {
    e.preventDefault();
});

filterDate.addEventListener("paste", function (e) {
    e.preventDefault();


});

filterDate.addEventListener("click", () => {
    if (filterDate.showPicker) {
        filterDate.showPicker();
    }
});

filterDate.addEventListener("focus", () => {
    if (filterDate.showPicker) {
        filterDate.showPicker();
    }
});



// DROPDOWN

const categoryChoices = new Choices("#categoryFilter", {
    searchEnabled: false,
    itemSelectText: "",
    shouldSort: false,
});


document.querySelector(".btn-filter").addEventListener("click", function () {

    loadNews();

});

document.addEventListener("click", function (e) {

    const btn = e.target.closest(".btn-page");

    if (!btn) return;

    loadNews(btn.dataset.page);

});

document.querySelector(".btn-reset-filter").addEventListener("click",function(){

    categoryChoices.setChoiceByValue("");

    document.getElementById("filterDate").value="";

    // document.querySelector(".btn-filter").click();
    loadNews();

});


document.querySelectorAll(".desk-tabs .nav-link").forEach(tab => {

    tab.addEventListener("shown.bs.tab", function () {

        // document.querySelector(".btn-filter").click();
        loadNews();

    });

});



// PAGINATOR
function loadNews(page = 1) {

    const category = document.getElementById("categoryFilter").value;
    const date = document.getElementById("filterDate").value;

    const url = newsList.dataset.filterUrl;

    const status = document.querySelector(".desk-tabs .nav-link.active").dataset.status;

    fetch(
        `${url}?status=${status}&category=${category}&date=${date}&page=${page}`
    )
    .then(res => res.json())
    .then(data => {

        newsList.classList.add("fade-out");

        setTimeout(() => {

            newsList.innerHTML = data.html;

            newsList.classList.remove("fade-out");

        }, 200);

    });

}
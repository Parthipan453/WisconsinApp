
console.log("js loaded")


document.addEventListener("click", function (e) {

  const link = e.target.closest(".pagination .page-link");

  if (!link) return;
  console.log("clicked");
  e.preventDefault();

  fetch(link.href, {
    headers: {
      "X-Requested-With": "XMLHttpRequest"
    }
  })

  .then(response => response.json())
  .then(data => {

    if (data.success) {

      document.getElementById("campus-news-container").innerHTML = data.html;
    }
  });
});
const searchInput = document.getElementById("event-search");
const clearButton = document.getElementById("clear-search");

let debounceTimer;

function loadEvents(url) {
  // Update the browser URL without reloading the page
  // syntax history.replaceState(state, title, url);
  history.replaceState({}, "", url);

  fetch(url)
    .then((response) => response.text())
    .then((html) => {
      const parser = new DOMParser();

      const responseDocument = parser.parseFromString(html, "text/html");

      document.querySelector(".events-main").innerHTML =
        responseDocument.querySelector(".events-main").innerHTML;

      document.querySelector("#calendar-container").innerHTML =
        responseDocument.querySelector("#calendar-container").innerHTML;

      document.querySelector("#browse-container").innerHTML =
        responseDocument.querySelector("#browse-container").innerHTML;

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    });
}

function performSearch() {
  const params = new URLSearchParams(window.location.search);

  params.set("search", searchInput.value);

  // Deletes pagination while searching
  params.delete("page");

  loadEvents(`?${params.toString()}`);
}

function toggleClearButton() {
  // When the condition is true, add "show" to classlist of clear button, else remove the same
  clearButton.classList.toggle("show", searchInput.value.trim() !== "");
}

searchInput.addEventListener("input", () => {
  toggleClearButton();

  // clears the previous timers
  clearTimeout(debounceTimer);

  debounceTimer = setTimeout(() => {
    performSearch();
  }, 300);
});

clearButton.addEventListener("click", () => {
  searchInput.value = "";

  toggleClearButton();

  searchInput.focus();

  performSearch();
});

toggleClearButton();

// Event Delegation => using one event listener for all the ajax filter links
// function(e) => Here 'e' is the event object
document.addEventListener("click", function (e) {
  const link = e.target.closest(".ajax-filter");

  if (!link) return;

  e.preventDefault();

  loadEvents(link.href);
});

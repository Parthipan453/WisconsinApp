// =======================
// TOAST
// =======================
const toastEl = document.getElementById("liveToast");
const toastMsg = document.getElementById("toastMessage");
const toast = new bootstrap.Toast(toastEl, {
    delay: 2000
});
function showToast(message, type) {
    toastMsg.innerText = message;
    toastEl.classList.remove(
        "text-bg-success",
        "text-bg-danger",
        "text-bg-warning",
        "text-bg-info"
    );
    toastEl.classList.add(`text-bg-${type}`);
    toast.show();
}
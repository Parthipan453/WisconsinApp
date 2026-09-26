/* *********************************************** Arun code ***************************************************  */

document.addEventListener("DOMContentLoaded", function () {
  AOS.init({
    once: true
  });
});

function toggleEdit() {
  const isEditing = document.getElementById("editToggle").dataset.editing === "true";
  if (isEditing) {
    cancelEdit();
  } else {
    startEdit();
  }
}

function startEdit() {
  const btn = document.getElementById("editToggle");

  btn.dataset.editing = "true";
  btn.innerHTML = '<i class="ti ti-x"></i> Cancel';

  document.querySelectorAll(".fv").forEach(el => {
    el.style.display = "none";
  });

  document.querySelectorAll(".fi").forEach(el => {
    el.style.display = "block";
  });

  document.querySelectorAll(".edit-bar").forEach(el => {
    el.style.display = "flex";
  });
}

function cancelEdit() {

  const btn = document.getElementById("editToggle");

  btn.dataset.editing = "false";
  btn.innerHTML = '<i class="ti ti-edit"></i> Edit Profile';

  document.querySelectorAll(".fv").forEach(el => {
    el.style.display = "";
  });

  document.querySelectorAll(".fi").forEach(el => {
    el.style.display = "none";
  });

  document.querySelectorAll(".edit-bar").forEach(el => {
    el.style.display = "none";
  });

}

function saveProfile() {

  document.querySelectorAll(".field").forEach(group => {

    const input = group.querySelector(".fi");
    const display = group.querySelector(".fv");

    if (input && display) {

      if (input.tagName === "SELECT") {
        display.textContent = input.options[input.selectedIndex].text;
      } else {
        display.textContent = input.value;
      }

    }

  });

  cancelEdit();

  toastSuccess("Profile updated successfully.");

}



document.querySelectorAll(".fi").forEach(el => {
  el.style.display = "none";
});

document.querySelectorAll(".edit-bar").forEach(el => {
  el.style.display = "none";
});

document.getElementById("editToggle").dataset.editing = "false";


// function showToast(msg) {
//   let toast = document.getElementById("toast");
//   if (!toast) {
//     toast = document.createElement("div");
//     toast.id = "toast";
//     toast.style.cssText =
//       "position:fixed;bottom:28px;right:28px;background:#228b22;color:#fff;padding:12px 22px;" +
//       "border-radius:10px;font-size:13.5px;font-weight:600;z-index:9999;box-shadow:0 4px 20px rgba(0,0,0,0.15);" +
//       "transition:opacity 0.3s;";
//     document.body.appendChild(toast);
//   }
//   toast.textContent = "✓ " + msg;
//   toast.style.opacity = "1";
//   setTimeout(() => {
//     toast.style.opacity = "0";
//   }, 2800);
// }



/* *********************************************** Arun code ***************************************************  */
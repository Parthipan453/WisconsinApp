
/* ============================================================
   Add Hospital Gallery — behavior script
   (Preview rendering + real-time validation UI only.
   No backend / upload logic included.)
============================================================ */
(function () {
  "use strict";

  const MAX_FILE_SIZE = 2 * 1024 * 1024; // 2MB
  const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
  const MAX_CAPTION_LENGTH = 200;

  const MAX_IMAGES = 10;
  const MIN_CAPTION_LENGTH = 5;

  const form            = document.getElementById("galleryForm");
  const dropzone         = document.getElementById("uploadDropzone");
  const fileInput        = document.getElementById("galleryImages");
  const uploadInvalidFB  = document.getElementById("uploadInvalidFeedback");

  const captionInput     = document.getElementById("galleryCaption");
  const captionCounter   = document.getElementById("captionCounter");
  const captionInvalidFB = document.getElementById("captionInvalidFeedback");

  const previewEmptyState = document.getElementById("previewEmptyState");
  const previewGrid        = document.getElementById("previewGrid");

  // Holds the currently "accepted" files (validated) for preview + submit
  let currentFiles = [];

  function isDuplicate(file) {

    return currentFiles.some(existing =>
        existing.name === file.name &&
        existing.size === file.size &&
        existing.lastModified === file.lastModified
    );

}

  /* ---------------- Helpers ---------------- */

  function isValidFile(file) {
    return ALLOWED_TYPES.includes(file.type) && file.size <= MAX_FILE_SIZE;
  }

  function setDropzoneValidity(hasFiles, allValid) {

    dropzone.classList.remove("is-invalid-zone", "is-valid-zone");

    if (!hasFiles) {

        fileInput.classList.remove("is-valid");
        fileInput.classList.add("is-invalid");

        dropzone.classList.add("is-invalid-zone");

        return;

    }

    if (allValid) {

        fileInput.classList.remove("is-invalid");
        fileInput.classList.add("is-valid");

        dropzone.classList.add("is-valid-zone");

    } else {

        fileInput.classList.remove("is-valid");
        fileInput.classList.add("is-invalid");

        dropzone.classList.add("is-invalid-zone");

    }

}

  function renderPreview() {
    previewGrid.innerHTML = "";

    if (currentFiles.length === 0) {
      previewEmptyState.classList.remove("d-none");
      previewGrid.classList.add("d-none");
      return;
    }

    previewEmptyState.classList.add("d-none");
    previewGrid.classList.remove("d-none");

    currentFiles.forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const card = document.createElement("div");
        card.className = "preview-card";
        card.innerHTML = `
          <img src="${e.target.result}" alt="${file.name}">
          <button type="button" class="remove-btn" data-index="${index}" aria-label="Remove image">
            <i class="bi bi-x-lg"></i>
          </button>
          <div class="caption-overlay">${file.name}</div>
        `;
        previewGrid.appendChild(card);

        // Remove handler
        card.querySelector(".remove-btn").addEventListener("click", () => {
          currentFiles.splice(index, 1);

          if (currentFiles.length === 0) {

                fileInput.classList.remove("is-valid", "is-invalid");
                dropzone.classList.remove("is-invalid-zone");

            }
          syncFileInput();
          renderPreview();
          validateUpload();
        });
      };
      reader.readAsDataURL(file);
    });
  }

  // Rebuild the hidden file input's FileList from currentFiles (DataTransfer trick)
  function syncFileInput() {
    const dt = new DataTransfer();
    currentFiles.forEach((file) => dt.items.add(file));
    fileInput.files = dt.files;
  }

function addFiles(fileList) {

    const file = fileList[0];

    if (!file) {
        return;
    }

    currentFiles = [];

    if (!ALLOWED_TYPES.includes(file.type)) {

        uploadInvalidFB.textContent =
            `${file.name} is not a supported image.`;

        setDropzoneValidity(true, false);
        return;
    }

    if (file.size > MAX_FILE_SIZE) {

        uploadInvalidFB.textContent =
            `${file.name} exceeds 2MB.`;

        setDropzoneValidity(true, false);
        return;
    }

    currentFiles.push(file);

    syncFileInput();
    renderPreview();
    validateUpload();

}

function validateUpload() {

        for (const file of currentFiles) {

            if (!ALLOWED_TYPES.includes(file.type)) {

                uploadInvalidFB.textContent =
                    `${file.name} is not a supported image.`;

                setDropzoneValidity(true, false);
                return false;
            }

            if (file.size > MAX_FILE_SIZE) {

                uploadInvalidFB.textContent =
                    `${file.name} exceeds 2MB.`;

                setDropzoneValidity(true, false);
                return false;
            }

        }

    if (currentFiles.length === 0) {

        uploadInvalidFB.textContent =
            "Please upload at least one image.";

        fileInput.classList.add("is-invalid");
        dropzone.classList.add("is-invalid-zone");

        setDropzoneValidity(false, false);
        return false;
    }

    if (currentFiles.length > MAX_IMAGES) {

        uploadInvalidFB.textContent =
            `Maximum ${MAX_IMAGES} images allowed.`;

        setDropzoneValidity(true, false);
        return false;
    }



    setDropzoneValidity(true, true);
    return true;

}

function validateCaption() {
    
    console.log("Caption validation running");

    const caption = captionInput.value.trim();

    const length = caption.length;

    captionCounter.textContent = `${length} / ${MAX_CAPTION_LENGTH}`;

    captionCounter.classList.remove("is-warning", "is-limit");
    captionInput.classList.remove("is-invalid", "is-valid");

    if (caption === "") {

        captionInvalidFB.textContent =
            "Caption is required.";

        captionInput.classList.add("is-invalid");

        return false;

    }

    if (length < MIN_CAPTION_LENGTH) {

        captionInvalidFB.textContent =
            `Caption must contain at least ${MIN_CAPTION_LENGTH} characters.`;

        captionInput.classList.add("is-invalid");

        return false;

    }

    if (!/[A-Za-z]/.test(caption)) {

        captionInvalidFB.textContent =
            "Caption must contain at least one alphabet.";

        captionInput.classList.add("is-invalid");

        return false;

    }

    if (length > MAX_CAPTION_LENGTH) {

        captionInvalidFB.textContent =
            `Caption cannot exceed ${MAX_CAPTION_LENGTH} characters.`;

        captionInput.classList.add("is-invalid");
        captionCounter.classList.add("is-limit");

        return false;

    }

    if (length >= MAX_CAPTION_LENGTH * 0.85) {

        captionCounter.classList.add("is-warning");

    }

    captionInput.classList.add("is-valid");

    return true;

}
  /* ---------------- Event listeners ---------------- */

  // Click / browse
fileInput.addEventListener("change", function () {

    addFiles(this.files);

    this.value = "";

});

  // Drag & drop states
  ["dragenter", "dragover"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("is-dragover");
    });
  });

  ["dragleave", "drop"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("is-dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length) {
      addFiles(dt.files);
    }
  });

  // Keyboard accessibility: Enter/Space opens file browser
  dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInput.click();
    }
  });

  // Caption live counter + validation
  ["input","blur","paste"].forEach(evt=>{
      captionInput.addEventListener(evt,validateCaption);
  });

  // Ripple effect on the primary button
  const uploadBtn = document.getElementById("uploadGalleryBtn");
  uploadBtn.addEventListener("click", function (e) {
    const rect = uploadBtn.getBoundingClientRect();
    const span = document.createElement("span");
    span.className = "ripple-span";
    span.style.left = `${e.clientX - rect.left}px`;
    span.style.top = `${e.clientY - rect.top}px`;
    uploadBtn.appendChild(span);
    setTimeout(() => span.remove(), 600);
  });

  // Real-time validation on submit (Bootstrap-style)
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    e.stopPropagation();

    const uploadOk  = validateUpload();
    const captionOk = validateCaption();

    form.classList.add("was-validated");

    if (uploadOk && captionOk) {

        const formData = new FormData();

        formData.append(
            "caption",
            captionInput.value.trim()
        );

        formData.append("images", currentFiles[0]);

        fetch(form.dataset.uploadUrl, {

            method: "POST",

            headers: {

                "X-CSRFToken": document.querySelector(
                    "[name=csrfmiddlewaretoken]"
                ).value,

            },

            body: formData,

        })
        .then(response => response.json())
        .then(data => {

            if (data.success) {

              const galleryGrid = document.getElementById("smh-galleryGrid");

              console.log(galleryGrid);
              console.log(data.html);

              if (galleryGrid) {
                  galleryGrid.innerHTML = data.html;
              }

              const modal = bootstrap.Modal.getInstance(
                  document.getElementById("galleryModal")
              );

              modal.hide();
          } else {

                console.log(data.message);

            }

        })
        .catch(error => {

            console.error(error);

        });

    }
  });

  // Reset state whenever modal is closed
  document.getElementById("galleryModal").addEventListener("hidden.bs.modal", () => {
    currentFiles = [];
    fileInput.value = "";
    captionInput.value = "";
    form.classList.remove("was-validated");
    fileInput.classList.remove("is-invalid");
    dropzone.classList.remove("is-invalid-zone");

    fileInput.classList.add("is-valid");
    dropzone.classList.add("is-valid-zone");
    captionInput.classList.remove("is-valid", "is-invalid");
    captionCounter.textContent = "0 / 200";
    captionCounter.classList.remove("is-warning", "is-limit");
    renderPreview();
  });
})();

(function () {
  "use strict";

  /* =========================================================================
     ARTICLE PUBLISHING WIZARD
     A 5-step form wizard (Basic Info -> Author/Hero -> Content Blocks ->
     Related Articles -> Preview/Publish). This IIFE keeps all internal state
     private and only exposes the functions the HTML (onclick=".." attributes)
     needs on the `window` object.
     ========================================================================= */

  // ─── STATE ───
  // currentStep / totalSteps drive the stepper UI and step navigation.
  // blockEditIndex tracks which content block is open in the edit modal.
  // isTransitioning guards against double-clicks firing renderStep() twice
  // while the step-change animation is still running.
  let currentStep = 1;
  const totalSteps = 5;
  let blockEditIndex = -1;
  let isTransitioning = false;

  // ─── DOM REFS ───
  // Cached once since these elements are static wrappers around the
  // step content that gets swapped out.
  const wrap = document.getElementById("stepContentWrap");
  const stepItems = document.querySelectorAll(".step-item");
  const connectors = document.querySelectorAll(".step-connector");

  // ─── FORM DATA STORE ───
  // Single source of truth for every field across all 5 steps. Because the
  // step HTML is re-rendered from scratch on every navigation, we can't rely
  // on the DOM to hold values between steps -- everything lives here instead.
  const formData = {
    title: "",
    subtitle: "",
    category: "",
    readingTime: "6",

    authorName: "",
    authorRole: "",
    authorBio: "",
    authorAvatar: null,
    authorAvatarName: "",
    heroFile: null,
    heroFileName: "",
    socialTwitter: "",
    socialLinkedin: "",
    socialWebsite: "",

    heroCaption: "",
    tags: [],
    blocks: [],
    related: [],
  };

  // If we're editing an existing article, `window.articleData` is injected
  // server-side. We merge it into formData, but file inputs (heroFile /
  // authorAvatar) always start as `null` because a browser can never
  // pre-populate a <input type="file"> with an existing uploaded file --
  // the existing image URL is shown separately via formData.heroMedia, etc.
  if (window.articleData) {
    Object.assign(formData, window.articleData);

    formData.heroFile = null;
    formData.authorAvatar = null;
    console.log(formData.blocks);
  }

  // Keeps the currently active step tab scrolled into view on the
  // horizontally-scrollable stepper (mainly matters on mobile).
  function scrollActiveStepIntoView() {
    const wrapper = document.getElementById("stepperWrapper");
    const activeStep = wrapper.querySelector(".step-item.active");

    if (!activeStep) return;

    const scrollLeft =
      activeStep.offsetLeft -
      wrapper.clientWidth / 2 +
      activeStep.offsetWidth / 2;

    wrapper.scrollTo({
      left: scrollLeft,
      behavior: "smooth",
    });
  }

  // ─── HELPERS ───
  // Paints the stepper bar: marks the active step, marks earlier steps as
  // "completed" (with a check icon), and colors the connecting lines
  // between them so progress is visually obvious.
  function updateStepper(activeStep) { 
    stepItems.forEach((item) => {
      const stepNum = parseInt(item.dataset.step);
      item.classList.remove("active", "completed", "inactive");
      const circle = item.querySelector(".step-circle");
      if (stepNum === activeStep) {
        item.classList.add("active");
        circle.innerHTML = stepNum;
      } else if (stepNum < activeStep) {
        item.classList.add("completed");
        circle.innerHTML = '<i class="bi bi-check-lg"></i>';
      } else {
        item.classList.add("inactive");
        circle.innerHTML = stepNum;
      }
    });

    connectors.forEach((conn) => {
      const idx = parseInt(conn.dataset.connector);
      conn.classList.remove("done", "partial");
      if (idx < activeStep) conn.classList.add("done");
      else if (idx === activeStep) conn.classList.add("partial");
    });
    requestAnimationFrame(scrollActiveStepIntoView);
  }

  // Normalizes any YouTube/Vimeo link a user pastes (share link, short link,
  // or already-an-embed link) into a proper `/embed/` URL so it can be
  // dropped straight into an <iframe>.
  function getEmbedUrl(url) {
    if (!url) return "";

    url = url.trim();

    // Already an embed URL
    if (url.includes("youtube.com/embed/")) {
      return url;
    }

    // https://youtu.be/VIDEO_ID
    let match = url.match(/^https?:\/\/(?:www\.)?youtu\.be\/([^?&]+)/);

    if (match) {
      return `https://www.youtube.com/embed/${match[1]}`;
    }

    // https://www.youtube.com/watch?v=VIDEO_ID
    match = url.match(/[?&]v=([^&]+)/);

    if (match) {
      return `https://www.youtube.com/embed/${match[1]}`;
    }

    // Vimeo (later support)
    if (url.includes("vimeo.com")) {
      const id = url.split("/").pop().split("?")[0];
      return `https://player.vimeo.com/video/${id}`;
    }

    return url;
  }

  // ─── VALIDATION HELPERS ───
  // Shared plumbing used by every per-field validator below: flip a field
  // into its "invalid" visual state with a message, or clear that state.
  function markInvalid(elId, feedbackId, message) {
    const el = document.getElementById(elId);
    const fb = document.getElementById(feedbackId);
    if (!el || !fb) return;
    fb.textContent = message;
    fb.classList.add("show");
    el.classList.add("is-invalid-custom");
  }

  function clearError(elId, feedbackId) {
    const el = document.getElementById(elId);
    const fb = document.getElementById(feedbackId);
    if (!el || !fb) return;
    fb.classList.remove("show");
    el.classList.remove("is-invalid-custom");
  }

  // ─── PER-FIELD VALIDATION FUNCTIONS ───
  // Each of these validates exactly one input, shows/clears its own inline
  // error, and returns true/false so callers (validateStep / validateAll)
  // can combine results. Kept one-function-per-field so a single field's
  // rules can change without touching anything else.

  // 1. Title
  function validateTitle() {
    const input = document.getElementById("editTitle");
    const fb = document.getElementById("titleFeedback");
    if (!input || !fb) return false;

    clearError("editTitle", "titleFeedback");
    const value = input.value.trim();

    if (value === "") {
      markInvalid("editTitle", "titleFeedback", "Title is required.");
      return false;
    }
    if (value.length < 5) {
      markInvalid(
        "editTitle",
        "titleFeedback",
        "Title must be at least 5 characters.",
      );
      return false;
    }
    if (value.length > 100) {
      markInvalid(
        "editTitle",
        "titleFeedback",
        "Title must not exceed 100 characters.",
      );
      return false;
    }
    if (!/[A-Za-z]/.test(value)) {
      markInvalid(
        "editTitle",
        "titleFeedback",
        "Title must contain at least one letter.",
      );
      return false;
    }

    if (/^[^A-Za-z0-9\s]+$/.test(value)) {
      markInvalid(
        "editTitle",
        "titleFeedback",
        "Title cannot contain only symbols.",
      );
      return false;
    }
    return true;
  }

  // Subtitle: required, minimum length only (no upper bound).
  function validateSubtitle() {
    const input = document.getElementById("editSubtitle");
    const fb = document.getElementById("subtitleFeedback");

    if (!input || !fb) return false;

    clearError("editSubtitle", "subtitleFeedback");

    const value = input.value.trim();

    if (value === "") {
      markInvalid("editSubtitle", "subtitleFeedback", "Subtitle is required.");
      return false;
    }

    if (value.length < 20) {
      markInvalid(
        "editSubtitle",
        "subtitleFeedback",
        "Subtitle must be at least 20 characters.",
      );
      return false;
    }

    return true;
  }

  // 2. Category
  function validateCategory() {
    const input = document.getElementById("editCategory");
    const fb = document.getElementById("categoryFeedback");
    if (!input || !fb) return false;

    clearError("editCategory", "categoryFeedback");
    if (!input.value || input.value === "") {
      markInvalid(
        "editCategory",
        "categoryFeedback",
        "Please select a category.",
      );
      return false;
    }
    return true;
  }

  // 3. Reading Time
  function validateReadingTime() {
    const input = document.getElementById("editReadingTime");
    const fb = document.getElementById("readingTimeFeedback");
    if (!input || !fb) return false;

    clearError("editReadingTime", "readingTimeFeedback");
    const val = parseInt(input.value);
    if (!input.value || input.value.trim() === "" || isNaN(val) || val < 1) {
      markInvalid(
        "editReadingTime",
        "readingTimeFeedback",
        "Please enter a valid reading time (minimum 1).",
      );
      return false;
    }
    return true;
  }

  // 5. Author Name
  function validateAuthorName() {
    const input = document.getElementById("editAuthorName");
    const fb = document.getElementById("authorNameFeedback");

    if (!input || !fb) return false;

    clearError("editAuthorName", "authorNameFeedback");

    const value = input.value.trim();

    if (value === "") {
      markInvalid(
        "editAuthorName",
        "authorNameFeedback",
        "Please enter the author's name.",
      );

      return false;
    }

    // Only letters and spaces allowed
    if (!/^[A-Za-z\s]+$/.test(value)) {
      markInvalid(
        "editAuthorName",
        "authorNameFeedback",
        "Author name can contain only letters and spaces.",
      );

      return false;
    }

    return true;
  }

  // Author role is optional; only rejects "symbols-only" junk input.
  function validateAuthorRole() {
    const input = document.getElementById("editAuthorRole");
    const fb = document.getElementById("authorRoleFeedback");

    if (!input || !fb) return false;

    clearError("editAuthorRole", "authorRoleFeedback");
    const value = input.value.trim();

    if (/^[^A-Za-z0-9\s]+$/.test(value)) {
      markInvalid(
        "editAuthorRole",
        "authorRoleFeedback",
        "Author role cannot contain only symbols.",
      );
      return false;
    }
    return true;
  }

  // Author bio is optional; when filled, enforces a max length and rejects
  // symbols-only / no-letters input.
  function validateAuthorBio() {
    const input = document.getElementById("editAuthorBio");
    const fb = document.getElementById("authorBioFeedback");

    if (!input || !fb) return false;

    clearError("editAuthorBio", "authorBioFeedback");

    const value = input.value.trim();

    // Optional field
    if (value === "") {
      return true;
    }

    // Maximum length
    if (value.length > 250) {
      markInvalid(
        "editAuthorBio",
        "authorBioFeedback",
        "Bio must not exceed 250 characters.",
      );
      return false;
    }

    // Only symbols not allowed
    if (/^[^A-Za-z0-9\s]+$/.test(value)) {
      markInvalid(
        "editAuthorBio",
        "authorBioFeedback",
        "Bio cannot contain only symbols.",
      );
      return false;
    }

    if (!/[A-Za-z]/.test(value)) {
      markInvalid(
        "editAuthorBio",
        "authorBioFeedback",
        "Bio must contain at least one letter.",
      );
      return false;
    }

    return true;
  }

  // Author avatar is optional; when a file is chosen it must be an
  // allowed image type.
  function validateAuthorImage() {
    const input = document.getElementById("editAuthorAvatar");
    const fb = document.getElementById("authorImageFeedback");

    if (!input || !fb) return false;

    clearError("editAuthorAvatar", "authorImageFeedback");

    // Optional field
    if (input.files.length === 0) {
      return true;
    }

    const file = input.files[0];

    const allowedTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"];

    if (!allowedTypes.includes(file.type)) {
      markInvalid(
        "editAuthorAvatar",
        "authorImageFeedback",
        "Only JPG, JPEG,Webp and PNG files are allowed.",
      );

      return false;
    }

    return true;
  }

  // Generic validator for the three optional social-link fields. `type`
  // picks the matching URL pattern (Twitter/X, LinkedIn, or "any https url"
  // for the generic website field).
  function validateSocialLink(inputId, feedbackId, type) {
    const input = document.getElementById(inputId);
    const fb = document.getElementById(feedbackId);

    if (!input || !fb) return false;

    clearError(inputId, feedbackId);

    const value = input.value.trim();

    // Optional field
    if (value === "") {
      return true;
    }

    let pattern;

    if (type === "twitter") {
      pattern = /^https:\/\/(x|twitter)\.com\/.+$/i;
    } else if (type === "linkedin") {
      pattern = /^https:\/\/(www\.)?linkedin\.com\/.+$/i;
    } else {
      pattern = /^https:\/\/.+$/i;
    }

    if (!pattern.test(value)) {
      markInvalid(inputId, feedbackId, `Please enter a valid ${type} URL.`);
      return false;
    }

    return true;
  }

  // Hero media (required). Has to account for two "already have a valid
  // image, no new upload needed" cases because a browser silently clears
  // <input type="file"> every time we re-render the step:
  //   1. Create mode: user already picked heroFile earlier in this session.
  //   2. Edit mode: article already has a saved heroMedia URL.
  // Only when neither of those applies do we require a fresh file, and
  // then we check its type.
  function validateMediaFile() {
    const input = document.getElementById("editHeroSrc");
    const fb = document.getElementById("heroSrcFeedback");

    if (!input || !fb) return false;

    clearError("editHeroSrc", "heroSrcFeedback");

    // CREATE MODE: already selected image exists in memory (browser clears
    // the file input after every re-render).
    if (!window.isEdit && formData.heroFile && input.files.length === 0) {
      return true;
    }

    // EDIT MODE: existing database image, nothing new chosen.
    if (window.isEdit && formData.heroMedia && input.files.length === 0) {
      return true;
    }

    // No file selected and no existing/remembered image either.
    if (input.files.length === 0) {
      markInvalid("editHeroSrc", "heroSrcFeedback", "Hero image is required.");
      return false;
    }

    // Validate the newly selected file's type.
    const file = input.files[0];

    const allowedTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"];

    if (!allowedTypes.includes(file.type)) {
      input.value = "";

      formData.heroFile = null;
      formData.heroFileName = "";

      markInvalid(
        "editHeroSrc",
        "heroSrcFeedback",
        "Only JPG, JPEG, PNG and WEBP images are allowed.",
      );

      return false;
    }

    return true;
  }

  // 7. Content Blocks - at least one block must exist before moving on.
  function validateBlocks() {
    const fb = document.getElementById("blocksFeedback");
    const blocks = document.querySelectorAll("#blockList .block-item");
    if (!fb) return false;

    fb.classList.remove("show");
    if (blocks.length === 0) {
      fb.textContent = "Please add at least one content block.";
      fb.classList.add("show");
      return false;
    }
    return true;
  }

  // ─── STEP VALIDATION ───
  // Runs only the validators relevant to the step the user is trying to
  // leave, so `goToStep()` can block forward navigation until it's valid.
  function validateStep(step) {
    let valid = true;
    if (step === 1) {
      if (!validateCategory()) valid = false;
      if (!validateSubtitle()) valid = false;
      if (!validateReadingTime()) valid = false;
    } else if (step === 2) {
      if (!validateAuthorName()) valid = false;
      if (!validateAuthorRole()) valid = false;
      if (!validateAuthorBio()) valid = false;
      if (!validateAuthorImage()) valid = false;
      if (
        !validateSocialLink("editSocialTwitter", "twitterFeedback", "twitter")
      )
        valid = false;

      if (
        !validateSocialLink(
          "editSocialLinkedin",
          "linkedinFeedback",
          "linkedin",
        )
      )
        valid = false;

      if (
        !validateSocialLink("editSocialWebsite", "websiteFeedback", "website")
      )
        valid = false;
      if (!validateMediaFile()) valid = false;
    } else if (step === 3) {
      if (!validateBlocks()) valid = false;
    }
    return valid;
  }

  // Runs every validator regardless of step -- used as a final safety net
  // (kept from the original for debugging/manual use); logs each result
  // to the console so the underlying cause of an "invalid form" state is
  // easy to spot while testing.
  function validateAll() {
    let valid = true;
    if (!validateTitle()) valid = false;
    if (!validateSubtitle()) valid = false;
    if (!validateCategory()) valid = false;
    if (!validateReadingTime()) valid = false;

    if (!validateAuthorName()) valid = false;
    if (!validateAuthorRole()) valid = false;
    if (!validateAuthorImage()) valid = false;
    if (!validateSocialLink("editSocialTwitter", "twitterFeedback", "twitter"))
      valid = false;

    if (
      !validateSocialLink("editSocialLinkedin", "linkedinFeedback", "linkedin")
    )
      valid = false;

    if (!validateSocialLink("editSocialWebsite", "websiteFeedback", "website"))
      valid = false;
    if (!validateAuthorBio()) valid = false;
    if (!validateMediaFile()) valid = false;
    if (!validateBlocks()) valid = false;

    console.log("Title:", validateTitle());
    console.log("Category:", validateCategory());
    console.log("Reading:", validateReadingTime());
    console.log("Author:", validateAuthorName());
    console.log("Author Role:", validateAuthorRole());
    console.log("Author Bio:", validateAuthorBio());
    console.log("Author Image:", validateAuthorImage());
    console.log("Hero Media:", validateMediaFile());
    console.log("Blocks:", validateBlocks());

    return valid;
  }

  // Checks the in-memory formData object directly (rather than the live
  // DOM) so it can be called from any step -- e.g. when jumping straight
  // to step 5 or hitting Publish, we need to know if an EARLIER step is
  // incomplete even though its inputs aren't currently rendered.
  // Returns `true` if everything required is present, otherwise returns
  // `{ step, field }` telling the caller where to send the user.
  function validateFormData() {
    if (!formData.title.trim()) {
      return { step: 1, field: "Title" };
    }

    if (!formData.subtitle.trim()) {
      return { step: 1, field: "Subtitle" };
    }

    if (!formData.category) {
      return { step: 1, field: "Category" };
    }

    if (!formData.readingTime) {
      return { step: 1, field: "Reading Time" };
    }

    if (!formData.authorName.trim()) {
      return { step: 2, field: "Author Name" };
    }

    if (!formData.heroFile && !formData.heroMedia) {
      return { step: 2, field: "Hero Media" };
    }

    if (formData.blocks.length === 0) {
      return { step: 3, field: "Content Blocks" };
    }

    return true;
  }

  // ─── HERO MEDIA PREVIEW ───
  // Renders either the newly-picked file (create mode / re-upload) or the
  // already-saved image (edit mode) below the hero file input.
  function renderHeroPreview() {
    const filePreview = document.getElementById("heroFilePreview");
    const mediaPreview = document.getElementById("heroMediaPreview");

    if (!filePreview || !mediaPreview) return;

    // Clear existing preview
    filePreview.innerHTML = "";
    mediaPreview.innerHTML = "";

    // CREATE MODE (or a fresh re-upload): show the newly chosen file.
    if (formData.heroFile && formData.heroFileName) {
      filePreview.innerHTML = `
            <i class="bi bi-check-circle-fill text-success"></i>
            ${formData.heroFileName}
        `;

      // Image preview only if actual File object exists
      if (formData.heroFile instanceof File) {
        const url = URL.createObjectURL(formData.heroFile);

        mediaPreview.innerHTML = `
                <img
                    src="${url}"
                    class="img-thumbnail mt-2"
                    style="max-width:220px;">
            `;
      }

      return;
    }

    // EDIT MODE: show the image already saved on the article.
    if (window.isEdit && formData.heroMedia) {
      filePreview.innerHTML = `
            Current Image :
            <a href="${formData.heroMedia}" target="_blank">
                ${formData.heroFileName}
            </a>
        `;

      mediaPreview.innerHTML = `
            <img
                src="${formData.heroMedia}"
                class="img-thumbnail mt-2"
                style="max-width:220px;">
        `;
    }
  }

  // ─── RENDER STEP CONTENT ───
  // Swaps the wizard's content pane for the given step. Each step's HTML
  // is rebuilt from formData every time (rather than toggling
  // show/hide), which keeps state management simple at the cost of
  // having to re-bind DOM event listeners on every render (see
  // bindStepEvents below).
  function renderStep(step, animate = true) {
    if (isTransitioning) return;
    isTransitioning = true;

    const currentContent = wrap.querySelector(".step-content");
    if (currentContent && animate) {
      currentContent.classList.add("exit");
    }

    // Wait for the exit animation to finish before swapping the HTML
    // (skipped entirely on the very first render via animate = false).
    setTimeout(
      () => {
        let html = "";
        if (step === 1) html = renderStep1();
        else if (step === 2) html = renderStep2();
        else if (step === 3) html = renderStep3();
        else if (step === 4) html = renderStep4();
        else if (step === 5) html = renderStep5();

        wrap.innerHTML = html;

        // Step 1's category <select> is upgraded into a Choices.js widget;
        // it has to be rebuilt every render since we just replaced the
        // underlying <select> element.
        if (step === 1) {
          if (window.editCategoryChoices) {
            window.editCategoryChoices.destroy();
          }

          window.editCategoryChoices = new Choices("#editCategory", {
            searchEnabled: false,
            itemSelectText: "",
            shouldSort: false,
          });

          document.getElementById("editTitle").value = formData.title || "";
          document.getElementById("editSubtitle").value = formData.subtitle || "";
          document.getElementById("editReadingTime").value =
              formData.readingTime || "6";
        }

        // STEP 2 (edit mode): populate the author/hero image previews from
        // whatever is already stored in formData (existing avatar file
        // picked this session, or the avatar/hero URLs saved on the
        // article being edited).
        if (step === 2 && window.articleData) {
          // Author avatar picked during this session (in-memory File).
          if (formData.authorAvatar instanceof File) {
            const url = URL.createObjectURL(formData.authorAvatar);

            document.getElementById("authorFilePreview").innerHTML = `
                    Selected Image :
                    <span class="text-success">${formData.authorAvatar.name}</span>
                `;

            document.getElementById("authorAvatarPreview").innerHTML = `
                    <img
                        src="${url}"
                        class="img-thumbnail mt-2"
                        style="max-width:120px;">
                `;
          }

          // Existing author avatar URL (edit mode).
          if (formData.authorAvatar) {
            document.getElementById("authorFilePreview").innerHTML = `
                    Current Image :
                    <a href="${formData.authorAvatar}" target="_blank">
                        ${formData.authorAvatarName}
                    </a>
                `;
          }

          renderHeroPreview();
        }

        if (step === 2 && window.articleData) {
          if (formData.authorAvatar) {
            document.getElementById("authorFilePreview").innerHTML = `
                  Current Image :
                  <a href="${formData.authorAvatar}" target="_blank">
                      ${formData.authorAvatarName}
                  </a>
              `;

            document.getElementById("authorAvatarPreview").innerHTML = `
                  <img
                      src="${formData.authorAvatar}"
                      class="img-thumbnail mt-2"
                      style="max-width:120px;">
              `;
          }

          if (formData.heroMedia) {
            document.getElementById("heroFilePreview").innerHTML = `
                  Current Media :
                  <a href="${formData.heroMedia}" target="_blank">
                      ${formData.heroFileName}
                  </a>
              `;

            document.getElementById("heroMediaPreview").innerHTML = `
                  <img
                      src="${formData.heroMedia}"
                      class="img-thumbnail mt-2"
                      style="max-width:220px;">
              `;
          }
        }

        if (step === 2) {
          renderHeroPreview();
        }

        bindStepEvents(step);
        updateStepper(step);
        currentStep = step;

        if (step === 5) {
          updatePublishButtonState();
          updatePreview();
          updateTemplateButton();
        } else {
          // Clear any leftover errors from previous renders
          document
            .querySelectorAll(".is-invalid-custom")
            .forEach((el) => el.classList.remove("is-invalid-custom"));
          document
            .querySelectorAll(".validation-feedback.show")
            .forEach((el) => el.classList.remove("show"));
        }

        isTransitioning = false;
      },
      animate ? 280 : 0,
    );
  }

  // Builds the <option> list for the category <select> from
  // window.categories, marking the currently chosen one as selected.
  // Exposed on window so it can be re-called after a new category is
  // added via the "Add Category" modal (see bottom of file).
  function renderCategoryOptions() {
    let html = `<option value="">Select</option>`;

    window.categories.forEach((category) => {
      html += `
            <option value="${category.category_name}"
                ${window.formData.category === category.category_name ? "selected" : ""}>
                ${category.category_name}
            </option>
        `;
    });

    return html;
  }

  window.renderCategoryOptions = renderCategoryOptions;

  // ─── RENDER FUNCTIONS ───
  // Each renderStepN() returns the raw HTML string for that step, built
  // from the current formData so re-entering a step shows previously
  // entered values.

  // STEP 1 - Basic Information (title, subtitle, category, reading time).
  function renderStep1() {
    return `
            <div class="step-content">
                <section class="admin-card">
                    <div class="card-title"><i class="bi bi-info-circle"></i> Basic Information</div>
                    <div class="row g-3">
                        <div class="col-12">
                            <label class="form-label">Title <span class="text-danger">*</span></label>
                            <input type="text" name="title" class="form-control" id="editTitle" placeholder="Enter the title" />
                            <div class="validation-feedback" id="titleFeedback">Please enter a title.</div>
                        </div>
                        <div class="col-12">
                            <label class="form-label">Subtitle <span class="optional text-danger">*</span></label>
                            <input type="text" name="subtitle" class="form-control" id="editSubtitle" placeholder="Enter the subtitle" />
                            <div class="validation-feedback" id="subtitleFeedback">
                                Please enter a subtitle.
                            </div>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Category <span class="text-danger">*</span></label>
                            <button type="button" class=" float-end category-btn" data-bs-toggle="modal" data-bs-target="#categoryModal" >[ + Add Category ]</button>
                            <select class="form-select" name="category_name" id="editCategory">
                                ${renderCategoryOptions()}
                            </select>
                            <div class="validation-feedback" id="categoryFeedback">Please select a category.</div>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Reading Time (min) <span class="text-danger">*</span></label>
                            <input type="number" name="reading_time" class="form-control" id="editReadingTime" value="${formData.readingTime}" min="1" />
                            <div class="validation-feedback" id="readingTimeFeedback">Please enter a valid reading time.</div>
                        </div>
                    </div>
                </section>
                <div class="step-nav">
                    <div class="nav-left"><span class="step-counter"><i class="bi bi-1-circle-fill"></i> Step 1 of 5</span></div>
                    <div class="nav-right"><button class="btn btn-primary" onclick="goToStep(2)">Next <i class="bi bi-arrow-right"></i></button></div>
                </div>
            </div>
        `;
  }

 

  // STEP 2 - Author details + Hero media.
  function renderStep2() {
    return `
            <div class="step-content">
                <section class="admin-card">
                    <div class="card-title"><i class="bi bi-person"></i> Author</div>
                    <div class="row g-3">
                        <div class="col-md-6">
                            <label class="form-label">Name <span class="text-danger">*</span></label>
                            <input type="text" name="author_name" class="form-control" id="editAuthorName" placeholder="Enter name" value="${formData.authorName}" />
                            <div class="validation-feedback" id="authorNameFeedback">Please enter the author's name.</div>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Role <span class="optional">(optional)</span></label>
                            <input type="text" name="author_role" class="form-control" id="editAuthorRole" maxlengh="20" placeholder="e.g. Senior Engineer" value="${formData.authorRole}" />
                            <div class="validation-feedback" id="authorRoleFeedback"></div>
                        </div>
                        <div class="col-12">
                            <label class="form-label">Bio <span class="optional">(optional)</span></label>
                            <textarea class="form-control" name="author_bio" id="editAuthorBio" rows="2" placeholder="Enter Short bio">${formData.authorBio}</textarea>
                            <div class="validation-feedback" id="authorBioFeedback"></div>
                        </div>
                        <div class="col-12">
                            <label class="form-label">Author image <span class="optional">(optional)</span></label>
                            <input type="file" class="form-control" name="author_avatar" id="editAuthorAvatar" value="${formData.authorAvatar}" />
                            <div class="validation-feedback" id="authorImageFeedback"></div>
                            <div id="authorFilePreview" class="small text-success mt-2"></div>
                        </div>
                        <div class="col-12">
                            <label class="form-label">Social Links <span class="optional">(optional)</span></label>
                            <div class="row g-2">
                                <div class="col-md-4">
                                    <input
                                        type="url"
                                        class="form-control"
                                        id="editSocialTwitter"
                                        name="author_twitter"
                                        placeholder="https://x.com/username"
                                        value="${formData.socialTwitter}"
                                    />
                                    <div class="validation-feedback" id="twitterFeedback"></div>
                                </div>

                                <div class="col-md-4">
                                    <input
                                        type="url"
                                        class="form-control"
                                        name="author_linkedin"
                                        id="editSocialLinkedin"
                                        placeholder="https://linkedin.com/in/username"
                                        value="${formData.socialLinkedin}"
                                    />
                                    <div class="validation-feedback" id="linkedinFeedback"></div>
                                </div>

                                <div class="col-md-4">
                                    <input
                                        type="url"
                                        class="form-control"
                                        id="editSocialWebsite"
                                        name="author_website"
                                        placeholder="https://example.com"
                                        value="${formData.socialWebsite}"
                                    />
                                    <div id="authorAvatarPreview" class="mt-2"></div>
                                    <div class="validation-feedback" id="websiteFeedback"></div>
                                </div>
                            </div>
                            <div class="validation-feedback" id="authorImageFeedback"></div>
                        </div>
                    </div>
                </section>
                <section class="admin-card">
                    <div class="card-title"><i class="bi bi-image"></i> Hero Media <span class="text-danger">*</span></div>
                    <div class="row g-3">
                        <div class="col-12" id="heroFields">
                            <label class="form-label">Media File <span class="text-danger">*</span></label>
                            <input type="file" name="hero_media" class="form-control" id="editHeroSrc" accept=".jpg,.jpeg,.png,.webp"/>
                            <div id="heroMediaPreview" class="mt-2"></div>
                            <div id="heroFilePreview" class="small text-success mt-2"></div>
                            <div class="validation-feedback" id="heroSrcFeedback">Please upload a hero image or video.</div>
                        </div>
                        <div class="col-12">
                            <label class="form-label">Caption <span class="optional">(optional)</span></label>
                            <input type="text" name="hero_caption" class="form-control" id="editHeroCaption" placeholder="Caption for hero" value="${formData.heroCaption}" />
                        </div>
                    </div>
                </section>
                <div class="step-nav">
                    <div class="nav-left">
                        <button class="btn btn-outline-secondary" onclick="goToStep(1)"><i class="bi bi-arrow-left"></i> Previous</button>
                        <span class="step-counter"><i class="bi bi-2-circle-fill"></i> Step 2 of 5</span>
                    </div>
                    <div class="nav-right"><button class="btn btn-primary" onclick="goToStep(3)">Next <i class="bi bi-arrow-right"></i></button></div>
                </div>
            </div>
        `;
  }

  // NOTE: kept for parity with the original file, but this function is not
  // currently invoked anywhere (bindStepEvents attaches its own listeners
  // for the hero/author file inputs). Left in place untouched so behavior
  // is 100% unchanged.
  function attachStep2Events() {
    console.log("attachStep2Events called");
    const heroInput = document.getElementById("editHeroSrc");

    if (heroInput) {
      heroInput.addEventListener("change", function () {
        console.log("Hero changed", this.files);

        formData.heroFile = this.files[0] || null;
        formData.heroFileName = this.files[0]?.name || "";
      });
    }

    const authorInput = document.getElementById("editAuthorAvatar");

    if (authorInput) {
      authorInput.addEventListener("change", function () {
        formData.authorAvatar = this.files[0] || null;
        formData.authorAvatarName = this.files[0]?.name || "";
      });
    }
  }

  // STEP 3 - Tags + Content Blocks (the article body).
  function renderStep3() {
    let tagsHtml = "";
    formData.tags.forEach((tag) => {
      tagsHtml += `<span class="tag-item">${tag} <i class="bi bi-x" onclick="removeTag(this)"></i></span>`;
    });

    let blocksHtml = "";
    const iconMap = {
      paragraph: "bi-paragraph",
      heading: "bi-type-h1",
      image: "bi-image",
      "pull-quote": "bi-quote",
      "box-highlight": "bi-star-fill",
      "box-info": "bi-info-circle-fill",
      "box-warning": "bi-exclamation-triangle-fill",
      list: "bi-list-ul",
      table: "bi-table",
      video: "bi-play-circle",
      cta: "bi-megaphone",
      gallery: "bi-images",
    };
    formData.blocks.forEach((block, idx) => {
      const icon = iconMap[block.type] || "bi-file-text";
      const preview = getBlockPreview(block);

      blocksHtml += `
                <div class="block-item"
                    data-type="${block.type}"
                    draggable="true"
                    data-index="${idx}">

                    <span class="block-type-badge">
                        ${block.type.replace("-", " ")}
                    </span>

                    <span class="block-content">
                        ${preview}
                    </span>

                    <span class="block-actions">
                        <button class="btn btn-outline-secondary btn-sm"
                            onclick="editBlock(${idx})">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-sm"
                            onclick="removeBlock(${idx})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </span>
                </div>
            `;
    });

    return `
            <div class="step-content">
                <section class="admin-card">
                    <div class="card-title"><i class="bi bi-tags"></i> Tags <span class="optional">(optional)</span></div>
                    <div class="row g-3">
                        <div class="col-12">
                            <div class="input-group">
                                <input type="text" name="tags" class="form-control" id="tagInput" placeholder="Enter tag (e.g. Design)" />
                                <button class="btn btn-outline-secondary addtag-btn" type="button" onclick="addTag()"><i class="bi bi-plus-lg"></i> Add</button>
                            </div>
                            <div class="tag-group mt-2" id="tagGroup">${tagsHtml}</div>
                        </div>
                    </div>
                </section>
                <section class="admin-card">
                    <div class="card-title"><i class="bi bi-body-text"></i> Article Body — Content Blocks <span class="text-danger">*</span></div>
                    <div class="block-list" id="blockList">${blocksHtml}</div>
                    <div class="add-block-area">
                        <button class="btn-block-type" data-type="paragraph">➕ Paragraph</button>
                        <button class="btn-block-type" data-type="heading">📝 Heading</button>
                        <button class="btn-block-type" data-type="image">🖼️ Image</button>
                        <button class="btn-block-type" data-type="pull-quote">💬 Pull Quote</button>
                        <button class="btn-block-type" data-type="box-highlight">✨ Highlight Box</button>
                        <button class="btn-block-type" data-type="box-info">ℹ️ Info Box</button>
                        <button class="btn-block-type" data-type="box-warning">⚠️ Warning Box</button>
                        <button class="btn-block-type" data-type="list">📋 List</button>
                        <button class="btn-block-type" data-type="table">📊 Table</button>
                        <button class="btn-block-type" data-type="video">🎬 Video</button>
                        <button class="btn-block-type" data-type="cta">🎯 CTA</button>
                        <button class="btn-block-type" data-type="gallery">🖼️ Gallery</button>
                    </div>
                    <div class="form-text mt-2">💡 Drag blocks to reorder. Click <i class="bi bi-pencil"></i> to edit a block.</div>
                    <div class="validation-feedback mt-2" id="blocksFeedback">Please add at least one content block.</div>
                </section>
                <div class="step-nav">
                    <div class="nav-left">
                        <button class="btn btn-outline-secondary" onclick="goToStep(2)"><i class="bi bi-arrow-left"></i> Previous</button>
                        <span class="step-counter"><i class="bi bi-3-circle-fill"></i> Step 3 of 5</span>
                    </div>
                    <div class="nav-right"><button class="btn btn-primary" onclick="goToStep(4)">Next <i class="bi bi-arrow-right"></i></button></div>
                </div>
            </div>
        `;
  }

  // STEP 4 - Related Articles (currently a disabled/placeholder picker --
  // inputs are `disabled` in markup, kept as-is from the original).
  function renderStep4() {
    let relatedHtml = "";
    formData.related.forEach((item, idx) => {
      relatedHtml += `
                <div class="related-item">
                    <span class="related-title">${item.title}</span>
                    <span class="related-meta">
                        ${item.category ? `<span class="related-category">${item.category}</span>` : ""}
                        ${item.date ? `<span class="related-date">${item.date}</span>` : ""}
                        ${item.read ? `<span class="related-read">${item.read} min</span>` : ""}
                        <i class="bi bi-x" onclick="removeRelated(${idx})"></i>
                    </span>
                </div>
            `;
    });

    return `
            <div class="step-content">
                <section class="admin-card">
                    <div class="card-title"><i class="bi bi-link-45deg"></i> Related Articles <span class="optional">(optional)</span></div>
                    <div class="row g-3">
                        <div class="col-12">
                            <div class="input-group ">
                                <input type="text" disabled class="form-control disabled" id="relatedTitleInput" placeholder="Article title" />
                                <input type="text" disabled  class="form-control disabled" id="relatedCategoryInput" placeholder="Category" style="max-width:130px;" />
                                <input type="date" disabled class="form-control disabled" id="relatedDateInput" placeholder="Date" style="max-width:110px;" />
                                <input type="text" disabled class="form-control disabled" id="relatedReadInput" placeholder="Read time" style="max-width:90px;" />
                                <button disabled class="btn btn-outline-secondary readdbtn" type="button" onclick="addRelated()"><i class="bi bi-plus-lg"></i> Add</button>
                            </div>
                            <div class="related-list" id="relatedList">${relatedHtml}</div>
                        </div>
                    </div>
                </section>
                <div class="step-nav">
                    <div class="nav-left">
                        <button class="btn btn-outline-secondary" onclick="goToStep(3)"><i class="bi bi-arrow-left"></i> Previous</button>
                        <span class="step-counter"><i class="bi bi-4-circle-fill"></i> Step 4 of 5</span>
                    </div>
                    <div class="nav-right"><button class="btn btn-primary" onclick="goToStep(5)">Next <i class="bi bi-arrow-right"></i></button></div>
                </div>
            </div>
        `;
  }

  // STEP 5 - Read-only preview of everything entered, plus Save Draft /
  // Publish actions. All the `<span id="preview...">` placeholders are
  // filled in afterwards by updatePreview().
  function renderStep5() {
    return `
            <div class="step-content">
                <section class="admin-card">
                    <div class="card-title"><i class="bi bi-eye"></i> Preview &amp; Publish</div>
                    <p class="text-muted mb-2">Review all your article details below. Click <strong>Edit</strong> on any section to go back and make changes.</p>
                    <div class="preview-grid" id="previewGrid">
                        <div class="preview-card full-width" id="previewBasic">
                            <button class="preview-edit-btn" onclick="goToStep(1)" title="Edit Basic Info"><i class="bi bi-pencil"></i> Edit</button>
                            <div class="preview-label"><i class="bi bi-info-circle"></i> Basic Information</div>
                            <div class="preview-value">
                                <div><strong>Title:</strong> <span id="previewTitle">—</span></div>
                                <div><strong>Subtitle:</strong> <span id="previewSubtitle">—</span></div>
                                <div><strong>Category:</strong> <span id="previewCategory">—</span></div>
                                <div><strong>Reading Time:</strong> <span id="previewReadingTime">—</span> min</div>
                            </div>
                        </div>
                        <div class="preview-card" id="previewAuthor">
                            <button class="preview-edit-btn" onclick="goToStep(2)" title="Edit Author"><i class="bi bi-pencil"></i> Edit</button>
                            <div class="preview-label"><i class="bi bi-person"></i> Author</div>
                            <div class="preview-value">
                                <div><strong>Name:</strong> <span id="previewAuthorName">—</span></div>
                                <div><strong>Role:</strong> <span id="previewAuthorRole">—</span></div>
                                <div><strong>Bio:</strong> <span id="previewAuthorBio">—</span></div>
                                <div><strong>Avatar:</strong> <span id="previewAuthorAvatar">—</span></div>
                                <div><strong>Social:</strong> <span id="previewSocial">—</span></div>
                            </div>
                        </div>
                        <div class="preview-card" id="previewHero">
                            <button class="preview-edit-btn" onclick="goToStep(2)" title="Edit Hero"><i class="bi bi-pencil"></i> Edit</button>
                            <div class="preview-label"><i class="bi bi-image"></i> Hero Media</div>
                            <div class="preview-value">
                                <div><strong>URL:</strong> <span id="previewHeroSrc">—</span></div>
                                <div><strong>Caption:</strong> <span id="previewHeroCaption">—</span></div>
                            </div>
                        </div>
                        <div class="preview-card" id="previewTags">
                            <button class="preview-edit-btn" onclick="goToStep(3)" title="Edit Tags"><i class="bi bi-pencil"></i> Edit</button>
                            <div class="preview-label"><i class="bi bi-tags"></i> Tags</div>
                            <div class="preview-value" id="previewTagsList"><span class="preview-empty">No tags added.</span></div>
                        </div>
                        <div class="preview-card full-width" id="previewBlocks">
                            <button class="preview-edit-btn" onclick="goToStep(3)" title="Edit Content"><i class="bi bi-pencil"></i> Edit</button>
                            <div class="preview-label"><i class="bi bi-body-text"></i> Content Blocks</div>
                            <div class="preview-value" id="previewBlocksList"><span class="preview-empty">No content blocks added.</span></div>
                        </div>
                        <div class="preview-card full-width" id="previewRelated">
                            <button class="preview-edit-btn" onclick="goToStep(4)" title="Edit Related"><i class="bi bi-pencil"></i> Edit</button>
                            <div class="preview-label"><i class="bi bi-link-45deg"></i> Related Articles</div>
                            <div class="preview-value" id="previewRelatedList"><span class="preview-empty">No related articles added.</span></div>
                        </div>
                    </div>
                    <div class="step-nav" style="border-top-color: var(--gray-300);">
                        <div class="nav-left">
                            <button class="btn btn-outline-secondary" onclick="goToStep(4)"><i class="bi bi-arrow-left"></i> Previous</button>
                            <span class="step-counter"><i class="bi bi-5-circle-fill"></i> Step 5 of 5</span>
                        </div>
                        <div class="nav-right">
                            <button class="btn btn-outline-secondary" onclick="saveDraft()"><i class="bi bi-file-earmark-check"></i> Save Draft</button>
                            <button class="btn btn-primary" id="publishBtn" onclick="publishArticle()"><i class="bi bi-cloud-upload"></i> Publish News</button>
                        </div>
                    </div>
                </section>
            </div>
        `;
  }

  // ─── BIND STEP EVENTS ───
  // Because renderStep() replaces the DOM every time, listeners must be
  // re-attached after each render. This function does that for whichever
  // step was just drawn -- live validation on input/blur, keeping
  // formData in sync (saveFormData), and the Publish button's
  // enabled/disabled state.
  function bindStepEvents(step) {
    if (step === 1) {
      const title = document.getElementById("editTitle");
      if (title) {
        title.addEventListener("input", function () {
          validateTitle();
          saveFormData();
          updatePublishButtonState();
        });
        title.addEventListener("blur", validateTitle);
      }

      const category = document.getElementById("editCategory");
      if (category) {
        category.addEventListener("change", function () {
          validateCategory();
          saveFormData();
          updatePublishButtonState();
        });
        category.addEventListener("blur", validateCategory);
      }

      const readingTime = document.getElementById("editReadingTime");
      if (readingTime) {
        readingTime.addEventListener("input", function () {
          validateReadingTime();
          saveFormData();
          updatePublishButtonState();
        });
        readingTime.addEventListener("blur", validateReadingTime);
      }

      const subtitle = document.getElementById("editSubtitle");
      if (subtitle) {
        subtitle.addEventListener("input", function () {
          validateSubtitle();
          saveFormData();
          updatePublishButtonState();
        });

        subtitle.addEventListener("blur", validateSubtitle);
      }
      const updated = document.getElementById("editUpdated");
      if (updated) {
        updated.addEventListener("input", saveFormData);
        updated.addEventListener("change", saveFormData);
      }
    }

    if (step === 2) {
      const authorName = document.getElementById("editAuthorName");
      if (authorName) {
        authorName.addEventListener("input", function () {
          validateAuthorName();
          saveFormData();
          updatePublishButtonState();
        });
        authorName.addEventListener("blur", validateAuthorName);
      }

      const authorRole = document.getElementById("editAuthorRole");
      if (authorRole) {
        authorRole.addEventListener("input", function () {
          validateAuthorRole();
          saveFormData();
          updatePublishButtonState();
        });
        authorRole.addEventListener("blur", validateAuthorRole);
      }

      const authorBio = document.getElementById("editAuthorBio");
      if (authorBio) {
        authorBio.addEventListener("input", function () {
          validateAuthorBio();
          saveFormData();
          updatePublishButtonState();
        });
        authorBio.addEventListener("blur", validateAuthorBio);
      }

      const authorImage = document.getElementById("editAuthorAvatar");
      if (authorImage) {
        authorImage.addEventListener("change", function () {
          validateAuthorImage();

          if (this.files.length) {
            formData.authorAvatar = this.files[0];
            formData.authorAvatarName = this.files[0].name;
          }
          saveFormData();
          updatePublishButtonState();
        });
        authorImage.addEventListener("blur", validateAuthorImage);
      }

      document
        .getElementById("editSocialTwitter")
        ?.addEventListener("input", () => {
          validateSocialLink("editSocialTwitter", "twitterFeedback", "twitter");
        });

      document
        .getElementById("editSocialLinkedin")
        ?.addEventListener("input", () => {
          validateSocialLink(
            "editSocialLinkedin",
            "linkedinFeedback",
            "linkedin",
          );
        });

      document
        .getElementById("editSocialWebsite")
        ?.addEventListener("input", () => {
          validateSocialLink("editSocialWebsite", "websiteFeedback", "website");
        });

      // Hero file: validate immediately on change, and if invalid, reset
      // the stored file so a rejected upload can't sneak through later.
      document
        .getElementById("editHeroSrc")
        ?.addEventListener("change", function () {
          if (!validateMediaFile()) {
            formData.heroFile = null;
            formData.heroFileName = "";

            renderHeroPreview();

            return;
          }

          formData.heroFile = this.files[0];
          formData.heroFileName = this.files[0].name;

          renderHeroPreview();

          saveFormData();
        });

      // Remaining step-2 fields only need to sync formData on change,
      // they don't have their own dedicated validators here.
      const fields = [
        "editAuthorRole",
        "editAuthorBio",
        "editAuthorAvatar",
        "editSocialTwitter",
        "editSocialLinkedin",
        "editSocialWebsite",
        "editHeroCaption",
      ];
      fields.forEach((id) => {
        const el = document.getElementById(id);
        if (el) {
          el.addEventListener("input", saveFormData);
          el.addEventListener("change", saveFormData);
        }
      });
    }

    const authorPreview = document.getElementById("authorFilePreview");

    if (authorPreview && formData.authorAvatarName) {
      authorPreview.innerHTML = `<i class="bi bi-check-circle-fill"></i>
            ${formData.authorAvatarName}`;
    }

    if (step === 3) {
      // Clicking a "+ Block type" button appends a new block of that type
      // (with sensible empty defaults) to formData.blocks, re-renders the
      // step so it shows up in the list, then immediately opens the edit
      // modal for it so the user fills it in right away.
      document.querySelectorAll(".btn-block-type").forEach((btn) => {
        btn.addEventListener("click", function () {
          const type = this.dataset.type;

          let block = {};

          switch (type) {
            case "paragraph":
              block = { type: "paragraph", content: "" };
              break;

            case "heading":
              block = { type: "heading", text: "", level: "h2" };
              break;

            case "image":
              block = {
                type: "image",
                file: null,
                fileName: "",
                caption: "",
                alt: "",
                alignment: "center",
              };
              break;

            case "video":
              block = {
                type: "video",
                sourceType: "file",
                file: null,
                fileName: "",
                embedUrl: "",
                caption: "",
              };
              break;

            case "pull-quote":
              block = { type: "pull-quote", quote: "", author: "" };
              break;

            case "box-highlight":
              block = { type: "box-highlight", title: "", content: "" };
              break;

            case "box-info":
              block = { type: "box-info", title: "", content: "" };
              break;

            case "box-warning":
              block = { type: "box-warning", title: "", content: "" };
              break;

            case "list":
              block = { type: "list", items: [] };
              break;

            case "table":
              block = { type: "table", rows: 2, columns: 2, data: [] };
              break;

            case "gallery":
              block = { type: "gallery", images: [] };
              break;

            case "cta":
              block = {
                type: "cta",
                title: "",
                buttonText: "",
                buttonLink: "",
              };
              break;

            default:
              block = { type: type };
          }

          formData.blocks.push(block);

          renderStep(3, true);

          setTimeout(() => {
            const idx = formData.blocks.length - 1;

            editBlock(idx);

            validateBlocks();

            updatePublishButtonState();
          }, 100);
        });
      });

      // Enter key inside the tag input adds the tag instead of submitting
      // anything.
      const tagInput = document.getElementById("tagInput");
      if (tagInput) {
        tagInput.addEventListener("keydown", function (e) {
          if (e.key === "Enter") {
            e.preventDefault();
            addTag();
          }
        });
      }

      // Drag-and-drop reordering of content blocks.
      const blockList = document.getElementById("blockList");
      if (blockList) {
        blockList.addEventListener("dragstart", function (e) {
          if (e.target.classList.contains("block-item")) {
            e.dataTransfer.setData("text/plain", e.target.dataset.index || "0");
          }
        });
        blockList.addEventListener("dragover", function (e) {
          e.preventDefault();
        });
        blockList.addEventListener("drop", function (e) {
          e.preventDefault();
          const fromIdx = parseInt(e.dataTransfer.getData("text/plain"));
          const toItem = e.target.closest(".block-item");
          if (!toItem) return;
          const toIdx = parseInt(toItem.dataset.index);
          if (fromIdx === toIdx) return;
          const [moved] = formData.blocks.splice(fromIdx, 1);
          formData.blocks.splice(toIdx, 0, moved);
          renderStep(3, true);
          validateBlocks();
          updatePublishButtonState();
        });
      }

      // Re-validate/re-check the Publish button whenever the user
      // interacts with the block list area at all (e.g. after
      // edit/remove button clicks bubble up here).
      const blockArea = document.getElementById("blockList");
      if (blockArea) {
        blockArea.addEventListener("click", function () {
          validateBlocks();
          updatePublishButtonState();
        });
      }

      saveFormData();
      validateBlocks();
      updatePublishButtonState();
    }

    if (step === 4) {
      const input = document.getElementById("relatedTitleInput");
      if (input) {
        input.addEventListener("keydown", function (e) {
          if (e.key === "Enter") {
            e.preventDefault();
            addRelated();
          }
        });
      }
      const relatedFields = [
        "relatedCategoryInput",
        "relatedDateInput",
        "relatedReadInput",
      ];
      relatedFields.forEach((id) => {
        const el = document.getElementById(id);
        if (el) {
          el.addEventListener("input", saveFormData);
          el.addEventListener("change", saveFormData);
        }
      });
    }

    if (step === 5) {
      updatePreview();
      updatePublishButtonState();
    }
  }

  // ─── SAVE FORM DATA ───
  // Pulls current values out of whatever step is on screen and writes them
  // back into formData, so nothing is lost when the user navigates away
  // (each field is guarded with `if (el)` since only one step's fields
  // exist in the DOM at any given time).
  function saveFormData() {
    const title = document.getElementById("editTitle");
    if (title) formData.title = title.value;
    const subtitle = document.getElementById("editSubtitle");
    if (subtitle) formData.subtitle = subtitle.value;
    const cat = document.getElementById("editCategory");
    if (cat) formData.category = cat.value;
    const rt = document.getElementById("editReadingTime");
    if (rt) formData.readingTime = rt.value;

    const name = document.getElementById("editAuthorName");
    if (name) formData.authorName = name.value;
    const role = document.getElementById("editAuthorRole");
    if (role) formData.authorRole = role.value;
    const bio = document.getElementById("editAuthorBio");
    if (bio) formData.authorBio = bio.value;
    const tw = document.getElementById("editSocialTwitter");
    if (tw) formData.socialTwitter = tw.value;
    const li = document.getElementById("editSocialLinkedin");
    if (li) formData.socialLinkedin = li.value;
    const web = document.getElementById("editSocialWebsite");
    if (web) formData.socialWebsite = web.value;
    const caption = document.getElementById("editHeroCaption");
    if (caption) formData.heroCaption = caption.value;

    const hero = document.getElementById("editHeroSrc");

    if (hero && hero.files.length) {
      formData.heroFile = hero.files[0];
      formData.heroFileName = hero.files[0].name;
    }

    // Tags live as rendered <span> chips in the DOM; rebuild the array
    // from whatever chips are currently present (handles removals too).
    const tagGroup = document.getElementById("tagGroup");
    if (tagGroup) {
      formData.tags = [];
      tagGroup.querySelectorAll(".tag-item").forEach((item) => {
        const text = item.textContent.trim();
        if (text) formData.tags.push(text);
      });
    }

    // Same idea for related-article entries.
    const relatedList = document.getElementById("relatedList");
    if (relatedList) {
      const items = relatedList.querySelectorAll(".related-item");
      formData.related = [];
      items.forEach((item) => {
        const titleEl = item.querySelector(".related-title");
        const catEl = item.querySelector(".related-category");
        const dateEl = item.querySelector(".related-date");
        const readEl = item.querySelector(".related-read");
        formData.related.push({
          title: titleEl?.textContent?.trim() || "",
          category: catEl?.textContent?.trim() || "",
          date: dateEl?.textContent?.trim() || "",
          read: readEl?.textContent?.trim() || "",
        });
      });
    }
  }

  // ─── NAVIGATION ───
  // Central gatekeeper for moving between steps: blocks forward movement
  // on validation failure, requires the whole form to be valid before
  // jumping to the Preview step, and always saves formData + re-renders
  // on success.
  window.goToStep = function (step) {
    if (isTransitioning) return;
    if (step < 1 || step > totalSteps) return;

    // Going forward: validate the step being left.
    if (step > currentStep) {
      if (!validateStep(currentStep)) {
        // Scroll to first error
        const firstError = document.querySelector(".is-invalid-custom");
        if (firstError) {
          firstError.scrollIntoView({ behavior: "smooth", block: "center" });
          firstError.focus();
        }
        return;
      }
    }

    // Going to step 5 for the first time: the whole form must be complete.
    if (step === 5 && currentStep < 5) {
      const result = validateFormData();

      if (result !== true) {
        Swal.fire({
          icon: "warning",
          title: "Missing Required Field",
          html: `<b>${result.field}</b> is required before preview.`,
          confirmButtonColor: "#c5050c",
        }).then(() => {
          goToStep(result.step);
        });

        return;
      }
    }

    saveFormData();
    renderStep(step, true);

    if (step === 5) {
      setTimeout(() => {
        updatePreview();
        updatePublishButtonState();
        updateTemplateButton();
      }, 100);
    }
  };

  // ─── PREVIEW ───

  // Returns a short, human-readable summary of a block's content, used
  // both in the step-3 block list and the step-5 final preview.
  function getBlockPreview(block) {
    switch (block.type) {
      case "paragraph":
        return block.content || "(Empty Paragraph)";

      case "heading":
        return `${(block.level || "h2").toUpperCase()} : ${block.text || "(Empty Heading)"}`;

      case "image":
        return block.fileName || "(No Image Selected)";

      case "video":
        if (block.sourceType === "embed") {
          return block.embedUrl || "(No Embed URL)";
        }

        return block.fileName || "(No Video Selected)";

      case "pull-quote":
        return block.quote || "(Empty Quote)";

      case "box-highlight":
        return block.title || "(Highlight Box)";

      case "box-info":
        return block.title || "(Info Box)";

      case "box-warning":
        return block.title || "(Warning Box)";

      case "list":
        return `${block.items?.length || 0} Item(s)`;

      case "table":
        return `${block.rows || 0} Rows × ${block.columns || 0} Columns`;

      case "gallery":
        return `${block.images?.length || 0} Image(s)`;

      default:
        return "(Empty)";
    }
  }

  // Fills in every placeholder on the Step 5 preview from formData / the
  // live hero file input. Bails out early if the preview markup isn't on
  // screen (e.g. called before step 5 has rendered).
  function updatePreview() {
    if (!document.getElementById("previewTitle")) {
      return;
    }

    function setPreviewText(id, value) {
      const el = document.getElementById(id);

      if (el) {
        el.textContent = value;
      }
    }

    setPreviewText("previewTitle", formData.title || "—");
    setPreviewText("previewSubtitle", formData.subtitle || "—");
    setPreviewText("previewCategory", formData.category || "—");
    setPreviewText("previewReadingTime", formData.readingTime || "—");

    setPreviewText("previewAuthorName", formData.authorName || "—");
    setPreviewText("previewAuthorRole", formData.authorRole || "—");
    setPreviewText("previewAuthorBio", formData.authorBio || "—");
    setPreviewText("previewAuthorAvatar", formData.authorAvatarName || "—");

    const parts = [];
    if (formData.socialTwitter)
      parts.push("Twitter: " + formData.socialTwitter);
    if (formData.socialLinkedin)
      parts.push("LinkedIn: " + formData.socialLinkedin);
    if (formData.socialWebsite)
      parts.push("Website: " + formData.socialWebsite);
    setPreviewText("previewSocial", parts.length ? parts.join(" | ") : "—");

    const heroSrc = document.getElementById("editHeroSrc");
    document.getElementById("previewHeroSrc").textContent =
      heroSrc && heroSrc.files && heroSrc.files.length > 0
        ? Array.from(heroSrc.files)
            .map((f) => f.name)
            .join(", ")
        : "—";
    setPreviewText("previewHeroCaption", formData.heroCaption || "—");

    const tagsContainer = document.getElementById("previewTagsList");
    if (formData.tags.length === 0) {
      tagsContainer.innerHTML =
        '<span class="preview-empty">No tags added.</span>';
    } else {
      let html = "";
      formData.tags.forEach((tag) => {
        html += `<span class="tag-pill">${tag}</span>`;
      });
      tagsContainer.innerHTML = html;
    }

    const blocksContainer = document.getElementById("previewBlocksList");
    if (formData.blocks.length === 0) {
      blocksContainer.innerHTML =
        '<span class="preview-empty">No content blocks added.</span>';
    } else {
      let html = "";
      const iconMap = {
        paragraph: "bi-paragraph",
        heading: "bi-type-h1",
        image: "bi-image",
        "pull-quote": "bi-quote",
        "box-highlight": "bi-star-fill",
        "box-info": "bi-info-circle-fill",
        "box-warning": "bi-exclamation-triangle-fill",
        list: "bi-list-ul",
        table: "bi-table",
        video: "bi-play-circle",
        cta: "bi-megaphone",
        gallery: "bi-images",
      };
      formData.blocks.forEach((block) => {
        const icon = iconMap[block.type] || "bi-file-text";
        const label = block.type
          .replace("-", " ")
          .replace(/\b\w/g, (l) => l.toUpperCase());
        const previewText = getBlockPreview(block);
        html += `
                <div class="block-preview">
                    <i class="bi ${icon}"></i>
                    <strong>${label}:</strong>
                    ${previewText}
                </div>`;
      });
      blocksContainer.innerHTML = html;
    }

    const relatedContainer = document.getElementById("previewRelatedList");
    if (formData.related.length === 0) {
      relatedContainer.innerHTML =
        '<span class="preview-empty">No related articles added.</span>';
    } else {
      let html = "";
      formData.related.forEach((item) => {
        let parts = [item.title || "(untitled)"];
        if (item.category) parts.push(`Category: ${item.category}`);
        if (item.date) parts.push(`Date: ${item.date}`);
        if (item.read) parts.push(`Read: ${item.read} min`);
        html += `<div class="block-preview"><i class="bi bi-link-45deg"></i> ${parts.join(" | ")}</div>`;
      });
      relatedContainer.innerHTML = html;
    }
  }

  // ─── PUBLISH BUTTON STATE ───
  // Simple heuristic: as long as no field is currently showing an
  // "invalid" state, allow Publish to be clicked. Real validation of
  // completeness happens separately in validateFormData() when Publish
  // is actually pressed.
  function updatePublishButtonState() {
    const btn = document.getElementById("publishBtn");
    if (!btn) return;

    const hasError = document.querySelector(".is-invalid-custom") !== null;
    if (hasError) {
      btn.classList.add("btn-publish-disabled");
      btn.classList.remove("btn-publish-ready");
      btn.disabled = true;
    } else {
      btn.classList.remove("btn-publish-disabled");
      btn.classList.add("btn-publish-ready");
      btn.disabled = false;
    }
  }

  // ─── TAG FUNCTIONS ───
  window.addTag = function () {
    const input = document.getElementById("tagInput");
    if (!input) return;
    const val = input.value.trim();
    if (!val) return;
    if (!formData.tags.includes(val)) {
      formData.tags.push(val);
      renderStep(3, true);
      updatePublishButtonState();
    }
    input.value = "";
  };

  window.removeTag = function (el) {
    const parent = el.closest(".tag-item");
    if (parent) {
      const text = parent.textContent.trim();
      const idx = formData.tags.indexOf(text);
      if (idx > -1) formData.tags.splice(idx, 1);
      parent.remove();
    }
  };

  // ─── BLOCK FUNCTIONS ───
  // Opens the shared "block editor" modal, building its inner form to
  // match whichever block type is being edited, then wires up that
  // form's own live validation/preview behavior.
  window.editBlock = function (index) {
    if (index < 0 || index >= formData.blocks.length) return;
    const block = formData.blocks[index];
    blockEditIndex = index;
    const modalBody = document.getElementById("blockModalBody");
    if (!modalBody) return;
    switch (block.type) {
      case "paragraph":
        modalBody.innerHTML = `
                    <div class="mb-3">
                        <label class="form-label">Paragraph</label>
                        <textarea class="form-control"
                            id="blockParagraphContent"
                            rows="8"
                            placeholder="Write your paragraph here...">${block.content || ""}</textarea>
                            <small
                              id="blockParagraphContentError"
                              class="text-danger">
                          </small>
                            <small class=" text-muted">*If you want another paragraph, use fresh paragraph block</small>
                    </div>
                `;
        break;

      case "heading":
        modalBody.innerHTML = `
                    <div class="mb-3">
                        <label class="form-label">Heading</label>
                        <input
                            type="text"
                            class="form-control"
                            id="blockHeadingText"
                            value="${block.text || ""}"
                            placeholder="Enter heading">
                            <small id="blockHeadingTextError" class="text-danger"></small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Heading Level</label>
                        <select class="form-select" id="blockHeadingLevel">
                            <option value="h1" ${block.level == "h1" ? "selected" : ""}>Large</option>
                            <option value="h2" ${block.level == "h2" ? "selected" : ""}>Medium</option>
                            <option value="h3" ${block.level == "h3" ? "selected" : ""}>Small</option></option>
                        </select>
                    </div>
                `;
        break;

      case "image":
        modalBody.innerHTML = `
                    <div class="mb-3">
                        <label class="form-label">Image</label>
                        <input
                            type="file"
                            class="form-control"
                            id="blockImageFile"
                            accept=".jpg,.jpeg,.png,.webp">
                            <div id="existingBlockImagePreview" class="mt-3"></div>
                            <small id="blockImageFileError" class="text-danger"></small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Caption</label>
                        <input
                            type="text"
                            class="form-control"
                            id="blockImageCaption"
                            value="${block.caption || ""}">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Alt Text</label>
                        <input
                            type="text"
                            class="form-control"
                            id="blockImageAlt"
                            value="${block.alt || ""}">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Image Alignment</label>
                        <select class="form-select" id="imageAlignment">
                            <option value="center" ${block.alignment === "center" ? "selected" : ""}>Center</option>
                            <option value="left" ${block.alignment === "left" ? "selected" : ""}>Left</option>
                            <option value="right" ${block.alignment === "right" ? "selected" : ""}>Right</option>
                        </select>
                    </div>
                `;
        break;

      case "video":
        modalBody.innerHTML = `
                        <div class="mb-3">
                            <label class="form-label">Video Source</label>
                            <select class="form-select" id="videoSourceType">
                                <option value="file" ${!block.embedUrl ? "selected" : ""}>Upload Video</option>
                                <option value="embed" ${block.embedUrl ? "selected" : ""}>YouTube / Vimeo</option>
                            </select>
                        </div>

                        <div class="mb-3" id="videoFileWrapper">
                            <label class="form-label">Video File</label>
                            <input
                                type="file"
                                class="form-control"
                                id="blockVideoFile"
                                accept=".mp4,.webm,.ogg">
                                <div class="text-danger small mt-1" id="blockVideoFileError"></div>
                            <div id="existingVideoPreview" class="mt-2"></div>
                        </div>

                        <div class="mb-3 d-none" id="videoEmbedWrapper">
                            <label class="form-label">YouTube / Vimeo URL</label>
                            <input
                                type="url"
                                class="form-control"
                                id="blockVideoEmbed"
                                value="${block.embedUrl || ""}"
                                placeholder="https://www.youtube.com/embed/...">
                                <div class="text-danger small mt-1" id="blockVideoEmbedError"></div>
                        </div>

                        <div class="mb-3">
                            <label class="form-label">Caption</label>
                            <input
                                type="text"
                                class="form-control"
                                id="blockVideoCaption"
                                value="${block.caption || ""}"
                                placeholder="Enter caption">
                                <div class="text-danger small mt-1" id="blockVideoCaptionError"></div>
                        </div>
                    `;
        break;

      case "pull-quote":
        modalBody.innerHTML = `
                    <div class="mb-3">
                        <label class="form-label">Quote</label>
                        <textarea
                            class="form-control"
                            id="blockQuote"
                            rows="5"
                            placeholder="Enter the quote...">${block.quote || ""}</textarea>
                            <small id="blockQuoteError" class="text-danger"></small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">
                            Author
                            <span class="optional">(Optional)</span>
                        </label>
                        <input
                            type="text"
                            class="form-control"
                            id="blockQuoteAuthor"
                            value="${block.author || ""}"
                            placeholder="Author Name">
                            <small
                                id="blockQuoteAuthorError"
                                class="text-danger">
                            </small>
                    </div>
                `;
        break;

      case "box-highlight":
        modalBody.innerHTML = `
                        <div class="mb-3">
                            <label class="form-label">Title</label>
                            <input
                                type="text"
                                class="form-control"
                                id="blockHighlightTitle"
                                value="${block.title || ""}"
                                placeholder="Enter title">
                                <small id="blockHighlightTitleError" class="text-danger"></small>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Content</label>
                            <textarea
                                class="form-control"
                                id="blockHighlightContent"
                                rows="5"
                                placeholder="Enter content...">${block.content || ""}</textarea>
                                <small id="blockHighlightContentError" class="text-danger"></small>
                        </div>
                    `;
        break;

      case "box-info":
        modalBody.innerHTML = `
                        <div class="mb-3">
                            <label class="form-label">Title</label>
                            <input
                                type="text"
                                class="form-control"
                                id="blockInfoTitle"
                                value="${block.title || ""}"
                                placeholder="Enter title">
                                <small id="blockInfoTitleError" class="text-danger"></small>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Content</label>
                            <textarea
                                class="form-control"
                                id="blockInfoContent"
                                rows="5"
                                placeholder="Enter content...">${block.content || ""}</textarea>
                                <small id="blockInfoContentError" class="text-danger"></small>
                        </div>
                    `;
        break;

      case "box-warning":
        modalBody.innerHTML = `
                        <div class="mb-3">
                            <label class="form-label">Title</label>
                            <input
                                type="text"
                                class="form-control"
                                id="blockWarningTitle"
                                value="${block.title || ""}"
                                placeholder="Enter title">
                                <small id="blockWarningTitleError" class="text-danger"></small>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Content</label>
                            <textarea
                                class="form-control"
                                id="blockWarningContent"
                                rows="5"
                                placeholder="Enter content...">${block.content || ""}</textarea>
                                <small id="blockWarningContentError" class="text-danger"></small>
                        </div>
                    `;
        break;

      case "list":
        modalBody.innerHTML = `
                        <div class="mb-3">
                            <label class="form-label">
                                List Items
                            </label>
                            <textarea
                                class="form-control"
                                id="blockListItems"
                                rows="8"
                                placeholder="One item per line">${block.items.join("\n")}</textarea>
                                <small id="blockListItemsError" class="text-danger"></small>
                            <small class="text-muted">
                                Enter one item per line.
                            </small>
                        </div>
                    `;
        break;

      case "table":
        modalBody.innerHTML = `
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Rows</label>
                                <input
                                    type="number"
                                    class="form-control"
                                    id="blockTableRows"
                                    value="${block.rows}"
                                    min="1"
                                    max="20">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Columns</label>
                                <input
                                    type="number"
                                    class="form-control"
                                    id="blockTableColumns"
                                    value="${block.columns}"
                                    min="1"
                                    max="10">
                            </div>
                        </div>
                        <button
                            class="btn btn-primary btn-sm mb-3"
                            type="button"
                            onclick="generateTableEditor()">
                            Generate Table
                        </button>
                        <div id="tableEditor"></div>
                        <small id="blockTableError" class="text-danger"></small>
                    `;

        // Draw the initial rows/columns grid using the block's current
        // dimensions as soon as the modal body is in the DOM.
        setTimeout(() => generateTableEditor(), 100);
        break;

      case "gallery":
        modalBody.innerHTML = `
                        <div class="mb-3">
                            <label class="form-label">Gallery Images</label>
                            <input
                            type="file"
                            class="form-control"
                            id="blockGalleryImages"
                            accept="image/*"
                            multiple>
                            <small
                                id="blockGalleryImagesError"
                                class="text-danger">
                            </small>
                        <div
                            id="galleryPreviewGrid"
                            class="row g-2 mt-3">
                        </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Gallery Caption</label>
                            <input
                                type="text"
                                class="form-control"
                                id="blockGalleryCaption"
                                value="${block.caption || ""}"
                                placeholder="Enter gallery caption">
                        </div>
                    `;
        break;

      default:
        modalBody.innerHTML = `
                    <div class="alert alert-warning">
                        ${block.type} editor is coming soon.
                    </div>
                `;
    }
    document.getElementById("blockModalLabel").textContent =
      `Edit ${block.type.replace("-", " ")} Block`;
    const modal = new bootstrap.Modal(document.getElementById("blockModal"));

    const modalElement = document.getElementById("blockModal");

    // If the user dismisses the modal without saving, drop the block if
    // it was left completely empty (so clicking a block-type button and
    // then closing without filling anything in doesn't leave clutter).
    modalElement.addEventListener(
      "hidden.bs.modal",
      function () {
        removeEmptyCurrentBlock();
      },
      { once: true },
    );

    setTimeout(() => {
      // Video Source Toggle: switch between "upload a file" and
      // "paste an embed URL" sub-forms.
      const sourceType = document.getElementById("videoSourceType");
      const fileWrapper = document.getElementById("videoFileWrapper");
      const embedWrapper = document.getElementById("videoEmbedWrapper");

      if (sourceType) {
        function toggleVideoSource() {
          if (sourceType.value === "file") {
            fileWrapper.classList.remove("d-none");
            embedWrapper.classList.add("d-none");
          } else {
            fileWrapper.classList.add("d-none");
            embedWrapper.classList.remove("d-none");
          }
        }

        toggleVideoSource();
        sourceType.addEventListener("change", toggleVideoSource);
      }

      // Image Validation: reject disallowed file types as soon as chosen.
      const imageInput = document.getElementById("blockImageFile");

      if (imageInput) {
        imageInput.addEventListener("change", function () {
          const error = document.getElementById("blockImageFileError");

          error.textContent = "";

          if (!this.files.length) return;

          const file = this.files[0];

          const allowedTypes = ["image/jpeg", "image/png", "image/webp"];

          if (!allowedTypes.includes(file.type)) {
            error.textContent = "Only JPG, PNG and WEBP images are allowed.";

            this.value = "";
          }
        });
      }

      // Video Validation: file type, embed URL pattern, and caption
      // length, all validated live as the user types/selects.
      const fileInput = document.getElementById("blockVideoFile");
      const embedInput = document.getElementById("blockVideoEmbed");
      const captionInput = document.getElementById("blockVideoCaption");

      const fileError = document.getElementById("blockVideoFileError");
      const embedError = document.getElementById("blockVideoEmbedError");
      const captionError = document.getElementById("blockVideoCaptionError");

      if (fileInput) {
        fileInput.addEventListener("change", function () {
          fileError.textContent = "";

          if (!this.files.length) return;

          const file = this.files[0];

          const allowedTypes = ["video/mp4", "video/webm", "video/ogg"];

          if (!allowedTypes.includes(file.type)) {
            fileError.textContent =
              "Only MP4, WebM and OGG videos are allowed.";

            this.value = "";
          }
        });
      }

      if (embedInput) {
        embedInput.addEventListener("input", function () {
          embedError.textContent = "";

          if (sourceType.value !== "embed") return;

          const value = this.value.trim();

          if (value.length === 0) return;

          const regex =
            /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|vimeo\.com)/i;

          if (!regex.test(value)) {
            embedError.textContent = "Enter a valid YouTube or Vimeo URL.";
          }
        });
      }

      if (captionInput) {
        captionInput.addEventListener("input", function () {
          captionError.textContent = "";

          const value = this.value.trim();

          if (value.length === 0) return;

          if (value.length < 3) {
            captionError.textContent = "Caption must be at least 3 characters.";

            return;
          }

          if (value.length > 100) {
            captionError.textContent = "Caption cannot exceed 100 characters.";

            return;
          }
        });
      }

      // Quote Author Validation: letters/spaces only.
      const quoteAuthor = document.getElementById("blockQuoteAuthor");

      if (quoteAuthor) {
        quoteAuthor.addEventListener("input", function () {
          const error = document.getElementById("blockQuoteAuthorError");

          const value = this.value;

          error.textContent = "";

          if (value.length === 0) {
            return;
          }

          if (!/^[A-Za-z ]+$/.test(value)) {
            error.textContent =
              "Author name can contain only letters and spaces.";
          }
        });
      }
    }, 0);

    // IMAGE EDIT PREVIEW - shows the image already saved on this block
    // (edit mode) before a new one is chosen.
    if (block.type === "image" && block.existingFile) {
      document.getElementById("existingBlockImagePreview").innerHTML = `
        <div class="mb-2">
            <img
                src="${block.existingFile}"
                class="img-thumbnail"
                style="max-width:220px;">
        </div>
        <div class="small text-success">
            Current Image :
            ${block.fileName}
        </div>
    `;
    }

    // VIDEO EDIT PREVIEW - same idea for an existing saved video.
    if (block.type === "video" && block.existingFile) {
      document.getElementById("existingVideoPreview").innerHTML = `
        <video
            controls
            style="max-width:250px;"
            class="mt-2">
            <source
                src="${block.existingFile}">
        </video>
        <div class="small text-success mt-2">
            Current Video :
            ${block.fileName}
        </div>
    `;
    }

    modal.show();
    const galleryInput = document.getElementById("blockGalleryImages");

    if (galleryInput) {
      console.log("Gallery Block:", block);
      renderGalleryPreview(block);

      galleryInput.addEventListener("change", function () {
        const galleryError = document.getElementById("blockGalleryImagesError");

        galleryError.textContent = "";

        if (!this.files.length) return;

        const allowedTypes = ["image/jpeg", "image/png", "image/webp"];

        for (const file of this.files) {
          if (!allowedTypes.includes(file.type)) {
            galleryError.textContent =
              "Only JPG, PNG and WEBP images are allowed.";

            this.value = "";

            return;
          }
        }

        block.images.push(...Array.from(this.files));

        this.value = "";

        renderGalleryPreview(block);
      });
    }
  };

  // Renders the thumbnail grid inside the gallery block editor: existing
  // (already-saved) images first, then any newly-added ones in this
  // session, each with its own Remove button.
  function renderGalleryPreview(block) {
    const grid = document.getElementById("galleryPreviewGrid");

    if (!grid) return;

    grid.innerHTML = "";

    // EXISTING GALLERY IMAGES HANDLING
    if (block.existingGallery) {
      block.existingGallery.forEach((image, index) => {
        grid.innerHTML += `
            <div class="col-md-3 existing-gallery-item">
                <div class="card">
                    <img
                        src="${image.url}"
                        class="card-img-top"
                        style="height:120px;object-fit:cover;">
                    <div class="card-body p-2 text-center">
                        <button
                            type="button"
                            class="btn btn-danger btn-sm"
                            onclick="removeExistingGalleryImage(${index})">
                            Remove
                        </button>
                    </div>
                </div>
            </div>
        `;
      });
    }

    (block.images || []).forEach((file, index) => {
      const url = URL.createObjectURL(file);

      grid.innerHTML += `
            <div class="col-md-3">
                <div class="card">
                    <img
                        src="${url}"
                        class="card-img-top"
                        style="height:120px;object-fit:cover;">
                    <div class="card-body p-2 text-center">
                        <button
                            class="btn btn-danger btn-sm"
                            onclick="removeGalleryImage(${index})">
                            Remove
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
  }

  // Remove an already-saved gallery image (edit mode).
  window.removeExistingGalleryImage = function (index) {
    if (blockEditIndex < 0) return;

    const block = formData.blocks[blockEditIndex];

    if (!block.existingGallery) return;

    block.existingGallery.splice(index, 1);

    renderGalleryPreview(block);
  };

  // Remove a newly-added (not-yet-saved) gallery image.
  window.removeGalleryImage = function (index) {
    if (blockEditIndex < 0) return;

    const block = formData.blocks[blockEditIndex];

    block.images.splice(index, 1);

    renderGalleryPreview(block);
  };

  // The following three validators (video file / embed / caption) mirror
  // the live-input checks wired up above, but are also called explicitly
  // from removeEmptyCurrentBlock() / save-block logic where needed.
  function validateVideoFile() {
    const sourceType = document.getElementById("videoSourceType");

    if (!sourceType || sourceType.value !== "file") {
      return true;
    }

    const input = document.getElementById("blockVideoFile");
    const error = document.getElementById("blockVideoFileError");

    error.textContent = "";

    if (!input.files.length && !formData.blocks[blockEditIndex]?.fileName) {
      error.textContent = "Please select a video.";
      return false;
    }

    if (input.files.length) {
      const file = input.files[0];

      const allowedTypes = ["video/mp4", "video/webm", "video/ogg"];

      if (!allowedTypes.includes(file.type)) {
        error.textContent = "Only MP4, WebM and OGG videos are allowed.";
        return false;
      }
    }

    return true;
  }

  function validateEmbed() {
    const sourceType = document.getElementById("videoSourceType");

    if (!sourceType || sourceType.value !== "embed") {
      return true;
    }

    const input = document.getElementById("blockVideoEmbed");
    const error = document.getElementById("blockVideoEmbedError");

    error.textContent = "";

    const value = input.value.trim();

    if (!value) {
      error.textContent = "Please enter a YouTube or Vimeo URL.";
      return false;
    }

    const regex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|vimeo\.com)/i;

    if (!regex.test(value)) {
      error.textContent = "Enter a valid YouTube or Vimeo URL.";
      return false;
    }

    return true;
  }

  function validateCaption() {
    const input = document.getElementById("blockVideoCaption");
    const error = document.getElementById("blockVideoCaptionError");

    error.textContent = "";

    const value = input.value.trim();

    if (!value) {
      error.textContent = "Caption is required.";
      return false;
    }

    if (value.length < 3) {
      error.textContent = "Caption must be at least 3 characters.";
      return false;
    }

    if (value.length > 100) {
      error.textContent = "Caption cannot exceed 100 characters.";
      return false;
    }

    return true;
  }

  // Auto-discards a block if the user closes the edit modal without
  // entering anything meaningful for that block type -- prevents empty
  // blocks from cluttering the article body.
  function removeEmptyCurrentBlock() {
    if (blockEditIndex < 0) return;

    const block = formData.blocks[blockEditIndex];

    switch (block.type) {
      case "paragraph":
        if (block.content?.trim()) return;
        break;

      case "heading":
        if (block.text?.trim()) return;
        break;

      case "pull-quote":
        if (block.quote?.trim()) return;
        break;

      case "box-highlight":
      case "box-info":
      case "box-warning":
        if (block.title?.trim() || block.content?.trim()) return;
        break;

      case "image":
        if (block.file || block.existingFile || block.fileName) return;
        break;

      case "video":
        if (block.file || block.embedUrl || block.fileName) return;
        break;

      case "list":
        if (block.items && block.items.some((item) => item.trim() !== "")) {
          return;
        }
        break;

      case "table": {
        const hasHeader =
          block.headers && block.headers.some((h) => String(h).trim() !== "");

        const hasRows =
          block.tableRows &&
          block.tableRows.some((row) =>
            row.some((cell) => String(cell).trim() !== ""),
          );

        if (hasHeader || hasRows) {
          return;
        }

        break;
      }

      case "gallery":
        if (
          (block.images && block.images.length) ||
          (block.existingGallery && block.existingGallery.length)
        ) {
          return;
        }
        break;

      case "cta":
        if (
          block.title?.trim() ||
          block.buttonText?.trim() ||
          block.buttonLink?.trim()
        ) {
          return;
        }
        break;

      default:
        return;
    }

    formData.blocks.splice(blockEditIndex, 1);

    renderStep(3, true);

    validateBlocks();

    updatePublishButtonState();

    blockEditIndex = -1;
  }

  // "Save" button inside the block edit modal: validates the fields for
  // whichever block type is open, writes the values back onto the block
  // object, then closes the modal and re-renders step 3.
  document
    .getElementById("saveBlockBtn")
    ?.addEventListener("click", function () {
      if (blockEditIndex < 0 || blockEditIndex >= formData.blocks.length)
        return;

      const block = formData.blocks[blockEditIndex];

      switch (block.type) {
        case "paragraph": {
          const input = document.getElementById("blockParagraphContent");
          const error = document.getElementById("blockParagraphContentError");

          error.textContent = "";

          block.content = input.value.trim();

          if (!block.content) {
            error.textContent = "Paragraph is required.";
            input.focus();
            return;
          }

          break;
        }

        case "heading": {
          const input = document.getElementById("blockHeadingText");
          const error = document.getElementById("blockHeadingTextError");

          error.textContent = "";

          block.text = input.value.trim();

          if (!block.text) {
            error.textContent = "Heading is required.";
            input.focus();
            return;
          }

          block.level = document.getElementById("blockHeadingLevel").value;

          break;
        }

        case "image": {
          const fileInput = document.getElementById("blockImageFile");
          const imageError = document.getElementById("blockImageFileError");

          imageError.textContent = "";

          if (
            !block.file &&
            !block.existingFile &&
            !block.fileName &&
            fileInput.files.length === 0
          ) {
            imageError.textContent = "Please select an image.";

            fileInput.focus();

            return;
          }

          if (fileInput.files.length) {
            block.file = fileInput.files[0];
            block.fileName = fileInput.files[0].name;
          }

          block.caption = document
            .getElementById("blockImageCaption")
            .value.trim();

          block.alt = document.getElementById("blockImageAlt").value.trim();

          block.alignment = document.getElementById("imageAlignment").value;

          break;
        }

        case "video": {
          const sourceType = document.getElementById("videoSourceType").value;

          const videoError = document.getElementById("blockVideoFileError");

          videoError.textContent = "";

          block.sourceType = sourceType;

          if (sourceType === "file") {
            const videoInput = document.getElementById("blockVideoFile");

            if (
              !block.file &&
              !block.existingFile &&
              !block.fileName &&
              videoInput.files.length === 0
            ) {
              videoError.textContent = "Please select a video.";

              videoInput.focus();

              return;
            }

            if (videoInput.files.length) {
              block.file = videoInput.files[0];
              block.fileName = videoInput.files[0].name;
            }

            block.embedUrl = "";
          } else {
            const embedInput = document.getElementById("blockVideoEmbed");

            if (!embedInput.value.trim()) {
              videoError.textContent = "Please enter a video URL.";

              embedInput.focus();

              return;
            }

            block.embedUrl = getEmbedUrl(embedInput.value);

            block.file = null;
            block.fileName = "";
          }

          block.caption = document
            .getElementById("blockVideoCaption")
            .value.trim();

          break;
        }

        case "pull-quote": {
          const quoteInput = document.getElementById("blockQuote");
          const authorInput = document.getElementById("blockQuoteAuthor");

          const quoteError = document.getElementById("blockQuoteError");
          const authorError = document.getElementById("blockQuoteAuthorError");

          quoteError.textContent = "";
          authorError.textContent = "";

          block.quote = quoteInput.value.trim();
          block.author = authorInput.value.trim();

          if (!block.quote) {
            quoteError.textContent = "Quote is required.";
            quoteInput.focus();
            return;
          }

          if (block.author && !/^[A-Za-z ]+$/.test(block.author)) {
            authorError.textContent = "Only letters and spaces are allowed.";
            authorInput.focus();
            return;
          }

          break;
        }

        case "box-highlight": {
          const title = document.getElementById("blockHighlightTitle");
          const content = document.getElementById("blockHighlightContent");

          const titleError = document.getElementById(
            "blockHighlightTitleError",
          );
          const contentError = document.getElementById(
            "blockHighlightContentError",
          );

          titleError.textContent = "";
          contentError.textContent = "";

          block.title = title.value.trim();
          block.content = content.value.trim();

          if (!block.content) {
            contentError.textContent = "Content is required.";
            content.focus();
            return;
          }

          break;
        }

        case "box-info": {
          const title = document.getElementById("blockInfoTitle");
          const content = document.getElementById("blockInfoContent");

          const titleError = document.getElementById("blockInfoTitleError");
          const contentError = document.getElementById("blockInfoContentError");

          titleError.textContent = "";
          contentError.textContent = "";

          block.title = title.value.trim();
          block.content = content.value.trim();

          if (!block.content) {
            contentError.textContent = "Content is required.";
            content.focus();
            return;
          }

          break;
        }

        case "box-warning": {
          const title = document.getElementById("blockWarningTitle");
          const content = document.getElementById("blockWarningContent");

          const titleError = document.getElementById("blockWarningTitleError");
          const contentError = document.getElementById(
            "blockWarningContentError",
          );

          titleError.textContent = "";
          contentError.textContent = "";

          block.title = title.value.trim();
          block.content = content.value.trim();

          if (!block.content) {
            contentError.textContent = "Content is required.";
            content.focus();
            return;
          }

          break;
        }

        case "list": {
          const input = document.getElementById("blockListItems");
          const error = document.getElementById("blockListItemsError");

          error.textContent = "";

          block.items = input.value
            .split("\n")
            .map((item) => item.trim())
            .filter((item) => item !== "");

          if (block.items.length === 0) {
            error.textContent = "Please add at least one list item.";
            input.focus();
            return;
          }

          break;
        }

        case "table": {
          const tableError = document.getElementById("blockTableError");

          tableError.textContent = "";

          const rowCount = parseInt(
            document.getElementById("blockTableRows").value,
          );

          const colCount = parseInt(
            document.getElementById("blockTableColumns").value,
          );

          const headers = [];
          const rows = [];

          let hasEmptyCell = false;

          // Header row
          for (let c = 0; c < colCount; c++) {
            const value = document
              .querySelector(`.table-cell[data-row="0"][data-col="${c}"]`)
              .value.trim();

            headers.push(value);

            if (value === "") {
              hasEmptyCell = true;
            }
          }

          // Remaining rows
          for (let r = 1; r < rowCount; r++) {
            const row = [];

            for (let c = 0; c < colCount; c++) {
              const value = document
                .querySelector(`.table-cell[data-row="${r}"][data-col="${c}"]`)
                .value.trim();

              row.push(value);

              if (value === "") {
                hasEmptyCell = true;
              }
            }

            rows.push(row);
          }

          if (hasEmptyCell) {
            tableError.textContent = "Please fill all table cells.";

            return;
          }

          block.rows = rowCount;
          block.columns = colCount;

          block.headers = headers;
          block.tableRows = rows;

          break;
        }

        case "gallery": {
          const galleryError = document.getElementById(
            "blockGalleryImagesError",
          );

          galleryError.textContent = "";

          if (
            block.images.length === 0 &&
            (!block.existingGallery || block.existingGallery.length === 0)
          ) {
            galleryError.textContent = "Please select at least one image.";
            return;
          }

          break;
        }
      }

      const modal = bootstrap.Modal.getInstance(
        document.getElementById("blockModal"),
      );

      blockEditIndex = -1;

      modal.hide();

      renderStep(3, true);

      validateBlocks();

      updatePublishButtonState();
    });

  // Draws the editable rows x columns grid of <input> cells for the
  // table block, seeding each cell from the block's saved headers/rows
  // if present, or blank otherwise.
  window.generateTableEditor = function () {
    const rows = parseInt(document.getElementById("blockTableRows").value);

    const cols = parseInt(document.getElementById("blockTableColumns").value);

    let html = `
                <div class="table-responsive">
                <table class="table table-bordered">
            `;

    for (let r = 0; r < rows; r++) {
      html += "<tr>";

      for (let c = 0; c < cols; c++) {
        let value = "";

        if (r === 0) {
          value = formData.blocks[blockEditIndex].headers?.[c] || "";
        } else {
          value = formData.blocks[blockEditIndex].tableRows?.[r - 1]?.[c] || "";
        }

        html += `
                <td>
                    <input
                        type="text"
                        class="form-control form-control-sm table-cell"
                        data-row="${r}"
                        data-col="${c}"
                        value="${value}">
                </td>
            `;
      }

      html += "</tr>";
    }

    html += "</table></div>";

    document.getElementById("tableEditor").innerHTML = html;
  };

  window.removeBlock = function (index) {
    if (index >= 0 && index < formData.blocks.length) {
      formData.blocks.splice(index, 1);
      renderStep(3, true);
      validateBlocks();
      updatePublishButtonState();
    }
  };

  // ─── RELATED FUNCTIONS ───
  window.addRelated = function () {
    const title =
      document.getElementById("relatedTitleInput")?.value?.trim() || "";
    if (!title) return;
    const category =
      document.getElementById("relatedCategoryInput")?.value?.trim() || "";
    const date = document.getElementById("relatedDateInput")?.value || "";
    const read =
      document.getElementById("relatedReadInput")?.value?.trim() || "";
    formData.related.push({ title, category, date, read });
    renderStep(4, true);
    document.getElementById("relatedTitleInput").value = "";
    document.getElementById("relatedCategoryInput").value = "";
    document.getElementById("relatedDateInput").value = "";
    document.getElementById("relatedReadInput").value = "";
    saveFormData();
  };

  window.removeRelated = function (index) {
    if (index >= 0 && index < formData.related.length) {
      formData.related.splice(index, 1);
      renderStep(4, true);
      saveFormData();
    }
  };

  // ─── GLOBAL FUNCTIONS ───
  window.saveDraft = function () {
    saveFormData();
    Swal.fire({
      icon: "success",
      title: "Draft Saved!",
      text: "Your article has been saved as a draft.",
      confirmButtonColor: "#c5050c",
    });
  };

  window.publishArticle = function () {
    saveFormData();

    const result = validateFormData();

    if (result !== true) {
      Swal.fire({
        icon: "warning",
        title: "Missing Required Field",
        html: `<b>${result.field}</b> is required before publishing.`,
        confirmButtonColor: "#c5050c",
      }).then(() => {
        goToStep(result.step);
      });

      return;
    }

    // Backend publish code later
    Swal.fire({
      icon: "success",
      title: "Published!",
      text: "Your article has been published successfully.",
      confirmButtonColor: "#c5050c",
    });
  };

  // ─── KEYBOARD SHORTCUTS ───
  // Ctrl+Enter / Ctrl+Arrow keys let power users move between steps
  // without reaching for the mouse.
  document.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && e.ctrlKey) {
      e.preventDefault();
      if (currentStep < totalSteps) goToStep(currentStep + 1);
    }
    if (e.key === "ArrowLeft" && e.ctrlKey) {
      e.preventDefault();
      if (currentStep > 1) goToStep(currentStep - 1);
    }
    if (e.key === "ArrowRight" && e.ctrlKey) {
      e.preventDefault();
      if (currentStep < totalSteps) goToStep(currentStep + 1);
    }
  });

  // ─── INIT ───
  // Draw step 1 as soon as the DOM is ready (or immediately, if it
  // already is by the time this script runs).
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      renderStep(1, false);

      console.log(
        "✅ News Publishing Wizard initialized with clean validation.",
      );
    });
  } else {
    renderStep(1, false);

    console.log("✅ News Publishing Wizard initialized with clean validation.");
  }

  // Expose what the rest of the page (and inline onclick handlers) needs.
  window.formData = formData;
  window.saveFormData = saveFormData;
  window.validateAll = validateAll;
  window.validateFormData = validateFormData;
})();

/* =========================================================================
   ADD CATEGORY MODAL
   Lives outside the wizard IIFE because it manages its own small,
   self-contained widget (the "+ Add Category" modal) that talks to the
   backend independently of the multi-step form above.
   ========================================================================= */

const categoryForm = document.getElementById("categoryForm");
const categoryInput = document.getElementById("categoryName");
const categoryError = document.getElementById("categoryError");
const saveCategoryBtn = document.getElementById("saveCategoryBtn");
const categoryModal = document.getElementById("categoryModal");

// Reset the form back to a clean state every time the modal is closed.
categoryModal.addEventListener("hidden.bs.modal", function () {
  categoryForm.reset();
  categoryError.textContent = "";
  categoryInput.classList.remove("is-invalid");
});

// Clear error while typing
categoryInput.addEventListener("input", function () {
  categoryError.textContent = "";
});

// Live validation as the user types a new category name.
categoryInput.addEventListener("input", function () {
  const value = this.value.trim();

  categoryError.textContent = "";

  // Empty
  if (value.length === 0) {
    return;
  }

  // Only alphabets and spaces
  if (!/^[A-Za-z &]+$/.test(value)) {
    categoryError.textContent = "Only alphabets and spaces and (&) are allowed.";
    return;
  }

  // Minimum length
  if (value.length < 3) {
    categoryError.textContent = "Category must contain at least 3 characters.";
    return;
  }

  // Maximum length
  if (value.length > 30) {
    categoryError.textContent = "Category cannot exceed 30 characters.";
    return;
  }
});

// Submits the new category to the backend, then updates the in-memory
// category list and the (rebuilt) Choices.js dropdown so the new
// category is immediately selectable without a page reload.
saveCategoryBtn.addEventListener("click", async function (e) {
  e.preventDefault();

  categoryError.textContent = "";

  const formDataObj = new FormData(categoryForm);
  formDataObj.set("category_name", categoryInput.value.trim());

  try {
    const response = await fetch("/dashboard/add_category/", {
      method: "POST",
      body: formDataObj,
      headers: {
        "X-CSRFToken": document.querySelector(
          "#categoryForm [name=csrfmiddlewaretoken]",
        ).value,
      },
    });

    

    const data = await response.json();

    if (!response.ok) {
      if (data.errors && data.errors.category_name) {
        categoryError.textContent = data.errors.category_name[0].message;
        return;
      }

      categoryError.textContent = "Something went wrong.";
      return;
    }

    // Update categories array
    window.categories.push(data.category);

    // Auto select new category
    window.formData.category = data.category.category_name;

    const categorySelect = document.getElementById("editCategory");

    if (categorySelect) {
      if (window.editCategoryChoices) {
        window.editCategoryChoices.destroy();
      }

      categorySelect.innerHTML = window.renderCategoryOptions();

      window.editCategoryChoices = new Choices(categorySelect, {
        searchEnabled: false,
        itemSelectText: "",
        shouldSort: false,
      });

      window.editCategoryChoices.setChoiceByValue(data.category.category_name);
    }

    // Reset modal
    categoryForm.reset();
    categoryError.textContent = "";

    // Close modal
    const modalElement = document.getElementById("categoryModal");
    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);

    modal.hide();

    setTimeout(() => {
      document.querySelectorAll(".modal-backdrop").forEach((el) => el.remove());
      document.body.classList.remove("modal-open");
      document.body.style.removeProperty("padding-right");
    }, 200);
  } catch (error) {
    console.error(error);
    categoryError.textContent = "Something went wrong.";
  }
});
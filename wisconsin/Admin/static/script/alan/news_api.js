function getCookie(name) {

    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {

        const cookies = document.cookie.split(";");

        for (let cookie of cookies) {

            cookie = cookie.trim();

            if (cookie.startsWith(name + "=")) {

                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );

                break;

            }

        }

    }

    return cookieValue;

}


window.saveDraft = function () {
    submitArticle("draft");
}

// 3
window.publishArticle = function () {
    submitArticle("published");
}


async function submitArticle(status) {

    window.saveFormData();

    if (status !== true) {

    const result = window.validateFormData();

    if (result !== true) {

        Swal.fire({
            icon: "error",
            title: status === "draft" ? "Cannot save Draft":"Cannot publish",
            html: `<b>${result.field}</b> is required.`,
            confirmButtonColor: "#c5050c"
        });

        window.goToStep(result.step);

        return;
    }

}

    const fd = new FormData();

    fd.append("status", status);

    fd.append("title", window.formData.title);

    fd.append("subtitle", window.formData.subtitle);

    fd.append("category", window.formData.category);

    fd.append("reading_time", window.formData.readingTime);

    fd.append("hero_caption", window.formData.heroCaption);

    fd.append("author_name", window.formData.authorName);

    fd.append("author_role", window.formData.authorRole);

    fd.append("author_bio", window.formData.authorBio);

    fd.append("author_twitter", window.formData.socialTwitter);

    fd.append("author_linkedin", window.formData.socialLinkedin);

    fd.append("author_website", window.formData.socialWebsite);

    
    const heroMedia = document.getElementById("editHeroSrc")

    if (window.formData.heroFile) {
    fd.append("hero_media", window.formData.heroFile);
}

    // AUTHORAVATAR
    const authorAvatar = document.getElementById("editAuthorAvatar");

    if (window.formData.authorAvatar) {
    fd.append("author_avatar", window.formData.authorAvatar);
}

    // TAGS
    fd.append("tags", JSON.stringify(formData.tags));

    // BLOCKS

    const blocks = [];

    formData.blocks.forEach((block,index) => {

      const blockData = {...block};

      // File objects JSON-la serialize panna mudiyathu

      delete blockData.file;
      delete blockData.images;

      blocks.push(blockData);

      // Single media (image/video)

      if(block.file) {
        fd.append(
          `block_file_${index}`, block.file
        );
      }

      // Gallery media

      if(block.images && block.images.length) {

        block.images.forEach((image, imgIndex) => {

          fd.append(`gallery_${index}_${imgIndex}`, image);
        });

      }

    });

    fd.append("blocks", JSON.stringify(blocks));

    console.log("========== FormData ==========");

    for (const pair of fd.entries()) {

        console.log(pair[0], pair[1]);

    }

    console.log("==============================");

    // Send request

    try {

      const url = window.isEdit
    ? `/dashboard/article/${window.articleId}/update/`
    : "/dashboard/article/create/";

      const response = await fetch(url, {
        method: "POST",

        headers: {
          "X-CSRFToken": getCookie("csrftoken")
        },
        body: fd
      }
    );

    const data = await response.json();

    if (data.success) {

      Swal.fire({
        icon: "success",
        title: status === "draft" ? "Draft saved" : "Article Published",
        text: data.message,
        confirmButtonColor: "#c5050c"
      }).then(() => {
        window.location.replace("/dashboard/admin_news/");
      })
    } else {  

      Swal.fire({

        icon: "error",
        title: "Error",
        text: data.message || "Unable to save article",
        confirmButtonColor: "#c50505c"
      });
    }


    } catch (error) {

      console.log(error);

      Swal.fire({

        icon: "error",
        title: "Server Error",
        text: "Something went wrong while saving the article",
        confirmButtonColor: "#c5050c"
      });
    }
  }


window.templatePreview = function () {

    saveFormData();

    const result = validateFormData();

    if (result !== true) {

      Swal.fire({

        icon: "warning",
        title: "Complete all required fields",
        html: `<b>${result.field}</b> is required.`,
        confirmButtonColor: "#c5050c"
      })
    }

    // Current editor data save pannrom
    const previewData =
    convertArticleForPreview(formData);
    console.log("Preview Article:", previewData);
    console.log("Body Blocks:", previewData.bodyBlocks);
    sessionStorage.setItem(
        "previewArticle",
        JSON.stringify(previewData)
    );

    // Preview page open
    window.open("/dashboard/preview_page/", "_blank");

};


function updateTemplateButton() {

    const btn = document.getElementById("viewTemplateBtn");

    console.log("Button :", btn);
    

    const result = validateFormData();

    console.log("Validation :", result);

    if (!btn) return;

    if (result === true) {
        btn.style.display = "inline-block";
    } else {
        btn.style.display = "none";
    }
}




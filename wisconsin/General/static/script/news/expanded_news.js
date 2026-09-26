

(function () {
  "use strict";

  /* ══════════════════════════════════════════════════════════
               FALLBACK BLOCKS (when bodyBlocks is empty)
               ══════════════════════════════════════════════════════════ */
  const fallbackBlocks = [
    {
      type: "paragraph",
      content:
        "This is a sample article using <strong>fallback blocks</strong>. The admin hasn't provided any body content yet, so these placeholder blocks are displayed instead.",
    },
    { type: "heading", level: 2, content: "How to Add Content" },
    {
      type: "paragraph",
      content:
        "Populate the <code>bodyBlocks</code> array in <code>articleData</code> with your own content blocks. The template supports paragraphs, headings, images, pull quotes, info boxes, galleries, videos, tables, lists, and CTA boxes.",
    },
    {
      type: "list",
      ordered: false,
      items: [
        '<strong>Paragraph:</strong> <code>{ type: "paragraph", content: "Your text here" }</code>',
        '<strong>Heading:</strong> <code>{ type: "heading", level: 2, content: "Section Title" }</code>',
        '<strong>Image:</strong> <code>{ type: "image", src: "url", caption: "Alt text", alignment: "center" }</code>',
      ],
    },
    {
      type: "box-info",
      content:
        "💡 <strong>Tip:</strong> Empty or null blocks are automatically detected and skipped during rendering. No manual cleanup needed!",
    },
  ];

  /* ══════════════════════════════════════════════════════════
               BLOCK VALIDATION — checks if a block has meaningful content
               ══════════════════════════════════════════════════════════ */
  function hasValidContent(block) {
    if (!block || !block.type) return false;
    switch (block.type) {
      case "paragraph":
      case "heading":
      case "pull-quote":
      case "box-highlight":
      case "box-info":
      case "box-warning":
        return (
          typeof block.content === "string" && block.content.trim().length > 0
        );
      case "image":
        return typeof block.src === "string" && block.src.trim().length > 0;
      case "list":
        return (
          Array.isArray(block.items) &&
          block.items.length > 0 &&
          block.items.some(
            (item) => typeof item === "string" && item.trim().length > 0,
          )
        );
      case "table":
        return (
          Array.isArray(block.headers) &&
          block.headers.length > 0 &&
          Array.isArray(block.rows) &&
          block.rows.length > 0 &&
          block.rows.some((row) => Array.isArray(row) && row.length > 0)
        );
      case "video":
        return (
          (typeof block.url === "string" && block.url.trim().length > 0) ||
          (typeof block.embedUrl === "string" &&
            block.embedUrl.trim().length > 0)
        );
      case "cta":
        return typeof block.title === "string" && block.title.trim().length > 0;
      case "gallery":
        return (
          Array.isArray(block.images) &&
          block.images.length > 0 &&
          block.images.some(
            (img) =>
              img && typeof img.src === "string" && img.src.trim().length > 0,
          )
        );
      default:
        return true; // unknown types pass through
    }
  }

  /* ══════════════════════════════════════════════════════════
               RENDER BLOCKS into #articleBody
               ══════════════════════════════════════════════════════════ */
  function renderBlocks(blocks) {
    const container = document.getElementById("articleBody");
    if (!container) {
      console.error("#articleBody not found!");
      return;
    }
    container.innerHTML = "";

    if (!blocks || blocks.length === 0) {
      container.innerHTML =
        '<p class="reveal"><em>No content blocks available. Please add some in <code>articleData.bodyBlocks</code>.</em></p>';
      initScrollReveal();
      return;
    }

    let renderedCount = 0,
      skippedCount = 0;

    blocks.forEach((block, index) => {
      if (!hasValidContent(block)) {
        skippedCount++;
        return;
      }
      renderedCount++;
      let html = "";
      const staggerDelay = renderedCount * 30 + "ms";
      const clearBlocks = [
          // "heading",
          // "pull-quote",
          // "box-highlight",
          // "box-info",
          // "box-warning",
          "list",
          "table",
          "gallery",
          "video",
          "cta",
      ];
      if (clearBlocks.includes(block.type)) {
        container.insertAdjacentHTML(
          "beforeend",
          '<div style="clear:both"></div>',
        );
      }

      try {
        switch (block.type) {
          case "paragraph":
            html = `<p class="reveal para" style="transition-delay:${staggerDelay}">${block.content}</p>`;
            break;
          case "heading":
            html = `<h${block.level || 2} class="reveal" style="transition-delay:${staggerDelay}">${block.content}</h${block.level || 2}>`;
            break;

          case "image": {
            const align = block.alignment || "center";

            html = `
                                    <div class="inline-img img-${align} reveal"
                                        style="transition-delay:${staggerDelay}">

                                        <img
                                            src="${block.src}"
                                            alt="${block.alt || block.caption || "Article image"}"
                                            loading="lazy">

                                        ${
                                          block.caption
                                            ? `<div class="img-caption">${block.caption}</div>`
                                            : ""
                                        }

                                    </div>
                                `;

            break;
          }
          case "pull-quote":
            html = `<div class="box pull-quote reveal" style="transition-delay:${staggerDelay}">“${block.content}”${block.attribution ? `<span class="attribution">— ${block.attribution}</span>` : ""}</div>`;
            break;
          case "box-highlight":
            html = `<div class="box box-highlight reveal" style="transition-delay:${staggerDelay}"><strong><i class="bi bi-highlighter box-icon"></i><span class=" ms-2">${block.title}</span> <div>${block.content}</div></strong></div>`;
            break;
          case "box-info":
            html = `<div class="box box-info reveal" style="transition-delay:${staggerDelay}"><strong><i class="bi bi-info-circle box-icon"></i> <span class=" ms-2">${block.title}</span> <div>${block.content}</div></strong></div>`;
            break;
          case "box-warning":
            html = `<div class="box box-warning reveal" style="transition-delay:${staggerDelay}"><strong><i class="bi bi-exclamation-triangle box-icon"></i> <span class=" ms-2">${block.title}</span> <div>${block.content}</div></strong></div>`;
            break;
          case "list": {
            const tag = block.ordered ? "ol" : "ul";
            html = `<${tag} class="reveal" style="transition-delay:${staggerDelay}">${block.items.map((i) => `<li>${i}</li>`).join("")}</${tag}>`;
            break;
          }
          case "table":
            html = `<div class="table-wrap reveal" style="transition-delay:${staggerDelay}"><table><thead><tr>${block.headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${block.rows.map((row) => `<tr>${row.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
            break;

          case "video": {
            const url =
              block.sourceType === "embed" ? block.embedUrl : block.url;

            const isEmbed = block.sourceType === "embed" && block.embedUrl;

            if (isEmbed) {
              html = `
                                    <div class="video-embed reveal" style="transition-delay:${staggerDelay}">
                                        <iframe
                                            src="${block.embedUrl}"
                                            title="Embedded video"
                                            width="100%"
                                            height="100%"
                                            frameborder="0"
                                            referrerpolicy="strict-origin-when-cross-origin"
                                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                                            allowfullscreen>
                                        </iframe>
                                    </div>`;
            } else {
              html = `
                                    <div class="video-embed reveal" style="transition-delay: ${staggerDelay}">

                                        <video controls preload="metadata" src="${block.url}" playsinline>
                                            
                                            Your browser does not support the video tag.
                                        </video>
                                    </div>`;
            }
            break;
          }

          case "cta":
            html = `<div class="cta-box reveal" style="transition-delay:${staggerDelay}"><h3>${block.title}</h3><p>${block.content}</p><a href="${block.buttonLink || "#"}" class="btn-cta">${block.buttonText || "Learn More"} <i class="bi bi-arrow-right"></i></a></div>`;
            break;
          case "gallery":
            html = `<div class="gallery reveal" style="transition-delay:${staggerDelay}">${block.images.map((img) => `<div class="gallery-item" tabindex="0" role="button" aria-label="${img.caption || "Gallery image"}"><img src="${img.src}" alt="${img.caption || ""}" loading="lazy" />${img.caption ? `<div class="gallery-caption">${img.caption}</div>` : ""}</div>`).join("")}</div>`;
            break;
          default:
            html = `<p class="reveal" style="transition-delay:${staggerDelay}"><em>⚠️ Unsupported block type: <code>${block.type}</code></em></p>`;
        }
      } catch (err) {
        html = `<p class="reveal" style="transition-delay:${staggerDelay}"><em>❌ Error rendering block #${index}: ${err.message}</em></p>`;
      }
      container.insertAdjacentHTML("beforeend", html);
    });

    console.log(
      `📝 Rendered: ${renderedCount} blocks | ⏭️ Skipped: ${skippedCount} empty/invalid blocks`,
    );
    initScrollReveal();
  }

  /* ══════════════════════════════════════════════════════════
               SCROLL REVEAL — Intersection Observer
               ══════════════════════════════════════════════════════════ */
  function initScrollReveal() {
    const items = document.querySelectorAll(".article-body .reveal");
    if (!("IntersectionObserver" in window)) {
      items.forEach((el) => el.classList.add("is-visible"));
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -30px 0px" },
    );
    items.forEach((el) => observer.observe(el));
  }

  /* ══════════════════════════════════════════════════════════
               RENDER FULL ARTICLE from data object
               ══════════════════════════════════════════════════════════ */
  function renderArticle(data) {
    // Title
    const titleEl = document.getElementById("heroTitle");
    titleEl.childNodes[0].textContent = (data.title || "Untitled") + " ";
    document.getElementById("breadcrumbTitle").textContent =
      data.title || "Article";

    // Subtitle
    const sub = document.getElementById("heroSubtitle");
    if (data.subtitle && data.subtitle.trim()) {
      sub.textContent = data.subtitle;
      sub.style.display = "";
    } else {
      sub.style.display = "none";
    }

    // Category badge
    const cat = document.getElementById("categoryBadge");
    const breadCat = document.getElementById("breadcrumbCategory");
    if (data.category && data.category.trim()) {
      cat.textContent = data.category;
      cat.href = data.categoryLink || "#";
      cat.style.display = "";
      breadCat.textContent = data.category;
      breadCat.href = data.categoryLink || "#";
    } else {
      cat.style.display = "none";
      breadCat.textContent = "Articles";
    }

    // Dateline
    const dl = document.getElementById("dateline");
    if (data.dateline && data.dateline.trim()) {
      dl.querySelector("span:last-child").innerHTML =
        `<span class="loc">${data.dateline}</span> — ${data.published || "Today"}`;
      dl.style.display = "";
    } else {
      dl.style.display = "none";
    }

    // Author
    if (data.author) {
      document.getElementById("authorName").textContent =
        data.author.name || "Author";
      const av = document.getElementById("authorAvatar");
      av.src =
        data.author.avatar ||
        `https://ui-avatars.com/api/?name=${encodeURIComponent(data.author.name || "Author")}&size=40&background=e83e3e&color=fff&font-size=0.5`;
      av.alt = data.author.name || "Author";
    }

    // Dates
    document.getElementById("publishedDate").textContent =
      data.published_at || "Today";
    const updWrap = document.getElementById("updatedDateWrap");
    const updEl = document.getElementById("updatedDate");
    if (data.updated && data.updated.trim()) {
      updEl.textContent = data.updated;
      updWrap.style.display = "";
    } else {
      updWrap.style.display = "none";
    }

    // Reading time
    document.getElementById("readingTime").textContent =
      `${data.reading_time || 5} min read`;

    // Hero media
    const heroMedia = document.getElementById("heroMedia");
    const heroImg = document.getElementById("heroImage");
    const heroCap = document.getElementById("heroCaption");
    if (data.hero && data.hero.src && data.hero.src.trim()) {
      heroMedia.style.display = "";
      if (data.hero.type === "video") {
        heroImg.outerHTML = `<video src="${data.hero.src}" controls autoplay muted loop playsinline style="width:100%;height:auto;display:block;aspect-ratio:16/9;object-fit:cover;"></video>`;
        const nc = heroMedia.querySelector(".media-caption");
        if (nc) nc.textContent = data.hero.caption || "";
      } else {
        heroImg.src = data.hero.src;
        heroImg.alt = data.hero.caption || "Hero image";
        heroCap.textContent = data.hero.caption || "";
      }
    } else {
      heroMedia.style.display = "none";
    }

    // Tags
    const tagsSec = document.getElementById("tagsSection");
    if (data.tags && data.tags.length > 0) {
      tagsSec.innerHTML = data.tags
        .map((t) => `<a href="#" class="tag">#${t}</a>`)
        .join("");
      tagsSec.style.display = "";
    } else {
      tagsSec.style.display = "none";
    }

    // Author bio
    const bioSec = document.getElementById("authorBio");
    if (
      data.showAuthorBio !== false &&
      data.author &&
      data.author.bio &&
      data.author.bio.trim()
    ) {
      const av = bioSec.querySelector(".bio-avatar");
      const name = bioSec.querySelector("h5");
      const role = bioSec.querySelector(".bio-role");
      const bioText = bioSec.querySelector("p");
      if (av)
        av.src =
          data.author.avatar ||
          `https://ui-avatars.com/api/?name=${encodeURIComponent(data.author.name || "Author")}&size=80&background=e83e3e&color=fff&font-size=0.5`;
      if (name) name.textContent = data.author.name || "Author";
      if (role) role.textContent = data.author.role || "";
      if (bioText) bioText.textContent = data.author.bio;
      const social = bioSec.querySelector(".bio-social");
      if (social && data.author.social) {
        const links = social.querySelectorAll("a");
        const keys = ["twitter", "github", "linkedin", "website"];
        links.forEach((link, i) => {
          const key = keys[i] || "website";
          if (data.author.social[key] && data.author.social[key].trim()) {
            link.href = data.author.social[key];
            link.style.display = "";
          } else {
            link.style.display = "none";
          }
        });
      }
      bioSec.style.display = "";
    } else {
      bioSec.style.display = "none";
    }

    // Prev/Next
    const pn = document.getElementById("prevNextNav");
    if (data.showPrevNext !== false && (data.prev || data.next)) {
      let html = "";
      if (data.prev && data.prev.title && data.prev.title.trim()) {
        html += `<a href="${data.prev.link || "#"}" class="pn-link pn-prev"><span class="pn-label"><i class="bi bi-arrow-left"></i> Previous</span><span class="pn-title">${data.prev.title}</span></a>`;
      } else {
        html += `<span class="pn-link pn-prev" style="opacity:0.35;cursor:default;pointer-events:none;">No previous article</span>`;
      }
      if (data.next && data.next.title && data.next.title.trim()) {
        html += `<a href="${data.next.link || "#"}" class="pn-link pn-next"><span class="pn-label">Next <i class="bi bi-arrow-right"></i></span><span class="pn-title">${data.next.title}</span></a>`;
      } else {
        html += `<span class="pn-link pn-next" style="opacity:0.35;cursor:default;pointer-events:none;">No next article</span>`;
      }
      pn.innerHTML = html;
      pn.style.display = "";
    } else {
      pn.style.display = "none";
    }

    // Related
    const relSec = document.getElementById("relatedSection");
    const relGrid = document.getElementById("relatedGrid");
    if (data.showRelated !== false && data.related && data.related.length > 0) {
      relGrid.innerHTML = data.related
        .map(
          (r) =>
            `<a href="${r.link || "#"}" class="related-card"><span class="rc-category">${r.category || "Article"}</span><h4 class="rc-title">${r.title}</h4><span class="rc-meta">${r.date || ""} · ${r.readTime || ""}</span></a>`,
        )
        .join("");
      relSec.style.display = "";
    } else {
      relSec.style.display = "none";
    }

    // Render body blocks
    let blocks = data.bodyBlocks;
    if (!blocks || blocks.length === 0) {
      blocks = fallbackBlocks;
    }
    renderBlocks(blocks);

    // Togglable sections
    // document.getElementById("commentsSection").style.display =
    //   data.showComments !== false ? "" : "none";
    // document.getElementById("newsletterSection").style.display =
    //   data.showNewsletter !== false ? "" : "none";
    // document.getElementById("adPlaceholder").style.display =
    //   data.showAd !== false ? "" : "none";
  }

  /* ══════════════════════════════════════════════════════════
               DARK MODE — with localStorage persistence
               ══════════════════════════════════════════════════════════ */
  // const darkToggle = document.getElementById("darkToggle");
  // const darkIcon = document.getElementById("darkIcon");

  // function getInitialDarkMode() {
    // Check localStorage first
    // const stored = localStorage.getItem("dispatch-dark-mode");
    // if (stored !== null) {
    //   return stored === "true";
    // }
    // Fall back to system preference
  //   return (
  //     window.matchMedia &&
  //     window.matchMedia("(prefers-color-scheme: dark)").matches
  //   );
  // }

  // let darkMode = getInitialDarkMode();

  // function applyDark(isDark) {
  //   darkMode = isDark;
  //   document.documentElement.setAttribute(
  //     "data-theme",
  //     isDark ? "dark" : "light",
  //   );
  //   darkIcon.className = isDark ? "bi bi-sun-fill" : "bi bi-moon-fill";
  //   darkToggle.setAttribute(
  //     "aria-label",
  //     isDark ? "Switch to light mode" : "Switch to dark mode",
  //   );
  //   // Persist
  //   localStorage.setItem("dispatch-dark-mode", String(isDark));
  // }

  // applyDark(darkMode);

  // darkToggle.addEventListener("click", () => {
  //   applyDark(!darkMode);
  //   // Brief pulse animation feedback
  //   darkToggle.style.transform = "scale(0.85)";
  //   setTimeout(() => {
  //     darkToggle.style.transform = "";
  //   }, 150);
  // });

  // Listen for system preference changes (if user hasn't manually set)
  // if (window.matchMedia) {
  //   window
  //     .matchMedia("(prefers-color-scheme: dark)")
  //     .addEventListener("change", (e) => {
  //       const stored = localStorage.getItem("dispatch-dark-mode");
  //       if (stored === null) {
  //         applyDark(e.matches);
  //       }
  //     });
  // }

  /* ══════════════════════════════════════════════════════════
               READING PROGRESS
               ══════════════════════════════════════════════════════════ */
  // const progressBar = document.getElementById("progressBar");
  // const progressReadout = document.getElementById("progressReadout");
  // let readoutTimer = null;

  // function updateProgress() {
  //   const scrollTop = window.scrollY;
  //   const docHeight =
  //     document.documentElement.scrollHeight - window.innerHeight;
  //   const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
  //   const clamped = Math.min(Math.max(progress, 0), 100);
  //   progressBar.style.width = clamped + "%";
  //   progressReadout.textContent =
  //     String(Math.round(clamped)).padStart(2, "0") + "%";
  //   progressReadout.classList.add("visible");
  //   clearTimeout(readoutTimer);
  //   readoutTimer = setTimeout(
  //     () => progressReadout.classList.remove("visible"),
  //     1000,
  //   );
  // }

  // window.addEventListener("scroll", updateProgress, { passive: true });
  
  // updateProgress();

  /* ══════════════════════════════════════════════════════════
               STICKY SHARE VISIBILITY
               ══════════════════════════════════════════════════════════ */
  const stickyShare = document.getElementById("stickyShare");
  let shareVisible = false;

  function updateShareVisibility() {

    if (!stickyShare) return;
    
    const heroEl = document.querySelector(".article-hero");
    const trigger = heroEl ? heroEl.offsetHeight * 0.55 : 300;
    if (window.scrollY > trigger && window.innerWidth > 640) {
      if (!shareVisible) {
        stickyShare.classList.add("visible");
        shareVisible = true;
      }
    } else {
      if (shareVisible) {
        stickyShare.classList.remove("visible");
        shareVisible = false;
      }
    }
  }

  window.addEventListener("scroll", updateShareVisibility, { passive: true });
  window.addEventListener("resize", updateShareVisibility, { passive: true });
  updateShareVisibility();

  /* ══════════════════════════════════════════════════════════
              SHARE HANDLERS
               ══════════════════════════════════════════════════════════ */
  function handleShare(e) {
    e.preventDefault();
    const type = e.currentTarget.getAttribute("data-share");
    const url = encodeURIComponent(window.location.href);
    const title = encodeURIComponent(document.title);

    if (type === "copy") {
      navigator.clipboard
        .writeText(window.location.href)
        .then(() => {
          const icon = e.currentTarget.querySelector("i");
          if (icon) {
            const orig = icon.className;
            icon.className = "bi bi-check-lg";
            setTimeout(() => {
              icon.className = orig;
            }, 1600);
          }
        })
        .catch(() => {
          alert("📋 Copy this link:\n" + window.location.href);
        });
      return;
    }

    const shareMap = {
      twitter: `https://twitter.com/intent/tweet?url=${url}&text=${title}`,
      linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${url}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${url}`,
      email: `mailto:?subject=${title}&body=${url}`,
    };

    if (shareMap[type]) {
      window.open(
        shareMap[type],
        "_blank",
        "width=600,height=450,noopener,noreferrer",
      );
    }
  }

  document.querySelectorAll("[data-share]").forEach((el) => {
    el.addEventListener("click", handleShare);
  });

  /* ══════════════════════════════════════════════════════════
              INITIALIZE
               ══════════════════════════════════════════════════════════ */
const slug = window.location.pathname

    .split("/")
    .filter(Boolean)
    .pop()

async function loadArticle() {

  try {
    const response = await fetch(`/api/news/${slug}/`);
    console.log(response)
    if (!response.ok) {
      throw new Error("Failed to load article");
    }

    const articleData = await response.json();
    
    console.log(articleData);
    console.log(articleData.bodyBlocks);

    renderArticle(articleData);
  } catch (error) {

    console.log(error)
  }
}

document.addEventListener("DOMContentLoaded", () => {

  loadArticle();
});


})();



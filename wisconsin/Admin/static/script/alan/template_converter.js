function getEmbedUrl(url) {
  if (!url) return "";

  url = url.trim();

  // Already embed URL
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

  // Vimeo
  if (url.includes("vimeo.com")) {
    const id = url.split("/").pop().split("?")[0];
    return `https://player.vimeo.com/video/${id}`;
  }

  return url;
}

function convertArticleForPreview(formData) {
  return {
    title: formData.title || "",

    subtitle: formData.subtitle || "",

    category: formData.category || "",

    readingTime: parseInt(formData.readingTime) || 0,

    author: {
      name: formData.authorName || "",

      role: formData.authorRole || "",

      bio: formData.authorBio || "",

      avatar:
        formData.authorAvatar instanceof File
          ? URL.createObjectURL(formData.authorAvatar)
          : formData.authorAvatar || "",

      social: {
        twitter: formData.socialTwitter || "",

        linkedin: formData.socialLinkedin || "",

        website: formData.socialWebsite || "",
      },
    },

    hero: {

            type:
                formData.heroFile
                    ? (
                        formData.heroFile.type.startsWith("video")
                            ? "video"
                            : "image"
                    )
                    : (
                        formData.heroMedia
                            ? "image"
                            : ""
                    ),

            src:
                formData.heroFile
                    ? URL.createObjectURL(formData.heroFile)
                    : (formData.heroMedia || ""),

            caption: formData.heroCaption || ""

        },

    tags: formData.tags || [],

    related: formData.related || [],

    bodyBlocks: convertBlocks(formData.blocks || []),
  };
}

function convertBlocks(blocks) {
  if (!Array.isArray(blocks)) return [];

  return blocks.map((block) => {
    switch (block.type) {
      case "paragraph":
        return {
          type: "paragraph",
          content: block.content || "",
        };

      case "heading":
        return {
          type: "heading",
          level: parseInt(block.level?.replace("h", "")) || 2,
          content: block.text || block.content || "",
        };

      case "pull-quote":
        return {
          type: "pull-quote",
          content: block.quote || block.content || "",
          attribution: block.author || "",
        };

      case "box-highlight":
        return {
          type: "box-highlight",
          content: block.content || "",
          title: block.title || "",
        };

      case "box-info":
        return {
          type: "box-info",
          content: block.content || "",
          title: block.title || "",
        };

      case "box-warning":
        return {
          type: "box-warning",
          content: block.content || "",
          title: block.title || "",
        };

      case "image":
        return {
          type: "image",

          src:
            block.file instanceof File
              ? URL.createObjectURL(block.file)
              : block.existingFile || block.src || "",

          caption: block.caption || "",

          alignment: block.alignment || "center",
        };

      case "video":
        return {
          type: "video",

          sourceType: block.sourceType || "file",

          url:
            block.sourceType === "file"
              ? block.file instanceof File
                ? URL.createObjectURL(block.file)
                : block.existingFile || block.url || ""
              : "",

          embedUrl:
            block.sourceType === "embed"
              ? getEmbedUrl(block.embedUrl || "")
              : "",

          caption: block.caption || "",
        };

      case "gallery":
        return {
          type: "gallery",

          images: [
            ...(block.existingGallery || []).map((image) => ({
              src: image.url,

              caption: image.caption || "",
            })),

            ...(block.images || []).map((image) => ({
              src: URL.createObjectURL(image),

              caption: image.caption || "",
            })),
          ],
        };

      case "list":
        return {
          type: "list",
          ordered: block.ordered || false,
          items: block.items || [],
        };

      case "table":
        return {
            type: "table",
            headers: block.headers || [],
            rows: block.tableRows || [],
        };

      case "cta":
        return {
          type: "cta",
          title: block.title || "",
          content: block.content || "",
          buttonText: block.buttonText || "Read More",
          buttonLink: block.buttonLink || "#",
        };

      default:
        return block;
    }
  });
}

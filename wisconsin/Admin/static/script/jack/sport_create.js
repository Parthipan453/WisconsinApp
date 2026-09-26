function getDefaultPreview() {
  return `
      <div class="sc-preview-card" style="background-color: #f5f7fa;">
        <div class="sc-card-overlay"></div>
        <div class="sc-card-glow"></div>
        
        <div class="sc-preview-header">
          <div class="sc-preview-icon">
            <i class="ti ti-ball"></i>
          </div>
          <span class="sc-preview-status active">
            <span class="sc-status-dot"></span>
            Active
          </span>
        </div>
        
        <h3 class="sc-preview-name">Unnamed Sport</h3>
        
        <div class="sc-preview-badges">
          <span class="sc-preview-badge">
            <i class="ti ti-building"></i> Not Set
          </span>
          <span class="sc-preview-badge">
            <i class="ti ti-user"></i> Not Set
          </span>
          <span class="sc-preview-badge">
            <i class="ti ti-user"></i> Individual
          </span>
          <span class="sc-preview-badge">
            <i class="ti ti-award"></i> Olympic
          </span>
        </div>
        
        <div class="sc-preview-metrics">
          <div class="sc-preview-metric">
            <i class="ti ti-users"></i>
            <span>Not specified</span>
          </div>
        </div>
      </div>
    `;
}

function togglePlayersSection() {
  const isTeam = document.getElementById("isTeamSport").checked;
  const playersSection = document.getElementById("playersSection");
  const minPlayers = document.getElementById("minPlayers");
  const maxPlayers = document.getElementById("maxPlayers");

  if (isTeam) {
    playersSection.style.display = "block";
    minPlayers.disabled = false;
    maxPlayers.disabled = false;
  } else {
    playersSection.style.display = "none";
    minPlayers.disabled = true;
    maxPlayers.disabled = true;
    minPlayers.value = "";
    maxPlayers.value = "";
  }
}

function updatePreview() {
  const name = document.getElementById("sportName").value || "Unnamed Sport";
  const type = document.getElementById("sportType").value;
  const gender = document.getElementById("sportGender").value;
  const isTeam = document.getElementById("isTeamSport").checked;
  const isOlympic = document.getElementById("isOlympic").checked;
  const isActive = document.getElementById("isActive").checked;

  let minPlayers = "";
  let maxPlayers = "";
  if (isTeam) {
    minPlayers = document.getElementById("minPlayers").value;
    maxPlayers = document.getElementById("maxPlayers").value;
  }

  const iconFile = document.getElementById("sportIcon").files[0];
  const thumbnailFile = document.getElementById("sportThumbnail").files[0];

  const container = document.getElementById("previewContainer");

  const typeMap = {
    INDOOR: "Indoor",
    OUTDOOR: "Outdoor",
    BOTH: "Both",
  };
  const typeLabel = typeMap[type] || "Not Set";

  const typeIcon =
    type === "INDOOR"
      ? "building"
      : type === "OUTDOOR"
        ? "tree"
        : "arrows-left-right";

  const genderMap = {
    MALE: "Male",
    FEMALE: "Female",
    TRANSGENDER: "Transgender",
    NON_BINARY: "Non-binary",
    OTHER: "Other",
    PREFER_NOT_TO_SAY: "Prefer not to say",
  };
  const genderLabel = genderMap[gender] || "Not Set";

  const genderIcon =
    gender === "MALE"
      ? "gender-male"
      : gender === "FEMALE"
        ? "gender-female"
        : "user";

  const teamLabel = isTeam ? "Team" : "Individual";
  const teamIcon = isTeam ? "users" : "user";

  const olympicLabel = isOlympic ? "Olympic" : "Non-Olympic";
  const olympicIcon = isOlympic ? "award" : "award-off";

  const statusClass = isActive ? "active" : "inactive";
  const statusLabel = isActive ? "Active" : "Inactive";

  let playersText = "Not specified";
  if (isTeam) {
    if (minPlayers && maxPlayers) {
      playersText = `${minPlayers} - ${maxPlayers} players`;
    } else if (minPlayers) {
      playersText = `${minPlayers}+ players`;
    } else if (maxPlayers) {
      playersText = `Up to ${maxPlayers} players`;
    } else {
      playersText = "Players not specified";
    }
  } else {
    playersText = "Individual sport - No team size";
  }

  let iconHTML = `<i class="ti ti-ball"></i>`;

  if (iconFile) {
      const iconUrl = URL.createObjectURL(iconFile);
      iconHTML = `<img src="${iconUrl}" alt="Icon">`;
  } else if (existingIcon) {
      iconHTML = `<img src="${existingIcon}" alt="Icon">`;
  }

  let bgStyle = "background-color: #f5f7fa;";

  if (thumbnailFile) {
      const thumbUrl = URL.createObjectURL(thumbnailFile);
      bgStyle = `background-image:url('${thumbUrl}');background-size:cover;background-position:center;`;
  } else if (existingThumbnail) {
      bgStyle = `background-image:url('${existingThumbnail}');background-size:cover;background-position:center;`;
  }

  container.innerHTML = `
      <div class="sc-preview-card" style="${bgStyle}">
        <div class="sc-card-overlay"></div>
        <div class="sc-card-glow"></div>
        
        <div class="sc-preview-header">
          <div class="sc-preview-icon">
            ${iconHTML}
          </div>
          <span class="sc-preview-status ${statusClass}">
            <span class="sc-status-dot"></span>
            ${statusLabel}
          </span>
        </div>
        
        <h3 class="sc-preview-name">${name}</h3>
        
        <div class="sc-preview-badges">
          <span class="sc-preview-badge">
            <i class="ti ti-${typeIcon}"></i> ${typeLabel}
          </span>
          <span class="sc-preview-badge">
            <i class="ti ti-${genderIcon}"></i> ${genderLabel}
          </span>
          <span class="sc-preview-badge">
            <i class="ti ti-${teamIcon}"></i> ${teamLabel}
          </span>
          <span class="sc-preview-badge">
            <i class="ti ti-${olympicIcon}"></i> ${olympicLabel}
          </span>
        </div>
        
        <div class="sc-preview-metrics">
          <div class="sc-preview-metric">
            <i class="ti ti-users"></i>
            <span>${playersText}</span>
          </div>
        </div>
      </div>
    `;
}

document.addEventListener("DOMContentLoaded", function () {
  AOS.init({ duration: 600, once: true, easing: "ease-out-cubic" });

  togglePlayersSection();
  updatePreview();

  document.querySelectorAll('.ss-form-select').forEach(select => {
        new SlimSelect({
            select: select,
            settings: {
                placeholderText: select.options[0].text,
                showSearch: false
            }
        });
  });
});
const API = "http://127.0.0.1:8000";

// ── DOM refs — matching index.html IDs exactly ────────────────────────────────
const profileEl    = document.querySelector("#profile");
const companyEl    = document.querySelector("#company");
const styleEl      = document.querySelector("#style");
const genBtn       = document.querySelector("#gen");
const pdfBtn       = document.querySelector("#pdf");
const outEl        = document.querySelector("#out");
const previewFrame = document.querySelector("#preview-frame");
const previewPH    = document.querySelector("#preview-placeholder");
const historyEl    = document.querySelector("#history");
const statusEl     = document.querySelector("#status");
const activeLbl    = document.querySelector("#active-label");

// ── State ─────────────────────────────────────────────────────────────────────
let activeFilename  = null;
let previewDebounce = null;
let currentTab      = "edit";

// ── Status ────────────────────────────────────────────────────────────────────
function setStatus(msg, type = "") {
  statusEl.textContent = msg;
  statusEl.className   = "status " + type;
}

// ── Tab switcher: Edit ↔ Preview ──────────────────────────────────────────────
function switchTab(tab) {
  currentTab = tab;
  document.querySelector("#tab-edit").classList.toggle("active", tab === "edit");
  document.querySelector("#tab-preview").classList.toggle("active", tab === "preview");

  if (tab === "edit") {
    outEl.style.display           = "block";
    previewFrame.style.display    = "none";
    previewPH.style.display       = "none";
  } else {
    outEl.style.display           = "none";
    // Show frame if we have content, placeholder if not
    const hasMd = outEl.value.trim();
    previewFrame.style.display    = hasMd ? "block" : "none";
    previewPH.style.display       = hasMd ? "none" : "flex";
    if (hasMd) refreshPreview();
  }
}

// ── Live preview ──────────────────────────────────────────────────────────────
async function refreshPreview() {
  const md = outEl.value.trim();
  if (!md) return;

  try {
    const res = await fetch(`${API}/api/preview`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ md_text: md }),
    });

    if (!res.ok) return;

    const html = await res.text();
    previewFrame.srcdoc = html;
  } catch {
    // Silent fail — preview is non-critical
  }
}

// Debounce preview refresh while editing
outEl.addEventListener("input", () => {
  clearTimeout(previewDebounce);
  previewDebounce = setTimeout(() => {
    if (currentTab === "preview") refreshPreview();
  }, 600);
});

// ── Load profiles into dropdown ───────────────────────────────────────────────
async function loadProfiles() {
  try {
    const res = await fetch(`${API}/api/profiles`);
    console.log("GET /api/profiles status:", res.status);
    const data = await res.json();
    console.log("profiles response:", data);
    const profiles = data.profiles || [];

    if (!profiles.length) {
      profileEl.innerHTML = `<option value="">No profiles found</option>`;
      setStatus("⚠ No profiles found — create a folder under data/profiles/", "error");
      return;
    }

    profileEl.innerHTML = profiles.map(p =>
      `<option value="${p}">${p.replace(/_/g, " ")}</option>`
    ).join("");

    await loadHistory(profiles[0]);

  } catch (err) {
    console.error("loadProfiles failed:", err);
    profileEl.innerHTML = `<option value="">Backend not running</option>`;
    setStatus("⚠ Cannot reach backend at " + API + " — is uvicorn running?", "error");
  }
}

profileEl.addEventListener("change", async () => {
  activeFilename = null;
  activeLbl.style.display = "none";
  outEl.value = "";
  previewFrame.srcdoc = "";
  setPdfEnabled(false);
  setStatus("");
  await loadHistory(profileEl.value);
});

// ── History ───────────────────────────────────────────────────────────────────
async function loadHistory(profile) {
  if (!profile) return;
  historyEl.innerHTML = `<div class="empty-state">Loading...</div>`;

  try {
    const res  = await fetch(`${API}/api/profiles/${encodeURIComponent(profile)}`);
    const data = await res.json();
    renderHistory(data.cover_letters || [], profile);
  } catch {
    historyEl.innerHTML = `<div class="empty-state">Failed to load history</div>`;
  }
}

function renderHistory(letters, profile) {
  if (!letters.length) {
    historyEl.innerHTML = `<div class="empty-state">No cover letters yet for this profile</div>`;
    return;
  }

  historyEl.innerHTML = letters.map(l => `
    <div class="history-item" data-file="${l.filename}" data-profile="${profile}">
      <div>
        <div class="history-name">${l.filename.replace(".md", "")}</div>
        <div class="history-meta">${l.created}</div>
      </div>
      <div class="history-meta">${(l.size / 1024).toFixed(1)} KB</div>
      <button class="delete-btn" data-file="${l.filename}" data-profile="${profile}" title="Delete">✖</button>
    </div>
  `).join("");

  historyEl.querySelectorAll(".history-item").forEach(item => {
    item.addEventListener("click", () => openHistoryItem(item));
  });

  historyEl.querySelectorAll(".delete-btn").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const file = btn.dataset.file;
      const profile = btn.dataset.profile;

      if (!confirm(`Delete ${file}? This cannot be undone.`)) return;

      setStatus("Deleting...");
      try {
        const res = await fetch(`${API}/api/profiles/${encodeURIComponent(profile)}/cover_letters/${encodeURIComponent(file)}`, {
          method: "DELETE",
        });

        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          setStatus("Delete failed: " + (data.detail || res.status), "error");
          return;
        }

        setStatus(`Deleted ${file}`, "success");

        if (activeFilename === file) {
          activeFilename = null;
          activeLbl.style.display = "none";
          outEl.value = "";
          setPdfEnabled(false);
        }

        await loadHistory(profile);
      } catch (err) {
        setStatus("Delete failed", "error");
      }
    });
  });
}

async function openHistoryItem(item) {
  const file    = item.dataset.file;
  const profile = item.dataset.profile;

  historyEl.querySelectorAll(".history-item").forEach(i => i.classList.remove("active"));
  item.classList.add("active");

  setStatus("Loading...");
  try {
    const res  = await fetch(`${API}/api/profiles/${encodeURIComponent(profile)}/cover_letters/${encodeURIComponent(file)}`);
    const data = await res.json();

    outEl.value = data.md;
    activeFilename = file;
    activeLbl.textContent   = file.replace(".md", "");
    activeLbl.style.display = "inline-block";
    setPdfEnabled(true);
    setStatus(`Loaded: ${file}`, "success");

    // Refresh preview if on preview tab
    if (currentTab === "preview") refreshPreview();
  } catch {
    setStatus("Failed to load cover letter", "error");
  }
}

// ── Generate ──────────────────────────────────────────────────────────────────
genBtn.addEventListener("click", async () => {
  const profile = profileEl.value;
  const company = companyEl.value.trim();
  const style   = styleEl.value;

  if (!profile) { setStatus("Please select a profile", "error"); return; }
  if (!company) { setStatus("Please enter a company name", "error"); return; }

  genBtn.disabled    = true;
  genBtn.textContent = "Generating...";
  setStatus("Calling Gemini API...");

  try {
    const res = await fetch(`${API}/api/generate`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ profile, company, style }),
    });

    const data = await res.json();

    if (!res.ok) {
      setStatus("Error: " + (data.detail || "Generate failed"), "error");
      return;
    }

    outEl.value = data.md;
    activeFilename = data.filename;
    activeLbl.textContent   = data.filename.replace(".md", "");
    activeLbl.style.display = "inline-block";
    setPdfEnabled(true);
    setStatus(`✓ Saved as ${data.filename}`, "success");

    // Auto-switch to edit tab so user can review immediately
    switchTab("edit");
    await loadHistory(profile);

  } catch {
    setStatus("Backend not running or blocked by CORS", "error");
  } finally {
    genBtn.disabled    = false;
    genBtn.textContent = "Generate Cover Letter";
  }
});

// ── PDF download ──────────────────────────────────────────────────────────────
pdfBtn.addEventListener("click", async () => {
  const md_text = outEl.value.trim();
  if (!md_text) { setStatus("Generate a cover letter first", "error"); return; }

  setStatus("Generating PDF...");
  setPdfEnabled(false);

  try {
    const res = await fetch(`${API}/api/pdf`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ md_text }),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setStatus("PDF error: " + (data.detail || "failed"), "error");
      return;
    }

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = (activeFilename || "cover_letter").replace(".md", "") + ".pdf";
    a.click();
    URL.revokeObjectURL(url);
    setStatus("✓ PDF downloaded", "success");

  } catch {
    setStatus("PDF generation failed", "error");
  } finally {
    setPdfEnabled(true);
  }
});

function setPdfEnabled(enabled) {
  pdfBtn.disabled = !enabled;
}

// ── Init ──────────────────────────────────────────────────────────────────────
setPdfEnabled(false);
loadProfiles();
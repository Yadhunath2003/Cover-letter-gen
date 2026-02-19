const API = "http://127.0.0.1:8000";

// ── State ────────────────────────────────────────────────────────────────────
let currentProfile = null;
let activeHistoryItem = null;

// ── DOM refs ─────────────────────────────────────────────────────────────────
const profileEl   = document.querySelector("#profile");
const companyEl   = document.querySelector("#company");
const styleEl     = document.querySelector("#style");
const genBtn      = document.querySelector("#gen");
const pdfBtn      = document.querySelector("#pdf");
const outEl       = document.querySelector("#out");
const historyEl   = document.querySelector("#history");
const statusEl    = document.querySelector("#status");
const activeLbl   = document.querySelector("#active-label");

// ── Helpers ───────────────────────────────────────────────────────────────────
function setStatus(msg, type = "") {
  statusEl.textContent = msg;
  statusEl.className   = "status " + type;
}

function clearStatus() { setStatus(""); }

// ── Load profiles into dropdown ───────────────────────────────────────────────
async function loadProfiles() {
  try {
    const res  = await fetch(`${API}/api/profiles`);
    const data = await res.json();
    const profiles = data.profiles || [];

    profileEl.innerHTML = profiles.length
      ? profiles.map(p => `<option value="${p}">${p}</option>`).join("")
      : `<option value="">No profiles found</option>`;

    if (profiles.length) {
      currentProfile = profiles[0];
      await loadHistory(currentProfile);
    }
  } catch {
    profileEl.innerHTML = `<option value="">Backend not running</option>`;
    setStatus("⚠ Cannot reach backend at " + API, "error");
  }
}

// ── Load history for selected profile ────────────────────────────────────────
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

// ── Render history list ───────────────────────────────────────────────────────
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
    </div>
  `).join("");

  historyEl.querySelectorAll(".history-item").forEach(item => {
    item.addEventListener("click", () => openHistoryItem(item));
  });
}

// ── Open a saved cover letter from history ────────────────────────────────────
async function openHistoryItem(item) {
  const file    = item.dataset.file;
  const profile = item.dataset.profile;

  // Highlight active
  historyEl.querySelectorAll(".history-item").forEach(i => i.classList.remove("active"));
  item.classList.add("active");
  activeHistoryItem = file;

  setStatus("Loading...");
  try {
    const res  = await fetch(`${API}/api/profiles/${encodeURIComponent(profile)}/cover_letters/${encodeURIComponent(file)}`);
    const data = await res.json();
    outEl.value = data.md;
    activeLbl.textContent = file.replace(".md", "");
    activeLbl.style.display = "inline-block";
    clearStatus();
  } catch {
    setStatus("Failed to load cover letter", "error");
  }
}

// ── Profile change handler ────────────────────────────────────────────────────
profileEl.addEventListener("change", async () => {
  currentProfile   = profileEl.value;
  activeHistoryItem = null;
  activeLbl.style.display = "none";
  outEl.value = "";
  clearStatus();
  await loadHistory(currentProfile);
});

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
    activeLbl.textContent  = data.filename.replace(".md", "");
    activeLbl.style.display = "inline-block";
    setStatus(`✓ Saved as ${data.filename}`, "success");

    // Refresh history so the new file appears
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
    a.download = (activeLbl.textContent || "coverletter") + ".pdf";
    a.click();
    URL.revokeObjectURL(url);
    setStatus("✓ PDF downloaded", "success");
  } catch {
    setStatus("PDF generation failed", "error");
  }
});

// ── Init ──────────────────────────────────────────────────────────────────────
loadProfiles();
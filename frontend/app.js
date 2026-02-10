const API = "http://127.0.0.1:8000";

document.querySelector("#gen").addEventListener("click", async () => {
  const style = document.querySelector("#style").value;

  const btn = document.querySelector("#gen");
  btn.disabled = true;
  btn.textContent = "Generating...";

  try {
    // Don't send resume_md or jd_text - let backend read from data folder
    const res = await fetch(`${API}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ style })
    });

    const data = await res.json();
    if (!res.ok) {
      alert(data.detail || "Generate failed");
      return;
    }

    document.querySelector("#out").value = data.md;
  } catch (e) {
    alert("Backend not running or blocked by CORS. Make sure the backend is running on http://127.0.0.1:8000");
  } finally {
    btn.disabled = false;
    btn.textContent = "Generate Cover Letter";
  }
});

document.querySelector("#pdf").addEventListener("click", async () => {
  const md_text = document.querySelector("#out").value.trim();
  if (!md_text) {
    alert("Generate a cover letter first.");
    return;
  }

  const res = await fetch(`${API}/api/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ md_text })
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    alert(data.detail || "PDF failed");
    return;
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "coverletter.pdf";
  a.click();

  URL.revokeObjectURL(url);
});